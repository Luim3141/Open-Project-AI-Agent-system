import json
import os
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import nullcontext

import httpx
from gateway.agent_trace import bind_run, bind_proposal, reset_run, trace_event, current_run
from gateway.gemini import Gemini
from gateway.native import Native
from gateway.store import Store
from tests import test_agent_queue as fixture


class AgentTraceTests(unittest.TestCase):
    def test_proposal_trace_requires_own_review_run_and_stored_proposal_link(self):
        import uuid
        proposal={'id':str(uuid.uuid4()),'command':{'_origin_run_id':self.identifier}}
        with self.assertRaises(PermissionError):bind_proposal(self.store,7,3,proposal)
        self.store.finish_run(7,self.identifier,{'status':'proposed','text':'Synthetic draft',
            'tools':[{'result':{'result':{'id':proposal['id']}}}]},'done')
        for actor,project in ((8,3),(7,4)):
            with self.assertRaises(PermissionError):bind_proposal(self.store,actor,project,proposal)
        with self.assertRaises(PermissionError):
            bind_proposal(self.store,7,3,{**proposal,'id':str(uuid.uuid4())})
        token=bind_proposal(self.store,7,3,proposal)
        try:
            self.assertEqual(current_run.get()[1].run_id,self.identifier)
            self.store.record(7,'knowledge_ingest',12,'ok')
        finally:reset_run(token)
        self.assertIsNone(current_run.get())
        self.assertEqual(self.rows()[-1]['trace_id'],self.response['correlation_id'])

    def setUp(self):
        self.fixture = fixture.AgentQueueTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.store = self.fixture.store
        self.task = self.fixture.task(instruction="Synthetic PRIVATE_PROMPT_NOT_FOR_TRACE")
        self.response = self.fixture.enqueue(self.task)
        self.identifier = self.response["result"]["id"]
        self.run = self.store.claim_run()

    def rows(self):
        with self.store.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY at,id")]

    def test_runtime_gateway_native_provider_share_ids_and_exclude_payload(self):
        token = bind_run(self.store, 7, 3, self.identifier)
        try:
            self.store.record(7, "analyze", "qldapm-local", "ok")
            self.store.record(7, "get_work_package", "PRIVATE_INVALID_ID_NOT_FOR_TRACE", "ValueError", version="PRIVATE_VERSION_NOT_FOR_TRACE")
            native = Native("http://localhost", "SYNTHETIC_API_KEY_NOT_FOR_TRACE", 3)
            response = httpx.Response(200, json={"synthetic": True}, request=httpx.Request("GET", "http://localhost/api/v3/projects/3"))
            with patch("gateway.native.httpx.stream", return_value=nullcontext(response)):
                self.assertTrue(native.call("/api/v3/projects/3")["synthetic"])
            sdk = SimpleNamespace(models=SimpleNamespace(count_tokens=Mock(side_effect=RuntimeError("synthetic stop before outbound"))))
            with self.assertRaises(RuntimeError):
                Gemini(self.store.root).sdk_post((sdk, SimpleNamespace()), {}, "countTokens", {"generateContentRequest": {"contents": []}})
        finally:
            reset_run(token)
        self.store.finish_run(7, self.identifier, {"status": "answered", "text": "Synthetic result", "tools": []}, "done")
        rows = self.rows()
        self.assertTrue({"start_ai_run", "agent_run_state", "analyze", "trace_native", "trace_provider"} <= {r["action"] for r in rows})
        for row in rows:
            self.assertEqual((row["actor"], row["project_id"], row["task_id"], row["run_id"], row["trace_id"]),
                (7, 3, self.task.task_id, self.identifier, self.response["correlation_id"]))
        serialized = json.dumps(rows)
        self.assertNotIn("PRIVATE_PROMPT_NOT_FOR_TRACE", serialized)
        self.assertNotIn("SYNTHETIC_API_KEY_NOT_FOR_TRACE", serialized)
        self.assertNotIn("/api/v3/", serialized)
        self.assertNotIn("PRIVATE_INVALID_ID_NOT_FOR_TRACE", serialized)
        self.assertNotIn("PRIVATE_VERSION_NOT_FOR_TRACE", serialized)
        self.assertIsNone(current_run.get())

    def test_scope_state_and_payload_labels_are_not_model_authority(self):
        for actor, project in ((8, 3), (7, 4)):
            with self.assertRaises(PermissionError):
                bind_run(self.store, actor, project, self.identifier)
        for layer, event in (("shell", "GET"), ("provider", "PRIVATE PROMPT"), ("native", "Bearer_secret=secret")):
            with self.assertRaises(ValueError):
                trace_event(layer, event)
        self.store.finish_run(7, self.identifier, {"tools": []}, "done")
        with self.assertRaises(PermissionError):
            bind_run(self.store, 7, 3, self.identifier)

    def test_different_actor_store_and_unbound_legacy_events_do_not_inherit_scope(self):
        token = bind_run(self.store, 7, 3, self.identifier)
        try:
            self.store.record(8, "identity", "qldapm-local", "ok")
            other = Store(self.store.root / "other")
            other.record(7, "identity", "qldapm-local", "ok")
            with other.connect() as db:
                self.assertIsNone(db.execute("SELECT trace_id FROM audit").fetchone()[0])
        finally:
            reset_run(token)
        self.store.record(7, "identity", "legacy", "ok")
        for row in self.rows():
            if row["action"] == "identity":
                self.assertIsNone(row["trace_id"])
        self.assertIsNone(current_run.get())

    def test_actual_child_process_loads_scope_without_model_trace_or_provider_call(self):
        (self.store.root / "config.json").write_text(json.dumps({"gateway_mode": "native", "project_id": 3, "users": {"7": "PM"}}))
        (self.store.root / "gemini.json").write_text('{"enabled":false}')
        payload = {"root": str(self.store.root), "workspaces": str(self.store.root / "workspaces"), "actor": 7,
            "prompt": "Synthetic private worker", "id": self.identifier, "allow_routine_writes": False, "write_scope_ids": []}
        result = subprocess.run([sys.executable, "-m", "gateway.ai_worker"], input=json.dumps(payload), capture_output=True, text=True,
            timeout=20, env={**os.environ, "QLDAPM_AI_ENVIRONMENT": "staging", "QLDAPM_GEMINI_FREE_PROOF": str(self.store.root / "absent-proof.json")})
        self.assertEqual(result.returncode, 0)
        self.assertIn("DISABLED", json.loads(result.stdout)["error"])
        worker = [row for row in self.rows() if row["action"] == "trace_worker"]
        self.assertEqual(len(worker), 1)
        self.assertEqual(worker[0]["trace_id"], self.response["correlation_id"])
        self.assertNotIn("Synthetic private worker", json.dumps(worker))

    def test_legacy_execution_and_original_audit_fields_remain_compatible(self):
        token = bind_run(self.store, 7, 3, "legacy-run-without-agent-metadata")
        try:
            trace_event("native", "GET")
            self.store.record(7, "identity", "legacy", "ok", version="lock-version-1")
        finally:
            reset_run(token)
        row = next(r for r in self.rows() if r["target"] == "legacy")
        self.assertEqual(row["version"], "lock-version-1")
        self.assertIsNone(row["trace_id"])
        self.assertFalse(any(r["action"] == "trace_native" for r in self.rows()))


if __name__ == "__main__":
    unittest.main()

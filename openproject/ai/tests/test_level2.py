import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from starlette.testclient import TestClient

from gateway.app import create_app
from gateway.gemini import Gemini, ProviderError, SMOKE_PROMPT
from gateway.native import NativeError
from gateway.service import Service
from gateway.store import Store


class NativeFixture:
    calls = []
    item = {"id": 12, "lockVersion": 1, "subject": "Fixture", "percentageDone": 0, "dueDate": "2020-01-01",
            "_links": {"project": {"href": "/api/v3/projects/5"}, "status": {"href": "/api/v3/statuses/1", "title": "NEW"}}}

    def __init__(self, *args): pass
    def identity(self, actor): return {"user_id": actor, "role": "PM", "project_id": 5}
    def package(self, identifier): return json.loads(json.dumps(self.item))
    def packages(self): return [self.package(12)]
    def call(self, path, method="GET", payload=None):
        self.calls.append((path, method, payload))
        if path.endswith('/form'):
            return {'_embedded': {'payload': {**self.item, **payload}, 'validationErrors': {}}}
        if method == "PATCH":
            self.item.update({key: value for key, value in payload.items() if key not in {"lockVersion", "_links"}})
            self.item["lockVersion"] += 1
            self.item["dueDate"] = payload.get("dueDate", self.item["dueDate"])
            self.item["_links"].update(payload.get("_links", {}))
            return self.package(12)
        raise NativeError(404, "OPENPROJECT_404")


class Level2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root)
        self.token = self.store.issue_token(7, "PM", "synthetic-native")
        self.config = {"users": {"7": "PM"}, "gateway_mode": "native", "project_id": 5,
            "openproject_url": "http://127.0.0.1:18091", "hosts": ["testserver"], "status_ids": [1, 2]}
        NativeFixture.calls = []
        NativeFixture.item["lockVersion"] = 1
        NativeFixture.item["dueDate"] = "2020-01-01"
        self.service = Service(self.store, self.config, self.root / "workspaces", NativeFixture)

    def execute(self, action, arguments=None, key="fixture", **extra):
        return self.service.execute(self.token, {"action": action, "arguments": arguments or {}, "idempotency_key": key, **extra})

    def test_native_patch_replay_readback_no_custom_capability_and_stale_lock(self):
        args = {"id": 12, "lock_version": 1, "changes": {"description": "Fixture description", "due_date": "2026-10-20", "priority_id": 3}}
        proposal = self.execute("update_work_package", args)["result"]
        result = self.service.confirm(7, proposal["id"], proposal["hash"])
        self.assertEqual(result["result"]["lockVersion"], 2)
        self.assertEqual(self.store.request_status(7, "proposal-" + proposal["id"])["result"], result)
        with self.assertRaisesRegex(ValueError, "CONSUMED"):
            self.service.confirm(7, proposal["id"], proposal["hash"])
        self.assertEqual(sum(method == "PATCH" for _, method, _ in NativeFixture.calls), 1)
        path, method, payload = NativeFixture.calls[-1]
        self.assertEqual((path, method), ("/api/v3/work_packages/12", "PATCH"))
        self.assertEqual(payload["description"], {"format": "markdown", "raw": "Fixture description"})
        self.assertEqual(payload["dueDate"], "2026-10-20")
        self.assertEqual(payload["_links"]["priority"]["href"], "/api/v3/priorities/3")
        with self.assertRaisesRegex(ValueError, "STALE"):
            self.execute("update_work_package", args, key="stale")
        self.assertEqual(sum(method == "PATCH" for _, method, _ in NativeFixture.calls), 1)

    def test_native_custom_gate_and_auto_privileged_operations_are_denied_before_write(self):
        for action in ("get_gate", "change_gate"):
            with self.assertRaisesRegex(ValueError, "CUSTOM_GATE_UNSUPPORTED"):
                self.execute(action, {"id": 12})
        # Native business mode now fences operator access even before the auto-execute check.
        with self.assertRaisesRegex(PermissionError, "NATIVE_BUSINESS_OPERATOR_TOOL_DENIED"):
            self.execute("propose_operation", {"operation": "release", "parameters": {}}, auto_execute=True)
        self.assertEqual(NativeFixture.calls, [])

    def test_reject_actor_hash_and_consumption_prevent_confirmation(self):
        result = self.execute("transition", {"id": 12, "lock_version": 1, "status_id": 2})["result"]
        with self.assertRaisesRegex(ValueError, "CONSUMED"):
            self.store.reject_proposal(8, result["id"], result["hash"])
        with self.assertRaisesRegex(ValueError, "CONSUMED"):
            self.store.reject_proposal(7, result["id"], "wrong")
        rejected = self.execute("reject_proposal", {"id": result["id"], "hash": result["hash"]}, key="reject")
        self.assertEqual(rejected["result"]["state"], "rejected")
        with self.assertRaisesRegex(ValueError, "CONSUMED"):
            self.service.confirm(7, result["id"], result["hash"])
        self.assertEqual(NativeFixture.calls, [])
        self.store.record(8, "other", 12, "ok")
        self.assertTrue(all(row["actor"] == 7 for row in self.execute("get_action_history")["result"]["audit"]))

    def test_proposal_cannot_be_confirmed_under_a_different_gateway_mode(self):
        proposal = self.execute("transition", {"id": 12, "lock_version": 1, "status_id": 2})["result"]
        self.service.mode = "strict"
        with self.assertRaisesRegex(PermissionError, "MODE_CHANGED"):
            self.service.confirm(7, proposal["id"], proposal["hash"])
        self.assertEqual(self.store.proposal(7, proposal["id"])["state"], "pending")
        self.assertEqual(NativeFixture.calls, [])

    def test_read_query_overdue_and_status_work_without_provider(self):
        result = self.execute("analyze", {"query": "fixTURE"})["result"]
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["overdue_ids"], [12])
        self.assertEqual(self.execute("analyze", {"query": "absent"})["result"]["count"], 0)
        status = self.execute("get_assistant_status")["result"]
        self.assertEqual(status["gateway_mode"], "native")
        self.assertEqual(status["gemini"]["state"], "BLOCKED_KEY_OR_MODEL")
        self.assertFalse(status["native_reporting"]["model_used"])

    def test_strict_default_still_denies_official_core_and_bad_mode_fails_closed(self):
        self.config.pop("gateway_mode")
        service = Service(self.store, self.config, self.root / "workspaces", NativeFixture)
        with self.assertRaisesRegex(NativeError, "CORE_GATES_NOT_ACTIVATED"):
            service.execute(self.token, {"action": "comment", "arguments": {}, "idempotency_key": "strict"})
        self.config["gateway_mode"] = "typo"
        with self.assertRaisesRegex(ValueError, "MODE_INVALID"):
            Service(self.store, self.config, self.root / "workspaces", NativeFixture)

    def test_role_assignment_requires_unique_registered_current_native_role(self):
        self.assertEqual(self.service.role_assignee("PM"), 7)
        with self.assertRaisesRegex(ValueError, "MISSING"):
            self.service.role_assignee("BE")
        self.config["users"]["8"] = "PM"
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS"):
            self.service.role_assignee("PM")
        self.config["users"]["7"] = "BA"
        with self.assertRaisesRegex(PermissionError, "ROLE_CHANGED"):
            self.service.role_assignee("BA")

    def test_sdk_continuation_is_disabled_and_response_body_is_bounded(self):
        (self.root / "gemini.key").write_text("synthetic")
        policy = {"data_scope": "synthetic-smoke-only", "project": "synthetic",
                  "limits": {"rpm": 20, "tpm": 10000, "rpd": 100}}
        calls = []
        def wire(request):
            calls.append(str(request.url))
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 10})
            return httpx.Response(200, json={"candidates": [{"finishReason": "CONTINUATION",
                "continuationToken": "c3ludGhldGlj", "content": {"role": "model", "parts": [{"text": "partial"}]}}]})
        with patch.object(Gemini, "settings", return_value=policy), self.assertRaisesRegex(ProviderError, "INCOMPLETE"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(wire), actor_role="PM")
        self.assertEqual(len(calls), 2)
        with patch.object(Gemini, "settings", return_value=policy), self.assertRaisesRegex(ProviderError, "RESPONSE_LIMIT"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: httpx.Response(200, content=b"x" * 65537)), actor_role="PM")

    def test_sdk_decodes_gzip_response_once(self):
        import gzip
        (self.root / "gemini.key").write_text("synthetic")
        policy = {"data_scope": "synthetic-smoke-only", "project": "synthetic",
                  "limits": {"rpm": 20, "tpm": 10000, "rpd": 100}}
        def wire(request):
            document = {"totalTokens": 10} if request.url.path.endswith(":countTokens") else {
                "candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": [{"text": "QLDAPM_OK"}]}}]}
            return httpx.Response(200, headers={"Content-Encoding": "gzip", "Content-Type": "application/json"},
                                  content=gzip.compress(json.dumps(document).encode()))
        with patch.object(Gemini, "settings", return_value=policy):
            self.assertEqual(Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(wire), actor_role="PM")["text"], "QLDAPM_OK")

    def test_distinct_503_sources_and_no_success_mask(self):
        headers = {"Authorization": "Bearer " + self.token}
        with TestClient(create_app(self.root, self.service)) as client:
            for error, source in ((NativeError(503, "OPENPROJECT_503"), "openproject"),
                                  (NativeError(503, "CORE_GATES_NOT_VERIFIED"), "gateway"),
                                  (ProviderError("GEMINI_UPSTREAM_REJECTED; HTTP=503"), "gemini")):
                with patch.object(self.service, "execute", side_effect=error):
                    response = client.post("/api/v1/commands", headers=headers, json={"action": "identity"})
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(response.json()["source"], source)

    def test_run_write_consent_requires_native_and_positive_integer_scope_ids(self):
        with patch.object(Gemini, "validate_prompt"), patch.object(Gemini, "settings", return_value={}):
            self.service.mode = "strict"
            with self.assertRaisesRegex(PermissionError, "CONSENT_REQUIRES_NATIVE"):
                self.execute("start_ai_run", {"prompt": "synthetic", "allow_routine_writes": True})
            self.service.mode = "native"
            with self.assertRaisesRegex(ValueError, "RUN_WRITE_SCOPE_POSITIVE_IDS"):
                self.execute("start_ai_run", {"prompt": "synthetic", "allow_routine_writes": True, "write_scope_ids": [True]}, key="bad-scope")
        self.assertEqual(self.store.history(7)["runs"], [])

    def test_confirmed_write_projection_does_not_send_ticket_text_or_assignee(self):
        item = {**NativeFixture.item, "subject": "synthetic-private-text", "description": {"raw": "synthetic-private-code"}}
        projected = Gemini.metadata_result("create_work_package", {"result": item})
        self.assertTrue(projected["result"]["native_confirmed"])
        self.assertNotIn("synthetic-private", json.dumps(projected))
        comment = Gemini.metadata_result("comment", {"result": {"id": 20, "_type": "Activity::Comment", "comment": {"raw": "synthetic-private"}}})
        self.assertEqual(comment, {"result": {"id": 20, "native_confirmed": True}})

    def test_sdk_quota_timeout_and_continuation_have_no_hidden_retry_or_tools(self):
        (self.root / "gemini.key").write_text("synthetic")
        policy = {"data_scope": "synthetic-smoke-only", "model": "gemini-fixture-model", "project": "synthetic",
                  "limits": {"rpm": 20, "tpm": 10000, "rpd": 100}}
        calls = []
        def wire(request):
            calls.append(str(request.url))
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 10})
            return httpx.Response(429, json={"error": {"status": "RESOURCE_EXHAUSTED", "message": "synthetic-secret"}})
        with patch.object(Gemini, "settings", return_value=policy), self.assertRaisesRegex(ProviderError, "HTTP=429") as caught:
            Gemini(self.root).run(SMOKE_PROMPT, lambda *a: self.fail("No tools"), httpx.MockTransport(wire), actor_role="PM")
        self.assertEqual(len(calls), 2)
        self.assertEqual(caught.exception.status, 429)
        self.assertNotIn("synthetic-secret", str(caught.exception))
        self.assertTrue(all("gemini-fixture-model" in url for url in calls))
        # The same circuit survives a new Service/SDK instance and prevents another outbound request.
        with patch.object(Gemini, "settings", return_value=policy), self.assertRaisesRegex(ProviderError, "CIRCUIT_OPEN"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: self.fail("No retry")), actor_role="PM")


if __name__ == "__main__":
    unittest.main()

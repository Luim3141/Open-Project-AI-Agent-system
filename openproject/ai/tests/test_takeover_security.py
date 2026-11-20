"""Offline security regressions. Synthetic Native API; never Main acceptance evidence."""
import concurrent.futures
import json
import tempfile
import threading
import unittest
from pathlib import Path

from gateway.native import NativeError
from gateway.service import Service
from gateway.store import Store, canonical


class NativeFixture:
    def __init__(self, url, credential, project):
        self.role = credential

    def identity(self, actor):
        return {"user_id": actor, "role": self.role, "project_id": 5}

    def package(self, identifier):
        return {"id": identifier, "lockVersion": 1, "subject": "Synthetic fixture", "_links": {}}


class ApprovalBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = Store(self.root)
        self.pm = self.store.issue_token(7, "PM", "PM")
        self.ba = self.store.issue_token(8, "BA", "BA")
        self.service = Service(self.store, {"users": {"7": "PM", "8": "BA"}, "project_id": 5,
            "gateway_mode": "native", "openproject_url": "http://127.0.0.1:8088"}, self.root / "workspaces", NativeFixture)
        self.writes = []
        # Record execution at the Native boundary without any network or real business data.
        def perform(who, native, action, arguments, key=None):
            # This fixture has no ingestion source; the real RAG worker is tested with a complete Native fixture elsewhere.
            if action == 'knowledge_ingest':raise NativeError(503,'ISOLATED_NATIVE_INGEST_SOURCE_UNAVAILABLE')
            self.writes.append((who["user_id"], action, arguments, key))
            return {"id": arguments["id"], "lockVersion": 2}
        self.service.perform = perform

    def proposal(self, **extra):
        command = {"action": "update_work_package", "arguments": {"id": 12, "lock_version": 1,
            "changes": {"subject": "Reviewed change"}}, "idempotency_key": "request-one", **extra}
        return self.service.execute(self.pm, command)["result"]

    def confirm(self, proposal):
        return self.service.confirm(7, proposal["id"], proposal["hash"])

    def test_no_approval_produces_preview_without_write(self):
        self.assertEqual(self.proposal()["state"], "pending")
        self.assertEqual(self.writes, [])

    def test_auto_execute_cannot_bypass_approval(self):
        with self.assertRaisesRegex(PermissionError, "PM_APPROVAL_REQUIRED"):
            self.proposal(auto_execute=True)
        self.assertEqual(self.writes, [])

    def test_ba_cannot_impersonate_pm(self):
        with self.assertRaises(PermissionError):
            self.service.execute(self.ba, {"action": "update_work_package", "arguments": {
                "id": 12, "actor_id": 7, "role": "PM", "approved": True}, "auto_execute": True})
        self.assertEqual(self.writes, [])

    def test_rejected_and_expired_are_not_executable(self):
        proposal = self.proposal()
        self.store.reject_proposal(7, proposal["id"], proposal["hash"])
        with self.assertRaises(ValueError):
            self.confirm(proposal)
        with self.store.connect() as db:
            db.execute("UPDATE proposals SET state='pending',expires=0 WHERE id=?", (proposal["id"],))
        with self.assertRaises(ValueError):
            self.confirm(proposal)
        self.assertEqual(self.writes, [])

    def test_wrong_actor_and_forged_hash_are_not_executable(self):
        proposal = self.proposal()
        with self.assertRaises(PermissionError):
            self.service.confirm(8, proposal["id"], proposal["hash"])
        with self.assertRaises(ValueError):
            self.service.confirm(7, proposal["id"], "forged")
        self.assertEqual(self.writes, [])

    def test_stored_payload_tampering_is_detected(self):
        proposal = self.proposal()
        changed = json.loads(json.dumps(proposal["command"]))
        changed["arguments"]["changes"]["subject"] = "Unreviewed change"
        with self.store.connect() as db:
            db.execute("UPDATE proposals SET payload=? WHERE id=?", (canonical(changed), proposal["id"]))
        with self.assertRaisesRegex(ValueError, "PROPOSAL_PAYLOAD_CHANGED"):
            self.confirm(proposal)
        self.assertEqual(self.writes, [])

    def test_policy_is_revalidated_at_confirmation(self):
        proposal = self.proposal()
        self.service.config["users"]["7"] = "BA"
        with self.assertRaises(PermissionError):
            self.confirm(proposal)
        self.assertEqual(self.writes, [])

    def test_stale_lock_is_revalidated_at_confirmation(self):
        proposal = self.proposal()
        self.service.perform = Service.perform.__get__(self.service)
        original = NativeFixture.package
        NativeFixture.package = lambda *_: {"id": 12, "lockVersion": 2}
        self.addCleanup(setattr, NativeFixture, "package", original)
        with self.assertRaisesRegex(ValueError, "STALE_WORK_PACKAGE"):
            self.confirm(proposal)
        self.assertEqual(self.store.proposal(7, proposal["id"])["state"], "failed_or_unknown")

    def test_concurrent_confirmation_and_replay_execute_once(self):
        proposal = self.proposal()
        barrier = threading.Barrier(2)
        def execute():
            barrier.wait()
            try:
                self.confirm(proposal)
                return "executed"
            except ValueError:
                return "denied"
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            outcomes = list(pool.map(lambda _: execute(), range(2)))
        self.assertCountEqual(outcomes, ["executed", "denied"])
        self.assertEqual(len(self.writes), 1)
        with self.assertRaises(ValueError):
            self.confirm(proposal)

    def test_network_failure_after_write_does_not_retry(self):
        proposal = self.proposal()
        def uncertain(*args):
            self.writes.append("remote write succeeded; response lost")
            raise NativeError(503, "READBACK_OUTCOME_UNKNOWN")
        self.service.perform = uncertain
        with self.assertRaises(NativeError):
            self.confirm(proposal)
        with self.assertRaises(ValueError):
            self.confirm(proposal)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.store.proposal(7, proposal["id"])["state"], "failed_or_unknown")

    def test_rest_decision_requires_authenticated_pm_and_exact_payload(self):
        from gateway.app import create_app
        from starlette.testclient import TestClient
        self.config = {**self.service.config, "hosts": ["testserver"]}
        (self.root / "config.json").write_text(json.dumps(self.config))
        proposal = self.proposal()
        path = f"/api/v1/proposals/{proposal['id']}/decision"
        payload = {"decision": "approve", "hash": proposal["hash"]}
        with TestClient(create_app(self.root, self.service)) as client:
            self.assertEqual(client.post(path, json=payload).status_code, 401)
            self.assertEqual(client.post(path, json=payload, headers={"Authorization": "Bearer " + self.ba}).status_code, 403)
            headers = {"Authorization": "Bearer " + self.pm}
            self.assertEqual(client.post(path, json={**payload, "actor_id": 7, "approved": True}, headers=headers).status_code, 409)
            self.assertEqual(self.writes, [])
            self.assertEqual(client.post(path, json=payload, headers=headers).status_code, 200)
            self.assertEqual(client.post(path, json=payload, headers=headers).status_code, 409)
        self.assertEqual(len(self.writes), 1)


if __name__ == "__main__":
    unittest.main()

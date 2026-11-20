import tempfile
import unittest
from pathlib import Path

from gateway.store import Store
from gateway.workspace import Workspace
from gateway.app import create_app
from gateway.service import Service
from gateway.native import Native, NativeError
from starlette.testclient import TestClient


class AuthenticationTests(unittest.TestCase):
    def test_maintenance_preserves_health_but_fences_rest_mcp_and_ui(self):
        with tempfile.TemporaryDirectory() as directory:
            import json
            config = {"users": {}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088",
                      "hosts": ["testserver"], "maintenance": True}
            Path(directory, "config.json").write_text(json.dumps(config))
            with TestClient(create_app(directory)) as client:
                self.assertEqual(client.get("/health").status_code, 200)
                self.assertEqual(client.get("/health").json(), {"status": "ok"})
                for route in ("/api/v1/commands", "/mcp", "/internal/ui"):
                    response = client.post(route, json={})
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(response.json()["error"], "MAINTENANCE")
                    self.assertEqual(response.headers['retry-after'],'15')
                    self.assertEqual(response.headers['x-qldapm-maintenance'],'true')
                    self.assertIn('gateway;dur=',response.headers['server-timing'])
                    self.assertEqual(len(response.headers['x-qldapm-request-id']),36)
                self.assertEqual(client.get("/health", headers={"Host": "evil.invalid"}).status_code, 403)
                self.assertEqual(client.get("/health", headers={"Origin": "https://evil.invalid"}).status_code, 403)

    def test_legacy_core_capability_cannot_enable_new_ai_business_writes(self):
        class LegacyCore:
            def __init__(self, *args): pass
            def identity(self, actor): return {"user_id": actor, "role": "PM", "project_id": 5}
            def call(self, path):
                assert path == "/api/v3/qldapm/capabilities"
                return {"project_id": 5, "gate_schema": 1, "enforced": True}
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            token = store.issue_token(22, "PM", "synthetic-only")
            service = Service(store, {"users": {"22": "PM"}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088"},
                              Path(folder) / "workspaces", LegacyCore)
            with self.assertRaisesRegex(NativeError, "NOT_VERIFIED"):
                service.execute(token, {"action": "create_work_package", "arguments": {}, "idempotency_key": "legacy"})

    def test_test_request_queues_before_snapshot_and_replay_returns_same_job(self):
        class OpenProjectFixture:
            def __init__(self, *args): pass
            def identity(self, expected): return {"user_id": expected, "role": "PM", "project_id": 5}
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            token = store.issue_token(20, "PM", "synthetic-only")
            service = Service(store, {"users": {"20": "PM", "21": "BE"}, "project_id": 5,
                "openproject_url": "http://127.0.0.1:8088"}, Path(directory) / "workspaces", OpenProjectFixture)
            command = {"action": "request_test", "arguments": {"suite": "gate-policy", "workspace_actor": 21},
                       "idempotency_key": "queued-test"}
            result = service.execute(token, command)
            self.assertEqual(result["result"]["state"], "queued")
            self.assertEqual(result["result"]["payload"]["snapshot_hash"], "AT_EXECUTION")
            self.assertEqual(service.execute(token, command), result)

    def test_native_role_change_is_audited_and_audit_metadata_is_bounded(self):
        class ChangedRole:
            def __init__(self, *args): pass
            def identity(self, expected): return {"user_id": expected, "role": "PM"}
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            token = store.issue_token(7, "FE", "synthetic-only")
            service = Service(store, {"users": {"7": "FE"}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088"},
                              Path(directory) / "workspaces", ChangedRole)
            with self.assertRaisesRegex(PermissionError, "ROLE_CHANGED"):
                service.execute(token, {"action": "identity"})
            store.record(7, "test", "x" * 1000, "denied", version="y" * 1000)
            with store.connect() as db:
                audit = db.execute("SELECT * FROM audit ORDER BY at").fetchall()
                self.assertEqual(audit[0]["actor"], 7)
                self.assertEqual(audit[0]["outcome"], "PermissionError")
                self.assertEqual(len(audit[1]["target"]), 256)
                self.assertEqual(len(audit[1]["version"]), 256)

    def test_official_core_cannot_receive_ai_writes_before_gate_cutover(self):
        class OfficialCore:
            def __init__(self, *args): pass
            def identity(self, expected): return {"user_id": expected, "role": "PM", "project_id": 5}
            def call(self, path):
                self_path = "/api/v3/qldapm/capabilities"
                assert path == self_path
                raise NativeError(404, "official core does not expose gates")
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            token = store.issue_token(7, "PM", "synthetic-only")
            service = Service(store, {"users": {"7": "PM"}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088"},
                              Path(directory) / "workspaces", OfficialCore)
            with self.assertRaisesRegex(NativeError, "CORE_GATES_NOT_ACTIVATED"):
                service.execute(token, {"action": "create_work_package", "arguments": {}, "idempotency_key": "must-not-write"})
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 0)
    def test_native_refuses_redirect_and_sets_trusted_https_proxy_header(self):
        from unittest.mock import patch
        import httpx
        from contextlib import nullcontext
        with patch("gateway.native.httpx.stream", return_value=nullcontext(httpx.Response(302, headers={"Location": "https://evil.invalid"}))) as request:
            with self.assertRaisesRegex(NativeError, "REDIRECT_REFUSED"):
                Native("http://127.0.0.1:8091", "synthetic-only", 3).call("/api/v3/users/me")
            self.assertFalse(request.call_args.kwargs["follow_redirects"])
            self.assertEqual(request.call_args.kwargs["headers"]["X-Forwarded-Proto"], "https")
        with self.assertRaisesRegex(ValueError, "UNTRUSTED"):
            Native("http://evil.invalid", "synthetic-only", 3)
    def test_unknown_write_cannot_be_replayed_or_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            payload = {"action": "comment", "arguments": {"id": 123, "text": "A test"}}
            self.assertIsNone(store.begin(7, "request-one", payload))
            self.assertEqual(store.pending_request(7, "request-one"), payload)
            with self.assertRaisesRegex(ValueError, "OUTCOME_UNKNOWN"):
                store.begin(7, "request-one", payload)
            with self.assertRaisesRegex(ValueError, "KEY_REUSED"):
                store.begin(7, "request-one", {**payload, "action": "transition"})
            store.finish(7, "request-one", {"result": "receipt"})
            self.assertEqual(store.begin(7, "request-one", payload), {"result": "receipt"})
            job = store.enqueue(7, "test", {"suite": "gateway"}, "test-one")
            self.assertEqual(store.job_for_request(7, "test-one"), job)
            self.assertIsNone(store.job_for_request(8, "test-one"))
    def test_expired_revoked_and_unknown_tokens_are_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory))
            token = store.issue_token(7, "FE", "private-openproject-token", ttl=60)
            self.assertEqual(store.authenticate(token)["user_id"], 7)
            self.assertNotIn(token, (Path(directory) / "credentials.json").read_text())
            store.revoke_token(token)
            with self.assertRaises(PermissionError):
                store.authenticate(token)
            expired = store.issue_token(7, "FE", "private-openproject-token", ttl=-1)
            with self.assertRaises(PermissionError):
                store.authenticate(expired)
            with self.assertRaises(PermissionError):
                store.authenticate("unknown")

    def test_workspace_checks_paths_and_stale_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "7/app").mkdir(parents=True)
            (root / "7/app/example.rb").write_text("old\n")
            workspace = Workspace(root)
            before = workspace.read(7, "app/example.rb")
            with self.assertRaises(ValueError):
                workspace.write(7, "app/example.rb", "new\n", "bad-hash")
            workspace.write(7, "app/example.rb", "new\n", before["sha256"])
            self.assertEqual(workspace.read(7, "app/example.rb")["content"], "new\n")
            for path in ("../credentials.json", ".git/config", ".GIT/config", ".git./config", "app/../../outside", "C:/secret", ".env", ".ENV", "app\\example.rb"):
                with self.assertRaises(ValueError):
                    workspace.read(7, path)
            first = workspace.tree_hash(7)
            self.assertEqual(first, workspace.tree_hash(7))
            workspace.write(7, "app/example.rb", "changed\n", workspace.read(7, "app/example.rb")["sha256"])
            self.assertNotEqual(first, workspace.tree_hash(7))
            import os
            os.link(root / "7/app/example.rb", root / "7/app/link.rb")
            with self.assertRaisesRegex(ValueError, "HARDLINK"):
                workspace.tree_hash(7)

    def test_rest_and_mcp_require_auth_and_match_project_identity(self):
        class OpenProjectFixture:
            def __init__(self, *args): pass
            def identity(self, expected): return {"user_id": expected, "role": "FE", "project_id": 5}
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            token = store.issue_token(7, "FE", "native-token")
            config = {"users": {"7": "FE"}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088",
                      "hosts": ["testserver"]}
            service = Service(store, config, Path(directory) / "workspaces", OpenProjectFixture)
            with TestClient(create_app(directory, service)) as client:
                for route in ("/api/v1/commands", "/mcp"):
                    self.assertEqual(client.post(route, json={}).status_code, 401)
                headers = {"Authorization": "Bearer " + token}
                response = client.post("/api/v1/commands", headers=headers, json={"action": "identity"})
                self.assertEqual(response.json()["result"]["user_id"], 7)
                self.assertEqual(client.post("/api/v1/commands", headers={**headers, "Origin": "https://evil.example"},
                                            json={"action": "identity"}).status_code, 403)
                initialize = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                    "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}}
                mcp_headers = {**headers, "Accept": "application/json, text/event-stream"}
                response = client.post("/mcp", json=initialize, headers=mcp_headers)
                self.assertEqual(response.status_code, 200)
                tools = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, headers=mcp_headers)
                names = [item["name"] for item in tools.json()["result"]["tools"]]
                self.assertNotIn("write_code", names)
                self.assertNotIn("change_gate", names)
                self.assertIn("comment", names)


if __name__ == "__main__":
    unittest.main()

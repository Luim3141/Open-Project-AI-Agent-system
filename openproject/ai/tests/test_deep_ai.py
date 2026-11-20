import hashlib
import hmac
import json
import tempfile
import time
import unittest
from pathlib import Path

import httpx
from starlette.testclient import TestClient

from gateway.app import create_app
from gateway.gemini import Gemini, ProviderError, MODEL
from gateway.service import Service
from gateway.store import Store, canonical


class CoreFixture:
    def __init__(self, *args): pass
    def identity(self, actor): return {"user_id": actor, "role": "BE", "project_id": 5}


class PMCoreFixture(CoreFixture):
    def identity(self, actor): return {"user_id": actor, "role": "PM", "project_id": 5}


class DeepAITests(unittest.TestCase):
    def test_general_chat_rejects_malformed_generation_without_tools(self):
        from unittest.mock import patch
        invalid = [[], {'candidates': None}, {'candidates': [None]},
                   {'candidates': [{'content': None}]},
                   {'candidates': [{'content': {'role': 'model', 'parts': [None]}}]},
                   {'candidates': [{'content': {'role': 'model', 'parts': [{'text': 1}]}}]},
                   {'candidates': [{'content': {'role': 'model', 'parts': [{'functionCall': None}]}}]},
                   {'candidates': [{'content': {'role': 'model', 'parts': [{'functionCall': {
                       'name': 'qldapm', 'args': []}}]}}]}]
        for document in invalid:
            with self.subTest(document=document), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'gemini.key').write_text('synthetic-not-a-real-key')
                policy = {'data_scope': 'offline-fixture', 'project': 'synthetic',
                          'limits': {'rpm': 20, 'tpm': 100000, 'rpd': 20}}
                def wire(request):
                    return httpx.Response(200, json={'totalTokens': 50}
                        if request.url.path.endswith(':countTokens') else document)
                with patch.object(Gemini, 'settings', return_value=policy), self.assertRaises(ProviderError):
                    Gemini(root).run('synthetic public fixture', lambda *args: self.fail('No tool may run'),
                                     httpx.MockTransport(wire), actor_role="PM")

    def test_general_chat_rejects_malformed_token_count_without_generation_or_tools(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'gemini.key').write_text('synthetic-not-a-real-key')
            policy = {'data_scope': 'offline-fixture', 'project': 'synthetic-project',
                      'limits': {'rpm': 20, 'tpm': 100000, 'rpd': 20}}
            def wire(request):
                self.assertTrue(request.url.path.endswith(':countTokens'))
                return httpx.Response(200, json=[])
            with patch.object(Gemini, 'settings', return_value=policy), self.assertRaisesRegex(ProviderError, 'INVALID_TOKEN_COUNT'):
                Gemini(root).run('synthetic public fixture', lambda *args: self.fail('No tool may run'), httpx.MockTransport(wire), actor_role="PM")

    def test_general_chat_stops_before_second_model_turn_when_project_budget_is_exhausted(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'gemini.key').write_text('synthetic-not-a-real-key')
            policy = {'data_scope': 'offline-fixture', 'project': 'synthetic-project',
                      'limits': {'rpm': 20, 'tpm': 100000, 'rpd': 2}}
            requests = []
            def wire(request):
                requests.append(request.url.path)
                if request.url.path.endswith(':countTokens'):
                    return httpx.Response(200, json={'totalTokens': 50})
                return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {
                    'role': 'model', 'parts': [{'functionCall': {'name': 'qldapm', 'args': {
                        'action': 'identity', 'arguments_json': '{}'}}}]}}]})
            with patch.object(Gemini, 'settings', return_value=policy), self.assertRaisesRegex(ProviderError, 'RPD_EXHAUSTED'):
                Gemini(root).run('synthetic public fixture', lambda *args: {'user_id': 21}, httpx.MockTransport(wire), actor_role="PM")
            self.assertEqual(len(requests), 2)

    def test_gemini_rejects_unstructured_or_fabricated_claims_even_with_a_citation(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("synthetic-not-a-real-key")
            for final in ("Tests passed [job-1]", {"claims": [{"tool": 0, "path": ["result", "passed"], "value": True}]},
                          {"claims": [{"tool": 9, "path": ["result", "passed"], "value": False}]}):
                responses = iter([
                    {"role": "model", "parts": [{"functionCall": {"name": "qldapm", "args": {
                        "action": "get_job", "arguments_json": '{"id":"job-1"}'}}}]},
                    {"role": "model", "parts": [{"text": final if isinstance(final, str) else json.dumps(final)}]}])
                def wire(request):
                    if request.url.path.endswith(':countTokens'):
                        return httpx.Response(200, json={'totalTokens': 50})
                    return httpx.Response(200, json={"candidates": [{"content": next(responses), "finishReason": "STOP"}]})
                with self.subTest(final=final), patch.object(Gemini, "settings", return_value={"data_scope": "offline-fixture", 'project': 'synthetic', 'limits': {'rpm': 100, 'tpm': 100000, 'rpd': 100}}), \
                        self.assertRaisesRegex(ProviderError, "CLAIM"):
                    Gemini(root).run("synthetic fixture", lambda *args: {"result": {"id": "job-1", "passed": False}},
                                     httpx.MockTransport(wire), actor_role="PM")

    def test_gateway_regression_cannot_be_attached_as_workspace_test_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            service = Service(store, {"users": {"21": "PM"}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088"},
                              root / "workspaces", PMCoreFixture)
            token = store.issue_token(21, "PM", "synthetic-only")
            with self.assertRaisesRegex(ValueError, "WORKSPACE_TEST_RECEIPT_REQUIRED"):
                service.execute(token, {"action": "request_test", "arguments": {"suite": "gateway", "work_package_id": 329},
                                        "idempotency_key": "gateway-not-core-evidence"})
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 0)

    def test_existing_source_is_not_a_creation_receipt(self):
        from gateway.native import NativeError
        class ExistingSource(PMCoreFixture):
            def packages(self): return [{"id": 123, "customField1": "EXISTING"}]
            def package(self,identifier):
                return {'id':identifier,'customField1':'EXISTING','subject':'Unrelated existing item','_links':{}}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            service = Service(store, {"users": {"21": "PM"}, "project_id": 5,
                "openproject_url": "http://127.0.0.1:8088", "source_field": "customField1"}, root / "workspaces", ExistingSource)
            native = ExistingSource()
            who = native.identity(21)
            arguments = {"source_id": "EXISTING", "subject": "Different request", "type_id": 1}
            with self.assertRaisesRegex(NativeError, "SOURCE_ID_ALREADY_EXISTS"):
                service.perform(who, native, "create_work_package", arguments, "new-key")
            store.begin(21, "timed-out", {"action": "create_work_package", "arguments": arguments})
            with self.assertRaisesRegex(ValueError, "OUTCOME_UNKNOWN_NO_PROVEN_RECEIPT"):
                service.perform(who, native, "reconcile_request", {"key": "timed-out"})
            self.assertEqual(store.request_status(21, "timed-out")["state"], "pending")

    def test_concurrent_code_confirmations_do_not_overwrite_the_same_base(self):
        import threading
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            token = store.issue_token(21, "PM", "synthetic")
            service = Service(store, {"users": {"21": "PM"}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088"},
                              root / "workspaces", PMCoreFixture)
            path = root / "workspaces/21/app/shared.rb"
            path.parent.mkdir(parents=True)
            path.write_text("base")
            proposals = [service.execute(token, {"action": "write_code", "arguments": {"path": "app/shared.rb", "content": content,
                "expected_hash": hashlib.sha256(b"base").hexdigest()}, "idempotency_key": content})["result"] for content in ("one", "two")]
            barrier, outcomes = threading.Barrier(2), []
            def confirm(proposal):
                barrier.wait(timeout=5)
                try:
                    service.confirm(21, proposal["id"], proposal["hash"])
                    outcomes.append("done")
                except ValueError as error:
                    outcomes.append(str(error))
            threads = [threading.Thread(target=confirm, args=(proposal,)) for proposal in proposals]
            for thread in threads: thread.start()
            for thread in threads: thread.join(timeout=10)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(sorted(outcomes), ["STALE_CONTENT", "done"])
            self.assertIn(path.read_text(), ("one", "two"))

    def test_published_openapi_and_catalog_match_shared_code(self):
        from gateway.app import openapi_document
        from gateway.service import Command, MUTATIONS
        from gateway.catalog import description
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(json.loads((root / "openapi.json").read_text()), openapi_document())
        scope = openapi_document()["paths"]["/api/v1/ai-runs"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]["write_scope_ids"]
        self.assertNotIn("maxItems", scope)
        self.assertEqual(scope["items"], {"type": "integer", "minimum": 1})
        names = Command.model_fields["action"].annotation.__args__
        self.assertEqual(json.loads((root / "mcp-tools.json").read_text()),
            [{"name": name, "description": description(name), "mutating": name in MUTATIONS} for name in names])

    def test_rest_mcp_write_only_proposes_signed_ui_confirms_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            token = store.issue_token(21, "PM", "synthetic")
            config = {"users": {"21": "PM"}, "project_id": 5, "hosts": ["testserver"], "openproject_url": "http://127.0.0.1:8088"}
            service = Service(store, config, root / "workspaces", PMCoreFixture)
            file = root / "workspaces/21/app/sample.rb"
            file.parent.mkdir(parents=True)
            file.write_text("old")
            request = {"action": "write_code", "arguments": {"path": "app/sample.rb", "content": "new", "expected_hash": hashlib.sha256(b"old").hexdigest()}, "idempotency_key": "one"}
            (root / "ui.key").write_bytes(b"synthetic-ui-secret")
            with TestClient(create_app(root, service)) as client:
                result = client.post("/api/v1/commands", headers={"Authorization": "Bearer " + token}, json=request)
                self.assertEqual(result.status_code, 200)
                proposal = result.json()["result"]
                self.assertEqual(file.read_text(), "old")
                mcp_headers = {"Authorization": "Bearer " + token, "Accept": "application/json, text/event-stream"}
                mcp_result = client.post("/mcp", headers=mcp_headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "write_code", "arguments": {"arguments": request["arguments"], "idempotency_key": "mcp-preview-only"}}})
                self.assertEqual(mcp_result.status_code, 200)
                self.assertFalse(mcp_result.json()["result"].get("isError"))
                self.assertIn("human_confirmation_required", mcp_result.text)
                self.assertEqual(file.read_text(), "old")
                self.assertEqual(client.post("/api/v1/commands", headers={"Authorization": "Bearer " + token}, json={**request, "confirmed": True}).status_code, 422)
                self.assertEqual(client.post("/api/v1/commands", headers={"Authorization": "Bearer " + token}, json={"action": "confirm", "arguments": {}}).status_code, 422)
                body = canonical({"actor": 21, "project": 5, "audience": "qldapm-ai-ui", "at": time.time(), "nonce": "a" * 32,
                                  "operation": "confirm", "command": {"id": proposal["id"], "hash": proposal["hash"]}}).encode()
                self.assertEqual(client.post("/internal/ui", content=body).status_code, 403)
                headers = {"X-Qldapm-Signature": hmac.new(b"synthetic-ui-secret", body, hashlib.sha256).hexdigest()}
                self.assertEqual(client.post("/internal/ui", content=body, headers=headers).status_code, 200)
                self.assertEqual(file.read_text(), "new")
                self.assertEqual(client.post("/internal/ui", content=body, headers=headers).status_code, 403)
                with self.assertRaisesRegex(ValueError, "CONSUMED"):
                    service.confirm(21, proposal["id"], proposal["hash"])

    def test_proposal_expiry_actor_and_stale_code(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            service = Service(store, {"users": {"21": "PM"}, "project_id": 5, "openproject_url": "http://127.0.0.1:8088"}, root / "workspaces", PMCoreFixture)
            token = store.issue_token(21, "PM", "synthetic")
            request = {"action": "write_code", "arguments": {"path": "app/new.rb", "content": "new", "expected_hash": "NEW"}, "idempotency_key": "one"}
            proposal = service.execute(token, request)["result"]
            with self.assertRaises(PermissionError):
                store.proposal(22, proposal["id"])
            with store.connect() as db:
                db.execute("UPDATE proposals SET expires=0")
            with self.assertRaisesRegex(ValueError, "EXPIRED"):
                service.confirm(21, proposal["id"], proposal["hash"])
            self.assertFalse((root / "workspaces/21/app/new.rb").exists())
            proposal = service.execute(token, {**request, "idempotency_key": "two"})["result"]
            path = root / "workspaces/21/app/new.rb"
            path.parent.mkdir(parents=True)
            path.write_text("changed")
            with self.assertRaisesRegex(ValueError, "STALE"):
                service.confirm(21, proposal["id"], proposal["hash"])
            self.assertEqual(path.read_text(), "changed")
            self.assertEqual(store.proposal(21, proposal["id"])["state"], "failed_or_unknown")

    def test_insights_visibility_and_disabled_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            service = Service(store, {"users": {"21": "BE", "22": "FE"}, "project_id": 5, "hosts": ["testserver"], "openproject_url": "http://127.0.0.1:8088"}, root / "workspaces", CoreFixture)
            token = store.issue_token(21, "BE", "synthetic")
            with self.assertRaisesRegex(PermissionError, "PM_OR_SELF"):
                service.execute(token, {"action": "get_insights", "arguments": {"user_id": 22}})
            with self.assertRaisesRegex(ProviderError, "DISABLED"):
                service.execute(token, {"action": "start_ai_run", "arguments": {"prompt": "hello"}, "idempotency_key": "disabled"})
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_runs").fetchone()[0], 0)
            with TestClient(create_app(root, service)) as client:
                self.assertEqual(client.get("/api/v1/insights").status_code, 401)
                headers = {"Authorization": "Bearer " + token}
                self.assertEqual(client.get("/api/v1/insights?user_id=22", headers=headers).status_code, 403)
                self.assertEqual(client.post("/api/v1/ai-runs", headers={**headers, "Idempotency-Key": "provider-off"}, json={"prompt": "test"}).status_code, 503)

    def test_bounded_native_stream_and_changed_restore_manifest(self):
        from contextlib import nullcontext
        from unittest.mock import patch
        from gateway.native import Native, NativeError
        from broker import backup_manifest
        with patch("gateway.native.httpx.stream", return_value=nullcontext(httpx.Response(200, content=b"x" * 8388609))):
            with self.assertRaisesRegex(NativeError, "TOO_LARGE"):
                Native("http://127.0.0.1:8088", "synthetic", 5).call("/api/v3/users/me")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            backup = root / "backups/fixture"
            backup.mkdir(parents=True)
            (backup / "database.dump").write_bytes(b"synthetic db")
            (backup / "assets.tar.gz").write_bytes(b"synthetic attachment")
            with patch("broker.PROJECT_RUNTIME", root):
                old = backup_manifest({"backup_path": str(backup)})
                (backup / "database.dump").write_bytes(b"changed")
                self.assertNotEqual(old, backup_manifest({"backup_path": str(backup)}))
                with self.assertRaisesRegex(ValueError, "PATH_DENIED"):
                    backup_manifest({"backup_path": str(root)})

    def test_gemini_signature_call_ids_tool_allowlist_and_no_hidden_tools(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("synthetic-not-a-real-key")
            requests = []
            def handler(request):
                document = json.loads(request.content)
                if request.url.path.endswith(':countTokens'):
                    extras = json.loads(document['contents'][-1]['parts'][0]['text'])
                    self.assertIn('tools', extras)
                    self.assertIn('systemInstruction', extras)
                    return httpx.Response(200, json={'totalTokens': 50})
                requests.append(document)
                self.assertEqual(request.url.host, "generativelanguage.googleapis.com")
                self.assertEqual(document["generationConfig"]["maxOutputTokens"], 4096)
                self.assertEqual(set(document["tools"][0]), {"functionDeclarations"})
                if len(requests) == 1:
                    content = {"role": "model", "parts": [{"thoughtSignature": "opaque-signature", "functionCall": {
                        "id": "call-1", "name": "qldapm", "args": {"action": "identity", "arguments_json": "{}"}}}]}
                else:
                    self.assertEqual(document["contents"][1]["parts"][0]["thoughtSignature"], "opaque-signature")
                    self.assertEqual(document["contents"][2]["parts"][0]["functionResponse"]["id"], "call-1")
                    content = {"role": "model", "parts": [{"text": json.dumps({"claims": [
                        {"tool": 0, "path": ["user_id"], "value": 21}]})}]}
                return httpx.Response(200, json={"candidates": [{"content": content, "finishReason": "STOP"}]})
            # Offline contract only: production settings never enable personnel/tool data on Free Tier.
            policy = {'data_scope': 'offline-fixture', 'project': 'synthetic', 'limits': {'rpm': 100, 'tpm': 100000, 'rpd': 100}}
            with patch.object(Gemini, "settings", return_value=policy):
                result = Gemini(root).run("test", lambda action, args: {"user_id": 21}, httpx.MockTransport(handler), actor_role="PM")
            self.assertEqual(len(result["tools"]), 1)
            self.assertEqual(result["model"], MODEL)
            self.assertEqual(result["claims"][0]["value"], 21)
            self.assertEqual(result["claims"][0]["action"], "identity")
            for status in (302, 429, 500):
                with patch.object(Gemini, "settings", return_value=policy), self.assertRaises(ProviderError):
                    Gemini(root).run("test", lambda *args: None, httpx.MockTransport(lambda request: httpx.Response(status)), actor_role="PM")
            malicious = {"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": [{"functionCall": {
                "name": "shell", "args": {"command": "read secrets"}}}]}}]}
            root = root / "independent-malicious-fixture"
            root.mkdir()
            (root / "gemini.key").write_text("synthetic-not-a-real-key")
            with patch.object(Gemini, "settings", return_value=policy), self.assertRaisesRegex(ProviderError, "DENIED"):
                Gemini(root).run("test", lambda *args: self.fail("must not execute"), httpx.MockTransport(lambda request:
                    httpx.Response(200, json={'totalTokens': 50} if request.url.path.endswith(':countTokens') else malicious)), actor_role="PM")


if __name__ == "__main__":
    unittest.main()

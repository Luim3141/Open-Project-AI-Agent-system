"""Scheduling classes borrow idle capacity but never borrow permissions or lift hard caps."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from gateway import RUN_ROUND_LIMITS
from gateway.ai_worker import main
from gateway.app import openapi_document
from gateway.catalog import ARGUMENTS
from gateway.gemini import Gemini, ProviderError
from gateway.service import Service
from gateway.store import Store


class QuotaClassTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_public_class_validation_default_and_contract_match(self):
        service = Service(self.store, {"gateway_mode": "native"}, self.root / "workspaces")
        with patch.object(service, "start_dispatcher"), patch.object(service.gemini, "settings", return_value={}):
            for invalid in (True, [], {}, "paid", "admin", 1):
                with self.subTest(value=invalid), self.assertRaisesRegex(ValueError, "AI_QUEUE_KIND_INVALID"):
                    service.start_run({"user_id": 7}, {"prompt": "synthetic", "run_class": invalid})
            default = service.start_run({"user_id": 7}, {"prompt": "synthetic"})["result"]
            self.assertEqual((default["run_class"], default["max_rounds"]), ("interactive", 32))
            for kind, rounds in RUN_ROUND_LIMITS.items():
                result = service.start_run({"user_id": 7}, {"prompt": "synthetic", "run_class": kind})["result"]
                self.assertEqual(result["max_rounds"], rounds)
                self.assertEqual(self.store.run_class(7, result["id"]), kind)
        schema = openapi_document()["paths"]["/api/v1/ai-runs"]["post"]["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(set(schema["properties"]["run_class"]["enum"]), set(RUN_ROUND_LIMITS))
        self.assertIn("run_class", ARGUMENTS["start_ai_run"])

    def test_all_classes_can_reuse_full_idle_project_budget_without_reserving_slices(self):
        limits = {"rpm": 13, "tpm": 225000, "rpd": 450}
        for kind in RUN_ROUND_LIMITS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                store = Store(folder)
                for _ in range(13):
                    store.enqueue_run(7, {"prompt": "synthetic", "allow_routine_writes": False, "write_scope_ids": []}, kind=kind)
                for _ in range(13):
                    run = store.claim_run()
                    self.assertEqual(store.run_class(7, run["id"]), kind)
                    store.reserve_gemini("same-project", limits, 100)
                    store.finish_run(7, run["id"], {}, "done")
                with self.assertRaisesRegex(ValueError, "RPM"):
                    store.reserve_gemini("same-project", limits, 100)

    def test_worker_uses_persisted_class_bound_without_expanding_consent(self):
        (self.root / "config.json").write_text('{"gateway_mode":"native","project_id":3}')
        for kind, maximum in RUN_ROUND_LIMITS.items():
            with self.subTest(kind=kind):
                identifier = self.store.enqueue_run(8, {"prompt": "synthetic", "allow_routine_writes": False, "write_scope_ids": []}, kind=kind)["result"]["id"]
                test = self
                class Provider:
                    def settings(self): return {}
                    def run(self, prompt, execute, **options):
                        test.assertEqual(options["max_rounds"], maximum)
                        test.assertFalse(options["allow_routine_writes"])
                        test.assertEqual(options["actor_role"], "BE")
                        test.assertEqual(options["permitted_tools"], ["identity"])
                        return {"verified": True}
                class FixtureService:
                    def __init__(self, store, *args):
                        self.store, self.mode, self.gemini = store, "native", Provider()
                        self.config = args[0]
                    def execute_actor(self, actor, command):
                        if command["action"] == "identity":
                            return {"result": {"role": "BE"}}
                        return {"result": {"tools": [{"name": "identity", "allowed": True}, {"name": "update_work_package", "allowed": False}]}}
                payload = {"root": str(self.root), "workspaces": str(self.root / "workspaces"), "actor": 8,
                           "prompt": "synthetic", "id": identifier, "allow_routine_writes": False, "write_scope_ids": []}
                output = io.BytesIO()
                with patch("gateway.service.Service", FixtureService), patch("sys.stdin", SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode()))), patch("sys.stdout", SimpleNamespace(buffer=output)):
                    main()
                self.assertTrue(json.loads(output.getvalue())["result"]["verified"])
                self.store.finish_run(8, identifier, {}, "done")

    def test_model_round_ceiling_keeps_tool_receipts_and_stops_before_next_provider_call(self):
        (self.root / "gemini.key").write_text("synthetic-only")
        policy = {"data_scope": "offline-fixture", "project": "fixture", "limits": {"rpm": 100, "tpm": 1000000, "rpd": 100}}
        requests, progress = [], []
        def wire(request):
            requests.append(str(request.url))
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 100})
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": [
                {"functionCall": {"name": "qldapm", "args": {"action": "identity", "arguments_json": "{}"}}}]}}]})
        with patch.object(Gemini, "settings", return_value=policy), self.assertRaisesRegex(ProviderError, "GEMINI_ROUND_LIMIT"):
            Gemini(self.root).run("Synthetic loop", lambda *args: {"result": {"role": "BE"}}, httpx.MockTransport(wire),
                                  progress=progress.append, actor_role="BE", max_rounds=2)
        self.assertEqual(len(requests), 4)
        self.assertEqual(len(progress[-1]["tools"]), 2)
        self.assertTrue(all(call["action"] == "identity" for call in progress[-1]["tools"]))
        for invalid in (0, 33, True):
            with self.assertRaisesRegex(ValueError, "AI_ROUND_LIMIT_INVALID"):
                Gemini(self.root).run("synthetic", None, max_rounds=invalid)

    def test_authenticated_rest_classes_share_actor_scope_and_do_not_grant_business_write(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        roles = {"7": "PM", "6": "BA-PM", "8": "BE", "9": "FE", "10": "QA"}
        class Native:
            def __init__(self, *args): pass
            def identity(self, actor): return {"user_id": actor, "role": roles[str(actor)]}
        service = Service(self.store, {"gateway_mode": "native", "users": roles, "project_id": 3,
                                      "hosts": ["testserver"], "openproject_url": "http://fixture.invalid"}, self.root / "workspaces", Native)
        tokens = {int(actor): self.store.issue_token(int(actor), role, "synthetic-native") for actor, role in roles.items()}
        with patch.object(service, "start_dispatcher"), patch.object(service.gemini, "settings", return_value={}), TestClient(create_app(self.root, service)) as client:
            for actor in tokens:
                for kind in RUN_ROUND_LIMITS:
                    headers = {"Authorization": "Bearer " + tokens[actor], "Idempotency-Key": f"{actor}-{kind}"}
                    payload = {"prompt": "synthetic", "run_class": kind}
                    response = client.post("/api/v1/ai-runs", headers=headers, json=payload)
                    self.assertEqual(response.status_code, 200)
                    receipt = response.json()["result"]
                    self.assertEqual(receipt["run_class"], kind)
                    self.assertEqual(client.post("/api/v1/ai-runs", headers=headers, json=payload).json(), response.json())
                    if actor != 7:
                        denied = client.post("/api/v1/commands", headers=headers,
                                             json={"action": "update_work_package", "arguments": {"id": 58}, "idempotency_key": "cannot-write"})
                        self.assertEqual(denied.status_code, 403)
                    other = 8 if actor != 8 else 9
                    denied = client.get("/api/v1/ai-runs/" + receipt["id"], headers={"Authorization": "Bearer " + tokens[other]})
                    self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()

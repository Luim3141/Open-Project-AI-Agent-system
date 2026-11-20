import concurrent.futures
import io
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from gateway.gemini import Gemini, MODEL, ProviderError, SMOKE_PROMPT, DEMO_PROMPT
from gateway.store import Store, canonical, digest
from free_tier_staging import enroll, verify, main, authorize_continuous


class FreeTierTests(unittest.TestCase):
    def setUp(self):
        offline = patch("free_tier_staging.require_offline")
        offline.start()
        self.addCleanup(offline.stop)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.proof = self.root / "operator-proof.json"
        self.policy = {"model": MODEL, "project": "synthetic-project", "tier": "Free", "billing_enabled": False,
            "terms_reviewed": True, "data_scope": "synthetic-smoke-only", "verification_method": "manual-official-console",
            "evidence_reference": "fixture, not Google verification", "key_sha256": digest("synthetic"),
            "checked_at": time.time(), "quota": {"rpm": 10, "tpm": 1000, "rpd": 100}}
        self.proof.write_text(canonical(self.policy))
        (self.root / "gemini.key").write_text("synthetic")
        (self.root / "gemini.json").write_text(canonical({"enabled": True, "model": MODEL}))
        env = patch.dict("os.environ", {"QLDAPM_AI_ENVIRONMENT": "staging", "QLDAPM_GEMINI_FREE_PROOF": str(self.proof)})
        env.start()
        self.addCleanup(env.stop)

    def continuous_policy(self):
        self.policy["authorization"] = {"mode": "continuous-free-only", "billing_allowed": False,
            "authorized_at": time.time() - 1, "user_request_sha256": digest("synthetic owner permits persistent Free-only use")}
        self.policy["checked_at"] = time.time() - 86400
        self.proof.write_text(canonical(self.policy))

    def test_continuous_authorization_has_no_expiry_but_off_key_and_environment_still_apply(self):
        self.continuous_policy()
        with patch("gateway.gemini.time.time", return_value=time.time() + 365 * 86400):
            self.assertTrue(Gemini.continuous_authorized(Gemini(self.root).settings()))
        for change in ({"authorization": {"mode": "continuous", "billing_allowed": True}}, {"key_sha256": digest("wrong")}):
            self.proof.write_text(canonical({**self.policy, **change}))
            with self.assertRaises(ProviderError):
                Gemini(self.root).settings()
        self.proof.write_text(canonical(self.policy))
        (self.root / "gemini.json").write_text(canonical({"enabled": False, "model": MODEL}))
        with self.assertRaises(ProviderError):
            Gemini(self.root).settings()
        with patch.dict("os.environ", {"QLDAPM_AI_ENVIRONMENT": "production"}):
            with self.assertRaises(ProviderError):
                Gemini(self.root).settings(require_enabled=False)

    def test_paid_or_billing_enabled_never_accepted_even_with_persistent_free_consent(self):
        self.continuous_policy()
        for change in ({"tier": "Paid"}, {"billing_enabled": True}, {"tier": "Paid", "billing_enabled": True}):
            self.proof.write_text(canonical({**self.policy, **change}))
            with self.subTest(change=change), self.assertRaises(ProviderError):
                Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: self.fail("no outbound")))

    def test_legacy_cost_authorization_route_refuses_before_any_private_write(self):
        proof = self.root / "free-tier-proof.json"
        proof.write_text(self.proof.read_text())
        store = Store(self.root)
        store.reserve_gemini("synthetic-project", {"rpm": 10, "tpm": 100, "rpd": 100}, 5)
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        with self.assertRaisesRegex(PermissionError, "PAID_API_DISABLED"):
            authorize_continuous(self.root, self.root, self.root / "unused.png", self.root / "unused.md")
        self.assertEqual({p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}, before)
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*),SUM(input_tokens) FROM gemini_usage").fetchone()[:], (1, 5))

    def test_free_only_defaults_deny_config_and_unknown_matching_model_before_sdk(self):
        state = {"enabled": True, "model": MODEL}
        self.assertEqual(Gemini(self.root).settings()["tier"], "Free")
        for change in ({"provider_policy": "PAID"}, {"paid_api_disabled": False}, {"auto_enable_billing": True}):
            (self.root / "gemini.json").write_text(canonical({**state, **change}))
            with patch.object(Gemini, "sdk_client", side_effect=AssertionError("SDK forbidden")) as sdk:
                with self.subTest(change=change), self.assertRaises(ProviderError):
                    Gemini(self.root).run(SMOKE_PROMPT, None)
                sdk.assert_not_called()
        self.proof.write_text(canonical({**self.policy, "model": "gemini-4-argon"}))
        (self.root / "gemini.json").write_text(canonical({**state, "model": "gemini-4-argon"}))
        with patch.object(Gemini, "sdk_client", side_effect=AssertionError("SDK forbidden")) as sdk:
            with self.assertRaises(ProviderError): Gemini(self.root).run(SMOKE_PROMPT, None)
            sdk.assert_not_called()

    def test_exact_historical_continuous_billing_proof_is_denied_before_sdk(self):
        self.continuous_policy()
        self.policy["authorization"].update(mode="continuous", billing_allowed=True)
        self.proof.write_text(canonical(self.policy))
        with patch.object(Gemini, "sdk_client", side_effect=AssertionError("SDK forbidden")) as sdk:
            with self.assertRaises(ProviderError): Gemini(self.root).run(SMOKE_PROMPT, None)
            sdk.assert_not_called()

    def test_liveness_and_authenticated_status_never_call_llm_or_consume_quota(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        from gateway.service import Service
        from tests.test_deep_ai import CoreFixture
        store = Store(self.root)
        token = store.issue_token(21, 'BE', 'synthetic-native-token')
        service = Service(store, {'users': {'21': 'BE'}, 'project_id': 5, 'hosts': ['testserver'],
            'openproject_url': 'http://127.0.0.1:8091'}, self.root / 'workspaces', CoreFixture)
        with TestClient(create_app(self.root, service)) as client, patch.object(Gemini, 'sdk_client', side_effect=AssertionError('no outbound')) as sdk:
            for _ in range(5):
                self.assertEqual(client.get('/health').status_code, 200)
                result = service.execute(token, {'action': 'get_assistant_status'})['result']
                self.assertEqual(result['gemini']['readiness']['state'], 'READINESS_NOT_VERIFIED')
            sdk.assert_not_called()
        with store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM gemini_usage').fetchone()[0], 0)

    def test_continuous_transient_cooldown_survives_restart_without_replaying_or_clearing_usage(self):
        self.continuous_policy()
        seen = []
        def unavailable(request):
            seen.append(request.url.path)
            return httpx.Response(503, json={"error": {"code": 503, "status": "UNAVAILABLE", "message": "synthetic transient"}})
        with self.assertRaises(ProviderError):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(unavailable), actor_role="PM")
        self.assertEqual(len(seen), 1)
        store = Store(self.root)
        block = store.gemini_block("synthetic-project")
        self.assertIsNotNone(block["retry_at"])
        with self.assertRaisesRegex(ValueError, "CIRCUIT_OPEN"):
            store.reserve_gemini("synthetic-project", {"rpm": 10, "tpm": 100, "rpd": 100}, 0)
        with patch("gateway.store.time.time", return_value=block["retry_at"] + 1):
            self.assertIsNone(Store(self.root).gemini_block("synthetic-project"))
            Store(self.root).reserve_gemini("synthetic-project", {"rpm": 10, "tpm": 100, "rpd": 100}, 0)
        store.block_gemini("synthetic-project", "GEMINI_PERMISSION_403")
        with patch("gateway.store.time.time", return_value=time.time() + 365 * 86400):
            self.assertIsNotNone(store.gemini_block("synthetic-project"))
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 2)

    def test_continuous_quota_cooldown_and_status_do_not_claim_a_current_free_billing_check(self):
        from gateway.service import Service, Command
        from tests.test_deep_ai import CoreFixture
        self.continuous_policy()
        store = Store(self.root)
        token = store.issue_token(21, "BE", "synthetic-native-token")
        service = Service(store, {"users": {"21": "BE"}, "project_id": 5,
            "openproject_url": "http://127.0.0.1:8091", "gateway_mode": "native"}, self.root / "workspaces", CoreFixture)
        status = service.execute(token, Command(action="get_assistant_status"))["result"]["gemini"]
        self.assertEqual(status["state"], "authorized")
        self.assertIsNone(status["expires"])
        self.assertFalse(status["billing_checked_live"])
        self.assertFalse(status["billing_allowed"])
        self.assertTrue(status["paid_api_disabled"])
        self.assertEqual(status["last_observed_at"], self.policy["checked_at"])
        before = time.time()
        with self.assertRaises(ProviderError) as caught:
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda request: httpx.Response(429,
                json={"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "synthetic quota"}})), actor_role="PM")
        self.assertEqual(caught.exception.status, 429)
        status = service.execute(token, Command(action="get_assistant_status"))["result"]["gemini"]
        self.assertEqual(status["state"], "WAITING_QUOTA")
        self.assertGreaterEqual(status["retry_at"], before + 3600)

    def handler(self, request):
        document = json.loads(request.content)
        self.assertEqual(request.url.host, "generativelanguage.googleapis.com")
        self.assertEqual(request.url.path.split(":")[0], "/v1beta/models/gemini-3.5-flash-lite")
        self.assertNotIn("tools", document)
        self.assertNotIn("systemInstruction", document)
        self.assertEqual(document["contents"][0]["parts"][0]["text"], SMOKE_PROMPT)
        if request.url.path.endswith(":countTokens"):
            return httpx.Response(200, json={"totalTokens": 20})
        self.assertEqual(document["generationConfig"]["maxOutputTokens"], 128)
        self.assertEqual(document["generationConfig"]["thinkingConfig"]["thinking_level"], "MINIMAL")
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"text": "QLDAPM_OK"}]}, "finishReason": "STOP"}]})

    def test_rest_and_mcp_reject_project_or_secret_prompts_before_creating_a_run(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        from gateway.service import Service
        from tests.test_deep_ai import CoreFixture
        store = Store(self.root)
        token = store.issue_token(21, "BE", "synthetic-native-token")
        service = Service(store, {"users": {"21": "BE"}, "project_id": 5, "hosts": ["testserver"],
            "openproject_url": "http://127.0.0.1:8091"}, self.root / "workspaces", CoreFixture)
        headers = {"Authorization": "Bearer " + token, "Accept": "application/json, text/event-stream"}
        with TestClient(create_app(self.root, service)) as client:
            response = client.post("/api/v1/ai-runs", headers={**headers, "Idempotency-Key": "secret-denied"},
                json={"prompt": "Email employee@example.invalid; password=synthetic-never-send"})
            self.assertEqual(response.status_code, 503)
            self.assertIn("FREE_DATA_SCOPE_DENIED", response.json()["error"])
            response = client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1,
                "method": "tools/call", "params": {"name": "start_ai_run", "arguments": {
                    "arguments": {"prompt": "Analyze private employee performance"}, "idempotency_key": "project-denied"}}})
            self.assertTrue(response.json()["result"]["isError"])
            for key in ("secret-denied", "project-denied"):
                with self.assertRaisesRegex(ValueError, "REQUEST_NOT_FOUND"):
                    store.request_status(21, key)

    def test_fixed_prompt_no_tools_and_usage_survives_restart(self):
        result = Gemini(self.root).run(SMOKE_PROMPT, lambda *args: self.fail("no tools"), httpx.MockTransport(self.handler), actor_role="PM")
        self.assertEqual(result["text"], "QLDAPM_OK")
        with Store(self.root).connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*),SUM(input_tokens) FROM gemini_usage").fetchone()[:], (2, 20))
        with self.assertRaisesRegex(ProviderError, "DATA_SCOPE_DENIED"):
            Gemini(self.root).run("employee confidential details", None, httpx.MockTransport(lambda r: self.fail("no outbound")), actor_role="PM")

    def test_public_demo_answers_without_project_data_or_tools_and_requires_its_scope(self):
        with self.assertRaisesRegex(ProviderError, "DATA_SCOPE_DENIED"):
            Gemini(self.root).run(DEMO_PROMPT, None, httpx.MockTransport(lambda r: self.fail("legacy proof cannot send demo")), actor_role="PM")
        self.policy["data_scope"] = "public-demo-only"
        self.proof.write_text(canonical(self.policy))
        def answer(request):
            document = json.loads(request.content)
            self.assertEqual(document["contents"], [{"role": "user", "parts": [{"text": DEMO_PROMPT}]}])
            self.assertNotIn("tools", document)
            self.assertNotIn("systemInstruction", document)
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 32})
            self.assertEqual(document["generationConfig"]["maxOutputTokens"], 768)
            return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [
                {"text": "Sprint là một khoảng thời gian ngắn trong Scrum."}]}, "finishReason": "STOP"}]})
        result = Gemini(self.root).run(DEMO_PROMPT, lambda *a: self.fail("demo cannot execute tools"), httpx.MockTransport(answer), actor_role="PM")
        self.assertEqual(result["text"], "Sprint là một khoảng thời gian ngắn trong Scrum.")
        self.assertEqual(result["tools"], [])
        with self.assertRaisesRegex(ProviderError, "DATA_SCOPE_DENIED"):
            Gemini(self.root).run(DEMO_PROMPT + " email=private@example.invalid", None,
                httpx.MockTransport(lambda r: self.fail("no private prompt outbound")), actor_role="PM")

    def test_project_metadata_loop_reads_counts_without_sending_people_or_source_text(self):
        self.policy["quota"]["tpm"] = 100000  # Full SDK payload byte budget includes the system/tool declarations.
        self.policy["data_scope"] = "project-metadata-only"
        self.proof.write_text(canonical(self.policy))
        turn = 0
        def wire(request):
            nonlocal turn
            body = json.loads(request.content)
            self.assertNotIn("employee@example.invalid", canonical(body))
            self.assertNotIn("synthetic-private-description", canonical(body))
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 50})
            turn += 1
            parts = [{"functionCall": {"name": "qldapm", "args": {
                "action": "analyze", "arguments_json": "{}"}}}] if turn == 1 else [{"text": json.dumps({"claims": [
                    {"tool": 0, "path": ["result", "count"], "value": 329}]})}]
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": parts}}]})
        result = Gemini(self.root).run("Dự án có bao nhiêu công việc?", lambda *a: {"result": {
            "count": 329, "by_status": {"NEW": 329}, "by_assignee": {"employee@example.invalid": 329},
            "description": "synthetic-private-description"}}, httpx.MockTransport(wire), actor_role="PM")
        self.assertEqual(result["claims"][0]["value"], 329)
        self.assertEqual(result["tools"][0]["result"], {"result": {"count": 329, "by_status": {"NEW": 329}}})
        with self.assertRaisesRegex(ProviderError, "DATA_SCOPE_DENIED"):
            Gemini(self.root).run("password=secret-value employee@example.invalid", None,
                httpx.MockTransport(lambda r: self.fail("secret input cannot go outbound")), actor_role="PM")

    def test_production_requires_its_own_target_binding_and_keeps_cost_guards(self):
        self.policy["data_scope"] = "project-metadata-only"
        self.proof.write_text(canonical(self.policy))
        with patch.dict("os.environ", {"QLDAPM_AI_ENVIRONMENT": "production"}):
            with self.assertRaisesRegex(ProviderError, "DISABLED"):
                Gemini(self.root).settings()
            self.policy["target_environment"] = "production"
            self.proof.write_text(canonical(self.policy))
            self.assertEqual(Gemini(self.root).settings()["tier"], "Free")
            for change in ({"billing_enabled": True}, {"checked_at": time.time() - 3601}, {"key_sha256": "changed"}):
                self.proof.write_text(canonical({**self.policy, **change}))
                with self.assertRaisesRegex(ProviderError, "DISABLED"):
                    Gemini(self.root).settings()

    def test_metadata_tool_results_drop_private_text_and_cannot_be_approvals(self):
        item = {"id": 38, "lockVersion": 7, "subject": "Private employee name", "description": "private token",
                "_links": {"status": {"href": "/api/v3/statuses/1"}, "assignee": {"title": "employee@example.invalid"}}}
        self.assertEqual(Gemini.metadata_result("get_work_package", {"result": item}),
                         {"result": {"id": 38, "lockVersion": 7, "status_id": 1}})
        identifier = "11111111-2222-4333-8444-555555555555"
        self.assertEqual(Gemini.metadata_result("update_work_package", {"result": {
            "id": identifier, "human_confirmation_required": True, "preview": item}}),
            {"result": {"id": identifier, "human_confirmation_required": True}})
        with self.assertRaises(ProviderError):
            Gemini.metadata_result("change_gate", {"result": {"approved": True}})
        for invalid in ({"result": {"count": -1}}, {"result": {"count": 1, "by_status": {"employee@example.invalid": 1}}}):
            with self.subTest(invalid=invalid), self.assertRaises(ProviderError):
                Gemini.metadata_result("analyze", invalid)
        for invalid in ({"result": {**item, "_links": []}}, {"result": {**item, "_links": {"status": None}}}):
            with self.subTest(invalid=invalid), self.assertRaises(ProviderError):
                Gemini.metadata_result("get_work_package", invalid)

    def test_rest_deadline_reports_unknown_and_never_retries_the_worker(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        from gateway.service import Service
        from tests.test_deep_ai import CoreFixture
        store = Store(self.root)
        token = store.issue_token(21, "BE", "synthetic-native-token")
        service = Service(store, {"users": {"21": "BE"}, "project_id": 5, "hosts": ["testserver"],
            "openproject_url": "http://127.0.0.1:8091"}, self.root / "workspaces", CoreFixture)
        original = Gemini.run
        def fixture_wire(provider, prompt, execute):
            return original(provider, prompt, execute, httpx.MockTransport(self.handler))
        with TestClient(create_app(self.root, service)) as client, patch.object(Gemini, "run", fixture_wire), \
                patch("subprocess.run", side_effect=subprocess.TimeoutExpired("fixed worker", 120)) as worker:
            headers = {"Authorization": "Bearer " + token, "Idempotency-Key": "deadline-no-retry"}
            response = client.post("/api/v1/ai-runs", headers=headers, json={"prompt": SMOKE_PROMPT})
            identifier = response.json()["result"]["id"]
            self.assertTrue(service.gemini.lock.acquire(timeout=5))
            service.gemini.lock.release()
            result = client.get("/api/v1/ai-runs/" + identifier, headers=headers).json()["result"]
            self.assertEqual(result["state"], "failed_or_unknown")
            self.assertIn("DEADLINE", result["result"]["error"])
            replay = client.post("/api/v1/ai-runs", headers=headers, json={"prompt": SMOKE_PROMPT})
            self.assertEqual(replay.json()["result"]["id"], identifier)
            self.assertEqual(worker.call_count, 1)
            self.assertEqual(worker.call_args.kwargs["timeout"], 600)

    def test_paid_unknown_expired_key_mismatch_and_production_fail_closed(self):
        for change in ({"model": "gemini-3.8-flash"}, {"tier": "Tier 1"}, {"billing_enabled": True}, {"checked_at": time.time() - 3601},
                       {"checked_at": time.time() + 1}, {"key_sha256": digest("changed")}, {"quota": {"rpm": 0}},
                       {"quota": {"rpm": True, "tpm": 1000, "rpd": 100}}, {"data_scope": "personnel"}):
            self.proof.write_text(canonical({**self.policy, **change}))
            with self.subTest(change=change), self.assertRaisesRegex(ProviderError, "DISABLED"):
                Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: self.fail("no outbound")), actor_role="PM")
        self.proof.write_text(canonical(self.policy))
        with patch.dict("os.environ", {"QLDAPM_AI_ENVIRONMENT": "production"}), self.assertRaisesRegex(ProviderError, "DISABLED"):
            Gemini(self.root).settings()
        for malformed in ([], None, {"quota": []}):
            self.proof.write_text(canonical(malformed))
            with self.assertRaises(ProviderError):
                Gemini(self.root).settings()

    def test_auth_quota_redirect_timeout_stop_without_retry_or_fallback(self):
        for status in (401, 403, 404, 429, 302, 500):
            with self.subTest(status=status):
                store = Store(self.root)
                with store.connect() as db:
                    db.execute("DELETE FROM gemini_blocks")
                    db.execute("DELETE FROM gemini_usage")
                requests = []
                def reject(request):
                    requests.append(str(request.url))
                    return httpx.Response(status, headers={"Location": "https://evil.invalid/"})
                with self.assertRaises(ProviderError):
                    Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(reject), actor_role="PM")
                with self.assertRaises(ProviderError):
                    Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: self.fail("latched across restart")), actor_role="PM")
                self.assertEqual(len(requests), 1)
        with Store(self.root).connect() as db:
            db.execute("DELETE FROM gemini_blocks")
        def timeout(request):
            raise httpx.ReadTimeout("synthetic secret must not appear")
        with self.assertRaisesRegex(ProviderError, "GEMINI_TIMEOUT"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(timeout), actor_role="PM")
        with self.assertRaisesRegex(ProviderError, "GEMINI_TIMEOUT"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: self.fail("no retry")), actor_role="PM")

    def test_atomic_rpm_tpm_daily_budget_and_no_reset_on_reverification(self):
        store = Store(self.root)
        limits = {"rpm": 2, "tpm": 100, "rpd": 3}
        def reserve(_):
            try:
                Store(self.root).reserve_gemini("shared-project", limits, 20)
                return True
            except ValueError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(reserve, range(6))), 2)
        with self.assertRaisesRegex(ValueError, "TPM"):
            store.reserve_gemini("other-project", limits, 101)
        with store.connect() as db:
            db.execute("UPDATE gemini_usage SET at=?", (time.time() - 61,))
        store.reserve_gemini("shared-project", limits, 20)
        with store.connect() as db:
            db.execute("UPDATE gemini_usage SET at=?", (time.time() - 61,))
        with self.assertRaisesRegex(ValueError, "RPD"):
            Store(self.root).reserve_gemini("shared-project", limits, 20)

    def test_http_diagnostics_keep_phase_status_and_never_echo_upstream_secrets(self):
        for phase, status, rpc, reason in (("countTokens", 400, "INVALID_ARGUMENT", "API_KEY_INVALID"),
                                           ("countTokens", 401, "UNAUTHENTICATED", "ACCESS_TOKEN_TYPE_UNSUPPORTED"),
                                           ("generateContent", 503, "UNAVAILABLE", "UNKNOWN"),
                                           ("countTokens", 500, "secret-value", "UNKNOWN")):
            with self.subTest(phase=phase, status=status):
                store = Store(self.root)
                with store.connect() as db:
                    db.execute("DELETE FROM gemini_blocks")
                    db.execute("DELETE FROM gemini_usage")
                requests = []
                def reject(request):
                    requests.append(request.url.path)
                    if not request.url.path.endswith(":" + phase):
                        return httpx.Response(200, json={"totalTokens": 20})
                    return httpx.Response(status, json={"error": {"status": rpc, "message": "secret-value",
                        "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": reason,
                                     "metadata": {"key": "secret-value"}}]}})
                with self.assertRaises(ProviderError) as caught:
                    Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(reject), actor_role="PM")
                error = str(caught.exception)
                self.assertIn("HTTP=" + str(status), error)
                self.assertIn("phase=" + phase, error)
                self.assertIn("status=" + (rpc if rpc != "secret-value" else "UNKNOWN"), error)
                self.assertIn("reason=" + reason, error)
                self.assertNotIn("secret-value", error)
                with store.connect() as db:
                    self.assertEqual(db.execute("SELECT reason FROM gemini_blocks").fetchone()[0], error)
                with self.assertRaises(ProviderError):
                    Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: self.fail("no retry")), actor_role="PM")
                self.assertEqual(len(requests), 2 if phase == "generateContent" else 1)

    def test_invalid_count_never_generates_and_malformed_output_is_safe(self):
        with self.assertRaisesRegex(ProviderError, "INVALID_TOKEN_COUNT"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(lambda r: httpx.Response(200, json={"totalTokens": -1})), actor_role="PM")
        def malicious(request):
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 20})
            return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"functionCall": {"name": "shell"}}]}, "finishReason": "STOP"}]})
        with self.assertRaisesRegex(ProviderError, "TOOL_DENIED"):
            Gemini(self.root).run(SMOKE_PROMPT, lambda *a: self.fail("must not execute"), httpx.MockTransport(malicious), actor_role="PM")

    def test_saved_503_is_reported_as_open_circuit_not_a_new_google_failure(self):
        requests = []
        def unavailable(request):
            requests.append(request.url.path)
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 20})
            return httpx.Response(503, json={"error": {"status": "UNAVAILABLE"}})
        with self.assertRaisesRegex(ProviderError, "^GEMINI_UPSTREAM_REJECTED; HTTP=503"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(unavailable), actor_role="PM")
        with self.assertRaisesRegex(ProviderError, "^GEMINI_CIRCUIT_OPEN; no outbound request; last_error=GEMINI_UPSTREAM_REJECTED; HTTP=503"):
            Gemini(self.root).run(SMOKE_PROMPT, None, httpx.MockTransport(unavailable), actor_role="PM")
        self.assertEqual(len(requests), 2)

    def test_enrollment_reuses_existing_key_and_keeps_off(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "other-value"}):
            enroll(self.root)
        self.assertEqual((self.root / "gemini.key").read_text(), "synthetic")
        self.assertFalse(json.loads((self.root / "gemini.json").read_text())["enabled"])

    def test_enrollment_rejects_truncated_key_without_overwriting_existing_key(self):
        for value in ("x", "short", "AQ." + "x" * 20 + " space", "AQ." + "é" * 30):
            with self.subTest(value_length=len(value)), patch("sys.stdin", io.StringIO(value)), \
                    self.assertRaisesRegex(ValueError, "INVALID_KEY_FORMAT"):
                enroll(self.root, stdin_key=True, replace_key=True)
            self.assertEqual((self.root / "gemini.key").read_text(), "synthetic")
            self.assertFalse(json.loads((self.root / "gemini.json").read_text())["enabled"])

    def test_replace_key_uses_hidden_prompt_not_environment_and_invalidates_proof(self):
        replacement = "AQ." + "fixture-not-a-real-key" * 2
        with patch.dict("os.environ", {"GEMINI_API_KEY": "wrong-environment-value"}), \
                patch("sys.stdin.isatty", return_value=True), patch("getpass.getpass", return_value=replacement) as hidden, \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            enroll(self.root, replace_key=True)
        hidden.assert_called_once()
        self.assertEqual((self.root / "gemini.key").read_text(), replacement)
        self.assertNotIn(replacement, output.getvalue())
        self.assertFalse(json.loads((self.root / "gemini.json").read_text())["enabled"])
        with self.assertRaisesRegex(ProviderError, "DISABLED"):
            Gemini(self.root).settings(require_enabled=False)

    def test_new_enrollment_rejects_one_character_key_before_saving(self):
        (self.root / "gemini.key").unlink()
        with patch("sys.stdin", io.StringIO("x")), self.assertRaisesRegex(ValueError, "INVALID_KEY_FORMAT"):
            enroll(self.root, stdin_key=True)
        self.assertFalse((self.root / "gemini.key").exists())

    def test_status_reports_valid_proof_and_circuit_even_when_off_without_outbound(self):
        state = self.root / "QLDAPM/openproject-ai/stage-ai"
        operator = self.root / "QLDAPM/openproject-ai/operator/gemini-free"
        state.mkdir(parents=True)
        operator.mkdir(parents=True)
        (state / "gemini.key").write_text("synthetic")
        (state / "gemini.json").write_text(canonical({"enabled": False, "model": MODEL}))
        (operator / "free-tier-proof.json").write_text(canonical(self.policy))
        store = Store(state)
        for blocked in (False, True):
            if blocked:
                store.block_gemini("synthetic-project", "GEMINI_UPSTREAM_REJECTED")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(self.root)}), patch("sys.argv", ["free_tier_staging.py", "status"]), \
                    patch("sys.stdout", new_callable=io.StringIO) as output, patch.object(Gemini, "run", side_effect=AssertionError("no outbound")):
                main()
            report = json.loads(output.getvalue())
            self.assertEqual(report["gemini"], "OFF")
            self.assertEqual(report["quota"], self.policy["quota"])
            self.assertEqual(report["project_tier"], "Free")
            self.assertIn("GEMINI_UPSTREAM_REJECTED" if blocked else "provider remains OFF", report["reason"])
            self.assertEqual(report["circuit_latched"], blocked)
            self.assertFalse(report["network_checked"])
            if blocked:
                self.assertTrue(report["reason"].startswith("GEMINI_CIRCUIT_OPEN; no outbound request; last_error="))
        with store.connect() as db:
            db.execute("DELETE FROM gemini_blocks")
        self.continuous_policy()
        self.policy["data_scope"] = "project-metadata-only"
        (operator / "free-tier-proof.json").write_text(canonical(self.policy))
        (state / "gemini.json").write_text(canonical({"enabled": True, "model": MODEL}))
        with patch.dict("os.environ", {"LOCALAPPDATA": str(self.root)}), patch("sys.argv", ["free_tier_staging.py", "status"]), \
                patch("sys.stdout", new_callable=io.StringIO) as output, patch.object(Gemini, "run", side_effect=AssertionError("no outbound")):
            main()
        report = json.loads(output.getvalue())
        self.assertEqual(report["gemini"], "ON_PROJECT_METADATA")
        self.assertEqual(report["authorization_mode"], "continuous-free-only")
        self.assertIsNone(report["expires"])
        self.assertFalse(report["network_checked"])

    def test_verify_reprompts_project_number_without_losing_existing_key(self):
        with patch("builtins.input", side_effect=["123456123456", "", "UPPERCASE", "a" * 31, "qldapm-demo-123", "STOP"]), patch("sys.stdout", new_callable=io.StringIO) as output:
            with self.assertRaisesRegex(PermissionError, "FREE_TIER_NOT_VERIFIED"):
                verify(self.root, self.root / "operator")
        self.assertIn("Project number", output.getvalue())
        self.assertEqual((self.root / "gemini.key").read_text(), "synthetic")
        self.assertFalse((self.root / "operator/free-tier-proof.json").exists())

    def test_configure_model_keeps_existing_key_usage_and_requires_new_matching_proof(self):
        state = self.root / "QLDAPM/openproject-ai/stage-ai"
        state.mkdir(parents=True)
        (state / "gemini.key").write_text("synthetic-existing-key")
        (state / "gemini.json").write_text(canonical({"enabled": True, "model": MODEL}))
        store = Store(state)
        store.reserve_gemini("synthetic-project", {"rpm": 10, "tpm": 1000, "rpd": 10}, 20)
        with patch.dict("os.environ", {"LOCALAPPDATA": str(self.root)}), patch("sys.argv", ["free_tier_staging.py", "configure-model", "--model", "gemini-fixture-new"]), patch("sys.stdout", new_callable=io.StringIO):
            main()
        self.assertEqual((state / "gemini.key").read_text(), "synthetic-existing-key")
        self.assertEqual(json.loads((state / "gemini.json").read_text()), {"enabled": False, "model": "gemini-fixture-new"})
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT count(*),sum(input_tokens) FROM gemini_usage").fetchone()[:], (1, 20))
        with self.assertRaisesRegex(ProviderError, "DISABLED"):
            Gemini(state).settings()

    def test_wizard_manual_stages_never_launch_default_browser(self):
        bash = Path("C:/Program Files/Git/bin/bash.exe")
        if not bash.is_file():
            self.skipTest("Windows Git Bash harness unavailable")
        script = (Path(__file__).resolve().parents[1] / "setup-gemini-free.sh").read_text(encoding="utf-8")
        stages = script[script.index('stage "1.'):script.index('stage "3.')]
        # Execute only guidance stages with browser launch stubbed and confirmations automated; no credentials/Google access.
        helpers = 'open_url() { exit 90; }; step() { :; }; say() { :; }; note() { :; }; confirm() { return 0; }; stage() { :; };\n'
        result = subprocess.run([str(bash), "--noprofile", "--norc", "-c", helpers + stages], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, "Wizard attempted to open the default browser instead of printing manual links")

    def test_rest_mcp_polling_fixed_smoke_and_safe_quota_error(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        from gateway.service import Service
        from tests.test_deep_ai import CoreFixture
        store = Store(self.root)
        token = store.issue_token(21, "BE", "synthetic-native-token")
        service = Service(store, {"users": {"21": "BE"}, "project_id": 5, "hosts": ["testserver"],
            "openproject_url": "http://127.0.0.1:8091"}, self.root / "workspaces", CoreFixture)
        def wait_for_worker():
            self.assertTrue(service.gemini.lock.acquire(timeout=5), "AI worker must finish audit before fixture cleanup")
            service.gemini.lock.release()
        self.addCleanup(wait_for_worker)
        original = Gemini.run
        transport = httpx.MockTransport(self.handler)
        def fake_wire(argv, **options):
            self.assertEqual(argv[1:], ["-m", "gateway.ai_worker"])
            payload = json.loads(options["input"])
            try:
                result = {"result": original(Gemini(self.root), payload["prompt"], None, transport)}
            except ProviderError as error:
                result = {"error": str(error)}
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(result), stderr="")
        with TestClient(create_app(self.root, service)) as client, patch("subprocess.run", fake_wire):
            headers = {"Authorization": "Bearer " + token, "Idempotency-Key": "free-smoke-rest"}
            response = client.post("/api/v1/ai-runs", headers=headers, json={"prompt": SMOKE_PROMPT})
            self.assertEqual(response.status_code, 200)
            identifier = response.json()["result"]["id"]
            for _ in range(100):
                result = service.execute(token, {"action": "get_ai_run", "arguments": {"id": identifier}})["result"]
                if result["state"] != "running":
                    break
                time.sleep(0.01)
            self.assertEqual(result["state"], "done")
            self.assertEqual(result["result"]["text"], "QLDAPM_OK")
            wait_for_worker()
            store.block_gemini("synthetic-project", "GEMINI_QUOTA_429; stopped until local quota recheck")
            response = client.post("/mcp", headers={"Authorization": "Bearer " + token, "Accept": "application/json, text/event-stream"},
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ai_run",
                      "arguments": {"arguments": {"prompt": SMOKE_PROMPT}, "idempotency_key": "free-smoke-mcp"}}})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["result"].get("isError"))
            with store.connect() as db:
                identifier = db.execute("SELECT id FROM ai_runs WHERE id!=?", (identifier,)).fetchone()[0]
            for _ in range(100):
                result = store.run(21, identifier)
                if (result.get("result") or {}).get("queue_state") == "WAITING_QUOTA":
                    break
                time.sleep(0.01)
            self.assertEqual(result["state"], "running")
            self.assertEqual(result["result"]["queue_state"], "WAITING_QUOTA")
            self.assertNotIn("synthetic-native-token", canonical(result))


if __name__ == "__main__":
    unittest.main()

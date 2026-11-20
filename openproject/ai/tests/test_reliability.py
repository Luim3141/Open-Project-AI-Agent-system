import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from gateway.gemini import Gemini
from gateway.native import NativeError
from gateway.presentation import error_info
from gateway.service import Service
from gateway.store import Store


class ReliabilityTests(unittest.TestCase):
    def test_invalid_updates_return_actionable_validation_without_mutation(self):
        class ReadNative:
            def package(self, identifier): return {"id": identifier, "lockVersion": 0}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            service = Service(Store(root), {}, root / "workspaces")
            for changes, reason in ((None, "CHANGES_REQUIRED"), ({}, "CHANGES_REQUIRED"),
                    ({"due_date": "2026-02-31"}, "DUE_DATE_INVALID"), ({"due_date": 20261015}, "DUE_DATE_INVALID")):
                with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, reason):
                    service.perform({"user_id": 8, "role": "PM"}, ReadNative(), "update_work_package", {
                        "id": 58, "lock_version": 0, "changes": changes})
            with self.assertRaisesRegex(ValueError, "ASSIGNEE_ROLE_DENIED"):
                service.role_assignee([])

    def test_waits_before_reserving_without_replaying_outbound_requests(self):
        class Budget:
            attempts = 0
            def reserve_gemini(self, project, limits, tokens):
                self.attempts += 1
                if self.attempts == 1:
                    error = ValueError("GEMINI_LOCAL_RPM_EXHAUSTED")
                    error.retry_at = 110
                    raise error
        budget, events = Budget(), []
        policy = {"project": "fixture", "limits": {}}
        with patch.object(Gemini, "settings", return_value=policy), patch("gateway.gemini.time.time", return_value=100), \
                patch("gateway.gemini.time.monotonic", return_value=0), patch("gateway.gemini.time.sleep") as sleep:
            Gemini(Path(".")).reserve_budget(budget, policy, 123, 600, lambda *args: events.append(args))
        sleep.assert_called_once_with(10)
        self.assertEqual(budget.attempts, 2)
        self.assertEqual(events[-1], (None, None))
        self.assertIn("tự tiếp tục", events[0][0])

    def test_parent_form_error_keeps_field_and_reason(self):
        class FormNative:
            project_id = 3
            def packages(self): return []
            def package(self, identifier): return {"id": identifier}
            def call(self, path, method="GET", payload=None):
                if path.endswith("/form"):
                    return {"_embedded": {"validationErrors": {"parent": {
                        "errorIdentifier": "urn:openproject-org:api:v3:errors:PropertyIsReadOnly",
                        "message": "Cha không thể ghi được."}}}}
                raise AssertionError("A rejected form must never POST a work package")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            service = Service(Store(root), {"source_field": "customField1", "type_ids": [8]}, root / "workspaces")
            with self.assertRaises(NativeError) as caught:
                service.perform({"user_id": 8, "role": "PM"}, FormNative(), "create_work_package", {
                    "source_id": "fixture", "subject": "PM review", "type_id": 8, "parent_id": 58})
            info = error_info(caught.exception)
            self.assertEqual(info["status"], 422)
            self.assertIn("parent", info["details"])
            self.assertIn("Công việc cha", info["message"])
            self.assertFalse(info["outcome_unknown"])

    def test_business_tools_accept_typed_arguments_without_nested_json(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("synthetic-only")
            policy = {"data_scope": "project-business-content", "project": "fixture",
                      "limits": {"rpm": 100, "tpm": 1000000, "rpd": 100}}
            turns = iter([[{"functionCall": {"name": "get_work_package", "args": {"id": 58}}}],
                          [{"text": '{"claims":[],"explanation":"Đã đọc công việc 58"}'}]])
            def wire(request):
                if request.url.path.endswith(":countTokens"):
                    return httpx.Response(200, json={"totalTokens": 100})
                declarations = json.loads(request.content)["tools"][0]["functionDeclarations"]
                self.assertIn("get_work_package", [row["name"] for row in declarations])
                self.assertFalse(any("arguments_json" in row["parameters"].get("properties", {}) for row in declarations))
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": next(turns)}}]})
            calls = []
            def execute(action, arguments):
                calls.append((action, arguments))
                return {"result": {"id": 58, "lockVersion": 0, "_links": {"status": {"href": "/api/v3/statuses/1"}},
                                   "description": {"raw": "Nghiệp vụ"}}}
            with patch.object(Gemini, "settings", return_value=policy):
                result = Gemini(root).run("Đọc công việc 58", execute, httpx.MockTransport(wire), actor_role="PM")
            self.assertEqual(calls, [("get_work_package", {"id": 58})])
            self.assertEqual(result["status"], "answered")

    def test_budget_reserves_counted_tokens_instead_of_utf8_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("synthetic-only")
            policy = {"data_scope": "project-business-content", "project": "fixture",
                      "limits": {"rpm": 100, "tpm": 1000, "rpd": 100}}
            def wire(request):
                if request.url.path.endswith(":countTokens"):
                    return httpx.Response(200, json={"totalTokens": 100})
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                    "role": "model", "parts": [{"text": '{"claims":[],"explanation":"Gợi ý"}'}]}}]})
            with patch.object(Gemini, "settings", return_value=policy):
                result = Gemini(root).run("Phân tích nghiệp vụ " * 100, None, httpx.MockTransport(wire), actor_role="PM")
            self.assertEqual(result["status"], "answered")
            with Store(root).connect() as db:
                self.assertEqual(db.execute("SELECT SUM(input_tokens) FROM gemini_usage").fetchone()[0], 100)

    def test_minute_quota_reports_eligible_time_without_clearing_usage(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            limits = {"rpm": 1, "tpm": 1000, "rpd": 10}
            store.reserve_gemini("fixture", limits, 1)
            with self.assertRaises(ValueError) as caught:
                store.reserve_gemini("fixture", limits, 1)
            self.assertGreater(getattr(caught.exception, "retry_at", 0), time.time())
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 1)

    def test_stale_run_does_not_erase_completed_tool_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            identifier = store.create_run(8)
            tools = [{"action": "comment", "arguments": {"id": 58, "text": "fixture"},
                      "result": {"result": {"id": 20, "native_confirmed": True}}}]
            store.progress_run(8, identifier, {"tools": tools})
            with store.connect() as db:
                db.execute("UPDATE ai_runs SET created=? WHERE id=?", (time.time() - 1000, identifier))
            result = store.run(8, identifier)
            self.assertEqual(result["state"], "failed_or_unknown")
            self.assertEqual(result["result"]["tools"], tools)
            self.assertEqual(result["result"]["status"], "partial")


if __name__ == "__main__":
    unittest.main()

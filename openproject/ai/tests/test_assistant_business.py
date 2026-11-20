import tempfile
import time
import unittest
import json
import os
from gateway.store import digest
from pathlib import Path
from unittest.mock import patch

from gateway.service import Service
from gateway.store import Store
from gateway.gemini import Gemini, ProviderError
from gateway.native import NativeError
from gateway.presentation import requested_ids, action_requested, execution_report
import httpx
from types import SimpleNamespace


class AssistantBusinessTests(unittest.TestCase):
    def test_more_than_six_explicit_or_inferred_scope_ids_reach_worker(self):
        for explicit in (False, True):
            with self.subTest(explicit=explicit), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                store = Store(root)
                service = Service(store, {"gateway_mode": "native", "project_id": 5}, root / "workspaces")
                ids = list(range(51, 59))
                captured = []
                def worker(*arguments):
                    captured.append(arguments[-1])
                    return {"text": "Synthetic receipt"}
                with patch("gateway.service.run_isolated", side_effect=worker), patch.object(service.gemini, "settings", return_value={}):
                    native = SimpleNamespace(package=lambda identifier: {"id": identifier})
                    run = service.perform({"user_id": 8, "role": "PM"}, native, "start_ai_run", {
                        "prompt": "Cập nhật " + " và ".join(f"công việc {identifier}" for identifier in ids),
                        "allow_routine_writes": True, "write_scope_ids": ids if explicit else []})
                    deadline = time.monotonic() + 2
                    while store.run(8, run["id"])["state"] == "running" or service.gemini.lock.locked():
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(0.01)
                self.assertEqual(captured, [ids])

    def test_more_than_six_tools_in_a_batch_and_across_model_turns(self):
        for batch in (False, True):
            with self.subTest(batch=batch), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "gemini.key").write_text("synthetic-only")
                ids = list(range(51, 59))
                calls = [{"functionCall": {"name": "comment", "args": {
                    "id": identifier, "lock_version": 1, "text": "staging"}}} for identifier in ids]
                turns = iter(([calls] if batch else [[call] for call in calls]) + [[{"text": '{"claims":[],"explanation":"Đã thêm bình luận"}'}]])
                policy = {"data_scope": "project-business-content", "project": "fixture",
                          "limits": {"rpm": 100, "tpm": 1000000, "rpd": 100}}
                def wire(request):
                    if request.url.path.endswith(":countTokens"):
                        return httpx.Response(200, json={"totalTokens": 100})
                    return httpx.Response(200, json={"candidates": [{"finishReason": "STOP",
                        "content": {"role": "model", "parts": next(turns)}}]})
                attempts, progress = [], []
                def execute(action, args):
                    attempts.append(args["id"])
                    return {"result": {"id": args["id"] + 100, "_type": "Activity::Comment"}}
                with patch.object(Gemini, "settings", return_value=policy):
                    result = Gemini(root).run("Thêm comment các công việc", execute, httpx.MockTransport(wire), True, ids, progress.append, actor_role="PM")
                self.assertEqual(attempts, ids)
                self.assertEqual(result["status"], "succeeded")
                self.assertEqual(len(progress), 8)
                self.assertEqual(len(result["tools"]), 8)
                self.assertTrue(all(row["state"] == "succeeded" for row in result["outcomes"]))

    def test_explicit_comment_target_with_consent_does_not_require_a_second_id_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            service = Service(store, {"gateway_mode": "native", "project_id": 5}, root / "workspaces")
            captured = []
            def worker(*arguments):
                captured.append(arguments[-1])
                return {"text": "Synthetic receipt"}
            with patch("gateway.service.run_isolated", side_effect=worker), patch.object(service.gemini, "settings", return_value={}):
                native = SimpleNamespace(package=lambda identifier: {"id": identifier})
                run = service.perform({"user_id": 8, "role": "BE"}, native, "start_ai_run", {
                    "prompt": "Thêm comment vào công việc 58: Đã kiểm tra trên staging",
                    "allow_routine_writes": True, "write_scope_ids": []})
                deadline = time.monotonic() + 2
                while store.run(8, run["id"])["state"] == "running" or service.gemini.lock.locked():
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.01)
            self.assertEqual(captured, [[58]], "Checkbox + explicit work-package target must authorize that target only")

    def test_scope_ignores_ids_in_new_comment_and_accepts_native_links(self):
        self.assertEqual(requested_ids("Thêm comment vào công việc 58: hãy sửa ticket 99 #70"), [58])
        self.assertEqual(requested_ids("Sửa công việc 0 và #58 tại /work_packages/58"), [58])
        for action, prompt in (("create_work_package", "Chia công việc 58 thành Subtask"),
                               ("update_work_package", "Giao công việc 58 cho BE, dời deadline"),
                               ("transition", "Đánh dấu công việc 58 đã Done"), ("comment", "Thêm bình luận công việc 58: ok")):
            self.assertTrue(action_requested(prompt, action))
        self.assertFalse(action_requested("Đọc công việc 58: tạo task khác", "create_work_package"))

    def test_native_receipts_override_model_success_and_expose_failure(self):
        calls = [{"action": "comment", "arguments": {"id": 58, "text": "Đã kiểm tra trên staging"},
                  "result": {"result": {"id": 20, "native_confirmed": True}}},
                 {"action": "transition", "arguments": {"id": 58}, "result": {"error": "PermissionError", "message": "Workflow từ chối"}}]
        report = execution_report(calls, "Đã chuyển Done thành công")
        self.assertEqual(report["status"], "partial")
        self.assertIn("#58", report["text"])
        self.assertIn("Đã kiểm tra trên staging", report["text"])
        self.assertIn("Workflow từ chối", report["text"])
        self.assertNotIn("Done thành công", report["text"])
        self.assertEqual(execution_report([{"action": "update_work_package", "result": {"result": {"id": 58}}}])["status"], "failed")

    def test_full_business_projection_excludes_profiles_secrets_but_keeps_comment_context(self):
        row = {"id": 58, "lockVersion": 1, "subject": "Đăng ký học phần",
               "description": {"raw": "Sinh viên chọn học phần. API key: AIza" + "x" * 32 + ' student@example.invalid token: opaque-private-token password="private phrase" Authorization: Bearer private-bearer-token'},
               "_links": {"status": {"href": "/api/v3/statuses/1", "title": "NEW"}, "author": {"title": "Private Name"}},
               "business_comments": [{"id": 11, "comment": {"raw": "Không cho đăng ký khi lớp đã đủ chỗ."}}],
               "business_relations": [{"id": 12, "type": "blocks", "_links": {"to": {"href": "/api/v3/work_packages/59"}}}]}
        result = Gemini.business_result("get_work_package", {"result": row})
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertIn("Không cho đăng ký", encoded)
        self.assertIn("Đăng ký học phần", encoded)
        self.assertIn("work_packages/59", encoded)
        for excluded in ("Private Name", "student@example.invalid", "AIza" + "x" * 32, "opaque-private-token", "private phrase", "private-bearer-token"):
            self.assertNotIn(excluded, encoded)

    def test_business_explanation_requires_exact_claims_and_is_not_accepted_by_legacy_mode(self):
        calls = [{"action": "get_work_package", "result": {"result": {"id": 58}}}]
        body = json.dumps({"claims": [{"tool": 0, "path": ["result", "id"], "value": 58}], "explanation": "Phân tích công việc #58"})
        self.assertEqual(Gemini.validate_claims(body, calls, True)[0]["value"], 58)
        with self.assertRaises(ProviderError): Gemini.validate_claims(body, calls)
        with self.assertRaises(ProviderError): Gemini.validate_claims(body.replace('58}', '59}'), calls, True)

    def test_real_sdk_loop_preserves_partial_tools_and_clear_native_permission_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("synthetic-only")
            policy = {"data_scope": "project-business-content", "project": "fixture", "limits": {"rpm": 100, "tpm": 1000000, "rpd": 100}}
            turns = iter([{"functionCall": {"name": "comment", "args": {"id":58,"lock_version":1,"text":"staging"}}},
                          {"functionCall": {"name": "transition", "args": {"id":58,"lock_version":1,"status_id":17}}},
                          {"text": '{"claims":[],"explanation":"Đã chuyển Done"}'}])
            def wire(request):
                if request.url.path.endswith(":countTokens"): return httpx.Response(200, json={"totalTokens": 100})
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": [next(turns)]}}]})
            def execute(action, args):
                if action == "transition": raise NativeError(403, "OPENPROJECT_403: Forbidden")
                return {"result": {"id": 20, "_type": "Activity::Comment"}}
            progress = []
            with patch.object(Gemini, "settings", return_value=policy):
                report = Gemini(root).run("Thêm comment công việc 58 và chuyển trạng thái", execute, httpx.MockTransport(wire), True, [58], progress.append, actor_role="PM")
            self.assertEqual(report["status"], "partial")
            self.assertEqual(len(progress), 2)
            self.assertEqual(report["outcomes"][0]["state"], "succeeded")
            self.assertEqual(report["outcomes"][1]["state"], "failed")
            self.assertIn("Quyền hiện tại", report["text"])
            self.assertNotIn("Đã chuyển Done", report["text"])

    def test_progress_is_private_and_survives_stop_without_replaying_write(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            identifier = store.create_run(8)
            store.progress_run(9, identifier, {"text": "must not write"})
            self.assertIsNone(store.run(8, identifier)["result"])
            store.progress_run(8, identifier, {"tools": [{"action": "comment"}]})
            self.assertEqual(store.run(8, identifier)["state"], "running")
            self.assertEqual(len(store.run(8, identifier)["result"]["tools"]), 1)

    def test_business_content_needs_its_own_bound_authorization(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("synthetic-only")
            (root / "gemini.json").write_text('{"enabled":true,"model":"gemini-3.5-flash-lite"}')
            policy = {"project": "fixture", "model": "gemini-3.5-flash-lite", "tier": "Free", "billing_enabled": False,
                "terms_reviewed": True, "data_scope": "project-business-content", "verification_method": "manual-official-console",
                "checked_at": time.time(), "evidence_reference": "fixture", "key_sha256": digest("synthetic-only"),
                "quota": {"rpm": 10, "tpm": 10000, "rpd": 100}}
            proof = root / "proof.json"
            proof.write_text(json.dumps(policy))
            with patch.dict(os.environ, {"QLDAPM_AI_ENVIRONMENT": "staging", "QLDAPM_GEMINI_FREE_PROOF": str(proof)}):
                with self.assertRaises(ProviderError): Gemini(root).settings()
                policy["business_content_authorization"] = {"authorized_at": time.time(), "user_request_sha256": digest("explicit fixture consent")}
                proof.write_text(json.dumps(policy))
                self.assertEqual(Gemini(root).settings()["data_scope"], "project-business-content")
                (root / "gemini.key").write_text("changed-synthetic-key")
                with self.assertRaises(ProviderError): Gemini(root).settings()

    def test_update_receipt_describes_changed_fields_in_words(self):
        report = execution_report([{"action": "update_work_package", "arguments": {"id": 58, "changes": {
            "subject": "Tên mới", "due_date": "2026-10-20", "assignee_role": "BE"}}, "result": {"result": {"native_confirmed": True}}}])
        for field in ("Tên công việc: Tên mới", "Hạn hoàn thành: 2026-10-20", "Vai trò phụ trách: BE"):
            self.assertIn(field, report["text"])

    def test_model_cannot_replay_a_write_after_unknown_native_readback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("synthetic-only")
            policy = {"data_scope": "project-business-content", "project": "fixture", "limits": {"rpm": 100, "tpm": 1000000, "rpd": 100}}
            call = {"functionCall": {"name": "comment", "args": {"id":58,"lock_version":1,"text":"staging"}}}
            turns = iter([call, call, {"text": '{"claims":[],"explanation":"Đã ghi hai lần"}'}])
            def wire(request):
                if request.url.path.endswith(":countTokens"): return httpx.Response(200, json={"totalTokens": 100})
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": [next(turns)]}}]})
            attempts = []
            def execute(action, args):
                attempts.append(action)
                raise NativeError(502, "OPENPROJECT_COMMENT_READBACK_MISSING")
            with patch.object(Gemini, "settings", return_value=policy):
                result = Gemini(root).run("Thêm comment công việc 58: staging", execute, httpx.MockTransport(wire), True, [58], actor_role="PM")
            self.assertEqual(attempts, ["comment"])
            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["tools"][0]["result"]["outcome_unknown"])
            self.assertIn("tránh ghi trùng", result["text"])
            self.assertNotIn("Đã ghi hai lần", result["text"])

    def test_historical_tool_refusal_is_visible_without_changing_or_replaying_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            identifier = store.create_run(8)
            legacy = {"text": "get_work_package id:58", "tools": [{"action": "comment", "result": {
                "error": "PermissionError", "message": "Arguments, permission or version rejected."}}]}
            store.finish_run(8, identifier, legacy, "done")
            result = Service(store, {"gateway_mode": "native", "project_id": 5}, root / "workspaces").perform({"user_id": 8, "role": "BE"}, None,
                "get_ai_run", {"id": identifier})
            self.assertEqual(result["result"]["status"], "failed")
            self.assertIn("chưa có xác nhận ghi thành công", result["result"]["text"])
            self.assertEqual(store.run(8, identifier)["result"], legacy)


if __name__ == "__main__":
    unittest.main()

"""Fixed populated-project migration checks; synthetic data, no Jira requests."""
import copy
import json
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_admin_mcp as admin


def issues():
    rows = []
    for number in range(1, 330):
        type_id = "10000" if number <= 11 else "10011" if number <= 64 else "10010"
        data = {"project": {"id": "10002", "key": "QAG3"}, "summary": f"Synthetic {number}",
                "issuetype": {"id": type_id}, "status": {"id": "10009" if number < 317 else "3"},
                "labels": ["qag3-simulation"], "assignee": {"accountId": admin.ACCOUNT_ID},
                "resolution": {"id": "10000"} if number < 317 else None,
                "updated": "2026-10-11T10:00:00Z", "description": None,
                "duedate": None, "timespent": 3600}
        if number > 11:
            parent = 1 if number <= 64 else 12
            data["parent"] = {"id": str(10000 + parent), "key": f"QAG3-{parent}"}
        rows.append({"id": str(10000 + number), "key": f"QAG3-{number}", "fields": data})
    return rows


def pages(rows):
    return [{"issues": rows[start:start + 100], "isLast": start + 100 >= len(rows),
             **({"nextPageToken": f"cursor-{start}"} if start + 100 < len(rows) else {})}
            for start in range(0, len(rows), 100)]


class SwitchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="qag3-switch-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = patch.object(admin, "AUDIT_ROOT", Path(self.temp.name))
        self.root.start()
        self.addCleanup(self.root.stop)

    def test_all_pages_fields_and_unknown_null_preserved(self):
        rows = issues()
        del rows[0]["fields"]["duedate"]
        with patch.object(admin, "request", side_effect=pages(rows)) as call:
            snapshot = admin.switch_issue_snapshot()
        self.assertEqual(snapshot["count"], 329)
        self.assertTrue(snapshot["readComplete"])
        self.assertEqual(call.call_count, 4)
        self.assertNotIn("duedate", snapshot["issues"][0]["fields"])
        self.assertIsNone(snapshot["issues"][1]["fields"]["duedate"])
        self.assertIn("nextPageToken", call.call_args.kwargs["params"])
        self.assertNotIn("parent", snapshot["issues"][0]["fields"])

    def test_incomplete_duplicate_foreign_status_and_count_block(self):
        mutations = [lambda rows: rows[0]["fields"].pop("assignee"),
                     lambda rows: rows[0].update(key="KAN-1"),
                     lambda rows: rows[0]["fields"]["status"].update(id="10008"),
                     lambda rows: rows[1].update(id=rows[0]["id"]),
                     lambda rows: rows[12]["fields"]["parent"].update(key="QAG3-12"),
                     lambda rows: rows[12]["fields"]["parent"].update(id="wrong-id"),
                     lambda rows: rows.pop(),
                     lambda rows: rows[0]["fields"].update(labels=[])]
        for mutate in mutations:
            rows = issues()
            mutate(rows)
            with self.subTest(mutate=mutate), patch.object(admin, "request", side_effect=pages(rows)):
                with self.assertRaises(ValueError):
                    admin.switch_issue_snapshot()

    def test_cursor_and_islast_required(self):
        for response in ({"issues": []}, {"issues": [], "isLast": False},
                         {"issues": issues()[:100], "isLast": False}):
            with self.subTest(response=response), patch.object(admin, "request", return_value=response):
                with self.assertRaises(ValueError):
                    admin.switch_issue_snapshot()
        response = {"issues": issues()[:100], "isLast": False, "nextPageToken": "same"}
        with patch.object(admin, "request", return_value=response), self.assertRaises(ValueError):
            admin.switch_issue_snapshot()

    def prepared(self, required, association=None, target=None):
        configs = {kind: {"statuses": [], "workflows": [{"id": wid, "name": admin.NAMES[kind],
                    "version": {"id": "v1", "versionNumber": 1},
                    "transitions": [],
                    "statuses": [{"statusReference": ref} for ref in ("3", "10009", "10010")]}]}
                   for kind, wid in admin.WORKFLOWS.items()}
        target = target if target is not None else {
            "id": "10004", "name": admin.SCHEME_NAME, "draft": False,
            "defaultWorkflow": admin.NAMES["task"],
            "issueTypeMappings": {admin.TYPE_IDS[k]: admin.NAMES[k] for k in admin.WORKFLOWS}}
        association = association if association is not None else {
            "values": [{"projectIds": ["10002"], "workflowScheme": {"id": 10003}}]}
        with patch.object(admin, "preflight", return_value={"permissions": {"ADMINISTER": True}}), \
                patch.object(admin, "scheme", return_value=target), \
                patch.object(admin, "inspect_scheme", return_value={"association": association}), \
                patch.object(admin, "workflow", side_effect=lambda k: configs[k]), \
                patch.object(admin, "switch_issue_snapshot", return_value={"issues": issues(), "count": 329}), \
                patch.object(admin, "rollout_blockers", return_value=["E2E missing"]), \
                patch.object(admin, "request", return_value=required) as call:
            result = admin.prepare("switch_scheme", {})
            self.assertEqual(call.call_args.args, ("POST", "/workflowscheme/update/mappings"))
            self.assertEqual(call.call_args.kwargs["body"]["id"], "10003")
            self.assertNotIn("projectId", call.call_args.kwargs["body"])
            return result

    def test_prepare_no_empty_project_check_and_gate_still_blocks(self):
        with patch.object(admin, "empty_project", side_effect=AssertionError("wrong endpoint")):
            current = self.prepared({"statusMappingsByIssueTypes": [], "statusMappingsByWorkflows": []})
        self.assertEqual(current["payload"], {"projectId": "10002", "targetSchemeId": "10004",
                                              "mappingsByIssueTypeOverride": []})
        self.assertEqual(current["blockers"], ["E2E missing"])
        with patch.object(admin, "prepare", return_value=current):
            saved = admin.preview_scheme_switch()
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "ROLLOUT_BLOCKED"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            call.assert_not_called()

    def test_required_mappings_only_known_baseline(self):
        required = {"statusMappingsByIssueTypes": [{"issueTypeId": "10000", "statusIds": ["10008"]}],
                    "statusMappingsByWorkflows": [{"sourceWorkflowId": admin.SWITCH_SOURCE_WORKFLOW_ID,
                        "targetWorkflowId": admin.WORKFLOWS["task"], "statusIds": ["10008"]}]}
        current = self.prepared(required)
        self.assertEqual(current["payload"]["mappingsByIssueTypeOverride"], [
            {"issueTypeId": "10000", "statusMappings": [{"oldStatusId": "10008", "newStatusId": "10010"}]},
            {"issueTypeId": "10011", "statusMappings": [{"oldStatusId": "10008", "newStatusId": "10010"}]}])
        for invalid in ({}, {"statusMappingsByIssueTypes": [], "statusMappingsByWorkflows": None},
                        {"statusMappingsByIssueTypes": [{"issueTypeId": "999", "statusIds": []}], "statusMappingsByWorkflows": []},
                        {"statusMappingsByIssueTypes": [{"issueTypeId": "10000", "statusIds": ["999"]}], "statusMappingsByWorkflows": []},
                        {"statusMappingsByIssueTypes": [], "statusMappingsByWorkflows": [{"sourceWorkflowId": "foreign", "statusIds": [], "targetWorkflowId": admin.WORKFLOWS["task"]}]}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.prepared(invalid)

    def test_source_target_and_arguments_cannot_expand_scope(self):
        for association in ({"values": []}, {"values": [{"projectIds": ["10001"], "workflowScheme": {"id": 10003}}]},
                            {"values": [{"projectIds": ["10002"], "workflowScheme": {"id": 10004}}]}):
            with self.subTest(association=association), self.assertRaisesRegex(ValueError, "SOURCE_ASSOCIATION"):
                self.prepared({}, association=association)
        with self.assertRaisesRegex(ValueError, "TARGET_MAPPING"):
            self.prepared({}, target={"id": "10004", "draft": True})
        with patch.object(admin, "preflight", return_value={"permissions": {"ADMINISTER": True}}), \
                patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "ARGUMENTS"):
                admin.prepare("switch_scheme", {"projectId": "KAN"})
            call.assert_not_called()
        with self.assertRaisesRegex(ValueError, "SCOPE_REJECTED"):
            admin.request("POST", "/workflowscheme/project/switch", body={"projectId": "10001"})
        with self.assertRaisesRegex(ValueError, "MAPPING_SCOPE_REJECTED"):
            admin.request("POST", "/workflowscheme/update/mappings", body={"id": "10001"})

    def test_apply_switch_is_one_async_post_and_no_replay(self):
        current = self.prepared({"statusMappingsByIssueTypes": [], "statusMappingsByWorkflows": []})
        current["blockers"] = []  # Synthetic unit fixture only; never Jira qualification evidence.
        with patch.object(admin, "prepare", return_value=current):
            saved = admin.preview_scheme_switch()
        with patch.object(admin, "prepare", return_value=current), \
                patch.object(admin, "request", return_value={"taskId": "task-1"}) as call:
            result = admin.apply_change(saved["previewId"], saved["fingerprint"])
            self.assertEqual(result["status"], "PENDING")
            call.assert_called_once_with("POST", "/workflowscheme/project/switch", body=current["payload"], expected=(303,))
            with self.assertRaisesRegex(ValueError, "ALREADY_ATTEMPTED"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])

    def test_switch_snapshot_change_invalidates_approval(self):
        current = self.prepared({"statusMappingsByIssueTypes": [], "statusMappingsByWorkflows": []})
        with patch.object(admin, "prepare", return_value=current):
            saved = admin.preview_scheme_switch()
        changed = copy.deepcopy(current)
        changed["before"]["issues"]["issues"][0]["fields"]["summary"] = "changed"
        with patch.object(admin, "prepare", return_value=changed), patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "PREVIEW_STALE"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            call.assert_not_called()

    def test_mapping_list_order_does_not_invalidate_preview(self):
        required = {"statusMappingsByIssueTypes": [
            {"issueTypeId": "10000", "statusIds": ["10008", "3"]},
            {"issueTypeId": "10011", "statusIds": ["10008"]}],
            "statusMappingsByWorkflows": [], "statuses": [{"id": "3"}, {"id": "10008"}],
            "statusesPerWorkflow": [{"workflowId": admin.WORKFLOWS["task"], "statuses": ["3", "10010"]}]}
        first = self.prepared(copy.deepcopy(required))
        required["statusMappingsByIssueTypes"].reverse()
        required["statusMappingsByIssueTypes"][1]["statusIds"].reverse()
        required["statuses"].reverse()
        required["statusesPerWorkflow"][0]["statuses"].reverse()
        self.assertEqual(admin.preview_fingerprint(first), admin.preview_fingerprint(self.prepared(required)))

    def poll_fixture(self):
        current = self.prepared({"statusMappingsByIssueTypes": [], "statusMappingsByWorkflows": []})
        with patch.object(admin, "prepare", return_value=current):
            saved = admin.preview_scheme_switch()
        admin.save_record(admin.AUDIT_ROOT / (saved["previewId"] + ".result.json"), {"status": "PENDING", "taskId": "task-1"})
        return saved, current

    def test_poll_never_claims_complete_on_pending_failed_unknown(self):
        saved, _ = self.poll_fixture()
        for state in ("ENQUEUED", "RUNNING", "FAILED", "CANCELLED", "DEAD", "unexpected"):
            with self.subTest(state=state), patch.object(admin, "preflight"), \
                    patch.object(admin, "request", return_value={"id": "task-1", "status": state}) as call:
                self.assertFalse(admin.inspect_scheme_switch_result(saved["previewId"])["verified"])
                call.assert_called_once_with("GET", "/task/task-1")
        with patch.object(admin, "preflight"), patch.object(admin, "request", return_value={"id": "other", "status": "COMPLETE"}):
            with self.assertRaisesRegex(ValueError, "TASK_TARGET"):
                admin.inspect_scheme_switch_result(saved["previewId"])
        for identifier in (str(uuid.uuid4()), "../elsewhere"):
            with self.assertRaises((ValueError, FileNotFoundError)):
                admin.inspect_scheme_switch_result(identifier)

    def test_complete_requires_actual_association_and_preserved_data(self):
        saved, current = self.poll_fixture()
        actual = copy.deepcopy(current["before"]["issues"])
        actual["issues"][0]["fields"]["updated"] = "new migration time"
        association = {"values": [{"projectIds": ["10002"], "workflowScheme": {"id": 10004}}]}
        with patch.object(admin, "preflight"), \
                patch.object(admin, "request", return_value={"id": "task-1", "status": "COMPLETE"}), \
                patch.object(admin, "inspect_scheme", return_value={"association": association}), \
                patch.object(admin, "scheme", return_value=current["before"]["target"]), \
                patch.object(admin, "switch_issue_snapshot", return_value=actual):
            result = admin.inspect_scheme_switch_result(saved["previewId"])
            self.assertTrue(result["verified"])
            self.assertEqual(result["issueCountVerified"], 329)
            self.assertFalse(result["worklogDetailsVerified"])
            first = (admin.AUDIT_ROOT / (saved["previewId"] + ".completed.json")).read_bytes()
            admin.inspect_scheme_switch_result(saved["previewId"])
            self.assertEqual(first, (admin.AUDIT_ROOT / (saved["previewId"] + ".completed.json")).read_bytes())
            actual["issues"][0]["fields"]["resolution"] = None
            with self.assertRaisesRegex(ValueError, "ISSUE_READBACK"):
                admin.inspect_scheme_switch_result(saved["previewId"])
            association["values"][0]["workflowScheme"]["id"] = 10003
            with self.assertRaisesRegex(ValueError, "ASSOCIATION_READBACK"):
                admin.inspect_scheme_switch_result(saved["previewId"])


if __name__ == "__main__":
    unittest.main()

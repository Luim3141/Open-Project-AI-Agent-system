"""Synthetic admin mutations: no live Jira writes or real secrets."""
import copy
import json
import os
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_admin_mcp as admin


def sample_workflow():
    return {"statuses": [{"id": "10009", "statusReference": "10009", "name": "Done", "statusCategory": "DONE"},
                         {"id": "3", "statusReference": "3", "name": "In Progress", "statusCategory": "IN_PROGRESS"}],
            "workflows": [{"id": admin.WORKFLOWS["epic"], "name": admin.NAMES["epic"],
                           "version": {"id": "v1", "versionNumber": 1}, "isEditable": True,
                           "statuses": [{"statusReference": "10009", "properties": {}},
                                        {"statusReference": "3", "properties": {}}],
                           "transitions": [{"id": "6", "name": "Accept Epic", "type": "DIRECTED",
                                            "toStatusReference": "10009", "links": [], "actions": [],
                                            "conditions": {"operation": "ALL", "conditions": [{"ruleKey": "existing-gate"}]},
                                            "validators": [{"ruleKey": "existing-validator"}]},
                                           {"id": "8", "name": "Reopen", "type": "DIRECTED",
                                            "toStatusReference": "3", "links": [], "actions": [], "validators": []}]}]}


class ChangeTests(unittest.TestCase):
    def subtask_fixture(self):
        definitions = [("10010", "NEW", "TODO"), ("3", "In Progress", "IN_PROGRESS"),
                       ("10012", "REVIEW", "IN_PROGRESS"), ("10009", "Done", "DONE")]
        statuses = [{"id": ref, "statusReference": ref, "name": name, "statusCategory": category}
                    for ref, name, category in definitions]
        transitions = []
        for index, (name, source, target) in enumerate((
            ("Create", None, "10010"), ("Start work", "10010", "3"),
            ("Submit work", "3", "10012"), ("Approve work", "10012", "10009"),
            ("Rework", "10012", "3"), ("Reopen", "10009", "3")), 1):
            transitions.append({"id": str(index), "name": name, "type": "DIRECTED" if source else "INITIAL",
                "toStatusReference": target, "links": [{"fromStatusReference": source}] if source else [],
                "actions": [{"ruleKey": "retained-resolution"}] if name in ("Approve work", "Reopen") else [],
                "validators": [{"ruleKey": "retained-validator"}]})
        before = {"statuses": statuses, "workflows": [{"id": admin.WORKFLOWS["subtask"],
            "name": admin.NAMES["subtask"], "version": {"id": "v1", "versionNumber": 1},
            "isEditable": True, "statuses": [{"statusReference": s["id"], "properties": {}} for s in statuses],
            "transitions": transitions}]}
        task = {"statuses": [{"id": ref, "statusReference": ref, "name": name, "statusCategory": "IN_PROGRESS"}
                             for ref, name in (("10016", "CODE REVIEW"), ("10017", "READY FOR TEST"), ("10018", "IN TESTING"))]}
        return before, task

    def test_subtask_paths_preserve_resolution_gates_and_no_input_mutation(self):
        before, task = self.subtask_fixture()
        original = copy.deepcopy(before)
        before["workflows"][0]["transitions"][2]["conditions"] = {"operation": "ALL", "conditions": [{"ruleKey": "retained-condition"}]}
        original = copy.deepcopy(before)
        payload = admin.subtask_delivery_payload(before, task)
        self.assertEqual(before, original)
        workflow = payload["workflows"][0]
        self.assertEqual(len(workflow["statuses"]), 7)
        self.assertEqual(len(workflow["transitions"]), 13)
        self.assertEqual(len({t["id"] for t in workflow["transitions"]}), 13)
        for old in original["workflows"][0]["transitions"]:
            new = next(t for t in workflow["transitions"] if t["id"] == old["id"])
            for key in ("name", "links", "toStatusReference", "actions", "validators"):
                self.assertEqual(old[key], new[key])
        submit = next(t for t in workflow["transitions"] if t["name"] == "Submit work")
        self.assertEqual(submit["conditions"]["conditionGroups"][0], before["workflows"][0]["transitions"][2]["conditions"])
        business = submit["conditions"]["conditionGroups"][1]
        self.assertEqual(business["operation"], "ANY")
        self.assertEqual({json.loads(c["parameters"]["fieldValue"])[0] for c in business["conditions"]}, set(admin.BUSINESS_ASSIGNEES))
        for transition in workflow["transitions"][6:]:
            self.assertEqual(transition["conditions"]["operation"], "ANY")
            values = set()
            for condition in transition["conditions"]["conditions"]:
                route = condition["parameters"]
                self.assertEqual(route["fieldId"], "assignee")
                self.assertEqual(route["comparisonType"], "OPTIONID")
                self.assertEqual(len(json.loads(route["fieldValue"])), 1)
                values.update(json.loads(route["fieldValue"]))
            self.assertEqual(values, set(admin.DEVELOPMENT_ASSIGNEES))
        self.assertFalse(set(admin.BUSINESS_ASSIGNEES) & set(admin.DEVELOPMENT_ASSIGNEES))
        self.assertFalse(any(t["type"] == "GLOBAL" for t in workflow["transitions"]))

    def test_subtask_rejects_unknown_baseline_statuses_or_noneditable(self):
        for fault in ("transitions", "statuses", "editable", "development"):
            before, task = self.subtask_fixture()
            if fault == "transitions":
                before["workflows"][0]["transitions"][0]["name"] = "Unknown"
            elif fault == "statuses":
                before["statuses"][0]["name"] = "Foreign"
            elif fault == "editable":
                before["workflows"][0]["isEditable"] = False
            else:
                task["statuses"] = []
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                admin.subtask_delivery_payload(before, task)

    def test_active_subtask_cannot_be_edited_and_other_kind_rejected(self):
        with patch.object(admin, "usages", return_value=[{"id": admin.PROJECT_ID}]), patch.object(admin, "workflow") as call:
            with self.assertRaisesRegex(ValueError, "ACTIVE"):
                admin.prepare("subtask_delivery", {"kind": "subtask"})
            with self.assertRaisesRegex(ValueError, "SUBTASK_ONLY"):
                admin.prepare("subtask_delivery", {"kind": "task"})
            call.assert_not_called()

    def test_subtask_prepare_validation_is_not_workflow_update(self):
        before, task = self.subtask_fixture()
        for errors in ([], [{"level": "ERROR"}], None):
            with self.subTest(errors=errors), patch.object(admin, "usages", return_value=[]), patch.object(
                admin, "workflow", side_effect=[before, task]), patch.object(admin, "request", return_value={"errors": errors}) as call:
                plan = admin.prepare("subtask_delivery", {"kind": "subtask"})
                self.assertEqual(bool(plan["blockers"]), errors != [])
                self.assertEqual(call.call_args.args, ("POST", "/workflows/update/validation"))
                self.assertFalse(plan["diff"]["activated"])
                self.assertEqual(plan["diff"]["issuesChanged"], 0)

    def test_subtask_apply_uses_approved_payload_and_readback_no_scheme_change(self):
        before, task = self.subtask_fixture()
        payload = admin.subtask_delivery_payload(before, task)
        current = {"operation": "subtask_delivery", "arguments": {"kind": "subtask"},
            "before": before, "payload": payload, "diff": ["fixed graph"], "blockers": [], "rollback": "review"}
        with patch.object(admin, "prepare", return_value=current):
            saved = admin.preview("subtask_delivery", current["arguments"])
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request") as call, patch.object(
            admin, "workflow", return_value=payload):
            self.assertEqual(admin.apply_change(saved["previewId"], saved["fingerprint"])["status"], "VERIFIED")
            call.assert_called_once_with("POST", "/workflows/update", body=payload)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="qag3-admin-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root_patch = patch.object(admin, "AUDIT_ROOT", Path(self.temp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.preflight_patch = patch.object(admin, "preflight", return_value={
            "permissions": {"ADMINISTER": True, "ADMINISTER_PROJECTS": False}})
        self.preflight_patch.start()
        self.addCleanup(self.preflight_patch.stop)

    def plan(self, operation="workflow_resolution", blockers=None):
        current = {"operation": operation, "arguments": {"kind": "epic"}, "before": {"version": 1},
                   "payload": {"workflows": []}, "diff": [], "blockers": blockers or [], "rollback": "review"}
        with patch.object(admin, "prepare", return_value=copy.deepcopy(current)):
            saved = admin.preview(operation, current["arguments"])
        return saved, current

    def test_wrong_approval_and_expiry_never_call_http(self):
        saved, current = self.plan()
        with patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "APPROVAL"):
                admin.apply_change(saved["previewId"], "not-approved")
            with patch.object(admin.time, "time", return_value=saved["createdAtEpoch"] + 901):
                with self.assertRaisesRegex(ValueError, "EXPIRED"):
                    admin.apply_change(saved["previewId"], saved["fingerprint"])
            call.assert_not_called()

    def test_stale_preview_has_no_write(self):
        saved, current = self.plan()
        current["before"]["version"] = 2
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "STALE"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            call.assert_not_called()

    def test_preview_ignores_generated_rule_ids_but_detects_real_changes(self):
        current = {"operation": "subtask_delivery", "arguments": {"kind": "subtask"},
                   "before": sample_workflow(), "payload": sample_workflow(),
                   "diff": [], "blockers": [], "rollback": "review"}
        with patch.object(admin, "prepare", return_value=copy.deepcopy(current)):
            saved = admin.preview(current["operation"], current["arguments"])
        current["before"]["workflows"][0]["transitions"][0]["validators"][0]["id"] = "new-generated-id"
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request") as call:
            self.assertEqual(admin.apply_change(saved["previewId"], saved["fingerprint"])["status"], "NOOP")
            call.assert_not_called()
        for field, value in (("version", {"id": "v2", "versionNumber": 2}),
                             ("id", "different-workflow"), ("description", "edited-description")):
            with patch.object(admin, "prepare", return_value=copy.deepcopy(current)):
                fresh = admin.preview(current["operation"], current["arguments"])
            changed = copy.deepcopy(current)
            changed["before"]["workflows"][0][field] = value
            with patch.object(admin, "prepare", return_value=changed), patch.object(admin, "request") as call:
                with self.assertRaisesRegex(ValueError, "STALE"):
                    admin.apply_change(fresh["previewId"], fresh["fingerprint"])
                call.assert_not_called()
        with patch.object(admin, "prepare", return_value=copy.deepcopy(current)):
            fresh = admin.preview(current["operation"], current["arguments"])
        current["before"]["workflows"][0]["transitions"][0]["validators"][0]["parameters"] = {"statusIds": "other"}
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "STALE"):
                admin.apply_change(fresh["previewId"], fresh["fingerprint"])
            call.assert_not_called()

    def test_blocker_never_writes(self):
        saved, current = self.plan(blockers=["gates untested"])
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "ROLLOUT_BLOCKED"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            call.assert_not_called()

    def test_noop_and_replay(self):
        saved, current = self.plan()
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request") as call:
            self.assertEqual(admin.apply_change(saved["previewId"], saved["fingerprint"])["status"], "NOOP")
            with self.assertRaisesRegex(ValueError, "ALREADY_ATTEMPTED"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            call.assert_not_called()

    def test_lock_blocks_parallel_process(self):
        admin.save_record(admin.AUDIT_ROOT / "apply.lock", {"pid": "synthetic"})
        with patch.object(admin, "prepare") as call:
            with self.assertRaisesRegex(ValueError, "LOCKED"):
                admin.apply_change(str(uuid.uuid4()), "hash")
            call.assert_not_called()
        self.assertTrue((admin.AUDIT_ROOT / "apply.lock").exists())

    def test_path_traversal_rejected(self):
        for identifier in ("../foreign", "https://evil.test", "C:/token"):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                admin.apply_change(identifier, "hash")

    def test_audit_redacts_environment_token(self):
        with patch.dict(os.environ, {"QLDAPM_JIRA_ADMIN_TOKEN": "synthetic-sensitive"}):
            path = admin.AUDIT_ROOT / "audit.json"
            admin.save_record(path, {"message": "synthetic-sensitive"})
            self.assertNotIn("synthetic-sensitive", path.read_text())
            with self.assertRaises(FileExistsError):
                admin.save_record(path, {})

    def test_audit_failure_prevents_write(self):
        saved, current = self.plan()
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "save_record", side_effect=OSError), patch.object(admin, "request") as call:
            with self.assertRaises(OSError):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            call.assert_not_called()

    def test_all_usage_pages_checked_for_foreign_project(self):
        pages = [{"workflowId": "wf", "projects": {"values": [{"id": admin.PROJECT_ID}], "nextPageToken": "next"}},
                 {"workflowId": "wf", "projects": {"values": [{"id": "10001"}]}}]
        with patch.object(admin, "request", side_effect=pages) as call:
            with self.assertRaisesRegex(ValueError, "SHARED"):
                admin.usages("/usage", "workflowId", "wf")
            self.assertEqual(call.call_count, 2)

    def test_usage_missing_and_loop_rejected(self):
        for response in ({"workflowId": "wf", "projects": {}},
                         {"workflowId": "wf", "projects": {"values": [], "nextPageToken": "same"}}):
            with self.subTest(response=response), patch.object(admin, "request", return_value=response):
                with self.assertRaises(ValueError):
                    admin.usages("/usage", "workflowId", "wf")

    def test_legacy_simplified_scheme_cannot_be_modified(self):
        with patch.object(admin, "request", return_value={"id": "10003", "name": "QAG3: Software Simplified Workflow Scheme"}):
            with self.assertRaisesRegex(ValueError, "NOT_MANAGED"):
                admin.scheme("10003")

    def test_not_empty_or_unknown_never_associated(self):
        for data in ({"issues": [{"key": "QAG3-1"}], "isLast": True}, {"issues": []}, {"issues": [], "isLast": False}):
            with self.subTest(data=data), patch.object(admin, "request", return_value=data):
                with self.assertRaisesRegex(ValueError, "EMPTY"):
                    admin.empty_project()

    def test_unknown_rollout_is_blocked(self):
        self.assertTrue(admin.rollout_blockers())

    def test_current_signed_off_configuration_evidence_and_stale(self):
        configs = {k: {"kind": k, "version": 1} for k in admin.WORKFLOWS}
        evidence = {"project": "QAG3", "cloudId": admin.CLOUD_ID, "reviewedBy": admin.ACCOUNT_ID,
                    "source": "jira-e2e", "observedAtEpoch": time.time(),
                    "tests": {f"T{i:02}": "PASS" for i in range(1, 24)},
                    "workflowFingerprints": {k: admin.digest(v) for k, v in configs.items()}}
        admin.save_record(admin.AUDIT_ROOT / "rollout-evidence.json", evidence)
        with patch.object(admin, "workflow", side_effect=lambda k: configs[k]):
            self.assertEqual(admin.rollout_blockers(), [])
            configs["epic"]["version"] = 2
            self.assertTrue(admin.rollout_blockers())

    def test_additive_resolution_keeps_existing_gates_and_global_statuses(self):
        before = sample_workflow()
        with patch.object(admin, "workflow", return_value=before), patch.object(admin, "request", side_effect=[
            [{"id": "10000", "name": "Done"}], {"errors": []}]):
            preview = admin.prepare("workflow_resolution", {"kind": "epic"})
        actual = preview["payload"]["workflows"][0]
        self.assertEqual(actual["transitions"][0]["conditions"], before["workflows"][0]["transitions"][0]["conditions"])
        self.assertEqual(actual["transitions"][0]["validators"], before["workflows"][0]["transitions"][0]["validators"])
        self.assertEqual(preview["payload"]["statuses"], before["statuses"])
        self.assertEqual(len(preview["diff"]), 2)
        self.assertEqual(before["workflows"][0]["transitions"][0]["actions"], [])

    def test_resolution_conflict_stops_before_validation(self):
        before = sample_workflow()
        before["workflows"][0]["transitions"][0]["actions"] = [{"ruleKey": "system:update-field", "parameters": {"field": "resolution", "value": "wrong"}}]
        with patch.object(admin, "workflow", return_value=before), patch.object(admin, "request", return_value=[{"id": "10000", "name": "Done"}]) as call:
            with self.assertRaisesRegex(ValueError, "CONFLICT"):
                admin.prepare("workflow_resolution", {"kind": "epic"})
            self.assertEqual(call.call_count, 1)

    def test_semantic_readback_ignores_only_rule_ids(self):
        original = sample_workflow()["workflows"][0]
        actual = copy.deepcopy(original)
        actual["transitions"][0]["validators"][0]["id"] = "server-generated"
        self.assertEqual(admin.workflow_semantics(original), admin.workflow_semantics(actual))
        actual["transitions"][0]["validators"] = []
        self.assertNotEqual(admin.workflow_semantics(original), admin.workflow_semantics(actual))

    def test_semantic_readback_accepts_status_transition_order_not_action_order(self):
        original = sample_workflow()["workflows"][0]
        original["transitions"][0]["actions"] = [{"ruleKey": "first"}, {"ruleKey": "second"}]
        actual = copy.deepcopy(original)
        actual["statuses"].reverse()
        actual["transitions"].reverse()
        self.assertEqual(admin.workflow_semantics(original), admin.workflow_semantics(actual))
        actual["transitions"][1]["actions"].reverse()
        self.assertNotEqual(admin.workflow_semantics(original), admin.workflow_semantics(actual))
        actual = copy.deepcopy(original)
        actual["transitions"][0]["toStatusReference"] = "3"
        self.assertNotEqual(admin.workflow_semantics(original), admin.workflow_semantics(actual))

    def test_workflow_write_checks_gates_after_write(self):
        current = {"operation": "workflow_resolution", "arguments": {"kind": "epic"},
                   "before": sample_workflow(), "payload": sample_workflow(), "diff": ["add"],
                   "blockers": [], "rollback": "review"}
        with patch.object(admin, "prepare", return_value=current):
            saved = admin.preview(current["operation"], current["arguments"])
        changed = sample_workflow()
        changed["workflows"][0]["transitions"][0]["validators"] = []
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request"), patch.object(admin, "workflow", return_value=changed):
            with self.assertRaisesRegex(ValueError, "OUTCOME_UNKNOWN"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
        unknown = json.loads((admin.AUDIT_ROOT / (saved["previewId"] + ".unknown.json")).read_text())
        self.assertEqual(unknown["errorCode"], "READBACK_MISMATCH")

    def test_created_scheme_readback_and_no_activation(self):
        saved, current = self.plan("create_scheme")
        actual = {"id": "10004", **current["payload"]}
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request", return_value={"id": "10004"}) as call, patch.object(admin, "scheme", return_value=actual):
            result = admin.apply_change(saved["previewId"], saved["fingerprint"])
            self.assertEqual(result["status"], "VERIFIED")
            self.assertFalse(result["activated"])
            self.assertEqual(call.call_count, 1)
            self.assertEqual(call.call_args.args, ("POST", "/workflowscheme"))

    def test_validation_errors_block_apply(self):
        for data in ({}, {"errors": [{"level": "ERROR"}]}):
            with self.subTest(data=data), patch.object(admin, "workflow", return_value=sample_workflow()), patch.object(admin, "request", side_effect=[[{"id": "10000", "name": "Done"}], data]):
                self.assertTrue(admin.prepare("workflow_resolution", {"kind": "epic"})["blockers"])

    def test_non_admin_cannot_prepare_writes(self):
        with patch.object(admin, "preflight", return_value={"permissions": {"ADMINISTER": False}}), patch.object(admin, "request") as call:
            with self.assertRaisesRegex(ValueError, "ADMINISTER_REQUIRED"):
                admin.prepare("create_scheme", {})
            call.assert_not_called()

    def test_existing_scheme_prevents_duplicate(self):
        with patch.object(admin, "request", return_value={"values": [{"name": admin.SCHEME_NAME}], "isLast": True}):
            with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                admin.prepare("create_scheme", {})

    def test_automation_scope_and_unsafe_pagination(self):
        responses = [{"data": [{"ruleScopeARIs": [admin.SCOPE_ARI, "foreign"]}], "links": {}},
                     {"data": [], "links": {"next": "https://evil.test?cursor=x"}},
                     {"data": [], "links": {"next": "?cursor=x&project=KAN"}},
                     {"data": []}]
        for response in responses:
            with self.subTest(response=response), patch.object(admin, "request", return_value=response):
                with self.assertRaises(ValueError):
                    admin.inspect_automation()

    def test_automation_complete_pagination(self):
        with patch.object(admin, "request", side_effect=[{"data": [], "links": {"next": "?cursor=x&limit=100"}}, {"data": [], "links": {}}]) as call:
            self.assertTrue(admin.inspect_automation()["readComplete"])
            self.assertEqual(call.call_args.kwargs["body"]["scope"], admin.SCOPE_ARI)

    def test_disable_existing_rule_and_refuse_enable(self):
        rid = str(uuid.uuid4())
        with patch.object(admin, "automation_rule", return_value={"uuid": rid, "state": "ENABLED"}):
            plan = admin.prepare("automation_state", {"rule_uuid": rid, "state": "DISABLED"})
            self.assertEqual(plan["payload"], {"value": "DISABLED"})
            with self.assertRaisesRegex(ValueError, "ENABLE_REQUIRES"):
                admin.prepare("automation_state", {"rule_uuid": rid, "state": "ENABLED"})

    def test_rule_detail_must_match_summary_scope_and_redact(self):
        rid = str(uuid.uuid4())
        with patch.object(admin, "inspect_automation", return_value={"rules": [{"uuid": rid}]}), patch.object(admin, "request", return_value={
            "rule": {"uuid": rid, "ruleScopeARIs": [admin.SCOPE_ARI], "components": [{"hidden": "secret"}], "name": "QAG3 rule", "state": "ENABLED"}}) as call:
            actual = admin.automation_rule(rid)
            self.assertNotIn("components", actual)
            self.assertEqual(call.call_args.kwargs["params"], {"redactSensitiveFields": "true"})

    def test_publish_task_only_accepts_fixed_gateway(self):
        with patch.dict(os.environ, {"QLDAPM_JIRA_ADMIN_TOKEN": "synthetic"}), patch.object(httpx, "Client") as client:
            instance = client.return_value.__enter__.return_value
            instance.request.return_value = httpx.Response(303, headers={"location": "https://evil.test/task/1"})
            with self.assertRaisesRegex(ValueError, "INVALID_TASK_LOCATION"):
                admin.request("POST", "/workflowscheme/10004/draft/publish", expected=(303,))
            instance.request.return_value = httpx.Response(303, headers={"location": admin.BASE + "/rest/api/3/task/123"})
            self.assertEqual(admin.request("POST", "/workflowscheme/10004/draft/publish", expected=(303,)), {"taskId": "123"})

    def test_failed_write_preserves_unknown_and_no_replay(self):
        saved, current = self.plan("create_scheme")
        with patch.object(admin, "prepare", return_value=current), patch.object(admin, "request", side_effect=ValueError("JIRA_API_HTTP_403: synthetic secret")) as call:
            with self.assertRaisesRegex(ValueError, "OUTCOME_UNKNOWN"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            with self.assertRaisesRegex(ValueError, "ALREADY_ATTEMPTED"):
                admin.apply_change(saved["previewId"], saved["fingerprint"])
            self.assertEqual(call.call_count, 1)
        unknown = json.loads((admin.AUDIT_ROOT / (saved["previewId"] + ".unknown.json")).read_text())
        self.assertEqual(unknown["errorCode"], "JIRA_API_HTTP_403")
        self.assertNotIn("synthetic secret", json.dumps(unknown))

    def test_async_publish_complete_requires_mapping_readback(self):
        saved, current = self.plan("publish_scheme")
        saved["arguments"] = {"scheme_id": "10004"}
        path = admin.AUDIT_ROOT / (saved["previewId"] + ".preview.json")
        path.write_text(json.dumps(saved), encoding="utf-8")
        admin.save_record(admin.AUDIT_ROOT / (saved["previewId"] + ".result.json"), {"taskId": "123", "status": "PENDING"})
        with patch.object(admin, "request", return_value={"id": "123", "status": "RUNNING"}):
            self.assertFalse(admin.inspect_publish_result(saved["previewId"])["verified"])
        with patch.object(admin, "request", return_value={"id": "123", "status": "COMPLETE"}), patch.object(admin, "scheme", return_value={"issueTypeMappings": {}}), patch.object(admin, "mappings", return_value={"10000": admin.NAMES["epic"]}):
            with self.assertRaisesRegex(ValueError, "READBACK_MISMATCH"):
                admin.inspect_publish_result(saved["previewId"])
        actual = {"issueTypeMappings": {"10000": admin.NAMES["epic"]}, "defaultWorkflow": admin.NAMES["task"]}
        with patch.object(admin, "request", return_value={"id": "123", "status": "COMPLETE"}), patch.object(admin, "scheme", return_value=actual), patch.object(admin, "mappings", return_value=actual["issueTypeMappings"]):
            self.assertTrue(admin.inspect_publish_result(saved["previewId"])["verified"])
            completion = admin.AUDIT_ROOT / (saved["previewId"] + ".completed.json")
            first = completion.read_bytes()
            self.assertTrue(admin.inspect_publish_result(saved["previewId"])["verified"])
            self.assertEqual(completion.read_bytes(), first)


if __name__ == "__main__":
    unittest.main()

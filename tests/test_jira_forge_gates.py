"""Synthetic inactive Epic preview tests; no Jira calls or credential reads."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_admin_mcp as admin


def fixtures():
    names = ["Approve scope", "Submit acceptance", "Accept Epic", "Cancel Epic", "Restore", "Reopen"]
    before = {"statuses": [], "workflows": [{"id": admin.WORKFLOWS["epic"], "isEditable": True,
        "version": {"id": "v4", "versionNumber": 4}, "description": "Retain me", "statuses": [],
        "startPointLayout": {"x": 17, "y": 23},
        "transitions": [{"id": str(i), "name": name, "validators": [{"ruleKey": "retained"}],
                         "actions": [{"ruleKey": "retained-action"}]} for i, name in enumerate(names, 2)]}]}
    rules = [{"id": admin.FORGE_EXTENSION + name, "ruleKey": "forge:expression-validator", "ruleType": "Validator"}
             for name in ("qag3-pm-only", "qag3-epic-children-done")]
    return before, rules


class ForgeGateTests(unittest.TestCase):
    def test_epic_delivery_additive_idempotent_and_conflicts(self):
        before, _ = fixtures()
        before["workflows"][0]["transitions"] = [
            {"id": "2", "name": "Approve scope", "toStatusReference": "10011", "links": [{"fromStatusReference": "10010"}], "validators": [{"ruleKey": "retained"}]},
            {"id": "6", "name": "Accept Epic", "toStatusReference": "10009", "links": [{"fromStatusReference": "10012"}], "validators": [{"ruleKey": "retained"}], "actions": [{"ruleKey": "resolution"}]}]
        rules = [{"id": admin.FORGE_EXTENSION + name, "ruleKey": "forge:expression-validator", "ruleType": "Validator"}
                 for name in ("qag3-epic-readiness", "qag3-epic-acceptance")]
        old = copy.deepcopy(before)
        payload, changes = admin.epic_delivery_payload(before, rules)
        self.assertEqual(before, old)
        self.assertEqual(len(changes), 4)
        for b, n in zip(old["workflows"][0]["transitions"], payload["workflows"][0]["transitions"]):
            self.assertEqual(n["transitionScreen"]["parameters"]["screenId"], "10011")
            self.assertEqual(n["validators"][:-1], b["validators"])
            for key in ("links", "actions"): self.assertEqual(n.get(key), b.get(key))
        repeated, changes = admin.epic_delivery_payload({"statuses": [], "workflows": [{**payload["workflows"][0], "isEditable": True}]}, rules)
        self.assertEqual(changes, [])
        self.assertEqual(repeated, payload)
        with self.assertRaises(ValueError): admin.epic_delivery_payload(before, rules[:-1])
        before["workflows"][0]["transitions"][0]["transitionScreen"] = {"ruleKey": "foreign"}
        with self.assertRaises(ValueError): admin.epic_delivery_payload(before, rules)
        before["workflows"][0]["transitions"][0].pop("transitionScreen")
        before["workflows"][0]["transitions"][0]["links"] = [{"fromStatusReference": "3"}]
        with self.assertRaises(ValueError): admin.epic_delivery_payload(before, rules)

    def test_subtask_acceptance_additive_screens_idempotent_fail_closed(self):
        before, _ = fixtures()
        before["workflows"][0]["id"] = admin.WORKFLOWS["subtask"]
        before["workflows"][0]["transitions"] = [
            {"id": "12", "name": "Pass testing", "toStatusReference": "10012",
             "links": [{"fromStatusReference": "10018"}], "conditions": {"operation": "ANY"}, "validators": []},
            {"id": "4", "name": "Approve work", "toStatusReference": "10009",
             "links": [{"fromStatusReference": "10012"}], "actions": [{"ruleKey": "resolution"}], "validators": []}]
        rules = [{"id": admin.FORGE_EXTENSION + name, "ruleKey": "forge:expression-validator", "ruleType": "Validator"}
                 for name in ("qag3-qa-attest", "qag3-subtask-acceptance")]
        old = copy.deepcopy(before)
        payload, changes = admin.subtask_acceptance_payload(before, rules)
        self.assertEqual(before, old)
        self.assertEqual(len(changes), 4)
        for b, n in zip(before["workflows"][0]["transitions"], payload["workflows"][0]["transitions"]):
            self.assertEqual(n["transitionScreen"]["parameters"]["screenId"], "10010")
            for key in ("links", "conditions", "actions"): self.assertEqual(b.get(key), n.get(key))
        repeated, changes = admin.subtask_acceptance_payload({"statuses": [], "workflows": [
            {**payload["workflows"][0], "isEditable": True}]}, rules)
        self.assertEqual(changes, [])
        self.assertEqual(repeated, payload)
        with self.assertRaises(ValueError): admin.subtask_acceptance_payload(before, rules[:-1])
        before["workflows"][0]["transitions"][0]["transitionScreen"] = {"ruleKey": "foreign"}
        with self.assertRaises(ValueError): admin.subtask_acceptance_payload(before, rules)

    def test_task_qa_additive_screen_retest_idempotent_and_conflicts(self):
        before, _ = fixtures()
        before["statuses"] = [{"name": name, "statusReference": ref} for name, ref in
                              [("IN TESTING", "10018"), ("REVIEW", "10012"), ("READY FOR RELEASE", "10019")]]
        wf = before["workflows"][0]
        wf["id"] = admin.WORKFLOWS["task"]
        wf["transitions"] = [{"id": "10", "name": "Pass testing", "toStatusReference": "10012",
                              "links": [{"fromStatusReference": "10018"}], "validators": []},
                             {"id": "13", "name": "Approve", "validators": [{"ruleKey": "retained"}]},
                             {"id": "14", "name": "Deploy", "actions": [{"ruleKey": "resolution"}],
                              "conditions": {"operation": "ALL"}, "validators": []}]
        rules = [{"id": admin.FORGE_EXTENSION + name, "ruleKey": "forge:expression-validator", "ruleType": "Validator"}
                 for name in ("qag3-qa-attest", "qag3-qa-current", "qag3-pm-only")]
        old = copy.deepcopy(before)
        payload, changes = admin.task_qa_payload(before, rules)
        self.assertEqual(before, old)
        self.assertEqual(len(changes), 6)
        transitions = payload["workflows"][0]["transitions"]
        self.assertEqual(transitions[0]["transitionScreen"]["parameters"]["screenId"], "10010")
        self.assertEqual(transitions[1]["validators"][0], {"ruleKey": "retained"})
        self.assertEqual(transitions[2]["actions"], wf["transitions"][2]["actions"])
        self.assertEqual(transitions[2]["conditions"], wf["transitions"][2]["conditions"])
        self.assertEqual(transitions[-1]["links"], [{"fromStatusReference": "10019"}])
        repeated, changes = admin.task_qa_payload({"statuses": before["statuses"], "workflows": [
            {**payload["workflows"][0], "isEditable": True}]}, rules)
        self.assertEqual(changes, [])
        self.assertEqual(repeated, payload)
        with self.assertRaises(ValueError): admin.task_qa_payload(before, rules[:-1])
        for field in ("screen", "transition", "status"):
            bad = copy.deepcopy(before)
            if field == "screen": bad["workflows"][0]["transitions"][0]["transitionScreen"] = {"ruleKey": "foreign"}
            elif field == "transition": bad["workflows"][0]["transitions"].append({"id": "16", "name": "Other"})
            else: bad["statuses"][0]["statusReference"] = "1"
            with self.subTest(field=field), self.assertRaises(ValueError): admin.task_qa_payload(bad, rules)

    def test_task_acceptance_additive_idempotent_and_fail_closed(self):
        before, _ = fixtures()
        before["workflows"][0]["id"] = admin.WORKFLOWS["task"]
        before["workflows"][0]["transitions"] = [
            {"id": str(i), "name": name, "validators": [{"ruleKey": "retained"}],
             "actions": [{"ruleKey": "resolution-action"}], "conditions": {"operation": "ALL"}}
            for i, name in enumerate(("Approve", "Deploy", "Reopen"), 13)]
        rules = [{"id": admin.FORGE_EXTENSION + name, "ruleKey": "forge:expression-validator", "ruleType": "Validator"}
                 for name in ("qag3-pm-only", "qag3-task-subtasks-done", "qag3-task-delivery-checklist")]
        original = copy.deepcopy(before)
        payload, changes = admin.task_acceptance_payload(before, rules)
        self.assertEqual(len(changes), 5)
        self.assertEqual(before, original)
        for old, new in zip(before["workflows"][0]["transitions"], payload["workflows"][0]["transitions"]):
            for field in ("actions", "conditions"):
                self.assertEqual(new[field], old[field])
            self.assertEqual(new["validators"][0], old["validators"][0])
        repeated, changes = admin.task_acceptance_payload({"statuses": [], "workflows": [
            {**payload["workflows"][0], "isEditable": True}]}, rules)
        self.assertEqual(changes, [])
        self.assertEqual(repeated, payload)
        with self.assertRaises(ValueError): admin.task_acceptance_payload(before, rules[:-1])
        before["workflows"][0]["transitions"][0]["validators"].append({
            "ruleKey": "forge:expression-validator", "parameters": {
                "key": rules[0]["id"], "config": '{"expression":"true"}', "disabled": "false"}})
        with self.assertRaises(ValueError): admin.task_acceptance_payload(before, rules)

    def test_additive_deterministic_and_idempotent(self):
        before, rules = fixtures()
        original = copy.deepcopy(before)
        payload, changes = admin.epic_forge_payload(before, rules)
        self.assertEqual(len(changes), 6)
        self.assertEqual(before, original)
        self.assertEqual((payload, changes), admin.epic_forge_payload(before, rules))
        for old, new in zip(before["workflows"][0]["transitions"], payload["workflows"][0]["transitions"]):
            self.assertEqual(new["actions"], old["actions"])
            self.assertEqual(new["validators"][0], old["validators"][0])
        self.assertEqual(payload["workflows"][0]["startPointLayout"], {"x": 17, "y": 23})
        repeated, diff = admin.epic_forge_payload({"statuses": [], "workflows": [{**payload["workflows"][0], "isEditable": True}]}, rules)
        self.assertEqual(diff, [])
        self.assertEqual(repeated, payload)

    def test_missing_foreign_or_wrong_kind_rule_rejected(self):
        for fault in ("missing", "foreign", "wrong-kind"):
            before, rules = fixtures()
            if fault == "missing": rules.pop()
            elif fault == "foreign": rules[0]["id"] = rules[0]["id"].replace("f6f77ef8", "ffffffff")
            else: rules[0]["ruleType"] = "Function"
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                admin.epic_forge_payload(before, rules)

    def test_actor_config_override_not_silently_preserved(self):
        before, rules = fixtures()
        before["workflows"][0]["transitions"][0]["validators"].append({
            "ruleKey": "forge:expression-validator", "parameters": {
                "key": rules[0]["id"], "config": '{"expression":"true"}', "disabled": "false"}})
        with self.assertRaises(ValueError): admin.epic_forge_payload(before, rules)

    def test_active_workflow_stops_before_payload(self):
        with patch.object(admin, "preflight", return_value={"permissions": {"ADMINISTER": True}}), \
             patch.object(admin, "usages", return_value=[{"id": admin.PROJECT_ID}]), \
             patch.object(admin, "workflow") as read:
            with self.assertRaises(ValueError): admin.prepare("epic_forge_gates", {"kind": "epic"})
            read.assert_not_called()


if __name__ == "__main__": unittest.main()

"""Local runtime behavior without Gemini/Jira network calls."""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_bot as bot
import jira_monitor as monitor
from test_jira_bot import TYPES, issue


def snapshot(items=None):
    return {"projectKey": bot.PROJECT, "projectId": bot.PROJECT_ID, "cloudId": bot.CLOUD_ID,
            "readComplete": True, "isLast": True,
            "observedAtUtc": datetime.now(timezone.utc).isoformat(),
            **bot.summarize(items or [], TYPES, datetime.now(timezone.utc).date())}


class MonitorTests(unittest.TestCase):
    def test_member_assessment_separates_levels_and_excludes_tests(self):
        sample = snapshot([
            issue(1, "1", assignee={"accountId": "pm"}, labels=["qag3-wbs", "qag3-simulation"]),
            issue(2, assignee={"accountId": "pm"}, labels=["qag3-wbs", "qag3-simulation"]),
            issue(3, "3", assignee={"accountId": "be"}, labels=["qag3-wbs", "qag3-simulation"]),
            issue(4, "3", status="NEW", category="new", assignee={"accountId": "be"}, labels=["qag3-wbs"]),
            issue(5, assignee={"accountId": "pm"}, labels=["qag3-wbs", "qag3-test"]),
            issue(6, assignee={"accountId": "pm"}, labels=["excluded-from-performance"]),
            issue(7, status="CANCELLED", labels=["qag3-wbs"]),
            issue(8, assignee=None, labels=["qag3-wbs"]),
        ])
        result = monitor.member_assessment(sample)
        self.assertEqual(result["members"]["be"]["Subtask"]["completionPercent"], 50)
        self.assertEqual(result["members"]["pm"]["Task"]["total"], 1)
        self.assertEqual(result["members"]["pm"]["Epic"]["total"], 1)
        self.assertEqual(result["excludedIssueKeys"], ["QAG3-5", "QAG3-6"])
        self.assertEqual(result["members"]["UNKNOWN"]["Task"]["done"], 0)
        self.assertIn("UNASSIGNED", result["members"])
        self.assertIsNone(result["overallScore"])
        self.assertEqual(result["overallScoreStatus"], "INSUFFICIENT_EVIDENCE")
        sample["observedAtUtc"] = "2026-10-13T04:00:00Z"
        self.assertEqual(result["fingerprint"], monitor.member_assessment(sample)["fingerprint"])
        sample["issues"][0]["labels"].remove("qag3-simulation")
        self.assertNotEqual(result["fingerprint"], monitor.member_assessment(sample)["fingerprint"])
        sample["readComplete"] = False
        with self.assertRaises(ValueError):
            monitor.member_assessment(sample)

    def test_cycle_stores_private_members_without_event_or_gemini_pii(self):
        assessor = Mock()
        sample = snapshot([issue(1, assignee={"accountId": "PRIVATE_ACCOUNT"},
                                 summary="PRIVATE_SUMMARY", labels=["qag3-wbs", "qag3-simulation"])])
        event = monitor.cycle(self.directory, collector=lambda: sample, assessor=assessor, environ={})
        state = json.loads((self.directory / "state-QAG3.json").read_text())
        self.assertIn("PRIVATE_ACCOUNT", state["memberAssessment"]["members"])
        self.assertNotIn("PRIVATE_ACCOUNT", json.dumps(event))
        self.assertNotIn("PRIVATE_SUMMARY", json.dumps(state))
        assessor.assert_not_called()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_failure_preserves_last_success_and_recovers(self):
        monitor.cycle(self.directory, collector=lambda: snapshot(), environ={})
        path = self.directory / "state-QAG3.json"
        old_bytes = path.read_bytes()
        failed = monitor.cycle(self.directory, collector=Mock(side_effect=RuntimeError("secret")), environ={})
        self.assertFalse(failed["readComplete"])
        self.assertEqual(path.read_bytes(), old_bytes)
        recovered = monitor.cycle(self.directory, collector=lambda: snapshot(), environ={})
        self.assertTrue(recovered["readComplete"])
        self.assertFalse(recovered["scopeChanged"])

    def test_changed_scope_but_ordinary_edit_ignored_no_raw_text(self):
        first = snapshot([issue(1, summary="PRIVATE", assignee=None, parent=None, duedate=None)])
        monitor.cycle(self.directory, collector=lambda: first, environ={})
        second = json.loads(json.dumps(first))
        second["observedAtUtc"] = "2026-10-09T01:00:00Z"
        second["issues"][0]["updated"] = "2026-10-09T01:00:00Z"
        second["issues"][0]["summary"] = "SECRET EDIT"
        self.assertFalse(monitor.cycle(self.directory, collector=lambda: second, environ={})["scopeChanged"])
        self.assertNotIn("SECRET", (self.directory / "state-QAG3.json").read_text())
        second["issues"][0]["parentKey"] = "QAG3-9"
        self.assertTrue(monitor.cycle(self.directory, collector=lambda: second, environ={})["scopeChanged"])

    def test_no_gemini_without_credentials_or_scope(self):
        assessor = Mock()
        monitor.cycle(self.directory, collector=lambda: snapshot(), assessor=assessor, environ={})
        monitor.cycle(self.directory, collector=lambda: snapshot(), assessor=assessor,
                      environ={"GEMINI_API_KEY": "synthetic", "GEMINI_FREE_TIER_CONFIRMED": "1"})
        assessor.assert_not_called()

    def test_assessment_on_change_dedup_and_error_preserves_report(self):
        env = {"GEMINI_API_KEY": "synthetic", "GEMINI_FREE_TIER_CONFIRMED": "1"}
        sample = snapshot([issue(1)])
        assessor = Mock(return_value={"assessmentComplete": True, "assessment": "old draft"})
        monitor.cycle(self.directory, collector=lambda: sample, assessor=assessor, environ=env)
        monitor.cycle(self.directory, collector=lambda: sample, assessor=assessor, environ=env)
        self.assertEqual(assessor.call_count, 1)
        sample["issues"][0]["statusId"] = "10"
        assessor.side_effect = RuntimeError("synthetic secret")
        result = monitor.cycle(self.directory, collector=lambda: sample, assessor=assessor, environ=env)
        self.assertEqual(result["geminiStatus"], "UNAVAILABLE")
        state = json.loads((self.directory / "state-QAG3.json").read_text())
        self.assertEqual(state["lastAssessment"]["assessment"], "old draft")
        self.assertNotIn("synthetic secret", json.dumps(state))

    def test_foreign_or_corrupt_state_never_overwritten(self):
        path = self.directory / "state-QAG3.json"
        for value in ['{"owner":"user"}', 'not JSON']:
            path.write_text(value)
            with self.subTest(value=value), self.assertRaises((ValueError, json.JSONDecodeError)):
                monitor.cycle(self.directory, collector=lambda: snapshot(), environ={})
            self.assertEqual(path.read_text(), value)

    def test_incomplete_assessment_preserves_old_draft(self):
        sample = snapshot([issue(1)])
        env = {"GEMINI_API_KEY": "synthetic", "GEMINI_FREE_TIER_CONFIRMED": "1"}
        assessor = Mock(return_value={"assessmentComplete": True, "assessment": "old draft"})
        monitor.cycle(self.directory, collector=lambda: sample, assessor=assessor, environ=env)
        sample["issues"][0]["statusId"] = "10"
        assessor.return_value = {"assessmentComplete": False}
        monitor.cycle(self.directory, collector=lambda: sample, assessor=assessor, environ=env)
        state = json.loads((self.directory / "state-QAG3.json").read_text())
        self.assertEqual(state["lastAssessment"]["assessment"], "old draft")

    def test_atomic_failure_preserves_file(self):
        path = self.directory / "state-QAG3.json"
        path.write_text("old")
        with patch("jira_monitor.os.replace", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                monitor.atomic_json(path, {"new": True})
        self.assertEqual(path.read_text(), "old")
        self.assertEqual(list(self.directory.glob("monitor-*.tmp")), [])

    def test_single_runner_lock_releases(self):
        with monitor.single_runner(self.directory):
            with self.assertRaises(OSError):
                with monitor.single_runner(self.directory):
                    self.fail("Second runner entered")
        with monitor.single_runner(self.directory):
            pass

    def test_bounded_loop_and_interval_validation(self):
        with patch("jira_monitor.time.sleep") as sleep, patch("builtins.print"):
            monitor.run(self.directory, interval=60, cycles=2, collector=lambda: snapshot())
        sleep.assert_called_once()
        events = [json.loads(line) for path in self.directory.glob("events-*.jsonl")
                  for line in path.read_text().splitlines()]
        self.assertEqual([x["cycle"] for x in events], [1, 2])
        self.assertEqual(events[0]["runId"], events[1]["runId"])
        with self.assertRaises(ValueError):
            monitor.run(self.directory, interval=1)


if __name__ == "__main__":
    unittest.main()

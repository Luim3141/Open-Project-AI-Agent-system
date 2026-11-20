"""Synthetic collector cases; never creates issues or impersonates team members."""

import json
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_bot as bot

TYPES = [{"id": "1", "name": "Epic", "subtask": False},
         {"id": "2", "name": "Task", "subtask": False},
         {"id": "3", "name": "Sub-task", "subtask": True}]


def issue(number, type_id="2", status="Done", category="done", **extra):
    return {"key": f"QAG3-{number}", "fields": {
        "issuetype": {"id": type_id}, "status": {
            "id": "9", "name": status, "statusCategory": {"key": category}},
        "labels": [], "updated": "2026-10-09T00:00:00+0700", **extra}}


class BotTests(unittest.TestCase):
    def test_empty_scope(self):
        result = bot.summarize([], TYPES, date(2026, 10, 9))
        self.assertIsNone(result["completionPercent"])
        self.assertEqual(result["functionalTotal"], 0)

    def test_no_parent_child_double_count(self):
        result = bot.summarize([issue(1, "1"), issue(2),
                                issue(3, status="In Progress", category="indeterminate"),
                                issue(4, "3")], TYPES, date(2026, 10, 9))
        self.assertEqual(result["completionPercent"], 50)
        self.assertEqual(result["countsByType"], {"Epic": 1, "Task": 2, "Story": 0, "Subtask": 1})
        self.assertEqual(result["functionalWip"], ["QAG3-3"])

    def test_cancelled_not_delivered(self):
        result = bot.summarize([issue(1, status="CANCELLED"), issue(2)], TYPES, date(2026, 10, 9))
        self.assertEqual(result["functionalDone"], 1)
        self.assertEqual(result["cancelledFunctional"], 1)
        self.assertEqual(result["functionalTotal"], 2)

    def test_unknown_not_null(self):
        result = bot.summarize([issue(1), issue(2, assignee=None, duedate=None)], TYPES, date(2026, 10, 9))
        self.assertEqual(result["unknownAssigneeField"], ["QAG3-1"])
        self.assertEqual(result["unassignedFunctional"], ["QAG3-2"])
        self.assertEqual(result["unknownDueDateField"], ["QAG3-1"])

    def test_overdue_open_only_and_due_today_not_late(self):
        result = bot.summarize([issue(1, status="New", category="new", duedate="2026-10-08"),
                                issue(2, duedate="2026-10-08"),
                                issue(3, status="New", category="new", duedate="2026-10-09")],
                               TYPES, date(2026, 10, 9))
        self.assertEqual(result["overdueFunctional"], ["QAG3-1"])

    def test_full_fields_required(self):
        compact = issue(1)
        compact["fields"]["status"] = {"name": "Done"}
        with self.assertRaises(KeyError):
            bot.summarize([compact], TYPES, date(2026, 10, 9))

    def test_updated_timestamp_requires_valid_timezone(self):
        for value in [None, "yesterday", "2026-10-09T00:00:00"]:
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                bot.summarize([issue(1, updated=value)], TYPES, date(2026, 10, 9))

    def test_unknown_type_category_or_malformed_date(self):
        for item in [issue(1, "unknown"), issue(1, category="unknown"), issue(1, duedate="yesterday")]:
            with self.subTest(item=item), self.assertRaises((KeyError, ValueError)):
                bot.summarize([item], TYPES, date(2026, 10, 9))

    def test_nested_payload_and_discovery_notes(self):
        payload = {"results": []}
        wrapped = {"content": [{"type": "text", "text": json.dumps(payload) + "\nnotes"}]}
        wrapped = {"content": [{"type": "text", "text": json.dumps(wrapped)}]}
        self.assertEqual(bot.unwrap(wrapped), payload)

    def test_error_never_becomes_empty_scope(self):
        for payload in [{"isError": True}, {"data": {"error": True}},
                        {"content": []}, {"data": []}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                bot.unwrap(payload)

    def test_pagination_full_and_complete(self):
        calls = []
        pages = iter([{"issues": [issue(1)], "isLast": False, "nextPageToken": "next"},
                      {"issues": [issue(2)], "isLast": True}])
        def call(tool, args):
            calls.append((tool, args))
            return next(pages)
        self.assertEqual(len(bot.read_all_issues(call)), 2)
        self.assertEqual(calls[0][1]["view"], "full")
        self.assertEqual(calls[1][1]["nextPageToken"], "next")

    def test_partial_missing_token_repeat_token_duplicate_foreign(self):
        bad_pages = [
            [{"issues": []}],
            [{"issues": [], "isLast": False}],
            [{"issues": [], "isLast": False, "nextPageToken": "x"}] * 2,
            [{"issues": [issue(1)], "isLast": False, "nextPageToken": "x"},
             {"issues": [issue(1)], "isLast": True}],
            [{"issues": [{"key": "KAN-1"}], "isLast": True}],
        ]
        for pages in bad_pages:
            iterator = iter(pages)
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                bot.read_all_issues(lambda tool, args: next(iterator))

    def test_failed_second_page_does_not_return_partial(self):
        page = {"issues": [issue(1)], "isLast": False, "nextPageToken": "x"}
        with self.assertRaises(RuntimeError):
            bot.read_all_issues(unittest.mock.Mock(side_effect=[page, RuntimeError("offline")]))

    def test_read_tool_boundary(self):
        with patch("jira_bot.subprocess.run") as run:
            for tool, args in [("executeWrite", {}), ("editJiraIssue", {}),
                               ("executeRead", {"name": "manageJiraSprint"})]:
                with self.subTest(tool=tool), self.assertRaises(ValueError):
                    bot.call_mcp(tool, args)
            run.assert_not_called()

    def test_google_secrets_not_inherited_by_mcp_child(self):
        with patch.dict(bot.os.environ, {"GEMINI_API_KEY": "synthetic", "GOOGLE_API_KEY": "synthetic"}), \
             patch("jira_bot.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = '{"data":{"accountId":"fixture"}}'
            bot.call_mcp("atlassianUserInfo", {})
        environment = run.call_args.kwargs["env"]
        self.assertNotIn("GEMINI_API_KEY", environment)
        self.assertNotIn("GOOGLE_API_KEY", environment)

    def test_collect_preflight_and_timezone(self):
        responses = [
            {"accountId": bot.ACCOUNT_ID},
            {"resources": [{"cloudId": bot.CLOUD_ID, "url": bot.SITE}]},
            {"results": [{"name": "listJiraProjects", "executeTool": "executeRead"}]},
            {"values": [{"key": bot.PROJECT, "id": bot.PROJECT_ID, "issueTypes": TYPES}], "isLast": True},
            {"issues": [issue(1, status="New", category="new", duedate="2026-10-08")], "isLast": True},
        ]
        result = bot.collect(unittest.mock.Mock(side_effect=responses),
                             datetime(2026, 10, 8, 18, tzinfo=timezone.utc))
        self.assertTrue(result["readComplete"])
        self.assertFalse(result["scheduledExecutionVerified"])
        self.assertEqual(result["overdueFunctional"], ["QAG3-1"])

    def test_wrong_identity_or_site_stops_before_issue_query(self):
        for responses in [[{"accountId": "wrong"}], [{"accountId": bot.ACCOUNT_ID}, {"resources": []}]]:
            call = unittest.mock.Mock(side_effect=responses)
            with self.assertRaises(ValueError):
                bot.collect(call)
            self.assertEqual(call.call_count, len(responses))

    def test_changed_project_or_incomplete_metadata(self):
        for project_page in [{"values": [], "isLast": True},
                             {"values": [], "isLast": False}]:
            call = unittest.mock.Mock(side_effect=[
                {"accountId": bot.ACCOUNT_ID},
                {"resources": [{"cloudId": bot.CLOUD_ID, "url": bot.SITE}]},
                {"results": [{"name": "listJiraProjects", "executeTool": "executeRead"}]},
                project_page,
            ])
            with self.assertRaises(ValueError):
                bot.collect(call)
            self.assertEqual(call.call_count, 4)


if __name__ == "__main__":
    unittest.main()

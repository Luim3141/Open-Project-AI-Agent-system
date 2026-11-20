"""Gemini contract/security tests without network, credentials or Jira writes."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_gemini as ai

ENV = {"GEMINI_API_KEY": "synthetic-test-secret", "GEMINI_FREE_TIER_CONFIRMED": "1"}


def snapshot():
    return {"projectKey": ai.PROJECT, "projectId": ai.PROJECT_ID, "cloudId": ai.CLOUD_ID,
            "readComplete": True, "isLast": True, "observedAtUtc": "2026-10-08T21:33:20Z",
            "functionalTotal": 0, "functionalDone": 0, "cancelledFunctional": 0,
            "functionalWip": [], "unassignedFunctional": [], "unknownAssigneeField": [],
            "overdueFunctional": [], "unknownDueDateField": [],
            "issues": [{"summary": "PRIVATE SUMMARY", "assigneeAccountId": "PRIVATE ID"}]}


def transport(result=None, finish="STOP"):
    result = result if result is not None else {
        "summary": "Chưa có phạm vi.", "risks": [], "recommendedActions": [],
        "limitations": ["Chưa có baseline lịch."]}
    response = {"candidates": [{"finishReason": finish, "content": {
        "parts": [{"text": json.dumps(result)}]}}]}
    mock = MagicMock()
    mock.return_value.__enter__.return_value.read.return_value = json.dumps(response).encode()
    return mock


class GeminiTests(unittest.TestCase):
    def test_missing_key_or_unconfirmed_billing_makes_no_request(self):
        for env in [{}, {"GEMINI_API_KEY": "test"}, {"GEMINI_FREE_TIER_CONFIRMED": "1"}]:
            call = transport()
            with self.subTest(env=env), self.assertRaises(ValueError):
                ai.assess(snapshot(), env, call)
            call.assert_not_called()

    def test_minimal_data_and_auth_header_not_url(self):
        call = transport()
        report = ai.assess(snapshot(), ENV, call)
        request = call.call_args.args[0]
        self.assertNotIn(ENV["GEMINI_API_KEY"], request.full_url)
        self.assertEqual(request.headers["X-goog-api-key"], ENV["GEMINI_API_KEY"])
        self.assertNotIn(b"PRIVATE", request.data)
        self.assertNotIn(b"accountId", request.data)
        self.assertEqual(call.call_args.kwargs["timeout"], 45)
        body = json.loads(request.data)
        self.assertEqual(body["generationConfig"]["responseFormat"]["text"]["mimeType"], "application/json")
        self.assertNotIn("tools", body)
        self.assertTrue(report["aiDraft"])
        self.assertFalse(report["scheduledExecutionVerified"])

    def test_partial_foreign_or_inconsistent_snapshot_never_sent(self):
        for changes in [{"readComplete": False}, {"projectKey": "KAN"},
                        {"functionalDone": 1}, {"functionalTotal": True},
                        {"functionalWip": "invalid"}, {"overdueFunctional": ["QAG3-1"]}]:
            item = {**snapshot(), **changes}
            call = transport()
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ai.assess(item, ENV, call)
            call.assert_not_called()

    def test_http_and_connection_errors_are_sanitized_without_retry(self):
        for error in [HTTPError(ai.ENDPOINT, 429, "synthetic-test-secret", {}, None),
                      HTTPError(ai.ENDPOINT, 401, "synthetic-test-secret", {}, None),
                      URLError("synthetic-test-secret")]:
            call = MagicMock(side_effect=error)
            with self.subTest(error=type(error).__name__), self.assertRaises(RuntimeError) as caught:
                ai.assess(snapshot(), ENV, call)
            self.assertNotIn(ENV["GEMINI_API_KEY"], str(caught.exception))
            self.assertEqual(call.call_count, 1)

    def test_invalid_incomplete_or_secret_output_rejected(self):
        valid = {"summary": "Draft", "risks": [], "recommendedActions": [], "limitations": []}
        for result, finish in [(valid, "MAX_TOKENS"), ({}, "STOP"),
                               ({**valid, "risks": "not array"}, "STOP"),
                               ({**valid, "summary": ENV["GEMINI_API_KEY"]}, "STOP")]:
            with self.subTest(result=result), self.assertRaises(ValueError):
                ai.assess(snapshot(), ENV, transport(result, finish))


if __name__ == "__main__":
    unittest.main()

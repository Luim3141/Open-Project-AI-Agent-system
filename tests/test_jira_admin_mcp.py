"""Synthetic API cases only. No real credentials, invitations or Jira writes."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jira_admin_mcp as admin


class AdminTests(unittest.TestCase):
    def test_runtime_fixed_scope_actor_and_complete_results(self):
        def evaluate(method, path, **kwargs):
            self.assertEqual((method, path), ("POST", "/expression/evaluate"))
            context = kwargs["body"]["context"]
            key = context["issue"]["key"]
            self.assertIn(key, ("QAG3-1", "QAG3-2", "QAG3-3"))
            self.assertEqual(context["custom"], {"originalIssue": {"type": "issue", "key": key}})
            self.assertNotIn("user", context)
            return {"value": {"project": "QAG3", "issueKey": key, "actor": admin.ACCOUNT_ID,
                              "issueType": {"QAG3-1": 10000, "QAG3-2": 10011, "QAG3-3": 10010}[key], "value": False}}
        with patch.object(admin, "preflight", return_value={}), patch.object(admin, "request", side_effect=evaluate) as request:
            result = admin.inspect_expression_runtime()
            self.assertEqual(request.call_count, len(admin.pinned_expressions()[1]))
            self.assertTrue(result["evaluationComplete"])
            self.assertFalse(result["jiraE2EVerified"])
        for value in [None, {"project": "KAN"}, {"project": "QAG3", "issueKey": "QAG3-2", "actor": "qa", "issueType": 10011, "value": True}]:
            with patch.object(admin, "preflight", return_value={}), patch.object(admin, "request", return_value={"value": value}):
                with self.assertRaisesRegex(ValueError, "CONTEXT_MISMATCH"): admin.inspect_expression_runtime()

    def test_pinned_expression_analysis_fixed_context_complete(self):
        def analyse(method, path, **kwargs):
            self.assertEqual((method, path), ("POST", "/expression/analyse"))
            self.assertEqual(kwargs["params"], {"check": "type"})
            self.assertEqual(kwargs["body"]["contextVariables"], {"originalIssue": "Issue"})
            return {"results": [{"expression": e, "valid": True} for e in kwargs["body"]["expressions"]]}
        with patch.object(admin, "preflight", return_value={}), patch.object(admin, "request", side_effect=analyse):
            result = admin.inspect_expression_validation()
            self.assertTrue(result["allValid"])
            self.assertEqual(result["analysisCheck"], "type")
            self.assertFalse(result["jiraE2EVerified"])
        self.assertEqual(len(result["results"]), len(admin.pinned_expressions()[1]))
        with patch.object(admin, "preflight", return_value={}), patch.object(admin, "request", return_value={"results": []}):
            with self.assertRaisesRegex(ValueError, "INCOMPLETE"): admin.inspect_expression_validation()
        with patch.object(admin, "preflight", return_value={}), patch.object(Path, "read_bytes", return_value=b"changed"), patch.object(admin, "request") as request:
            with self.assertRaisesRegex(ValueError, "MANIFEST_CHANGED"): admin.inspect_expression_validation()
            request.assert_not_called()

    def test_type_analysis_echo_final_expression_and_errors(self):
        def analyse(method, path, **kwargs):
            return {"results": [{"expression": e.rsplit("; ", 1)[-1], "valid": False,
                                 "type": "TypeError", "errors": [{"type": "type", "message": "Synthetic type error"}]}
                                for e in kwargs["body"]["expressions"]]}
        with patch.object(admin, "preflight", return_value={}), patch.object(admin, "request", side_effect=analyse):
            result = admin.inspect_expression_validation()
            self.assertFalse(result["allValid"])
        self.assertEqual(len(result["results"]), len(admin.pinned_expressions()[1]))
        self.assertEqual(result["results"][0]["type"], "TypeError")
        with patch.object(admin, "preflight", return_value={}), patch.object(admin, "request", return_value={"results": [None] * 10}):
            with self.assertRaisesRegex(ValueError, "INCOMPLETE"): admin.inspect_expression_validation()

    def test_type_analysis_echo_outer_lambda(self):
        # Jira echoes the outer final expression, not a semicolon inside its lambda.
        def analyse(method, path, **kwargs):
            expressions = kwargs['body']['expressions']
            return {'results': [{'expression': e.removeprefix('let scope = issue.project; ')
                if e.startswith('let scope = issue.project; ') and '(ignored => {' in e else e,
                'valid': True, 'type': 'Boolean'} for e in expressions]}
        with patch.object(admin, 'preflight', return_value={}), patch.object(admin, 'request', side_effect=analyse):
            self.assertTrue(admin.inspect_expression_validation()['allValid'])

    def test_missing_token_never_sends_request(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(httpx, "Client") as client:
            self.assertFalse(admin.api_status()["credentialPresent"])
            with self.assertRaisesRegex(ValueError, "CREDENTIAL_MISSING"):
                admin.preflight()
            client.assert_not_called()

    def test_allowlist_rejects_mutations_and_foreign_paths(self):
        for method, path in [("PUT", "/workflows/update"), ("GET", "https://evil.test"),
                             ("GET", "/project/KAN"), ("POST", "/workflowscheme/KAN/draft/publish")]:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "allowlist"):
                admin.request(method, path)

    def test_foreign_identity_stops_before_project(self):
        with patch.object(admin, "request", return_value={"accountId": "other", "active": True}) as call:
            with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
                admin.preflight()
            self.assertEqual(call.call_count, 1)

    def test_wrong_project_stops_before_permissions(self):
        with patch.object(admin, "request", side_effect=[
            {"accountId": admin.ACCOUNT_ID, "active": True},
            {"id": "10001", "key": "KAN", "style": "classic"},
        ]) as call:
            with self.assertRaisesRegex(ValueError, "PROJECT_MISMATCH"):
                admin.preflight()
            self.assertEqual(call.call_count, 2)

    def test_permission_unknown_is_not_false_or_verified(self):
        with patch.object(admin, "request", side_effect=[
            {"accountId": admin.ACCOUNT_ID, "active": True},
            {"id": admin.PROJECT_ID, "key": "QAG3", "style": "classic"},
            {"permissions": {}},
        ]):
            with self.assertRaisesRegex(ValueError, "INCOMPLETE"):
                admin.preflight()

    def test_permission_false_reported_not_full_admin(self):
        with patch.object(admin, "request", side_effect=[
            {"accountId": admin.ACCOUNT_ID, "active": True},
            {"id": admin.PROJECT_ID, "key": "QAG3", "style": "classic"},
            {"permissions": {key: {"havePermission": False}
                             for key in ("ADMINISTER", "ADMINISTER_PROJECTS")}},
        ]):
            self.assertFalse(admin.preflight()["adminWriteVerified"])

    def test_workflow_foreign_kind_and_response_rejected(self):
        with self.assertRaises(ValueError):
            admin.inspect_workflow("KAN")
        with patch.object(admin, "preflight", return_value={}), patch.object(
            admin, "request", return_value={"workflows": [{"id": "foreign"}]}
        ) as call:
            with self.assertRaisesRegex(ValueError, "MISMATCH"):
                admin.inspect_workflow("epic")
            self.assertEqual(call.call_count, 1)

    def test_redirects_http_errors_do_not_leak_response_or_secret(self):
        for code in (302, 401, 403, 429, 500):
            with self.subTest(code=code), patch.dict(os.environ, {"QLDAPM_JIRA_ADMIN_TOKEN": "synthetic"}):
                with patch.object(httpx, "Client") as client:
                    instance = client.return_value.__enter__.return_value
                    instance.request.return_value = httpx.Response(code, text="synthetic secret body")
                    with self.assertRaisesRegex(ValueError, f"JIRA_API_HTTP_{code}") as error:
                        admin.request("GET", "/myself")
                    self.assertNotIn("synthetic", str(error.exception))
                    self.assertFalse(client.call_args.kwargs["follow_redirects"])
                    self.assertEqual(instance.request.call_count, 1)

    def test_transport_failure_redacted(self):
        with patch.dict(os.environ, {"QLDAPM_JIRA_ADMIN_TOKEN": "synthetic"}), patch.object(httpx, "Client") as client:
            client.return_value.__enter__.return_value.request.side_effect = httpx.ReadTimeout("synthetic")
            with self.assertRaisesRegex(ValueError, "TRANSPORT_ERROR") as error:
                admin.request("GET", "/myself")
            self.assertNotIn("synthetic", str(error.exception))


if __name__ == "__main__":
    unittest.main()

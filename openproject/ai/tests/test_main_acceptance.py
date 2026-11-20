import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from automation import run_full_e2e_acceptance as runner


class MainPlanBoundaryTests(unittest.TestCase):
    def test_wrong_approval_or_unknown_outcome_cannot_send_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "docs/ai").mkdir(parents=True)
            private = repo / "private"
            private.mkdir()
            preview = {"proposal_hash": "a" * 64, "proposal_id": "19efe751-4af7-4cb4-96f0-0836ee504948"}
            (repo / "docs/ai/CODEX_SCENARIO_F_APPROVAL_PREVIEW.json").write_text(json.dumps(preview))
            (private / "scenario-f-confirm-response.json").write_text(json.dumps({"http_status": 503}))
            with patch.object(runner, "__file__", str(repo / "openproject/ai/automation/runner.py")), \
                 patch.object(runner.requests, "Session") as session:
                with self.assertRaisesRegex(ValueError, "EXACT_OWNER_APPROVED_PROPOSAL_REQUIRED"):
                    runner.confirm_scenario_f(private, "b" * 64)
                with self.assertRaisesRegex(ValueError, "KNOWN_SUCCESS_REQUIRED"):
                    runner.verify_scenario_f(private)
                session.assert_not_called()

    def test_plan_only_requires_pm_unchanged_resource_and_never_restarts(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            private = repo / "runtime/operator/current"
            private.mkdir(parents=True)
            (repo / "runtime/gateway").mkdir()
            (repo / "docs/ai").mkdir(parents=True)
            (private / "incident-secrets.json").write_text(json.dumps({
                "test:PM_TOKEN": "fixture-pm", "webhook_secret.json:webhook_token": "fixture-ingress"}))
            (repo / "runtime/gateway/credentials.json").write_text(json.dumps({"19": "fixture-native"}))
            (repo / "docs/ai/CODEX_MAIN_API_QUALIFICATION_RESULT.json").write_text(json.dumps({
                "status": "PASS", "observed_at": datetime.now(timezone.utc).isoformat()}))
            (repo / "docs/ai/CODEX_SCENARIO_F_DRAFT_NOT_EXECUTABLE.json").write_text(json.dumps({
                "before_description": "before", "after_description": "before\n\nfixture-marker"}))
            native = Mock()
            native.identity.return_value = {"role": "BA"}
            native.package.return_value = {"lockVersion": 1, "description": {"raw": "before"}}
            response = Mock(status_code=200)
            response.json.return_value = {"result": {"id": "fixture-run"}}
            session = Mock()
            session.post.return_value = response
            with patch.object(runner, "__file__", str(repo / "openproject/ai/automation/runner.py")), \
                 patch("gateway.native.Native", return_value=native), \
                 patch.object(runner.requests, "Session", return_value=session):
                with self.assertRaisesRegex(ValueError, "GENUINE_PM_REQUIRED"):
                    runner.start_scenario_f_plan(private)
                native.identity.return_value = {"role": "PM"}
                native.package.return_value["lockVersion"] = 2
                with self.assertRaisesRegex(ValueError, "TEST_RESOURCE_CHANGED"):
                    runner.start_scenario_f_plan(private)
                session.post.assert_not_called()
                native.package.return_value["lockVersion"] = 1
                result = runner.start_scenario_f_plan(private)
                self.assertEqual(result["run_id"], "fixture-run")
                self.assertEqual(result["native_writes"], 0)
                session.post.assert_called_once()
                args, kwargs = session.post.call_args
                self.assertEqual(args, ("http://127.0.0.1:5679/webhook/qldapm-agent-request",))
                self.assertEqual(kwargs["json"]["operation"], "plan")
                self.assertEqual(set(kwargs["json"]), {"operation", "request_id", "prompt"})
                self.assertFalse(kwargs["allow_redirects"])
                self.assertFalse(session.trust_env)
                native.call.assert_not_called()
                with self.assertRaisesRegex(ValueError, "PLAN_ALREADY_ATTEMPTED"):
                    runner.start_scenario_f_plan(private)
                session.post.assert_called_once()


if __name__ == "__main__":
    unittest.main()

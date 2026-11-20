"""Unit tests for GitHub REST API Reconciliation Module (Milestone 3 & Phase 2.6 Enhancement)."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from gateway.engineering_github_sync import (
    get_github_token,
    fetch_pull_requests,
    reconcile_github_with_openproject,
)
from gateway.store import Store


class EngineeringGitHubSyncTests(unittest.TestCase):
    def setUp(self):
        # Reset cached token and in-memory cache between tests
        import gateway.engineering_github_sync as mod
        mod._CACHED_TOKEN = None
        mod._SYNC_CACHE.clear()
        mod._CACHED_PRS = []
        mod._CACHED_PRS_TIME = 0
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = Store(Path(temporary.name))

    @staticmethod
    def package(wp):
        return {'id': wp, '_links': {'project': {'href': '/api/v3/projects/6'},
                                    'parent': {'href': '/api/v3/work_packages/379'}}}

    @patch.dict("os.environ", {"GITHUB_TOKEN": "mock-env-token"})
    def test_get_github_token_from_env(self):
        token = get_github_token()
        self.assertEqual(token, "mock-env-token")

    @patch.dict("os.environ", {}, clear=True)
    @patch("pathlib.Path.is_file", return_value=True)
    @patch("pathlib.Path.read_text", return_value='{"engineering": {"github_token": "mock-config-token"}}')
    def test_get_github_token_from_config_file(self, mock_read, mock_isfile):
        token = get_github_token()
        self.assertEqual(token, "mock-config-token")

    @patch.dict("os.environ", {}, clear=True)
    @patch("pathlib.Path.is_file", return_value=False)
    @patch("subprocess.run")
    def test_get_github_token_from_credential_helper(self, mock_run, mock_isfile):
        mock_run.return_value = MagicMock(
            stdout="protocol=https\nhost=github.com\nusername=Luim3141\npassword=mock-cred-token\n",
            returncode=0,
        )
        token = get_github_token()
        self.assertEqual(token, "mock-cred-token")
        mock_run.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_fetch_pull_requests_parses_response(self, mock_urlopen):
        mock_data = [
            {
                "number": 4,
                "title": "PR 4 Title",
                "state": "open",
                "merged_at": None,
                "head": {"sha": "def9d0a8852af42a407bd42fb0051615a2de9331"},
                "base": {"ref": "codex/openclaw-feedback-283138e910432528"},
                "html_url": "https://github.com/Luim3141/mini-task-manager/pull/4",
                "created_at": "2026-10-30T00:00:00Z",
                "updated_at": "2026-10-30T01:00:00Z",
            },
            {
                "number": 2,
                "title": "PR 2 Title",
                "state": "closed",
                "merged_at": "2026-10-30T00:30:00Z",
                "head": {"sha": "29ff0ec1e531d917ce96737d768c8e16dad895c5"},
                "base": {"ref": "codex/openclaw-create-list-persistence-v1"},
                "html_url": "https://github.com/Luim3141/mini-task-manager/pull/2",
                "created_at": "2026-10-30T00:00:00Z",
                "updated_at": "2026-10-30T01:00:00Z",
            },
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        prs = fetch_pull_requests("Luim3141/mini-task-manager", token="mock-token")
        self.assertEqual(len(prs), 2)
        self.assertEqual(prs[0]["number"], 4)
        self.assertEqual(prs[0]["state"], "open")
        self.assertFalse(prs[0]["is_merged"])
        self.assertEqual(prs[0]["merge_target"], "UNMERGED")
        self.assertEqual(prs[1]["number"], 2)
        self.assertEqual(prs[1]["state"], "closed")
        self.assertTrue(prs[1]["is_merged"])
        self.assertEqual(prs[1]["merge_target"], "FEATURE_BRANCH (codex/openclaw-create-list-persistence-v1)")

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_reconcile_github_with_openproject_success_and_idempotency(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "number": 1,
                "title": "PR 1",
                "state": "open",
                "is_merged": False,
                "merge_target": "UNMERGED",
                "head_sha": "726f9738fd1af08bb19502227df886e075c0259b",
                "base_ref": "main",
                "html_url": "https://github.com/Luim3141/mini-task-manager/pull/1",
            },
            {
                "number": 2,
                "title": "PR 2",
                "state": "closed",
                "is_merged": True,
                "merge_target": "FEATURE_BRANCH (codex/openclaw-create-list-persistence-v1)",
                "head_sha": "29ff0ec1e531d917ce96737d768c8e16dad895c5",
                "base_ref": "codex/openclaw-create-list-persistence-v1",
                "html_url": "https://github.com/Luim3141/mini-task-manager/pull/2",
            },
        ]

        service = MagicMock()
        service.store = self.store
        native = MagicMock()
        native.collection.return_value = []
        native.package.return_value = {
            "id": 380,
            "lockVersion": 5,
            "_links": {"status": {"href": "/api/v3/statuses/34"}},
        }
        native.package.side_effect = self.package
        native.collection.side_effect = lambda path: [call.args[2] for call in native.call.call_args_list]

        # First sync run
        receipt1 = reconcile_github_with_openproject(service, native, actor=20)
        self.assertEqual(receipt1["status"], "SUCCESS")
        self.assertEqual(receipt1["total_prs_synced"], 2)
        self.assertTrue(receipt1["changed"])

        # Second sync run with identical data -> idempotent (changed=False, no calls)
        native.call.reset_mock()
        receipt2 = reconcile_github_with_openproject(service, native, actor=20)
        self.assertEqual(receipt2["status"], "SUCCESS")
        self.assertFalse(receipt2["changed"])
        native.call.assert_not_called()

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_reconcile_github_with_openproject_network_error_handled_gracefully(self, mock_fetch):
        mock_fetch.side_effect = urllib.error.URLError("Connection timed out")

        service = MagicMock()
        service.store = None
        native = MagicMock()

        receipt = reconcile_github_with_openproject(service, native, actor=20)
        self.assertEqual(receipt["status"], "SYNC_FAILED")
        self.assertEqual(receipt["error"], "GITHUB_SYNC_NETWORK_ERROR")
        native.call.assert_not_called()

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_persistent_db_sync_cache_across_instances(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "number": 1,
                "title": "PR 1",
                "state": "open",
                "is_merged": False,
                "merge_target": "UNMERGED",
                "head_sha": "1aa7c395555a8d44",
                "base_ref": "main",
                "html_url": "https://github.com/Luim3141/mini-task-manager/pull/1",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(Path(tmpdir))
            service1 = MagicMock(store=store)
            native1 = MagicMock()
            native1.collection.return_value = []
            native1.package.side_effect = self.package
            native1.collection.side_effect = lambda path: [call.args[2] for call in native1.call.call_args_list]

            # First sync: writes to DB
            receipt1 = reconcile_github_with_openproject(service1, native1, actor=20)
            self.assertTrue(receipt1["changed"])
            native1.call.assert_called_once()

            # Simulate new service instance / process restart by clearing in-memory cache
            import gateway.engineering_github_sync as mod
            mod._SYNC_CACHE.clear()

            # Second sync with new service instance pointing to same DB store:
            service2 = MagicMock(store=store)
            native2 = MagicMock()
            receipt2 = reconcile_github_with_openproject(service2, native2, actor=20)
            self.assertFalse(receipt2["changed"])
            native2.call.assert_not_called()


if __name__ == "__main__":
    unittest.main()

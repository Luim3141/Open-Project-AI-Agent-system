"""Regression checks use isolated SQLite and fake network boundaries only."""
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from gateway import engineering_github_sync as sync
from gateway.store import Store


class GitHubRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name))
        self.service = SimpleNamespace(store=self.store)
        sync._SYNC_CACHE.clear()
        sync._CACHED_PRS = []
        sync._CACHED_PRS_TIME = 0
        self.native = MagicMock()
        self.native.collection.return_value = []
        self.native.package.side_effect = lambda wp: {
            'id': wp, '_links': {'project': {'href': '/api/v3/projects/6'},
                                  'parent': {'href': '/api/v3/work_packages/379'}}}
        self.native.collection.side_effect = lambda path: [call.args[2] for call in self.native.call.call_args_list]
        self.pr = {'number': 1, 'state': 'closed', 'is_merged': True,
                   'merge_target': 'MAIN', 'head_sha': 'a' * 40, 'base_ref': 'main',
                   'html_url': 'https://github.com/Luim3141/mini-task-manager/pull/1'}

    def seed_run(self, number, child, project=6, repo='Luim3141/mini-task-manager'):
        payload = {'project_id': project, 'engine': 'openclaw', 'repository': repo,
                   'native_id': 379}
        result = {'status': 'succeeded', 'pr_url': f'https://github.com/{repo}/pull/{number}',
                  'native_readback': {'child_id': child, 'project_id': project}}
        with self.store.connect() as db:
            db.execute('INSERT INTO ai_queue(id,actor,payload,state) VALUES(?,20,?,?)',
                       (str(number), json.dumps(payload), 'finished'))
            db.execute('INSERT INTO ai_runs(id,actor,state,result) VALUES(?,20,?,?)',
                       (str(number), 'done', json.dumps(result)))

    def test_dynamic_mapping_joins_queue_payload_and_uses_child_receipt(self):
        self.seed_run(7, 387)
        self.seed_run(8, 388, project=5)
        self.seed_run(9, 389, repo='other/repo')
        mapping = sync.get_pr_wp_map(self.service)
        self.assertEqual(mapping.get(7), 387)
        self.assertNotIn(8, mapping)
        self.assertNotIn(9, mapping)
        self.assertNotIn(379, mapping.values())

    @patch.object(sync, 'fetch_pull_requests')
    def test_failed_native_write_is_visible_persisted_and_retryable(self, fetch):
        fetch.return_value = [self.pr]
        from gateway.native import NativeError
        self.native.call.side_effect = NativeError(403, 'OPENPROJECT_403: rejected')
        result = sync.reconcile_github_with_openproject(self.service, self.native)
        self.assertEqual(result['status'], 'SYNC_FAILED')
        self.assertEqual(result['total_prs_synced'], 0)
        self.assertEqual(result['items'][0]['status'], 'FAILED')
        self.assertFalse(result['changed'])
        self.assertEqual(sync.get_sync_meta(self.service)['status'], 'SYNC_FAILED')
        self.native.call.side_effect = None
        self.native.call.reset_mock()
        retried = sync.reconcile_github_with_openproject(self.service, self.native)
        self.assertEqual(retried['status'], 'SUCCESS')
        self.assertTrue(retried['changed'])

    @patch.object(sync, 'fetch_pull_requests')
    def test_partial_result_counts_actual_changes_and_preserves_success_cache(self, fetch):
        fetch.return_value = [self.pr, {**self.pr, 'number': 2}, {**self.pr, 'number': 3}]
        from gateway.native import NativeError
        self.native.call.side_effect = [{}, NativeError(403, 'OPENPROJECT_403: rejected'), {}]
        result = sync.reconcile_github_with_openproject(self.service, self.native)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['total_prs_synced'], 2)
        self.assertEqual(result['sync_meta']['total_changed'], 2)
        self.native.call.reset_mock(side_effect=True)
        retried = sync.reconcile_github_with_openproject(self.service, self.native)
        self.assertEqual(retried['status'], 'SUCCESS')
        self.native.call.assert_called_once()

    @patch.object(sync, 'fetch_pull_requests')
    def test_scope_readback_prevents_comment_to_other_project(self, fetch):
        fetch.return_value = [self.pr]
        self.native.package.side_effect = None
        self.native.package.return_value = {'id': 380, '_links': {
            'project': {'href': '/api/v3/projects/5'}}}
        result = sync.reconcile_github_with_openproject(self.service, self.native)
        self.assertEqual(result['status'], 'SYNC_FAILED')
        self.native.call.assert_not_called()

    @patch.object(sync, 'fetch_pull_requests')
    def test_fetch_failure_updates_previous_success_meta(self, fetch):
        fetch.return_value = [self.pr]
        sync.reconcile_github_with_openproject(self.service, self.native)
        fetch.side_effect = urllib.error.URLError('timeout')
        result = sync.reconcile_github_with_openproject(self.service, self.native)
        self.assertEqual(sync.get_sync_meta(self.service)['status'], 'SYNC_FAILED')
        self.assertEqual(result['total_prs_synced'], 0)

    @patch('urllib.request.urlopen')
    def test_fetch_paginates_and_does_not_claim_unchecked_ci(self, urlopen):
        def response(data):
            r = MagicMock(); r.__enter__.return_value = r
            r.read.return_value = json.dumps(data).encode()
            return r
        urlopen.side_effect = [response([{'number': n} for n in range(1, 101)]),
                               response([{'number': 101}])]
        prs = sync.fetch_pull_requests('one/repo', token='', force=True)
        self.assertEqual(len(prs), 101)
        self.assertIn('page=2', urlopen.call_args_list[1].args[0].full_url)
        self.assertEqual(prs[0]['checks_state'], 'NOT_CHECKED')
        self.assertEqual(prs[0]['reviews_state'], 'NOT_CHECKED')

    @patch('urllib.request.urlopen')
    def test_fetch_cache_does_not_mix_repositories_and_caches_empty_results(self, urlopen):
        def response(data):
            r = MagicMock(); r.__enter__.return_value = r
            r.read.return_value = json.dumps(data).encode()
            return r
        urlopen.side_effect = [response([{'number': 1}]), response([])]
        self.assertEqual(len(sync.fetch_pull_requests('one/repo', token='')), 1)
        self.assertEqual(sync.fetch_pull_requests('two/repo', token=''), [])
        self.assertEqual(sync.fetch_pull_requests('two/repo', token=''), [])
        self.assertEqual(urlopen.call_count, 2)


if __name__ == '__main__':
    unittest.main()

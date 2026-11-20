"""P0 sync completion means read-back, with durable correlated outcomes."""
import json
import tempfile
import unittest
import concurrent.futures
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gateway import engineering_github_sync as sync
from gateway.store import Store


class OwnerGitHubContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.service=SimpleNamespace(store=Store(Path(self.tmp.name)))
        self.native=MagicMock()
        self.native.package.return_value={'id':380,'_links':{'project':{'href':'/api/v3/projects/6'},'parent':{'href':'/api/v3/work_packages/379'}}}
        self.native.collection.return_value=[]
        self.pr={'number':1,'state':'open','head_sha':'a'*40,'base_ref':'main','is_merged':False}

    def test_successful_post_without_remote_marker_stays_unknown(self):
        with patch.object(sync,'fetch_pull_requests',return_value=[self.pr]):
            result=sync.reconcile_github_with_openproject(self.service,self.native)
        self.assertEqual(result['items'][0]['status'],'UNKNOWN')
        self.assertEqual(result['status'],'SYNC_FAILED')

    def test_sync_outcome_has_persisted_correlation_and_sanitized_error(self):
        with patch.object(sync,'fetch_pull_requests',side_effect=TimeoutError('secret=CANARY')):
            result=sync.reconcile_github_with_openproject(self.service,self.native)
        self.assertNotIn('CANARY',json.dumps(result))
        self.assertEqual(result['error'],'GITHUB_SYNC_TIMEOUT')
        self.assertEqual(sync.get_sync_meta(self.service)['correlation_id'],result['correlation_id'])

    def test_old_async_completion_cannot_replace_newer_sync_metadata(self):
        def meta(start,correlation):
            return {'started_at':start,'last_synced_at':start+30,'total_checked':0,'total_changed':0,
                    'status':'SUCCESS','error':None,'correlation_id':correlation}
        sync._save_sync_meta(self.service,meta(200,'new'))
        sync._save_sync_meta(self.service,meta(100,'old'))
        self.assertEqual(sync.get_sync_meta(self.service)['correlation_id'],'new')

    def test_old_github_response_cannot_replace_newer_cached_pr_state(self):
        entered=threading.Event(); release=threading.Event()
        def response(state):
            item=MagicMock(); item.__enter__.return_value=item
            item.read.return_value=json.dumps([{'number':1,'state':state}]).encode()
            return item
        def open_request(*args,**kwargs):
            if not entered.is_set():
                entered.set(); release.wait(5)
                return response('open')
            return response('closed')
        with patch('urllib.request.urlopen',side_effect=open_request):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(sync.fetch_pull_requests,token='',force=True)
                self.assertTrue(entered.wait(5))
                try:
                    self.assertEqual(sync.fetch_pull_requests(token='',force=True)[0]['state'],'closed')
                finally:
                    release.set()
                self.assertEqual(first.result(timeout=5)[0]['state'],'open')
            self.assertEqual(sync.fetch_pull_requests(token='')[0]['state'],'closed')

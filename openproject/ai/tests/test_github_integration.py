"""Bounded GitHub enrichment and automatic polling, no real provider or Native writes."""
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gateway import engineering_github_sync as sync
from gateway.store import Store


class GitHubIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.service=SimpleNamespace(store=Store(Path(temporary.name)),config={'engineering':{'github_sync':{'enabled':True,'actor':18,'interval_seconds':300}}})
        self.pr={'number':10,'head_sha':'a'*40}

    def test_reviews_and_checks_are_measured_and_old_head_approval_is_not_current(self):
        from gateway.engineering_github_details import enrich
        def get(path,headers,deadline):
            if '/reviews?' in path:return [{'id':1,'user':{'id':7},'commit_id':'b'*40,'state':'APPROVED'}]
            if '/check-runs?' in path:return {'total_count':1,'check_runs':[{'id':2,'status':'completed','conclusion':'success'}]}
            return {'state':'pending','total_count':0,'statuses':[]}
        with patch('gateway.engineering_github_details.get_json',side_effect=get):
            result=enrich([self.pr],'Luim3141/mini-task-manager',{},float('inf'))[0]
        self.assertEqual(result['reviews_state'],'NO_CURRENT_REVIEW')
        self.assertEqual(result['checks_state'],'SUCCESS')
        self.assertEqual(result['review_count'],1)

    def test_absent_ci_is_not_success_and_partial_network_failure_is_visible(self):
        from gateway.engineering_github_details import enrich
        with patch('gateway.engineering_github_details.get_json',side_effect=[[],{'total_count':0,'check_runs':[]},{'total_count':0,'statuses':[],'state':'pending'}]):
            result=enrich([self.pr],'Luim3141/mini-task-manager',{},float('inf'))[0]
        self.assertEqual(result['checks_state'],'NOT_CONFIGURED')
        with patch('gateway.engineering_github_details.get_json',side_effect=TimeoutError('private-token-canary')):
            result=enrich([self.pr],'Luim3141/mini-task-manager',{},float('inf'))[0]
        self.assertEqual(result['details_error'],'GITHUB_SYNC_TIMEOUT')
        self.assertNotIn('canary',json.dumps(result))

    def test_latest_review_per_reviewer_and_check_failure(self):
        from gateway.engineering_github_details import enrich
        reviews=[{'id':1,'user':{'id':7},'commit_id':'a'*40,'state':'CHANGES_REQUESTED'},
                 {'id':2,'user':{'id':7},'commit_id':'a'*40,'state':'APPROVED'}]
        with patch('gateway.engineering_github_details.get_json',side_effect=[reviews,{'total_count':1,'check_runs':[{'id':3,'status':'completed','conclusion':'failure'}]},{'total_count':0,'statuses':[]}]):
            result=enrich([self.pr],'Luim3141/mini-task-manager',{},float('inf'))[0]
        self.assertEqual(result['reviews_state'],'APPROVED')
        self.assertEqual(result['checks_state'],'FAILURE')

    def test_automatic_poll_is_opt_in_persistent_and_does_not_depend_on_engineering_mode(self):
        from gateway.engineering_github_poll import tick
        expected={'status':'SUCCESS'}
        with patch('gateway.engineering.scoped_service',return_value=self.service),patch('gateway.engineering.authorized',return_value=(object(),{})),patch.object(sync,'reconcile_github_with_openproject',return_value=expected) as reconcile:
            self.assertEqual(tick(self.service)['status'],'SUCCESS')
            self.assertEqual(tick(self.service)['reason'],'NOT_DUE')
            reconcile.assert_called_once()
        self.service.config['engineering']['github_sync']['enabled']=False
        self.assertEqual(tick(self.service)['reason'],'DISABLED')

    def test_poll_lease_prevents_concurrent_processes_and_failure_is_bounded(self):
        from gateway.engineering_github_poll import tick
        entered=threading.Event();release=threading.Event()
        def reconcile(*args,**kwargs):entered.set();release.wait(5);raise TimeoutError('secret')
        with patch('gateway.engineering.scoped_service',return_value=self.service),patch('gateway.engineering.authorized',return_value=(object(),{})),patch.object(sync,'reconcile_github_with_openproject',side_effect=reconcile):
            worker=threading.Thread(target=tick,args=(self.service,));worker.start()
            self.assertTrue(entered.wait(5));self.assertEqual(tick(self.service)['reason'],'NOT_DUE');release.set();worker.join(5)
        self.assertEqual(tick(self.service)['reason'],'NOT_DUE')
        with self.service.store.connect() as db:
            row=db.execute('select error,lease_until from engineering_github_poll where project=6').fetchone()
        self.assertEqual(row[0],'GITHUB_SYNC_TIMEOUT');self.assertEqual(row[1],0)


if __name__=='__main__':unittest.main()

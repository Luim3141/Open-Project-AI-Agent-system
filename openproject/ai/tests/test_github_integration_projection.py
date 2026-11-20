import json
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock,patch

from gateway import engineering_github_sync as sync
from gateway import engineering_github_details as details
from gateway.store import Store


class GitHubIntegrationProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.service=SimpleNamespace(store=Store(Path(self.tmp.name)),config={'engineering':{'github_sync':{'enabled':True}}})
        self.pr={'number':1,'state':'open','title':'Fixture','is_merged':False,'merge_target':'UNMERGED','head_sha':'a'*40,'base_ref':'main','html_url':'https://github.com/Luim3141/mini-task-manager/pull/1','reviews_state':'NO_REVIEWS','checks_state':'NOT_CONFIGURED','details_hash':'b'*64}

    def test_fetch_details_opt_in_does_not_share_basic_cache(self):
        sync._CACHED_PRS_TIME=0
        response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps([{'number':1,'head':{'sha':'a'*40}}]).encode()
        with patch('urllib.request.urlopen',return_value=response),patch.object(details,'enrich',side_effect=lambda prs,*args:[{**p,'checks_state':'SUCCESS'} for p in prs]) as enrich:
            self.assertEqual(sync.fetch_pull_requests(token='fixture',force=True)[0]['checks_state'],'NOT_CHECKED')
            self.assertFalse(enrich.called)
            self.assertEqual(sync.fetch_pull_requests(token='fixture',include_details=True)[0]['checks_state'],'SUCCESS')
            self.assertEqual(enrich.call_count,1)

    def test_multiple_pr_details_are_bounded_parallel_and_preserve_order(self):
        active=0;peak=0;guard=threading.Lock();first_two=threading.Barrier(2)
        def fake(path,headers,deadline):
            nonlocal active,peak
            with guard:active+=1;peak=max(peak,active)
            try:
                if '/pulls/' in path:first_two.wait(timeout=1)
                if '/pulls/' in path:return []
                if '/check-runs?' in path:return {'total_count':0,'check_runs':[]}
                return {'total_count':0,'statuses':[]}
            finally:
                with guard:active-=1
        prs=[{**self.pr,'number':n,'head_sha':format(n,'040x')} for n in (1,2)]
        with patch.object(details,'get_json',side_effect=fake):
            actual=details.enrich(prs,'Luim3141/mini-task-manager',{},time.monotonic()+5)
        self.assertEqual([p['number'] for p in actual],[1,2])
        self.assertGreaterEqual(peak,2);self.assertLessEqual(peak,3)
        self.assertTrue(all(p['checks_state']=='NOT_CONFIGURED' for p in actual))

    def test_poll_rotates_first_prs_so_a_large_backlog_cannot_starve_last_prs(self):
        prs=[{**self.pr,'number':n,'head_sha':format(n,'040x')} for n in range(1,7)]
        def fetch(epoch):
            first=[];guard=threading.Lock();barrier=threading.Barrier(3)
            def fake(path,headers,deadline):
                if '/pulls/' in path:
                    with guard:
                        if len(first)<3:first.append(int(path.split('/pulls/')[1].split('/')[0]));wait=True
                        else:wait=False
                    if wait:barrier.wait(timeout=2)
                    return []
                if '/check-runs?' in path:return {'total_count':0,'check_runs':[]}
                return {'total_count':0,'statuses':[]}
            with patch.object(details.time,'time',return_value=epoch),patch.object(details,'get_json',side_effect=fake):
                result=details.enrich(prs,'Luim3141/mini-task-manager',{},time.monotonic()+5)
            self.assertEqual([r['number'] for r in result],list(range(1,7)))
            return sorted(first)
        self.assertEqual(fetch(0),[1,2,3])
        self.assertEqual(fetch(300),[4,5,6])

    def test_review_must_match_head_and_failed_checks_are_not_success(self):
        responses=[[{'id':1,'user':{'id':9},'state':'APPROVED','commit_id':'f'*40}],{'total_count':1,'check_runs':[{'id':2,'status':'completed','conclusion':'failure'}]},{'total_count':0,'statuses':[]}]
        with patch.object(details,'get_json',side_effect=responses):
            item=details.enrich([self.pr],'Luim3141/mini-task-manager',{},time.monotonic()+10)[0]
        self.assertEqual(item['reviews_state'],'NO_CURRENT_REVIEW');self.assertEqual(item['checks_state'],'FAILURE')

    def test_neutral_skipped_or_unknown_checks_are_not_success(self):
        for conclusion,expected in [('neutral','NEUTRAL_OR_SKIPPED'),('skipped','NEUTRAL_OR_SKIPPED'),(None,'UNKNOWN'),('future_result','UNKNOWN')]:
            responses=[[],{'total_count':1,'check_runs':[{'id':2,'status':'completed','conclusion':conclusion}]},{'total_count':0,'statuses':[]}]
            with self.subTest(conclusion=conclusion),patch.object(details,'get_json',side_effect=responses):
                item=details.enrich([self.pr],'Luim3141/mini-task-manager',{},time.monotonic()+10)[0]
                self.assertEqual(item['checks_state'],expected)

    def test_check_payload_from_wrong_commit_is_not_accepted(self):
        responses=[[],{'total_count':1,'check_runs':[{'id':2,'head_sha':'f'*40,'status':'completed','conclusion':'success'}]},{'sha':'a'*40,'total_count':0,'statuses':[]}]
        with patch.object(details,'get_json',side_effect=responses):
            item=details.enrich([self.pr],'Luim3141/mini-task-manager',{},time.monotonic()+10)[0]
        self.assertEqual(item['checks_state'],'NOT_CHECKED');self.assertEqual(item['details_error'],'GITHUB_CHECK_COMMIT_MISMATCH')

    def test_release_file_must_match_actual_safe_http_identity(self):
        metadata={'state':'INTEGRATION_TEST_RELEASE','head_sha':'a'*40,'branch':'codex/integration','included_prs':[6,10],'deployed_at':time.time()-1,'tests_passed':True,'source':'UNMERGED_INTEGRATION','main_merged':False}
        (self.service.store.root/'demo-release.json').write_text(json.dumps(metadata))
        response=SimpleNamespace(status_code=200,headers={'x-qldapm-revision':'a'*40,'x-qldapm-release-type':'UNMERGED_INTEGRATION_TEST_RELEASE'},content=json.dumps({'revision':'a'*40,'type':'UNMERGED_INTEGRATION_TEST_RELEASE','included_prs':[6,10]}).encode())
        with patch.object(details,'release_probe',return_value=response):
            result=details.verified_release(self.service)
        self.assertEqual(result['state'],'DEPLOYED_TO_DEMO');self.assertFalse(result['main_merged'])
        response.headers['x-qldapm-revision']='c'*40
        self.service._demo_release_cache=None
        with patch.object(details,'release_probe',return_value=response):
            self.assertEqual(details.verified_release(self.service)['state'],'RELEASE_IDENTITY_MISMATCH')

    def test_arbitrary_release_metadata_cannot_claim_deployed(self):
        (self.service.store.root/'demo-release.json').write_text(json.dumps({'head_sha':'a'*40,'state':'DEPLOYED_TO_DEMO'}))
        with patch.object(details,'release_probe') as probe:
            self.assertEqual(details.verified_release(self.service)['state'],'DEMO_RELEASE_METADATA_INVALID')
        probe.assert_not_called()

    def test_deployment_proof_is_bound_to_current_pr_commit_not_number(self):
        release={'state':'DEPLOYED_TO_DEMO','head_sha':'c'*40,'included_prs':[1],'main_merged':False}
        compared={'status':'ahead','merge_base_commit':{'sha':'a'*40},'base_commit':{'sha':'a'*40}}
        with patch.object(details,'verified_release',return_value=release),patch.object(details,'get_json',return_value=compared),patch.object(sync,'get_github_token',return_value=''):
            _,prs=details.deployment_projection(self.service,[self.pr],verify_ancestry=True)
        self.assertEqual(prs[0]['deployment_state'],'DEPLOYED_TO_DEMO')
        updated={**self.pr,'head_sha':'d'*40}
        with patch.object(details,'verified_release',return_value=release),patch.object(details,'get_json') as network:
            _,prs=details.deployment_projection(self.service,[updated])
        self.assertEqual(prs[0]['deployment_state'],'INCLUDED_PR_COMMIT_NOT_VERIFIED');network.assert_not_called()

    def test_unknown_native_write_does_not_emit_delivery_event(self):
        native=MagicMock();native.package.return_value={'id':380,'_links':{'project':{'href':'/api/v3/projects/6'},'parent':{'href':'/api/v3/work_packages/379'}}};native.collection.return_value=[]
        with patch.object(sync,'fetch_pull_requests',return_value=[self.pr]):
            result=sync.reconcile_github_with_openproject(self.service,native)
        self.assertEqual(result['items'][0]['status'],'UNKNOWN')
        with self.service.store.connect() as db:
            tables={r[0] for r in db.execute("select name from sqlite_master where type='table'")}
            self.assertNotIn('integration_event_outbox',tables)

    def test_incomplete_details_and_unmapped_release_pr_are_explicit(self):
        native=MagicMock();self.pr['details_error']='GITHUB_SYNC_TIMEOUT'
        with patch.object(sync,'fetch_pull_requests',return_value=[self.pr]):
            result=sync.reconcile_github_with_openproject(self.service,native)
        self.assertEqual(result['status'],'SYNC_FAILED');native.call.assert_not_called()
        self.pr.pop('details_error');self.pr['number']=11
        with patch.object(sync,'fetch_pull_requests',return_value=[self.pr]):
            result=sync.reconcile_github_with_openproject(self.service,native)
        self.assertEqual(result['status'],'SUCCESS');native.call.assert_not_called()
        with self.service.store.connect() as db:
            event=json.loads(db.execute('SELECT document FROM integration_event_outbox').fetchone()[0])
            self.assertEqual(event['payload']['pr_number'],11);self.assertIsNone(event['payload']['work_package_id'])

    def test_review_change_is_journalled_and_delivered_once_only_after_native_readback(self):
        native=MagicMock();native.package.return_value={'id':380,'_links':{'project':{'href':'/api/v3/projects/6'},'parent':{'href':'/api/v3/work_packages/379'}}}
        activities=[];native.collection.side_effect=lambda _:activities
        native.call.side_effect=lambda path,method,body:activities.append(body) or {'id':len(activities)}
        with patch.object(sync,'fetch_pull_requests',return_value=[self.pr]):
            first=sync.reconcile_github_with_openproject(self.service,native)
            second=sync.reconcile_github_with_openproject(self.service,native)
        self.assertTrue(first['changed']);self.assertFalse(second['changed']);self.assertEqual(native.call.call_count,1)
        with self.service.store.connect() as db:self.assertEqual(db.execute("SELECT count(*) FROM integration_event_outbox WHERE workflow='WF04'").fetchone()[0],1)
        self.pr.update(reviews_state='APPROVED',details_hash='c'*64)
        with patch.object(sync,'fetch_pull_requests',return_value=[self.pr]):
            third=sync.reconcile_github_with_openproject(self.service,native)
        self.assertTrue(third['changed']);self.assertEqual(native.call.call_count,2)
        with self.service.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM integration_event_outbox').fetchone()[0],2)

if __name__=='__main__':unittest.main()

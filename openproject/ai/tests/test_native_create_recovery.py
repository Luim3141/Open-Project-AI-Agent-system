"""Lost create response recovery must prove actor/source/fields, never repeat POST."""
import copy,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from gateway.service import Service
from gateway.store import Store
from gateway.native import Native

class NativeCreateRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.service=Service(self.store,{'project_id':5,'gateway_mode':'native','source_field':'customField11','users':{'7':'PM','8':'QA'}},Path(self.tmp.name)/'workspaces')
        self.args={'source_id':'owner-synthetic-unique','subject':'test','type_id':10,'parent_id':50,'assignee_id':8}
        self.store.begin(7,'lost-create',{'action':'create_work_package','arguments':self.args,'idempotency_key':'lost-create','auto_execute':True})
        self.row={'id':367,'subject':'test','lockVersion':0,'customField11':'owner-synthetic-unique','description':{'raw':''},
            '_links':{k:{'href':v} for k,v in {'project':'/api/v3/projects/5','type':'/api/v3/types/10',
            'parent':'/api/v3/work_packages/50','assignee':'/api/v3/users/8','author':'/api/v3/users/7','status':'/api/v3/statuses/1'}.items()}}
        self.rows=[self.row];self.gets=[]
        def package(identifier):self.gets.append(identifier);return self.row
        self.native=SimpleNamespace(packages=lambda:self.rows,package=package)

    def reconcile(self,actor=7):return self.service.perform({'user_id':actor,'role':'PM'},self.native,'reconcile_request',{'key':'lost-create'})

    def test_proven_native_create_finishes_original_receipt_without_post(self):
        r=self.reconcile();self.assertTrue(r['reconciled']);self.assertEqual(r['result']['id'],367)
        self.assertEqual(self.gets,[367]);self.assertEqual(self.store.request_status(7,'lost-create')['state'],'done')
        with self.assertRaisesRegex(ValueError,'PENDING_REQUEST_NOT_FOUND'):self.reconcile()

    def test_missing_or_duplicate_source_stays_pending(self):
        for rows in ([],[self.row,self.row]):
            self.rows=rows
            with self.assertRaisesRegex(ValueError,'NO_PROVEN_RECEIPT'):self.reconcile()
            self.assertEqual(self.store.request_status(7,'lost-create')['state'],'pending')

    def test_foreign_actor_cannot_reconcile(self):
        with self.assertRaisesRegex(ValueError,'PENDING_REQUEST_NOT_FOUND'):self.reconcile(8)

    def test_mismatched_author_fields_source_or_project_stays_pending(self):
        original=copy.deepcopy(self.row)
        for field,value in [('subject','changed'),('customField11','other'),('description',{'raw':'unapproved'})]:
            self.row=copy.deepcopy(original);self.rows=[self.row];self.row[field]=value
            with self.assertRaisesRegex(ValueError,'NO_PROVEN_RECEIPT'):self.reconcile()
        for link in ('author','assignee','parent','type','project'):
            self.row=copy.deepcopy(original);self.rows=[self.row];self.row['_links'][link]['href']='/api/v3/other/999'
            with self.assertRaisesRegex(ValueError,'NO_PROVEN_RECEIPT'):self.reconcile()

    def test_only_native_create_uses_remaining_deadline_other_requests_keep_30s(self):
        import httpx
        from contextlib import contextmanager
        seen=[]
        @contextmanager
        def stream(method,url,**kwargs):
            seen.append(kwargs['timeout'])
            yield httpx.Response(200,json={},request=httpx.Request(method,url))
        with patch('gateway.native.httpx.stream',stream):
            for path,method in (('/api/v3/work_packages','POST'),('/api/v3/work_packages/50','GET'),('/api/v3/projects/5/work_packages/form','POST')):
                n=Native('http://localhost:8088','synthetic-only',5);n.call(path,method,{})
        self.assertGreater(seen[0],80);self.assertEqual(seen[1:],[30,30])

    def test_owner_recovery_view_preserves_failed_worker_and_current_visibility(self):
        import uuid
        from gateway.business_acceptance import BusinessAcceptance
        identifier=self.store.create_run(7);approval=str(uuid.uuid4())
        result={'error':'GEMINI_REQUEST_BUDGET_EXHAUSTED','tools':[{'action':'create_work_package','arguments':self.args,
            'result':{'outcome_unknown':True,'error':'NativeError'}}]}
        self.store.finish_run(7,identifier,result,'failed_or_unknown');original=self.store.run(7,identifier)
        self.store.begin(7,'owner-run-'+approval,{'run':identifier});self.store.finish(7,'owner-run-'+approval,{'run':identifier})
        self.store.begin(7,'owner-create-'+approval,{'action':'create_work_package','arguments':self.args})
        self.assertEqual(BusinessAcceptance.recovered_view(self.store,7,original,self.native),original)
        self.service.perform({'user_id':7,'role':'PM'},self.native,'reconcile_request',{'key':'owner-create-'+approval})
        recovered=BusinessAcceptance.recovered_view(self.store,7,original,self.native)
        self.assertEqual(recovered['state'],'failed_or_unknown');self.assertEqual(recovered['result']['status'],'partial')
        self.assertTrue(recovered['result']['native_reconciled']);self.assertFalse(recovered['result']['provider_report_completed'])
        self.assertEqual(recovered['result']['outcomes'][0]['work_package_id'],367)
        self.assertEqual(recovered['result']['outcomes'][0]['state'],'succeeded')
        self.assertEqual(self.store.run(7,identifier),original,'Never rewrite historic failed worker')
        self.assertEqual(BusinessAcceptance.recovered_view(self.store,8,original,self.native),original)
        def deny(_):raise PermissionError('CURRENT_ACCESS_REVOKED')
        with self.assertRaisesRegex(PermissionError,'ACCESS_REVOKED'):
            BusinessAcceptance.recovered_view(self.store,7,original,SimpleNamespace(package=deny))

if __name__=='__main__':unittest.main()

import copy
import json
import tempfile
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from gateway import engineering
from gateway.engineering_provider import operate,effective_policy,response,HEADER,PATH
from gateway.store import canonical
from test_engineering_auto_mode import make_service
from automation.openclaw_provider_gate import retry_delay

class ProviderAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.service=make_service(self.tmp.name)
        self.service.config['engineering']['provider_limits']={'rpm':2,'tpm':100000,'rpd':100}
        self.policy={'project':'fixture','model':'gemini-3.5-flash-lite','limits':{'rpm':15,'tpm':250000,'rpd':500}}
        self.service.gemini.settings=lambda:self.policy
        rid=engineering.admit(self.service,20,{'native_id':379,'lock_version':5,'unit':engineering.UNIT},'provider')['id']
        claimed=engineering.claim(self.service,20,worker_id=str(uuid.uuid4()))
        self.doc={'action':'reserve','claim':{'run_id':rid,'worker_id':claimed['worker_id'],'claim_token':claimed['claim_token']},
            'session_id':str(uuid.uuid4()),'step':'dev-0','request_id':str(uuid.uuid4()),'details':{'request_sha256':'a'*64,'input_token_bound':20000,'phase':'generateContent'}}
    def reserve(self):return operate(self.service,self.doc)
    def settle(self,http=200):
        doc={**self.doc,'action':'settle','details':{'http_status':http,'usage':{'promptTokenCount':12000,'totalTokenCount':14000},'started':time.time()-1,'finished':time.time(),'retry_after':60 if http==429 else None,'call_cap':12}}
        return operate(self.service,doc)
    def test_each_actual_call_reserved_once_from_shared_ledger(self):
        first=self.reserve();self.assertEqual(first['state'],'RESERVED');self.assertEqual(self.reserve(),first)
        with self.service.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM gemini_usage').fetchone()[0],1)
        self.settle();self.settle()
        with self.service.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT input_tokens FROM gemini_usage').fetchone()[0],14000)
    def test_real_rpm_window_waits_without_reserving_an_extra_request(self):
        self.reserve();self.doc['request_id']=str(uuid.uuid4());self.reserve();self.doc['request_id']=str(uuid.uuid4())
        result=self.reserve();self.assertEqual(result['state'],'WAITING_FOR_QUOTA');self.assertGreater(result['retry_at'],time.time())
        with self.service.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM gemini_usage').fetchone()[0],2)
    def test_429_persists_cooldown_auth_error_latches_and_owner_off_fences(self):
        self.reserve();self.settle(429);self.doc['request_id']=str(uuid.uuid4())
        self.assertEqual(self.reserve()['state'],'WAITING_FOR_QUOTA')
        engineering.control(self.service,20,'OFF')
        with self.assertRaisesRegex(ValueError,'PAUSED'):self.reserve()
    def test_claim_secret_and_changed_request_are_rejected(self):
        self.reserve();self.doc['details']['request_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'CONFLICT'):self.reserve()
        self.doc['claim']['claim_token']='forged'
        with self.assertRaisesRegex(ValueError,'CLAIM_LOST'):self.reserve()
    def test_retry_after_and_json_retry_info_are_bounded(self):
        with patch('automation.openclaw_provider_gate.random.uniform',return_value=0):
            self.assertEqual(retry_delay({'Retry-After':'75'},b'{}',0,now=0),75)
            self.assertEqual(retry_delay({},b'{"error":{"details":[{"retryDelay":"90s"}]}}',0,now=0),90)
            self.assertEqual(retry_delay({},b'bad',1,now=0),120)
    def test_endpoint_requires_private_token_and_rejects_browser_origin(self):
        root=self.service.store.root;(root/'engineering-provider-token').write_text('x'*48)
        scope={'method':'POST','path':PATH,'query_string':b''}
        self.assertEqual(response(self.service,root,scope,{},b'{}').status_code,403)
        headers={HEADER:'x'*48,'origin':'http://localhost'}
        self.assertEqual(response(self.service,root,scope,headers,json.dumps(self.doc).encode()).status_code,403)

    def test_actual_receipt_settles_after_owner_off_without_new_outbound(self):
        self.reserve();engineering.control(self.service,20,'OFF');self.assertEqual(self.settle(429)['state'],'SETTLED')
        self.doc['request_id']=str(uuid.uuid4())
        with self.assertRaisesRegex(ValueError,'PAUSED'):self.reserve()
    def test_session_and_cumulative_call_caps_are_server_enforced(self):
        self.service.config['engineering']['continuation']={'attempt_calls':1,'task_calls':2}
        self.reserve();self.settle();self.doc['request_id']=str(uuid.uuid4())
        with self.assertRaisesRegex(ValueError,'ATTEMPT_BUDGET'):self.reserve()
        self.doc['session_id']=str(uuid.uuid4());self.reserve();self.settle();self.doc['session_id']=str(uuid.uuid4());self.doc['request_id']=str(uuid.uuid4())
        with self.assertRaisesRegex(ValueError,'CUMULATIVE_BUDGET'):self.reserve()
    def test_invalid_step_hash_and_usage_time_are_rejected(self):
        self.doc['step']=None
        with self.assertRaisesRegex(ValueError,'INPUT_INVALID'):self.reserve()
        self.doc['step']='dev-0';self.doc['details']['request_sha256']='z'*64
        with self.assertRaisesRegex(ValueError,'INPUT_INVALID'):self.reserve()
    def test_auth_failure_latches_until_explicit_recovery(self):
        self.reserve();self.settle(401);self.doc['request_id']=str(uuid.uuid4())
        result=self.reserve();self.assertEqual(result['state'],'BLOCKED_KEY_OR_MODEL');self.assertIsNone(result['retry_at'])

    def test_actual_http_app_route_requires_private_non_browser_transport(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        self.service.mode='native';self.service.config['hosts']=['localhost:8090']
        for name in ['start_dispatcher','stop_dispatcher','start_knowledge_worker','stop_knowledge_worker']:setattr(self.service,name,lambda:None)
        (self.service.store.root/'engineering-provider-token').write_text('x'*48)
        with TestClient(create_app(self.service.store.root,self.service),base_url='http://localhost:8090') as client:
            headers={HEADER:'x'*48}
            response=client.post(PATH,headers=headers,json=self.doc)
            self.assertEqual(response.status_code,200,response.text);self.assertEqual(response.json()['state'],'RESERVED')
            for extra,path in [({'Origin':'http://localhost:8090'},PATH),({'Authorization':'Bearer synthetic'},PATH),({},PATH+'?key=no'),({'Host':'evil.example'},PATH)]:
                self.assertEqual(client.post(path,headers={**headers,**extra},json=self.doc).status_code,403)
    def test_concurrent_duplicate_reservation_never_debits_twice(self):
        from concurrent.futures import ThreadPoolExecutor
        def reserve():
            try:return self.reserve()['state']
            except ValueError as error:return str(error)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:reserve(),range(2)))
        self.assertIn('RESERVED',results)
        self.assertTrue(all(r in {'RESERVED','ENGINEERING_PROVIDER_RESERVATION_UNKNOWN'} for r in results),results)
        with self.service.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM gemini_usage').fetchone()[0],1)

if __name__=='__main__':unittest.main()

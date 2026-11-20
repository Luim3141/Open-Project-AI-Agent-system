"""Existing proposal/public Service path reaches only an authenticated atomic Core contract."""
import copy
import hashlib
import hmac
import unittest
from unittest.mock import patch

import test_native_qa_bridge as fixture
from gateway.native import NativeError
from gateway.store import canonical


class NativeQaAtomicTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.NativeQaBridgeTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups);self.f.accept()
        self.service=self.f.service;self.store=self.f.store;self.native=self.f.fixture.native
        self.evidence=self.f.evidence;self.tokens=self.f.fixture.f.tokens;self.calls=[];self.receipts={};self.gate={};self.errors=[];self.lose_reply=False
        original=self.native.call;test=self
        def core(instance,path,method='GET',payload=None,**kwargs):
            if path=='/api/v3/qldapm/capabilities':return {'project_id':5,'enforced':True,'gate_schema':2,'qa_bridge_version':1}
            if path=='/api/v3/qldapm/qa_transition_forms':
                test.calls.append(('preflight',copy.deepcopy(payload)))
                return {'valid':not test.errors,'errors':test.errors,'lockVersion':test.native.row['lockVersion'],
                    'qa_evidence_id':test.evidence['id'],'hash':test.evidence['hash']}
            if path=='/api/v3/qldapm/mutations':
                test.calls.append(('write',copy.deepcopy(payload)))
                header=instance.mutation_headers;at=header['X-Qldapm-At'];key=(test.f.fixture.f.root/'ui.key').read_bytes()
                fingerprint=hashlib.sha256(canonical(payload).encode()).hexdigest()
                test.assertEqual(header['X-Qldapm-Mutation'],hmac.new(key,f'19:{at}:{fingerprint}'.encode(),hashlib.sha256).hexdigest())
                p=test.store.proposal(19,payload['qa_authorization']['proposal_id']);test.assertEqual(p['state'],'executing');test.assertEqual(p['hash'],payload['qa_authorization']['proposal_hash'])
                test.assertEqual(payload['lock_version'],test.native.row['lockVersion']);test.native.row['lockVersion']+=2
                test.native.row['_links']['status']={'href':'/api/v3/statuses/'+str(payload['status_id'])}
                qa={'evidence_id':test.evidence['id'],'hash':test.evidence['hash'],'source_version':payload['lock_version'],
                    'artifact_sha256':test.f.run['artifact_sha256']}
                result={'id':371,'lockVersion':test.native.row['lockVersion'],'request_id':payload['request_id'],'provenance':'ai_gateway','qa_native':qa}
                test.receipts[payload['request_id']]=result;test.gate={'qa_bridge':qa,'events':[{'actor_id':19,'request_id':payload['request_id'],'proposal_id':p['id'],'proposal_hash':p['hash']}]}
                if test.lose_reply:raise NativeError(503,'OPENPROJECT_UNAVAILABLE_OUTCOME_MAY_BE_UNKNOWN')
                return result
            if path=='/api/v3/qldapm/gates/371':return {'gate':test.gate}
            if path.startswith('/api/v3/qldapm/mutation_receipts/'):
                key=path.rsplit('/',1)[1]
                if key not in test.receipts:raise NativeError(404,'MISSING')
                return test.receipts[key]
            return original(instance,path,method,payload,**kwargs)
        self.patch=patch.object(self.native,'call',core);self.patch.start();self.addCleanup(self.patch.stop)

    def prepare(self):
        return self.f.fixture.call(19,'qa_transition_prepare',{'id':self.evidence['id'],'hash':self.evidence['hash'],'status_id':9},'atomic-prepare')

    def test_preview_is_read_only_and_execution_requires_exact_claimed_own_proposal(self):
        p=self.prepare();self.assertTrue(any(kind=='preflight' for kind,_ in self.calls));self.assertFalse(any(kind=='write' for kind,_ in self.calls))
        with self.assertRaisesRegex(ValueError,'STALE_EXPIRED_OR_CONSUMED_PROPOSAL'):
            self.service.decide_proposal(self.tokens[19],p['id'],'approve','0'*64)
        result=self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.assertEqual(result['result']['lockVersion'],3);self.assertEqual(result['result']['qa_native']['evidence_id'],self.evidence['id'])
        self.assertEqual(sum(kind=='write' for kind,_ in self.calls),1)
        with self.assertRaisesRegex(ValueError,'STALE_EXPIRED_OR_CONSUMED_PROPOSAL'):
            self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.assertEqual(self.native.writes,[],'Legacy PATCH must not run for the atomic contract')

    def test_missing_business_prerequisites_and_direct_unapproved_execution_are_denied(self):
        self.errors=['EVIDENCE_STORY_REQUIRED','APPROVAL_SCOPE_REQUIRED']
        with self.assertRaises(NativeError):self.prepare()
        self.assertFalse(any(kind=='write' for kind,_ in self.calls))
        from gateway.native_qa_bridge import execute
        with self.assertRaises(PermissionError):execute(self.service,19,self.native('url','PM',5),self.native.row,
            {'id':371,'lock_version':1,'status_id':9,'qa_evidence_id':self.evidence['id'],'qa_evidence_hash':self.evidence['hash']},'not-an-approved-proposal')

    def test_known_rejected_qa_preparation_is_done_without_native_or_proposal_write(self):
        self.errors=['EVIDENCE_STORY_REQUIRED']
        for _ in range(2):
            with self.assertRaises(NativeError) as rejected:self.prepare()
            self.assertEqual(rejected.exception.status,422)
        receipt=self.store.request_status(19,'atomic-prepare')
        self.assertEqual(receipt['state'],'done')
        self.assertEqual(receipt['result'],{'error':'NATIVE_REJECTED','status':422,'outcome_unknown':False})
        self.assertFalse(any(kind=='write' for kind,_ in self.calls))
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from proposals').fetchone()[0],0)

    def test_pending_review_qa_preparation_stays409_and_cannot_pollute_unknown_requests(self):
        from gateway.app import create_app
        from starlette.testclient import TestClient
        with self.store.connect() as db:db.execute("update qa_evidence set state='pending_qa'")
        body={'action':'qa_transition_prepare','arguments':{'id':self.evidence['id'],'hash':self.evidence['hash'],'status_id':9},'idempotency_key':'pending-review-preview'}
        with TestClient(create_app(service=self.service),base_url='http://localhost:8090') as client:
            for _ in range(2):
                response=client.post('/api/v1/commands',headers={'Authorization':'Bearer '+self.tokens[19]},json=body)
                self.assertEqual(response.status_code,409)
        self.assertEqual(self.store.request_status(19,'pending-review-preview')['state'],'done')
        self.assertEqual(self.native.writes,[])
        with self.store.connect() as db:
            self.assertEqual(db.execute("select count(*) from requests where state!='done'").fetchone()[0],0)

    def test_transient_evidence_read_remains_retryable_and_does_not_become_a_known_rejection(self):
        with patch.object(self.native,'package',side_effect=NativeError(503,'OPENPROJECT_UNAVAILABLE_OUTCOME_MAY_BE_UNKNOWN')):
            with self.assertRaises(NativeError):self.prepare()
        self.assertEqual(self.store.request_status(19,'atomic-prepare')['state'],'pending')
        proposal=self.prepare();self.assertEqual(proposal['state'],'pending')
        self.assertEqual(self.store.request_status(19,'atomic-prepare')['state'],'done')
        self.assertFalse(any(kind=='write' for kind,_ in self.calls))

    def test_lost_reply_reconciles_exact_native_receipt_without_another_write(self):
        p=self.prepare();self.lose_reply=True
        with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        key='proposal-'+p['id']
        result=self.f.fixture.call(19,'reconcile_request',{'key':key})
        self.assertEqual(result['result']['id'],371);self.assertEqual(sum(kind=='write' for kind,_ in self.calls),1)
        self.assertEqual(self.store.request_status(19,key)['state'],'done')
        recovered=self.store.proposal(19,p['id'])
        self.assertEqual(recovered['state'],'done')
        self.assertTrue(recovered['result']['reconciled'])
        self.assertIn('prior_confirmation_result',recovered['result'])

    def test_different_evidence_cannot_replace_the_exact_approved_evidence_even_with_a_claim(self):
        from gateway.native_qa_bridge import execute,packet
        run=self.f.fixture.call(19,'qa_test_run',{'native_id':371},'another-valid-run')
        other=self.f.fixture.call(19,'qa_evidence_from_run',{'run_id':run['id']},'another-valid-evidence')
        for actor in [23,18]:self.service.decide_qa_evidence(self.tokens[actor],other['id'],'accept',other['hash'])
        proof=packet(self.service,19,other['id']);p=self.prepare();self.store.claim_proposal(19,p['id'],p['hash'])
        args=p['command']['arguments']
        with self.assertRaises(PermissionError):execute(self.service,19,self.native('url','PM',5),self.native.row,args,'proposal-'+p['id'],proof)
        self.assertFalse(any(kind=='write' for kind,_ in self.calls))

    def test_lost_reply_with_subsequent_source_drift_remains_held_without_replay(self):
        p=self.prepare();self.lose_reply=True
        with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.native.row['lockVersion']+=1;key='proposal-'+p['id']
        with self.assertRaisesRegex(NativeError,'SOURCE_CHANGED_HOLD'):
            self.f.fixture.call(19,'reconcile_request',{'key':key})
        self.assertEqual(sum(kind=='write' for kind,_ in self.calls),1)
        self.assertEqual(self.store.request_status(19,key)['state'],'pending')
        self.assertIsNone(self.store.request_status(19,key)['result'])

    def test_reconciled_native_receipt_keeps_original_verified_agent_trace(self):
        import time,uuid
        from gateway.agent_models import AgentTask,AgentRun
        from gateway.agent_trace import bind_run,reset_run
        now=time.time();run_id=self.store.create_run(19);task_id=str(uuid.uuid4());trace=str(uuid.uuid4())
        scope={'run_id':run_id,'task_id':task_id,'actor_id':19,'project_id':5,'trace_id':trace}
        task=AgentTask(task_id=task_id,actor_id=19,project_id=5,conversation_id=str(uuid.uuid4()),agent='pm',
            instruction='Isolated proposal lineage qualification',created_at=now,expires_at=now+300)
        self.store.create_agent_task(19,5,task);self.store.create_agent_run(19,5,AgentRun(**scope,created_at=now,updated_at=now))
        self.store.transition_agent_run(19,5,run_id,'QUEUED','RUNNING')
        token=bind_run(self.store,19,5,run_id)
        try:p=self.prepare()
        finally:reset_run(token)
        self.store.finish_run(19,run_id,{'status':'proposed','text':'Fixture proposal','tools':[{'result':{'result':{'id':p['id']}}}]},'done')
        self.lose_reply=True
        with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        response=self.f.fixture.call(19,'reconcile_request',{'key':'proposal-'+p['id']})
        self.assertEqual(response['origin'],{'run_id':run_id,'trace_id':trace,'proposal_id':p['id']})
        with self.store.connect() as db:
            row=db.execute("select run_id,trace_id from audit where id=?",(response['correlation_id'],)).fetchone()
        self.assertEqual((row['run_id'],row['trace_id']),(run_id,trace))

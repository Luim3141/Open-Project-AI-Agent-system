import copy
import unittest
from unittest.mock import patch

from gateway.native import NativeError
from gateway.store import canonical, digest
from tests import test_native_bug_lifecycle as fixtures


class NativeDependencyTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.NativeBugLifecycleTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        self.service, self.store, self.native, self.tokens = fixture.service, fixture.store, fixture.native, fixture.tokens
        self.native.rows[38] = copy.deepcopy(self.native.rows[39])
        self.native.rows[38].update(id=38,lockVersion=0)
        (self.store.root/'ui.key').write_bytes(b'isolated-dependency-key')
        self.plan = {'project_id':5,'predecessor_id':38,'successor_id':39,'type':'follows','lag':2,
                     'scope_hash':'a'*64,'possible_affected':[{'id':38,'lockVersion':0},{'id':39,'lockVersion':3}]}
        self.posts = []
        self.receipts = {}
        original = self.native.call
        def call(native,path,method='GET',payload=None):
            if path == '/api/v3/qldapm/dependency_forms': return copy.deepcopy(self.plan)
            if path == '/api/v3/qldapm/dependencies':
                self.posts.append(copy.deepcopy(payload))
                result = {'id':39,'lockVersion':3,'request_id':payload['request_id'],'provenance':'ai_gateway',
                        'scope_hash':payload['scope_hash'],'proposal_id':payload['proposal_id'],'proposal_hash':payload['proposal_hash'],
                        'relation':{'id':9,'type':'follows','predecessor_id':38,'successor_id':39,'lag':2},
                        'changed_ids':[], 'readback':[{'id':38,'lockVersion':self.native.rows[38]['lockVersion']},
                                                      {'id':39,'lockVersion':self.native.rows[39]['lockVersion']}]}
                self.receipts[payload['request_id']] = copy.deepcopy(result)
                return result
            if path.startswith('/api/v3/qldapm/mutation_receipts/'):
                return copy.deepcopy(self.receipts[path.rsplit('/',1)[-1]])
            if path == '/api/v3/relations/9':
                return {'id':9,'type':'follows','lag':2,'_links':{'from':{'href':'/api/v3/work_packages/39'},'to':{'href':'/api/v3/work_packages/38'}}}
            return original(native,path,method,payload)
        self.native.call = call

    def proposal(self, actor=18, key='dependency'):
        return self.service.execute(self.tokens[actor],{'action':'create_dependency','arguments':{'predecessor_id':38,'successor_id':39,'lag':2},'idempotency_key':key})['result']

    def test_exact_scope_proposal_separate_approval_and_atomic_multi_source_outbox(self):
        proposal = self.proposal(); self.assertEqual(self.posts,[])
        self.assertEqual(proposal['command']['arguments']['scope_hash'],'a'*64)
        with self.assertRaises(ValueError): self.service.decide_proposal(self.tokens[18],proposal['id'],'approve','0'*64)
        receipt = self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(len(self.posts),1)
        self.assertEqual({r['native_id'] for r in receipt['knowledge_syncs']},{38,39})
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from knowledge_sync').fetchone()[0],2)
            self.assertTrue(all(r[0].startswith('dependency:proposal-') for r in db.execute('select request_key from knowledge_sync')))
        with self.assertRaises(ValueError): self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(len(self.posts),1)

    def test_old_roles_cannot_create_or_approve_and_caller_flags_do_not_grant_rights(self):
        for actor in [20,21,22,23]:
            with self.subTest(actor=actor), self.assertRaises(PermissionError): self.proposal(actor,'denied-'+str(actor))
        for field in ['actor_id','admin','approved','scope_hash']:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.service.execute(self.tokens[18],{'action':'create_dependency','arguments':{'predecessor_id':38,'successor_id':39,'lag':2,field:True},'idempotency_key':'forged-'+field})
        self.assertEqual(self.posts,[])
        with self.store.connect() as db:
            self.assertEqual(db.execute("select count(*) from requests where state!='done'").fetchone()[0],0)

    def test_stale_scope_and_tampered_sealed_command_fail_before_native_post(self):
        p = self.proposal(); self.plan['scope_hash']='c'*64
        with self.assertRaises(NativeError): self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.assertEqual(self.posts,[])
        self.plan['scope_hash']='a'*64; p=self.proposal(key='tamper')
        with self.store.connect() as db:
            command=copy.deepcopy(p['command']); command['arguments']['lag']=3
            db.execute('update proposals set payload=? where id=?',(canonical(command),p['id']))
        with self.assertRaisesRegex(ValueError,'PROPOSAL_PAYLOAD_CHANGED'): self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.assertEqual(self.posts,[])

    def test_source_outbox_is_atomic_with_request_receipt_and_does_not_change_legacy_id(self):
        self.store.begin(18,'multi',{'action':'fixture'})
        with self.assertRaises(ValueError): self.store.finish(18,'multi',{'result':{}},knowledge_ids=[38,False])
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from knowledge_sync').fetchone()[0],0)
            self.assertEqual(db.execute("select state from requests where key='multi'").fetchone()[0],'pending')

    def test_lost_reply_reconciles_exact_receipt_and_both_sources_without_another_post(self):
        proposal = self.proposal()
        from gateway import native_dependency
        with patch.object(native_dependency,'readback',side_effect=NativeError(409,'simulated readback loss')):
            with self.assertRaises(NativeError):
                self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        key = 'proposal-'+proposal['id']
        self.assertEqual(self.store.request_status(18,key)['state'],'pending')
        self.assertEqual(len(self.posts),1)
        receipt = self.service.execute(self.tokens[18],{'action':'reconcile_request','arguments':{'key':key}})['result']
        self.assertTrue(receipt['reconciled'])
        self.assertEqual({r['native_id'] for r in receipt['knowledge_syncs']},{38,39})
        self.assertEqual(self.store.proposal(18,proposal['id'])['state'],'done')
        self.assertEqual(len(self.posts),1)

    def test_lost_reply_with_later_source_drift_is_held_without_native_retry(self):
        proposal = self.proposal()
        from gateway import native_dependency
        with patch.object(native_dependency,'readback',side_effect=NativeError(409,'simulated readback loss')):
            with self.assertRaises(NativeError):
                self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.native.rows[39]['lockVersion'] += 1
        key = 'proposal-'+proposal['id']
        with self.assertRaisesRegex(NativeError,'SOURCE_CHANGED_HOLD'):
            self.service.execute(self.tokens[18],{'action':'reconcile_request','arguments':{'key':key}})
        self.assertEqual(self.store.request_status(18,key)['state'],'pending')
        self.assertEqual(len(self.posts),1)

    def test_multi_source_worker_keeps_original_proposal_binding_and_waits_for_all_jobs(self):
        import time, uuid
        from gateway.agent_models import AgentTask, AgentRun
        from gateway.agent_trace import bind_run, reset_run
        now=time.time(); run_id=self.store.create_run(18); task_id=str(uuid.uuid4()); trace=str(uuid.uuid4())
        task=AgentTask(task_id=task_id,actor_id=18,project_id=5,conversation_id=str(uuid.uuid4()),agent='pm',
                       instruction='Isolated dependency proposal lineage',created_at=now,expires_at=now+300)
        self.store.create_agent_task(18,5,task)
        self.store.create_agent_run(18,5,AgentRun(run_id=run_id,task_id=task_id,actor_id=18,project_id=5,trace_id=trace,created_at=now,updated_at=now))
        self.store.transition_agent_run(18,5,run_id,'QUEUED','RUNNING')
        token=bind_run(self.store,18,5,run_id)
        try: proposal=self.proposal()
        finally: reset_run(token)
        self.store.finish_run(18,run_id,{'status':'proposed','text':'Fixture dependency','tools':[{'result':{'result':{'id':proposal['id']}}}]},'done')
        self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(self.store.proposal(18,proposal['id'])['lifecycle'],'NATIVE_CONFIRMED_RAG_PENDING')
        from gateway.agent_trace import current_run
        def ingest(actor,command):
            binding = current_run.get()
            self.assertIsNotNone(binding)
            self.assertEqual(binding[1].actor_id,18)
            return {'result':{'vector_indexed':True}}
        with patch.object(self.service,'execute_actor',side_effect=ingest),patch.object(self.service,'sync_canonical_native',return_value={'vector_indexed':True}):
            self.assertTrue(self.service.process_knowledge_sync())
            self.assertEqual(self.store.proposal(18,proposal['id'])['lifecycle'],'NATIVE_CONFIRMED_RAG_PENDING')
            self.assertTrue(self.service.process_knowledge_sync())
        self.assertEqual(self.store.proposal(18,proposal['id'])['lifecycle'],'VERIFIED_COMPLETED')

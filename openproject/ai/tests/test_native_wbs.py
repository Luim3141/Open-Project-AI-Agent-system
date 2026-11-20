"""Progressive hierarchy qualification with isolated Native fixture and real durable Store."""
import copy
import concurrent.futures
import unittest
from unittest.mock import patch

from gateway.native import NativeError
from gateway.service import Service
from tests import test_native_bug_lifecycle as bugs

SPEC={'requirements':[{'id':'R1','text':'Export results with Unicode fidelity'}],
      'nodes':[{'key':'epic','kind':'Epic','subject':'Unicode export delivery','requirement_ids':['R1']},
               {'key':'task','kind':'Task','parent':'epic','subject':'Implement streamed CSV export','requirement_ids':['R1']},
               {'key':'subtask','kind':'Subtask','parent':'task','subject':'Add Unicode serializer tests','requirement_ids':['R1'],'depends_on':['epic']}]}


class NativeWbsTests(unittest.TestCase):
    def setUp(self):
        fixture=bugs.NativeBugLifecycleTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.service=fixture.service;self.store=fixture.store;self.native=fixture.native;self.tokens=fixture.tokens;self.root=fixture.root
        original=self.native.call
        def call(native,path,method='GET',payload=None):
            result=original(native,path,method,payload)
            if method=='POST' and path=='/api/v3/work_packages':
                actor={'AI_SYSTEM_OWNER':18,'PM':19}[native.role]
                self.native.rows[result['id']]['_links']['author']={'href':f'/api/v3/users/{actor}'}
            return result
        self.native.call=call

    def call(self,action,args,actor=18,key=None):
        command={'action':action,'arguments':args}
        if key:command['idempotency_key']=key
        return self.service.execute(self.tokens[actor],command)['result']

    def draft(self,shared=True,key='wbs-draft'):
        return self.call('wbs_draft',{**copy.deepcopy(SPEC),'share_for_review':shared},20,key)

    def plan(self):
        draft=self.draft();return self.call('wbs_adopt',{'id':draft['id'],'hash':draft['hash']},18,'wbs-adopt')

    def next(self,plan,key='next',**extra):return self.call('wbs_next',{'id':plan['id'],'hash':plan['hash'],**extra},18,key)

    def verify_sync(self,receipt):
        claim=self.store.claim_knowledge_sync()
        self.assertEqual(claim['id'],receipt['knowledge_sync']['id'])
        self.assertTrue(self.store.finish_knowledge_sync(claim,{'vector_indexed':True,'fixture':'isolated pipeline receipt'}))

    def test_ba_draft_is_immutable_shared_explicitly_and_adopted_as_own_owner_plan(self):
        draft=self.draft();self.assertEqual(draft['actor'],20)
        self.assertEqual(self.draft()['id'],draft['id'])
        plan=self.plan();self.assertEqual(plan['actor'],18);self.assertEqual(plan['kind'],'plan')
        self.assertEqual(plan['origin'],{'id':draft['id'],'hash':draft['hash'],'actor':20})
        self.assertEqual(self.native.writes,[])
        with self.assertRaises(PermissionError):self.call('wbs_get',{'id':plan['id']},19)
        with self.assertRaises(PermissionError):self.call('wbs_next',{'id':plan['id'],'hash':plan['hash']},20,'ba-next')

    def test_unshared_draft_tamper_or_forged_actor_does_not_grant_authority(self):
        d=self.draft(False)
        with self.assertRaises(PermissionError):self.call('wbs_adopt',{'id':d['id'],'hash':d['hash']},18,'not-shared')
        d=self.draft(True,'shared')
        with self.assertRaisesRegex(ValueError,'WBS_EXACT_HASH_REQUIRED'):self.call('wbs_adopt',{'id':d['id'],'hash':'0'*64},18,'wrong-hash')
        with self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):self.call('wbs_draft',{**SPEC,'actor_id':18},20,'forged')
        with self.store.connect() as db:db.execute('UPDATE wbs_documents SET actor=19 WHERE id=?',(d['id'],))
        with self.assertRaises(ValueError):self.call('wbs_adopt',{'id':d['id'],'hash':d['hash']},18,'tampered')

    def test_coverage_hierarchy_cycles_unknown_keys_and_statuses_are_validated(self):
        variants=[]
        for mutate in [lambda s:s['nodes'][0].update(kind='Bug'),lambda s:s['nodes'][1].update(parent='subtask'),
                       lambda s:s['nodes'][0].update(depends_on=['subtask']),lambda s:s['nodes'][0].update(key='task'),
                       lambda s:s['requirements'].append({'id':'R2','text':'Uncovered'}),
                       lambda s:s['nodes'][1].update(requirement_ids=['unknown']),lambda s:s['nodes'][0].update(status_id=True),
                       lambda s:s['nodes'][2].update(actor_id=18)]:
            spec=copy.deepcopy(SPEC);mutate(spec);variants.append(spec)
        for index,spec in enumerate(variants):
            with self.subTest(index=index),self.assertRaises(ValueError):self.call('wbs_draft',spec,20,'invalid-'+str(index))
        self.assertEqual(self.native.writes,[])

    def test_progressive_three_node_tree_requires_each_exact_approval_and_verified_sync(self):
        plan=self.plan();ids=[]
        for index,node in enumerate(SPEC['nodes']):
            result=self.next(plan,'node-'+str(index));p=result['proposal']
            self.assertEqual(result['node_key'],node['key']);self.assertEqual(len(self.native.writes),index)
            self.assertEqual(self.next(plan,'same-node-'+str(index))['proposal']['id'],p['id'])
            with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],p['id'],'approve','0'*64)
            receipt=self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash']);ids.append(receipt['result']['id'])
            waiting=self.next(plan,'rag-pending-'+str(index));self.assertEqual(waiting['state'],'RAG_PENDING')
            self.verify_sync(receipt)
        result=self.call('wbs_get',{'id':plan['id']});self.assertEqual(result['progress']['state'],'VERIFIED_COMPLETED')
        self.assertEqual(self.native.rows[ids[1]]['_links']['parent']['href'],f'/api/v3/work_packages/{ids[0]}')
        self.assertEqual(self.native.rows[ids[2]]['_links']['parent']['href'],f'/api/v3/work_packages/{ids[1]}')
        self.assertEqual(len(self.native.writes),3)

    def test_unknown_post_stops_restart_and_reconciles_without_replay(self):
        plan=self.plan();p=self.next(plan)['proposal'];perform=self.service.perform
        def lose_reply(who,native,action,args,request_key=None):
            r=perform(who,native,action,args,request_key)
            if action=='create_work_package':raise NativeError(503,'ISOLATED_RESPONSE_LOST_AFTER_NATIVE_CREATE')
            return r
        with patch.object(self.service,'perform',side_effect=lose_reply):
            with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.service=Service(self.store,self.service.config,self.root/'workspace',self.native)
        self.assertEqual(self.next(plan,'after-restart')['state'],'UNKNOWN_HOLD');self.assertEqual(len(self.native.writes),1)
        receipt=self.call('reconcile_request',{'key':'proposal-'+p['id']},18,'reconcile-read-only')
        self.verify_sync(receipt);self.assertEqual(len(self.native.writes),1)
        self.assertEqual(self.next(plan,'after-reconcile')['node_key'],'task')

    def test_native_drift_role_revocation_and_proposal_tamper_block_children(self):
        plan=self.plan();p=self.next(plan)['proposal'];receipt=self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.verify_sync(receipt);self.native.rows[receipt['result']['id']]['lockVersion']+=1
        self.assertEqual(self.next(plan,'drift')['state'],'SOURCE_CHANGED')
        self.service.config['users']['18']='PM'
        with self.assertRaises(PermissionError):self.next(plan,'revoked')
        self.assertEqual(len(self.native.writes),1)

    def test_rejected_node_needs_explicit_exact_retry_and_fresh_proposal(self):
        plan=self.plan();p=self.next(plan)['proposal']
        self.call('reject_proposal',{'id':p['id'],'hash':p['hash']},18,'reject-node')
        self.assertEqual(self.next(plan,'after-reject')['state'],'REJECTED')
        with self.assertRaises(ValueError):self.next(plan,'bad-retry',retry_hash='0'*64)
        next_p=self.next(plan,'explicit-retry',retry_hash=p['hash'])['proposal']
        self.assertNotEqual(next_p['id'],p['id']);self.assertNotEqual(next_p['hash'],p['hash']);self.assertEqual(self.native.writes,[])

    def test_duplicate_subject_requires_disposition_and_form_rejection_never_writes(self):
        spec=copy.deepcopy(SPEC);spec['nodes'][0]['subject']='Other task'
        d=self.call('wbs_draft',{**spec,'share_for_review':True},20,'duplicate-draft')
        p=self.call('wbs_adopt',{'id':d['id'],'hash':d['hash']},18,'duplicate-plan')
        with self.assertRaisesRegex(ValueError,'WBS_DUPLICATE_DISPOSITION_REQUIRED'):self.next(p,'blocked-duplicate')
        self.native.form_errors={'type':{'message':'Native policy changed'}}
        with self.assertRaisesRegex(NativeError,'OPENPROJECT_FORM_REJECTED'):self.next(self.plan(),'form-rejected')
        self.assertEqual(self.native.writes,[])

    def test_concurrent_next_returns_one_proposal_or_retriable_lock_without_duplicates(self):
        plan=self.plan()
        def attempt(index):
            try:return self.next(plan,'concurrent-'+str(index))
            except ValueError as error:
                self.assertIn('KNOWLEDGE_BUSY_RETRY_LATER',str(error));return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,range(2)))
        proposals=[r['proposal']['id'] for r in results if r]
        self.assertTrue(proposals);self.assertEqual(len(set(proposals)),1)
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM proposals').fetchone()[0],1)
        self.assertEqual(self.next(plan,'after-contention')['proposal']['id'],proposals[0])
        self.assertEqual(self.native.writes,[])

    def test_lost_metadata_receipt_recovers_same_draft_and_same_node_proposal(self):
        finish=self.store.finish
        def lose_draft(actor,key,result,knowledge_id=None):
            if key=='lost-draft':raise RuntimeError('ISOLATED_METADATA_REPLY_LOSS')
            return finish(actor,key,result,knowledge_id)
        with patch.object(self.store,'finish',side_effect=lose_draft):
            with self.assertRaises(RuntimeError):self.draft(key='lost-draft')
        d=self.draft(key='lost-draft');self.assertEqual(d['kind'],'draft')
        plan=self.plan()
        def lose_proposal(actor,key,result,knowledge_id=None):
            if key.startswith('wbs-'+plan['id']):raise RuntimeError('ISOLATED_PROPOSAL_REPLY_LOSS')
            return finish(actor,key,result,knowledge_id)
        with patch.object(self.store,'finish',side_effect=lose_proposal):
            with self.assertRaises(RuntimeError):self.next(plan,'lost-node')
        recovered=self.next(plan,'lost-node');self.assertEqual(recovered['state'],'AWAITING_APPROVAL')
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM proposals').fetchone()[0],1)
        self.assertEqual(self.native.writes,[])


if __name__=='__main__':unittest.main()

"""Explicit Native relations extend new plans without changing legacy sequencing semantics."""
import copy
import unittest
import uuid
from unittest.mock import patch
from gateway.native import NativeError
from gateway.store import canonical,digest
from tests import test_native_wbs as fixtures


class WbsNativeRelationTests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.NativeWbsTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.fixture=fixture;self.service=fixture.service;self.store=fixture.store;self.native=fixture.native;self.tokens=fixture.tokens
        (self.store.root/'ui.key').write_bytes(b'isolated-wbs-native-relations-key')
        self.spec=copy.deepcopy(fixtures.SPEC)
        self.spec['share_for_review']=True
        self.spec['nodes'].append({'key':'verify','kind':'Subtask','parent':'task','subject':'Verify export fixture','requirement_ids':['R1']})
        self.spec['relations']=[{'predecessor':'subtask','successor':'verify','lag':0}]
        self.posts=[];self.receipts={};self.relations={};self.outside_scope=False;original=self.native.call
        def call(native,path,method='GET',payload=None):
            from gateway.native_wbs_relations import scope
            if path=='/api/v3/qldapm/dependency_forms':
                ids=sorted(identifier for identifier in self.native.rows if identifier>=900)
                if self.outside_scope:ids.append(39)
                rows=[scope(self.native.rows[identifier]) for identifier in ids]
                return {'project_id':5,'type':'follows',**payload,'scope_hash':digest(canonical(rows)),'possible_affected':rows}
            if path=='/api/v3/qldapm/dependencies':
                self.posts.append(copy.deepcopy(payload));identifier=100+len(self.posts)
                pre,suc=payload['predecessor_id'],payload['successor_id'];item=self.native.rows[suc]
                item.update(lockVersion=item['lockVersion']+1,startDate='2026-10-28',dueDate='2026-10-29',scheduleManually=True)
                relation={'id':identifier,'type':'follows','lag':payload['lag'],'_links':{'from':{'href':f'/api/v3/work_packages/{suc}'},'to':{'href':f'/api/v3/work_packages/{pre}'}}};self.relations[identifier]=relation
                result={'id':suc,'lockVersion':item['lockVersion'],'request_id':payload['request_id'],'provenance':'ai_gateway',
                    'proposal_id':payload['proposal_id'],'proposal_hash':payload['proposal_hash'],'scope_hash':payload['scope_hash'],
                    'relation':{'id':identifier,'type':'follows','predecessor_id':pre,'successor_id':suc,'lag':payload['lag']},'changed_ids':[suc],
                    'readback':[{k:v for k,v in scope(self.native.rows[i]).items() if k!='parent_id'} for i in [pre,suc]]}
                self.receipts[payload['request_id']]=copy.deepcopy(result);return result
            if path.startswith('/api/v3/qldapm/mutation_receipts/'):return copy.deepcopy(self.receipts[path.rsplit('/',1)[-1]])
            if path.startswith('/api/v3/relations/'):return copy.deepcopy(self.relations[int(path.rsplit('/',1)[-1])])
            return original(native,path,method,payload)
        self.native.call=call

    def tree(self):
        draft=self.fixture.call('wbs_draft',self.spec,20,'relation-draft')
        plan=self.fixture.call('wbs_adopt',{'id':draft['id'],'hash':draft['hash']},18,'relation-plan')
        for index in range(len(self.spec['nodes'])):
            proposal=self.fixture.next(plan,'create-node-'+str(index))['proposal']
            receipt=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
            self.fixture.verify_sync(receipt)
        return plan

    def sync_relation(self,receipt):
        jobs={row['id'] for row in receipt['knowledge_syncs']}
        for _ in jobs:
            claim=self.store.claim_knowledge_sync();self.assertIn(claim['id'],jobs)
            self.assertTrue(self.store.finish_knowledge_sync(claim,{'vector_indexed':True,'fixture':'isolated state-machine receipt, not live vector proof'}))

    def test_explicit_relations_are_typed_and_do_not_infer_legacy_sequencing(self):
        draft=self.fixture.call('wbs_draft',self.spec,20,'typed-relations')
        self.assertEqual(draft['spec']['relations'],self.spec['relations'])
        legacy=self.fixture.draft();self.assertNotIn('relations',legacy['spec'])
        for index,relation in enumerate([{'predecessor':'subtask','successor':'unknown','lag':0},
                {'predecessor':'task','successor':'subtask','lag':0},
                {'predecessor':'verify','successor':'verify','lag':0},
                {'predecessor':'subtask','successor':'verify','lag':True},
                {'predecessor':'subtask','successor':'verify','lag':2001},
                {'predecessor':'subtask','successor':'verify','lag':0,'approved':True}]):
            spec={**copy.deepcopy(self.spec),'relations':[relation]}
            with self.subTest(index=index),self.assertRaises(ValueError):self.fixture.call('wbs_draft',spec,20,'invalid-relation-'+str(index))
        for relations in [self.spec['relations']*2,self.spec['relations']+[{'predecessor':'verify','successor':'subtask','lag':0}]]:
            with self.assertRaises(ValueError):self.fixture.call('wbs_draft',{**self.spec,'relations':relations},20,'invalid-graph-'+str(len(relations)))
        self.assertEqual(self.native.writes,[])

    def test_nodes_alone_never_complete_a_plan_with_explicit_relations(self):
        plan=self.tree()
        progress=self.fixture.call('wbs_get',{'id':plan['id']})['progress']
        self.assertEqual(progress['state'],'READY_FOR_DEPENDENCIES')
        self.assertEqual(progress['relations'][0]['state'],'NOT_PROPOSED')
        self.assertEqual(len(self.native.writes),4)

    def test_relation_requires_own_exact_approval_receipt_and_all_rag_jobs(self):
        plan=self.tree();result=self.fixture.next(plan,'native-relation');proposal=result['proposal']
        self.assertEqual(result['relation_index'],0);self.assertEqual(proposal['command']['action'],'create_dependency');self.assertFalse(self.posts)
        self.assertEqual(self.fixture.next(plan,'same-relation')['proposal']['id'],proposal['id'])
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve','0'*64)
        receipt=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash']);self.assertEqual(len(self.posts),1)
        self.assertEqual(self.fixture.call('wbs_get',{'id':plan['id']})['progress']['state'],'RAG_PENDING')
        self.sync_relation(receipt);state=self.fixture.call('wbs_get',{'id':plan['id']})['progress']
        self.assertEqual(state['state'],'VERIFIED_COMPLETED');self.assertEqual(state['relations'][0]['native_relation_id'],101)
        self.assertEqual(self.fixture.next(plan,'completed-plan')['state'],'VERIFIED_COMPLETED');self.assertEqual(len(self.posts),1)
        self.native.rows[state['native_ids']['verify']]['subject']='External source change'
        self.assertEqual(self.fixture.call('wbs_get',{'id':plan['id']})['progress']['state'],'SOURCE_CHANGED')

    def test_unknown_commit_holds_restart_and_recovers_without_replaying_relation(self):
        plan=self.tree();proposal=self.fixture.next(plan,'native-relation')['proposal'];original=self.service.perform
        def fault(who,native,action,args,request_key=None):
            result=original(who,native,action,args,request_key)
            if action=='create_dependency':raise NativeError(503,'FIXTURE_LOST_ACK_AFTER_RELATION_COMMIT')
            return result
        with patch.object(self.service,'perform',side_effect=fault):
            with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        from gateway.service import Service
        from gateway.store import Store
        self.service=Service(Store(self.store.root),self.service.config,self.store.root/'workspace',self.native);self.fixture.service=self.service
        self.assertEqual(self.fixture.next(plan,'unknown-plan')['state'],'UNKNOWN_HOLD');self.assertEqual(len(self.posts),1)
        receipt=self.fixture.call('reconcile_request',{'key':'proposal-'+proposal['id']})
        self.sync_relation(receipt);self.assertEqual(self.fixture.next(plan,'reconciled-plan')['state'],'VERIFIED_COMPLETED');self.assertEqual(len(self.posts),1)

    def test_external_native_scope_and_old_role_limits_hold(self):
        plan=self.tree();self.outside_scope=True
        with self.assertRaisesRegex(NativeError,'EXTERNAL_SCOPE_HOLD'):self.fixture.next(plan,'external-plan')
        self.assertFalse(self.posts)
        for actor in [20,21,22,23]:
            with self.assertRaises(PermissionError):self.fixture.call('wbs_next',{'id':plan['id'],'hash':plan['hash']},actor,'wrong-actor-'+str(actor))

    def test_multiple_relations_apply_in_order_with_separate_receipts_and_rag_gates(self):
        self.spec['nodes'].append({'key':'finish','kind':'Subtask','parent':'task','subject':'Final fixture checks','requirement_ids':['R1']})
        self.spec['relations'].append({'predecessor':'verify','successor':'finish','lag':2})
        plan=self.tree()
        for index in range(2):
            result=self.fixture.next(plan,'relation-stage-'+str(index));self.assertEqual(result['relation_index'],index)
            p=result['proposal'];receipt=self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
            self.assertEqual(self.fixture.next(plan,'rag-stage-'+str(index))['state'],'RAG_PENDING')
            self.sync_relation(receipt)
        result=self.fixture.call('wbs_get',{'id':plan['id']})['progress'];self.assertEqual(result['state'],'VERIFIED_COMPLETED')
        self.assertEqual([row['native_relation_id'] for row in result['relations']],[101,102]);self.assertEqual(len(self.posts),2)

    def test_private_native_baseline_is_not_a_public_wbs_document(self):
        plan=self.tree();self.fixture.next(plan,'native-relation')
        identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f'qldapm.wbs:18:5:dependency_baseline:{plan["id"]}'))
        with self.assertRaisesRegex(PermissionError,'PRIVATE_RECORD_DENIED'):self.fixture.call('wbs_get',{'id':identifier})

    def test_rejected_relation_requires_exact_retry_hash_and_a_new_approval(self):
        plan=self.tree();proposal=self.fixture.next(plan,'first-relation')['proposal']
        self.service.decide_proposal(self.tokens[18],proposal['id'],'reject',proposal['hash'])
        self.assertEqual(self.fixture.next(plan,'rejected-relation')['state'],'REJECTED');self.assertFalse(self.posts)
        with self.assertRaisesRegex(ValueError,'EXACT_RETRY_HASH_REQUIRED'):self.fixture.next(plan,'bad-retry',retry_hash='0'*64)
        retry=self.fixture.next(plan,'retry-relation',retry_hash=proposal['hash'])['proposal'];self.assertNotEqual(retry['id'],proposal['id'])
        self.assertFalse(self.posts);receipt=self.service.decide_proposal(self.tokens[18],retry['id'],'approve',retry['hash']);self.sync_relation(receipt)
        self.assertEqual(self.fixture.call('wbs_get',{'id':plan['id']})['progress']['state'],'VERIFIED_COMPLETED');self.assertEqual(len(self.posts),1)

    def test_tampered_local_receipt_cannot_replace_authoritative_core_commit(self):
        plan=self.tree();proposal=self.fixture.next(plan,'native-relation')['proposal']
        receipt=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash']);self.sync_relation(receipt)
        altered=copy.deepcopy(receipt);altered['result']['relation']['lag']=7
        with self.store.connect() as db:db.execute('update requests set result=? where actor=18 and key=?',(canonical(altered),'proposal-'+proposal['id']))
        with self.assertRaisesRegex(NativeError,'RECEIPT_HOLD'):self.fixture.call('wbs_get',{'id':plan['id']})

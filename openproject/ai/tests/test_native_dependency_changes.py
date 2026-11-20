"""Version-bound update/delete of an existing relation, never a Work Package delete."""
import copy
import unittest
from unittest.mock import patch

from gateway.native import NativeError
from tests import test_native_dependency as fixtures


class NativeDependencyChangeTests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.NativeDependencyTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.service,self.store,self.native,self.tokens=fixture.service,fixture.store,fixture.native,fixture.tokens
        self.posts=[];self.receipts={};self.deleted=False;self.lag=0;self.scope='a'*64
        original=self.native.call
        def call(native,path,method='GET',payload=None):
            if path=='/api/v3/qldapm/dependency_change_forms':
                return {'project_id':5,'operation':payload['operation'],'relation_id':9,
                        'predecessor_id':38,'successor_id':39,'lag':payload.get('lag',self.lag),
                        'before':{'lag':self.lag},'scope_hash':self.scope,'possible_affected':[{'id':38,'lockVersion':0},{'id':39,'lockVersion':3}]}
            if path=='/api/v3/qldapm/dependency_changes':
                self.posts.append(copy.deepcopy(payload));self.deleted=payload['operation']=='delete';self.lag=payload.get('lag',self.lag)
                result={'id':39,'lockVersion':3,'request_id':payload['request_id'],'provenance':'ai_gateway',
                        'proposal_id':payload['proposal_id'],'proposal_hash':payload['proposal_hash'],
                        'scope_hash':payload['scope_hash'],'operation':payload['operation'],
                        'relation':{'id':9,'type':'follows','predecessor_id':38,'successor_id':39,'lag':self.lag},
                        'changed_ids':[],'readback':[{'id':38,'lockVersion':0},{'id':39,'lockVersion':3}]}
                self.receipts[payload['request_id']]=copy.deepcopy(result);return result
            if path.startswith('/api/v3/qldapm/mutation_receipts/'):
                return copy.deepcopy(self.receipts[path.rsplit('/',1)[-1]])
            if path=='/api/v3/relations/9':
                if self.deleted:raise NativeError(404,'OPENPROJECT_404')
                return {'id':9,'type':'follows','lag':self.lag,'_links':{'from':{'href':'/api/v3/work_packages/39'},'to':{'href':'/api/v3/work_packages/38'}}}
            return original(native,path,method,payload)
        self.native.call=call

    def proposal(self,action,actor=18,key=None,extra=None):
        args={'relation_id':9,**({'lag':2} if action=='update_dependency' else {}),**(extra or {})}
        return self.service.execute(self.tokens[actor],{'action':action,'arguments':args,'idempotency_key':key or action})['result']

    def test_both_operations_require_exact_approval_and_enqueue_both_sources(self):
        for action in ['update_dependency','delete_dependency']:
            with self.subTest(action=action):
                proposal=self.proposal(action);self.assertEqual(len(self.posts),0 if action=='update_dependency' else 1)
                self.assertEqual(proposal['command']['arguments']['scope_hash'],self.scope)
                with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve','0'*64)
                receipt=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
                self.assertEqual(receipt['result']['operation'],'update' if action=='update_dependency' else 'delete')
                self.assertEqual({row['native_id'] for row in receipt['knowledge_syncs']},{38,39})
                with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(len(self.posts),2)

    def test_existing_role_limits_and_caller_scope_forgery_are_preserved(self):
        for action in ['update_dependency','delete_dependency']:
            for actor in [20,21,22,23]:
                with self.subTest(action=action,actor=actor),self.assertRaises(PermissionError):self.proposal(action,actor,key=action+str(actor))
            for field in ['scope_hash','predecessor_id','successor_id','operation','actor_id','admin','approved']:
                with self.subTest(action=action,field=field),self.assertRaises(ValueError):self.proposal(action,key=action+field,extra={field:True})
        self.assertEqual(self.posts,[])

    def test_changed_scope_is_rejected_before_native_mutation(self):
        proposal=self.proposal('update_dependency');self.scope='b'*64
        with self.assertRaisesRegex(NativeError,'STALE'):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(self.posts,[])

    def test_native_unset_lag_is_preserved_in_preview_and_delete_receipt(self):
        self.lag=None
        update=self.proposal('update_dependency',key='unset-update-preview')
        self.assertIsNone(update['command']['preview']['before']['lag'])
        self.assertEqual(update['command']['arguments']['lag'],2)
        proposal=self.proposal('delete_dependency')
        self.assertIsNone(proposal['command']['preview']['before']['lag'])
        receipt=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertIsNone(receipt['result']['relation']['lag'])

    def test_deleted_relation_requires_bound_receipt_and_recovers_lost_reply_without_second_write(self):
        proposal=self.proposal('delete_dependency')
        from gateway import native_dependency_change
        with patch.object(native_dependency_change,'readback',side_effect=NativeError(409,'ISOLATED_REPLY_LOSS')):
            with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(len(self.posts),1)
        receipt=self.service.execute(self.tokens[18],{'action':'reconcile_request','arguments':{'key':'proposal-'+proposal['id']}})['result']
        self.assertTrue(receipt['reconciled']);self.assertEqual(len(self.posts),1)
        self.assertEqual(self.store.proposal(18,proposal['id'])['state'],'done')
        self.assertEqual({row['native_id'] for row in receipt['knowledge_syncs']},{38,39})

    def test_receipt_cannot_be_rebound_to_another_relation_or_operation(self):
        proposal=self.proposal('delete_dependency');args=proposal['command']['arguments']
        from gateway import native_dependency_change
        result={'id':39,'request_id':'forged','provenance':'ai_gateway','relation':{'id':999},'operation':'update'}
        with self.assertRaises(NativeError):native_dependency_change.readback(self.native('url','AI_SYSTEM_OWNER',5),result,args,18,proposal)

    def test_lost_reply_with_source_drift_remains_held(self):
        proposal=self.proposal('update_dependency')
        from gateway import native_dependency_change
        with patch.object(native_dependency_change,'readback',side_effect=NativeError(409,'ISOLATED_REPLY_LOSS')):
            with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.native.rows[39]['lockVersion']+=1
        with self.assertRaises(NativeError):self.service.execute(self.tokens[18],{'action':'reconcile_request','arguments':{'key':'proposal-'+proposal['id']}})
        self.assertEqual(len(self.posts),1)


if __name__=='__main__':unittest.main()

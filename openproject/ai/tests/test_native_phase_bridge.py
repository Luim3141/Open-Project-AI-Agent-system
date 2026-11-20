"""Exact phase proposal claims, authoritative receipts, and RAG outbox never replay Native writes."""
import copy
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from gateway.native import NativeError
from gateway.service import Service
from tests import test_native_phase as fixtures


class NativePhaseBridgeTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.NativePhaseTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.service=self.f.service;self.store=self.f.store;self.tokens=self.f.tokens;self.native=self.f.h.native
        self.service.config['status_ids'].append(37);self.doc=self.f.draft();self.f.review(self.doc)
        self.posts=[];self.receipts={};self.lose=False;self.bad_form=False;self.events=[];original=self.native.call
        def core(native,path,method='GET',payload=None):
            if path=='/api/v3/qldapm/capabilities':return {'project_id':5,'enforced':True,'native_phase_bridge_version':1,'qa_bridge_version':0}
            if path=='/api/v3/qldapm/phase_transition_forms':
                if self.bad_form:raise NativeError(422,'PHASE_NATIVE_TRANSITION_DENIED')
                return {'valid':True,'id':self.doc['id'],'hash':self.doc['hash'],'source_version':self.doc['source']['version'],'lockVersion':self.native.rows[39]['lockVersion'],'status_id':37}
            if path=='/api/v3/qldapm/mutations':
                self.posts.append(copy.deepcopy(payload));self.native.rows[39]['lockVersion']+=2
                self.native.rows[39]['_links']['status']={'href':'/api/v3/statuses/37'}
                approved=payload['phase_authorization'];summary={'id':self.doc['id'],'hash':self.doc['hash'],'source_version':payload['lock_version'],
                    'kind':'scope','gate_revision':2,'status_id':37,'proposal_id':approved['proposal_id'],'proposal_hash':approved['proposal_hash']}
                result={'id':39,'lockVersion':self.native.rows[39]['lockVersion'],'request_id':payload['request_id'],'provenance':'ai_gateway','phase_native':summary}
                self.receipts[payload['request_id']]=copy.deepcopy(result)
                self.events=[{'operation':'native_source_phase_transition','actor_id':19,'request_id':payload['request_id'],'proposal_id':approved['proposal_id'],'proposal_hash':approved['proposal_hash'],'phase_id':self.doc['id'],'phase_hash':self.doc['hash']}]
                if self.lose:raise NativeError(503,'FIXTURE_LOST_ACK_AFTER_COMMIT')
                return result
            if path.startswith('/api/v3/qldapm/mutation_receipts/'):
                if path.rsplit('/',1)[-1] not in self.receipts:raise NativeError(404,'NOT_FOUND')
                return copy.deepcopy(self.receipts[path.rsplit('/',1)[-1]])
            if path=='/api/v3/qldapm/gates/39':return {'id':39,'lockVersion':self.native.rows[39]['lockVersion'],'gate':{'revision':1,'contributors':[],'events':self.events}}
            return original(native,path,method,payload)
        self.native.call=core

    def prepare(self):
        return self.service.execute(self.tokens[19],{'action':'transition','arguments':{'id':39,'lock_version':3,'status_id':37,
            'phase_id':self.doc['id'],'phase_hash':self.doc['hash']},'idempotency_key':'source-phase-transition'})['result']

    def test_invalid_native_transition_and_missing_claim_cannot_execute(self):
        from gateway.native_phase_bridge import execute
        native,who=self.service.native_actor(19)
        with self.assertRaises(PermissionError):execute(self.service,19,native,native.package(39),{'id':39,'phase_id':self.doc['id'],'phase_hash':self.doc['hash']},'not-a-proposal')
        self.bad_form=True
        with self.assertRaises(NativeError):self.prepare()
        self.assertFalse(self.posts)

    def test_public_prepare_is_only_a_separate_exact_proposal_and_never_a_write(self):
        command={'action':'phase_transition_prepare','arguments':{'id':self.doc['id'],'hash':self.doc['hash'],'status_id':37},'idempotency_key':'public-phase-prepare'}
        for actor in [20,21,22,23]:
            with self.assertRaises(PermissionError):self.service.execute(self.tokens[actor],command)
        proposal=self.service.execute(self.tokens[19],command)['result']
        self.assertEqual(proposal['command']['action'],'transition')
        self.assertEqual(proposal['command']['arguments']['phase_hash'],self.doc['hash'])
        self.assertEqual(proposal['state'],'pending');self.assertFalse(self.posts)
        self.assertEqual(self.service.execute(self.tokens[19],command)['result']['id'],proposal['id'])

    def test_exact_proposal_replay_and_rag_pending_contract(self):
        p=self.prepare();self.assertFalse(self.posts)
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[19],p['id'],'approve','0'*64)
        result=self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.assertEqual(result['result']['phase_native']['id'],self.doc['id']);self.assertEqual(result['knowledge_sync']['state'],'pending')
        self.assertEqual(len(self.posts),1);self.assertFalse(self.native.writes)
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])

    def test_lost_ack_restart_and_receipt_reconciliation_does_not_reexecute(self):
        p=self.prepare();self.lose=True
        with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        restarted=Service(self.store,self.service.config,self.f.h.root/'workspace',self.native)
        receipt=restarted.execute(self.tokens[19],{'action':'reconcile_request','arguments':{'key':'proposal-'+p['id']}})['result']
        self.assertTrue(receipt['reconciled']);self.assertEqual(self.store.proposal(19,p['id'])['state'],'done')
        self.assertEqual(receipt['knowledge_sync']['state'],'pending');self.assertEqual(len(self.posts),1)
        self.assertFalse(self.native.writes)

    def test_concurrent_human_decisions_claim_one_native_write(self):
        p=self.prepare()
        def decide():
            try:return self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
            except ValueError:return 'CONFLICT'
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(lambda _:decide(),range(2)))
        self.assertEqual(outcomes.count('CONFLICT'),1);self.assertEqual(len(self.posts),1)
        self.assertEqual(self.store.proposal(19,p['id'])['state'],'done')


if __name__=='__main__':unittest.main()

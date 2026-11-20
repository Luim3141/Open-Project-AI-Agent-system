"""Synthetic Native outcomes and persistent RAG outbox; never Main or Google."""
import concurrent.futures
import tempfile
import unittest
from pathlib import Path

from gateway.store import Store


class KnowledgeSyncTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.store=Store(self.root)

    def enqueue(self,key='write-1'):
        self.store.begin(7,key,{'action':'update_work_package'})
        result={'result':{'id':12,'lockVersion':2}}
        self.store.finish(7,key,result,knowledge_id=12)
        return result['knowledge_sync']['id']

    def test_native_receipt_and_sync_are_durable_together_and_actor_scoped(self):
        identifier=self.enqueue()
        restarted=Store(self.root)
        self.assertEqual(restarted.request_status(7,'write-1')['state'],'done')
        self.assertEqual(restarted.knowledge_sync(7,identifier)['state'],'pending')
        with self.assertRaises(PermissionError):
            restarted.knowledge_sync(8,identifier)

    def test_outbox_insert_rolls_back_without_the_native_request_receipt(self):
        with self.assertRaisesRegex(ValueError,'NATIVE_REQUEST_RECEIPT_REQUIRED'):
            self.store.finish(7,'missing',{'result':{'id':12}},knowledge_id=12)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_sync').fetchone()[0],0)

    def test_proven_reconciliation_enqueues_once_without_replaying_native(self):
        self.store.begin(7,'lost-reply',{'action':'create_work_package'})
        first=self.store.finish_reconciliation(7,'lost-reply',{'id':12},5,knowledge_id=12)
        second=self.store.finish_reconciliation(7,'lost-reply',{'id':12},5,knowledge_id=12)
        self.assertEqual(first,second)
        self.assertEqual(self.store.knowledge_sync(7,first['knowledge_sync']['id'])['state'],'pending')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_sync').fetchone()[0],1)

    def test_concurrent_claim_and_expired_lease_recovery_are_single_owner(self):
        self.enqueue()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            claims=list(pool.map(lambda _:self.store.claim_knowledge_sync(now=1000),range(2)))
        first=next(c for c in claims if c)
        self.assertEqual(sum(c is not None for c in claims),1)
        self.assertIsNone(self.store.claim_knowledge_sync(now=1001))
        next_claim=self.store.claim_knowledge_sync(now=1401)
        self.assertNotEqual(first['lease'],next_claim['lease'])
        self.assertFalse(self.store.finish_knowledge_sync(first,{'vector_indexed':True},now=1402))
        self.assertTrue(self.store.finish_knowledge_sync(next_claim,{'vector_indexed':True},now=1402))

    def test_exponential_retry_dlq_and_explicit_actor_retry_survive_restart(self):
        identifier=self.enqueue()
        now=1000
        for attempt in range(1,6):
            claim=self.store.claim_knowledge_sync(now=now)
            self.assertEqual(claim['attempts'],attempt)
            self.store.finish_knowledge_sync(claim,None,error='VECTOR_UNAVAILABLE',now=now)
            job=Store(self.root).knowledge_sync(7,identifier)
            if attempt<5:
                self.assertEqual(job['next_at'],now+5*2**(attempt-1))
                self.assertIsNone(self.store.claim_knowledge_sync(now=now+1))
                now=job['next_at']
        self.assertEqual(job['state'],'dlq')
        self.assertIsNone(self.store.claim_knowledge_sync(now=now+1000))
        with self.assertRaises(PermissionError):
            self.store.retry_knowledge_sync(8,identifier)
        retried=self.store.retry_knowledge_sync(7,identifier)
        self.assertEqual(retried['state'],'pending')
        self.assertEqual(retried['attempts'],0)
        self.assertEqual(self.store.request_status(7,'write-1')['state'],'done')

    def test_vector_failure_never_replays_native_write_and_completion_waits_for_readback(self):
        from gateway.service import Service
        from tests.test_takeover_security import NativeFixture
        token=self.store.issue_token(7,'PM','PM')
        service=Service(self.store,{'users':{'7':'PM'},'project_id':5,'gateway_mode':'native',
            'openproject_url':'http://127.0.0.1:8088'},self.root/'workspaces',NativeFixture)
        writes=[]
        def perform(who,native,action,args,key=None):
            if action=='update_work_package':
                writes.append(args)
                return {'id':12,'lockVersion':2}
            if action=='knowledge_ingest':
                if not getattr(service,'vector_recovered',False):
                    raise RuntimeError('synthetic vector outage')
                return {'vector_indexed':True,'native_id':12,'lock_version':2}
            raise AssertionError(action)
        service.perform=perform
        service.sync_canonical_native=lambda actor,identifier:{'vector_indexed':True,'native_id':identifier,'lock_version':2}
        proposal=service.execute(token,{'action':'update_work_package','arguments':{'id':12,'lock_version':1,
            'changes':{'subject':'approved fixture'}},'idempotency_key':'proposal-fixture'})['result']
        receipt=service.confirm(7,proposal['id'],proposal['hash'])
        identifier=receipt['knowledge_sync']['id']
        self.assertEqual(self.store.proposal(7,proposal['id'])['lifecycle'],'NATIVE_CONFIRMED_RAG_PENDING')
        service.process_knowledge_sync()
        self.assertEqual(self.store.knowledge_sync(7,identifier)['state'],'retry')
        service.vector_recovered=True
        with self.store.connect() as db:
            db.execute('UPDATE knowledge_sync SET next_at=0 WHERE id=?',(identifier,))
        service.process_knowledge_sync()
        self.assertEqual(self.store.proposal(7,proposal['id'])['lifecycle'],'VERIFIED_COMPLETED')
        with self.assertRaises(ValueError):
            service.confirm(7,proposal['id'],proposal['hash'])
        self.assertEqual(len(writes),1)

    def test_gateway_recovery_replay_is_idempotent_and_other_actor_cannot_read_job(self):
        from gateway.service import Service
        from tests.test_takeover_security import NativeFixture
        pm=self.store.issue_token(7,'PM','PM');ba=self.store.issue_token(8,'BA','BA')
        service=Service(self.store,{'users':{'7':'PM','8':'BA'},'project_id':5,'gateway_mode':'native',
            'openproject_url':'http://127.0.0.1:8088'},self.root/'workspaces',NativeFixture)
        identifier=self.enqueue()
        with self.store.connect() as db:
            db.execute("UPDATE knowledge_sync SET state='dlq',attempts=5 WHERE id=?",(identifier,))
        command={'action':'knowledge_sync_retry','arguments':{'id':identifier},'idempotency_key':'fixed-recovery-request'}
        first=service.execute(pm,command)
        self.assertEqual(first['result']['state'],'pending')
        self.assertEqual(service.execute(pm,command),first)
        self.assertEqual(self.store.knowledge_sync(7,identifier)['attempts'],0)
        with self.assertRaises(PermissionError):
            service.execute(ba,{'action':'knowledge_sync_status','arguments':{'id':identifier}})


if __name__=='__main__':
    unittest.main()

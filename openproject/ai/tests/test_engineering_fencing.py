"""Real SQLite claims; synthetic Native and host subprocesses, no external writes."""
import json
import tempfile
import time
import unittest
import uuid
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gateway import engineering
from gateway.engineering_operator import operation, native_once
from gateway.store import Store
from test_engineering_continuation import Native


class FencingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.native=Native()
        self.service=SimpleNamespace(store=self.store,config={'project_id':6,'engineering':{'enabled':True}},
            native_actor=lambda actor:(self.native,{'user_id':actor,'role':'PM'}))
        self.run=engineering.admit(self.service,20,{'native_id':379,'lock_version':0,'unit':engineering.UNIT},'fixture')['id']
        self.worker=str(uuid.uuid4())

    def claim(self):
        return operation(self.service,'claim',{'worker_id':self.worker})

    def args(self,claim):
        return {'run_id':self.run,'worker_id':self.worker,'claim_token':claim['claim_token']}

    def expire(self):
        with self.store.connect() as db:db.execute('UPDATE ai_queue SET lease_until=0 WHERE id=?',(self.run,))

    def test_claim_identity_is_durable_and_missing_or_wrong_token_is_rejected(self):
        claim=self.claim()
        self.assertEqual(claim['worker_id'],self.worker)
        self.assertGreater(claim['claim_generation'],0)
        for token in (None,str(uuid.uuid4())):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError,'CLAIM_LOST'):
                operation(self.service,'finish',{**self.args(claim),'claim_token':token,'result':{'status':'blocked'}})
        self.assertTrue(operation(self.service,'guard',self.args(claim))['claim_valid'])

    def test_expired_worker_cannot_finish_checkpoint_or_publish_and_new_claim_has_new_generation(self):
        claim=self.claim();self.expire()
        for op,extra in [('finish',{'result':{'status':'succeeded'}}),('checkpoint',{'document':{}}),('publish_native',{'result':{}})]:
            with self.subTest(op=op),self.assertRaisesRegex(ValueError,'CLAIM_LOST'):
                operation(self.service,op,{**self.args(claim),**extra})
        self.assertIsNone(engineering.claim(self.service,20,worker_id=str(uuid.uuid4())))
        from gateway.engineering_planning import PLANNING
        new=engineering.admit(self.service,20,{'native_id':379,'lock_version':0,'unit':PLANNING,'feedback':'Different fixture requirement'},'next')
        b=engineering.claim(self.service,20,worker_id=str(uuid.uuid4()))
        self.assertEqual(b['id'],new['id']);self.assertGreater(b['claim_generation'],claim['claim_generation'])
        self.assertFalse(operation(self.service,'signal',self.args(claim))['claim_valid'])
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM ai_runs WHERE id=?',(self.run,)).fetchone()[0],'failed_or_unknown')

    def test_concurrent_claims_have_one_winner(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims=list(pool.map(lambda _:engineering.claim(self.service,20,worker_id=str(uuid.uuid4())),range(2)))
        self.assertEqual(sum(v is not None for v in claims),1)

    def test_post_outcome_unknown_preserves_pending_receipt_and_never_replays(self):
        claim=self.claim();fence=self.args(claim)
        calls=[]
        def post(*args):
            calls.append(args);self.expire();raise TimeoutError('synthetic')
        native=SimpleNamespace(call=post)
        with self.assertRaises(TimeoutError):
            native_once(self.service,native,self.run,'child','/api/v3/work_packages','POST',{'subject':'fixture'},fence=fence)
        with self.assertRaisesRegex(ValueError,'CLAIM_LOST'):
            native_once(self.service,native,self.run,'child','/api/v3/work_packages','POST',{'subject':'fixture'},fence=fence)
        self.assertEqual(len(calls),1)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM requests WHERE key=?',('engineering-'+self.run+'-child',)).fetchone()[0],'pending')

    def test_native_success_after_expiry_cannot_be_recorded_as_current_success(self):
        claim=self.claim()
        def post(*args):self.expire();return {'id':391}
        with self.assertRaisesRegex(ValueError,'CLAIM_LOST'):
            native_once(self.service,SimpleNamespace(call=post),self.run,'child','/api/v3/work_packages','POST',{},fence=self.args(claim))
        with self.store.connect() as db:
            self.assertNotEqual(db.execute('SELECT state FROM requests WHERE key=?',('engineering-'+self.run+'-child',)).fetchone()[0],'done')

    def test_stale_host_cannot_invoke_git_or_pr_subprocess(self):
        from automation import engineering_worker as worker
        with patch.object(worker,'CURRENT_CLAIM',{'id':self.run,'worker_id':self.worker,'claim_token':'expired'}), \
             patch.object(worker,'operator',side_effect=RuntimeError('ENGINEERING_CLAIM_LOST')), \
             patch.object(worker.subprocess,'run') as spawn:
            for argv in (['git','push','fixture'],[worker.GH,'pr','create']):
                with self.assertRaisesRegex(RuntimeError,'CLAIM_LOST'):worker.command(argv)
            spawn.assert_not_called()

    def test_current_finish_succeeds_but_same_claim_cannot_finish_twice(self):
        claim=self.claim()
        result=operation(self.service,'finish',{**self.args(claim),'result':{'status':'blocked'}})
        self.assertEqual(result['mode'],'OFF')
        with self.assertRaisesRegex(ValueError,'CLAIM_LOST'):
            operation(self.service,'finish',{**self.args(claim),'result':{'status':'blocked'}})

    def test_known_same_run_resume_changes_identity_and_rejects_previous_worker(self):
        from gateway import engineering_lifecycle as lifecycle
        claim=self.claim()
        saved=lifecycle.save(self.service,20,self.run,{'stage':'prepare','completed_steps':[],
            'terminal_known':True,'resumable':True,'revision':None,'session_id':None,'error':None})
        operation(self.service,'finish',{**self.args(claim),'result':{'status':'paused'}})
        lifecycle.resume(self.service,20,self.run,saved['version'])
        new=self.claim()
        self.assertNotEqual(new['claim_token'],claim['claim_token'])
        self.assertGreater(new['claim_generation'],claim['claim_generation'])
        with self.assertRaisesRegex(ValueError,'CLAIM_LOST'):
            operation(self.service,'finish',{**self.args(claim),'result':{'status':'blocked'}})
        self.assertTrue(operation(self.service,'guard',self.args(new))['claim_valid'])

    def test_host_guard_observes_pause_cancel_and_deadline_before_tool_start(self):
        claim=self.claim()
        engineering.control(self.service,20,'PAUSED')
        with self.assertRaisesRegex(ValueError,'PAUSED_CHECKPOINT'):
            operation(self.service,'guard',self.args(claim))
        with self.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='RUN_ONCE' WHERE project=6")
            db.execute("UPDATE ai_queue SET payload=json_set(payload,'$.deadline',0) WHERE id=?",(self.run,))
        with self.assertRaisesRegex(ValueError,'DEADLINE_EXCEEDED'):
            operation(self.service,'guard',self.args(claim))

    def test_revocation_during_transaction_rolls_back_checkpoint_write(self):
        from gateway.engineering_fencing import bound
        claim=self.claim()
        with self.assertRaisesRegex(ValueError,'CLAIM_LOST'),bound(self.args(claim)),self.store.connect() as db:
            db.execute("UPDATE ai_queue SET payload=json_set(payload,'$.claim_token','revoked') WHERE id=?",(self.run,))
            db.execute("UPDATE ai_runs SET result='late success' WHERE id=?",(self.run,))
        with self.store.connect() as db:
            self.assertNotEqual(db.execute('SELECT result FROM ai_runs WHERE id=?',(self.run,)).fetchone()[0],'late success')

    def test_second_host_process_cannot_own_shared_openclaw_runtime(self):
        from automation.engineering_worker import worker_lock
        path=Path(self.tmp.name)/'worker.lock'
        code='from pathlib import Path;from automation.engineering_worker import worker_lock\nwith worker_lock(Path('+repr(str(path))+')):print("acquired")'
        with worker_lock(path):
            other=subprocess.run([sys.executable,'-c',code],capture_output=True,timeout=15)
            self.assertNotEqual(other.returncode,0)
            self.assertIn(b'ENGINEERING_HOST_WORKER_ALREADY_RUNNING',other.stderr)
        after=subprocess.run([sys.executable,'-c',code],capture_output=True,timeout=15)
        self.assertEqual(after.returncode,0,after.stderr.decode())

    def test_delivery_always_drains_runtime_before_releasing_claim_identity(self):
        from automation import engineering_worker as worker
        with patch('automation.engineering_delivery.run',side_effect=RuntimeError('fixture crash')), \
             patch.object(worker,'fence_runtime') as fence:
            with self.assertRaisesRegex(RuntimeError,'fixture crash'):
                worker.execute({'id':self.run})
            fence.assert_called_once()
            self.assertIsNone(worker.CURRENT_CLAIM)

    def test_transport_cleanup_error_still_attempts_runtime_stop(self):
        from automation import engineering_worker as worker
        with patch.object(worker,'gate',side_effect=RuntimeError('fixture transport unavailable')), \
             patch.object(worker,'wsl',return_value=Mock(returncode=0)) as stop:
            with self.assertRaises(SystemExit):worker.fence_runtime()
            stop.assert_called_once()

    def test_expiry_during_embedding_cannot_publish_or_prune_vectors(self):
        from gateway.engineering_fencing import bound
        from gateway.knowledge_classifier import classify_document,KnowledgeDocType
        from gateway.knowledge_ingestion import KnowledgeIngester
        from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
        from test_rag_recovery import VectorFixture
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(Path(self.tmp.name)/'knowledge.sqlite')))
        storage.migrate_schema();vector=VectorFixture();calls=[]
        def embed(texts):
            with bound(None):self.expire()
            return [[0.1]*1024 for _ in texts]
        vector.embed_texts=embed
        vector.upsert_points=lambda points:calls.append('upsert') or True
        vector.delete_registered_points=lambda *args:calls.append('prune')
        doc=classify_document(doc_type=KnowledgeDocType.WORK_PACKAGE,project_id='6',source_id='fixture',
            title='Fixture',content='Authorized fixture text',metadata={'native_id':379,'lock_version':1},allowed_roles=['PM'])
        claim=self.claim()
        with bound(self.args(claim),self.store):
            result=KnowledgeIngester(storage,vector).ingest(doc)
        self.assertFalse(result.vector_indexed)
        self.assertEqual(calls,[])

    def test_knowledge_sqlite_commit_rolls_back_if_claim_expires_during_write(self):
        from gateway.engineering_fencing import bound
        from gateway.knowledge_classifier import classify_document,KnowledgeDocType
        from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(Path(self.tmp.name)/'knowledge.sqlite')))
        storage.migrate_schema()
        doc=classify_document(doc_type=KnowledgeDocType.WORK_PACKAGE,project_id='6',source_id='fixture',
            title='Fixture',content='Authorized text',metadata={'native_id':379,'lock_version':1},allowed_roles=['PM'])
        claim=self.claim()
        def tokenize(text):
            with bound(None):self.expire()
            return ['fixture']
        with bound(self.args(claim),self.store),patch('gateway.knowledge_search._tokenize',side_effect=tokenize):
            self.assertFalse(storage.store_document(doc))
        with storage._connection() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_documents').fetchone()[0],0)

    def test_real_vector_transport_does_not_put_after_collection_read_expires_claim(self):
        import httpx
        from gateway.engineering_fencing import bound
        from gateway.vector_client import VectorClient
        calls=[]
        def respond(request):
            calls.append(request.method)
            if request.method=='GET':
                with bound(None):self.expire()
                return httpx.Response(200,json={'result':{'config':{'params':{'vectors':{'size':1024,'distance':'Cosine'}}}}})
            raise AssertionError('late vector write')
        vector=VectorClient(enabled=True)
        vector._http.close();vector._http=httpx.Client(transport=httpx.MockTransport(respond));self.addCleanup(vector.close)
        claim=self.claim()
        with bound(self.args(claim),self.store):self.assertFalse(vector.upsert_points([{'id':'fixture'}]))
        self.assertEqual(calls,['GET'])


if __name__=='__main__':unittest.main()

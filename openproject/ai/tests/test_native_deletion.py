import copy
import hashlib
import hmac
import json
import unittest
import uuid
import httpx
from unittest.mock import patch

from gateway.native import NativeError
from gateway.store import canonical, digest
from tests import test_native_dependency as fixtures


class NativeDeletionTests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.NativeDependencyTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.service,self.store,self.native,self.tokens=fixture.service,fixture.store,fixture.native,fixture.tokens
        self.posts=[];self.receipts={};self.sha='a'*64;original=self.native.call
        def call(native,path,method='GET',payload=None):
            if path=='/api/v3/qldapm/native_deletion_forms':
                if payload['id'] not in self.native.rows:raise NativeError(404,'OPENPROJECT_404')
                return {'id':38,'lock_version':0,'project_id':5,'snapshot_sha256':self.sha,'permanent_delete':True,'cascade':False,'subject':'Isolated new Task'}
            if path=='/api/v3/qldapm/native_deletions':
                self.posts.append(copy.deepcopy(payload));del self.native.rows[payload['id']]
                document={'schema':'QLDAPM_NATIVE_DELETE_V1','producer':'qldapm-native-delete-v1','event_id':str(uuid.uuid4()),
                    'project_id':5,'native_id':payload['id'],'source_version':payload['lock_version'],'snapshot_sha256':payload['snapshot_sha256'],
                    'actor_id':18 if native.role=='AI_SYSTEM_OWNER' else 19,'proposal_id':payload['proposal_id'],'proposal_hash':payload['proposal_hash'],
                    'request_id':payload['request_id'],'request_hash':digest(canonical(payload)),'deleted_at':'2026-10-26T10:00:00.000000Z'}
                encoded=canonical(document);key=(self.store.root/'ui.key').read_bytes()
                result={'document':encoded,'signature':hmac.new(key,b'qldapm.native-delete.v1\0'+encoded.encode(),hashlib.sha256).hexdigest()}
                self.receipts[payload['request_id']]=copy.deepcopy(result);return result
            if path.startswith('/api/v3/qldapm/native_deletions/'):
                return copy.deepcopy(self.receipts[path.rsplit('/',1)[-1]])
            return original(native,path,method,payload)
        self.native.call=call

    def proposal(self,actor=18,key='delete',extra=None):
        return self.service.execute(self.tokens[actor],{'action':'delete_work_package','arguments':{'id':38,'lock_version':0,**(extra or {})},'idempotency_key':key})['result']

    def test_exact_hash_approval_only_signed_commit_and_cache_outbox(self):
        proposal=self.proposal();self.assertEqual(self.posts,[])
        self.assertTrue(proposal['command']['preview']['permanent_delete'])
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve','0'*64)
        receipt=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(receipt['knowledge_sync']['native_id'],38);self.assertEqual(len(self.posts),1)
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])

    def test_old_role_limits_and_unsealed_flags(self):
        for actor in [20,21,22,23]:
            with self.subTest(actor=actor),self.assertRaises(PermissionError):self.proposal(actor,key='role-'+str(actor))
        for field in ['approved','actor_id','snapshot_sha256','admin','cascade','proposal_hash']:
            with self.subTest(field=field),self.assertRaises(ValueError):self.proposal(key='forged-'+field,extra={field:True})
        self.assertFalse(self.posts)

    def test_stale_source_rejected_before_native_delete(self):
        proposal=self.proposal();self.sha='b'*64
        with self.assertRaisesRegex(NativeError,'STALE'):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertFalse(self.posts)

    def test_lost_response_recovers_one_delete_via_own_signed_ledger(self):
        proposal=self.proposal()
        from gateway import native_deletion
        with patch.object(native_deletion,'readback',side_effect=NativeError(409,'FIXTURE_REPLY_LOSS')):
            with self.assertRaises(NativeError):self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        receipt=self.service.execute(self.tokens[18],{'action':'reconcile_request','arguments':{'key':'proposal-'+proposal['id']}})['result']
        self.assertTrue(receipt['reconciled']);self.assertEqual(len(self.posts),1)
        self.assertEqual(self.store.proposal(18,proposal['id'])['state'],'done')
        self.assertEqual(receipt['knowledge_sync']['native_id'],38)

    def test_missing_or_forged_proof_never_authorizes_cache_deletion(self):
        proposal=self.proposal();args=proposal['command']['arguments']
        from gateway import native_deletion
        with self.assertRaises((ValueError,NativeError)):native_deletion.readback(self.service,self.native('url','AI_SYSTEM_OWNER',5),{},18,proposal)
        receipt=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])['result']
        forged={**receipt,'signature':'0'*64}
        with self.assertRaises(ValueError):native_deletion.verify(self.service,forged,18,proposal)
        encoded=json.loads(receipt['document']);encoded['native_id']=39;forged={'document':canonical(encoded),'signature':receipt['signature']}
        with self.assertRaises(ValueError):native_deletion.verify(self.service,forged,18,proposal)

    def test_pending_unknown_source_write_holds_delete(self):
        self.store.begin(19,'unknown-write',{'action':'comment','arguments':{'id':38}})
        with self.assertRaisesRegex(NativeError,'PENDING_SOURCE_WRITE_HOLD'):self.proposal()
        self.assertFalse(self.posts)

    def test_failed_cache_only_requests_do_not_hold_native_delete_or_get_replayed(self):
        for action in ['knowledge_ingest','knowledge_deindex']:
            self.store.begin(19,'old-'+action,{'action':action,'arguments':{'id':38}})
        with self.store.connect() as db:
            before=[dict(r) for r in db.execute("select * from requests where state!='done' order by actor,key")]
        proposal=self.proposal()
        self.assertEqual(proposal['state'],'pending');self.assertFalse(self.posts)
        with self.store.connect() as db:
            after=[dict(r) for r in db.execute("select * from requests where state!='done' order by actor,key")]
        self.assertEqual(after,before)

    def test_model_context_cannot_request_destructive_proposal(self):
        with patch('gateway.service.current_run',return_value=('isolated-model-context',object())):
            with self.assertRaisesRegex(PermissionError,'DIRECT_HUMAN_REQUEST_REQUIRED'):self.proposal()
        self.assertFalse(self.posts)

    def indexed(self):
        import httpx
        from gateway.knowledge_classifier import classify_document,KnowledgeDocType
        from gateway.knowledge_ingestion import KnowledgeIngester
        from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
        from gateway.vector_client import VectorClient
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.store.root/'knowledge.sqlite')))
        client=VectorClient(enabled=False);client._http.close();client.enabled=True;points={};self.vector_deletes=[];self.vector_reply_loss=False
        def transport(request):
            if request.method=='GET':return httpx.Response(200,json={'result':{'config':{'params':{'vectors':{'size':1024,'distance':'Cosine'}}}}})
            body=json.loads(request.content)
            if request.method=='POST' and request.url.path.endswith('/points'):
                return httpx.Response(200,json={'result':[{'id':identifier,'payload':points[identifier]} for identifier in body['ids'] if identifier in points]})
            if request.url.path.endswith('/points/delete'):
                self.assertEqual(set(body),{'points'});self.vector_deletes.append(body['points'])
                for identifier in body['points']:points.pop(identifier,None)
                if self.vector_reply_loss:self.vector_reply_loss=False;raise httpx.ReadTimeout('fixture loss after delete commit')
                return httpx.Response(200,json={'result':{'status':'completed'}})
            if request.method=='PUT':
                points.update({p['id']:p['payload'] for p in body['points']});return httpx.Response(200,json={'result':{'status':'completed'}})
            if request.url.path.endswith('/delete') and 'filter' in body:
                return httpx.Response(200,json={'status':'ok'})
            raise AssertionError(request.url)
        client._http=httpx.Client(transport=httpx.MockTransport(transport));self.addCleanup(client.close)
        documents=[]
        for source,project,identifier in [('op:wp:38','5',38),('actor:18:wp:38','5',38),('op:wp:39','5',39),('op:wp:38','6',38)]:
            metadata={'native_id':identifier,'lock_version':0}
            if source.startswith('actor:'):metadata['actor_id']=18
            doc=classify_document(KnowledgeDocType.WORK_PACKAGE,project,source,'Owned document','Native test content',allowed_roles=['PM'],metadata=metadata)
            with patch.object(client,'embed_texts',return_value=[[0.1]*1024]),patch.object(client,'delete_stale_points',return_value=True):
                result=KnowledgeIngester(storage,client).ingest(doc);self.assertTrue(result.vector_indexed)
            documents.append(doc)
        points['legacy-unregistered']={'source_id':'op:wp:38','project_id':'5','document_id':'never-registered'}
        return storage,client,points,documents

    def deleted_job(self):
        proposal=self.proposal();self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        return self.store.claim_knowledge_sync()

    def test_cache_delete_exact_registered_points_sqlite_fts_and_unrelated_preservation(self):
        from gateway.native_deletion import synchronize
        storage,client,points,docs=self.indexed();job=self.deleted_job()
        result=synchronize(self.service,job,client);self.assertTrue(result['vector_indexed'])
        self.assertEqual(result['documents_removed'],2);self.assertEqual(result['points_removed'],2)
        self.assertIn('legacy-unregistered',points);self.assertEqual(len(points),3)
        self.assertEqual({d.source_hash for d in storage.query_documents('5')},{docs[2].source_hash})
        self.assertEqual({d.source_hash for d in storage.query_documents('6')},{docs[3].source_hash})
        with storage._connection() as db:
            self.assertEqual(db.execute('select count(*) from knowledge_fts').fetchone()[0],2)
            self.assertEqual(db.execute('select count(*) from knowledge_chunks').fetchone()[0],2)
        again=synchronize(self.service,job,client);self.assertTrue(again['vector_indexed'])
        self.assertEqual(len(self.posts),1)

    def test_vector_reply_loss_and_sqlite_failure_recover_cache_only(self):
        from gateway.native_deletion import synchronize
        from gateway.knowledge_storage import KnowledgeStorage
        from gateway.service import Service
        from gateway.store import Store
        storage,client,points,docs=self.indexed();job=self.deleted_job();self.vector_reply_loss=True
        with self.assertRaises(httpx.ReadTimeout):synchronize(self.service,job,client)
        self.assertEqual(len(storage.query_documents('5')),3)
        restarted=Service(Store(self.store.root),self.service.config,self.store.root/'workspace',self.native)
        with patch.object(KnowledgeStorage,'delete_document',side_effect=ValueError('fixture SQLite fault')):
            with self.assertRaises(ValueError):synchronize(restarted,job,client)
        self.assertEqual(len(storage.query_documents('5')),3)
        self.assertTrue(synchronize(restarted,job,client)['vector_indexed']);self.assertEqual(len(self.posts),1)
        self.assertIn('legacy-unregistered',points)

    def test_payload_drift_and_newer_cache_revision_hold_before_vector_delete(self):
        from gateway.native_deletion import synchronize
        storage,client,points,docs=self.indexed();job=self.deleted_job()
        target=client.deterministic_uuid(docs[0].source_hash+':0');prior=points[target];points[target]={**prior,'project_id':'6'}
        with self.assertRaisesRegex(ValueError,'PAYLOAD_MISMATCH'):synchronize(self.service,job,client)
        self.assertFalse(self.vector_deletes);points[target]=prior
        with storage._connection() as db:
            metadata={**docs[0].metadata,'lock_version':1}
            db.execute('update knowledge_documents set metadata=? where source_hash=?',(json.dumps(metadata),docs[0].source_hash))
            db.commit()
        with self.assertRaisesRegex(ValueError,'SOURCE_SCOPE_HOLD'):synchronize(self.service,job,client)
        self.assertFalse(self.vector_deletes)

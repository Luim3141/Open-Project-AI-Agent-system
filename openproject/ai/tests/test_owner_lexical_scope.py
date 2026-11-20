"""SQLite FTS parity with server-scoped Owner dense search, including Native version0."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.knowledge_classifier import classify_document,KnowledgeDocType
from gateway.knowledge_ingestion import KnowledgeIngester
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.service import Service
from gateway.store import Store
from tests.test_rag_recovery import VectorFixture


class OwnerLexicalScopeTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.root/'knowledge.sqlite')))
        self.vector=VectorFixture();self.roles=['PM','BA','BE','FE','QA'];self.docs={}
        for native_id,project in [(371,'5'),(372,'5'),(999,'9')]:
            doc=classify_document(KnowledgeDocType.WORK_PACKAGE,project,f'op:wp:{native_id}',f'OwnerFTSmarker {native_id}',
                'OwnerFTSmarker requirement evidence',allowed_roles=self.roles,metadata={'native_id':native_id,'lock_version':0})
            self.docs[native_id]=doc;KnowledgeIngester(self.storage,self.vector).ingest(doc)

    def test_owner_fts_uses_only_explicit_server_document_scope_with_business_role_payloads(self):
        engine=KnowledgeSearchEngine(self.storage)
        hits=engine.search('OwnerFTSmarker','5','AI_SYSTEM_OWNER',document_ids=[self.docs[371].source_hash],actor_id=18)
        self.assertEqual([(h.native_id,h.lock_version) for h in hits],[(371,0)])
        self.assertEqual(hits[0].match_type,'FTS_BM25')
        self.assertEqual(engine.search('OwnerFTSmarker','5','AI_SYSTEM_OWNER',document_ids=[self.docs[999].source_hash],actor_id=18),[])

    def test_unscoped_owner_search_fails_closed_and_empty_scope_has_no_hits(self):
        engine=KnowledgeSearchEngine(self.storage)
        for args in [{},{'actor_id':18}]:
            with self.assertRaisesRegex(PermissionError,'OWNER_RAG_DOCUMENT_SCOPE_REQUIRED'):
                engine.search('OwnerFTSmarker','5','AI_SYSTEM_OWNER',**args)
        self.assertEqual(engine.search('OwnerFTSmarker','5','AI_SYSTEM_OWNER',actor_id=18,document_ids=[]),[])

    def test_gateway_six_role_native_zero_version_citations_and_foreign_project_denial(self):
        roles={18:'AI_SYSTEM_OWNER',19:'PM',20:'BA',21:'BE',22:'FE',23:'QA'};store=Store(self.root)
        tokens={a:store.issue_token(a,role,role) for a,role in roles.items()}
        class Native:
            def __init__(self,url,credential,project):self.role=credential
            def identity(self,actor):return {'user_id':actor,'role':self.role,'capabilities':[self.role]}
            def packages(self):return [{'id':371,'lockVersion':0},{'id':372,'lockVersion':0}]
            def package(self,identifier):return {'id':identifier,'lockVersion':0}
        service=Service(store,{'project_id':5,'gateway_mode':'native','openproject_url':'http://127.0.0.1:8088',
                         'users':{str(a):role for a,role in roles.items()}},self.root/'workspace',Native)
        with patch('gateway.vector_client.VectorClient',return_value=self.vector):
            for actor in tokens:
                r=service.execute(tokens[actor],{'action':'knowledge_search','arguments':{'query':'OwnerFTSmarker','native_ids':[371,372]}})['result']
                self.assertEqual({h['native_id'] for h in r['items']},{371,372},actor)
                self.assertTrue(all(h['lock_version']==0 and h['source_id'].startswith('op:wp:') for h in r['items']))
            r=service.execute(tokens[18],{'action':'knowledge_search','arguments':{'query':'OwnerFTSmarker','native_ids':[999]}})['result']
            self.assertEqual(r['items'],[])


if __name__=='__main__':unittest.main()

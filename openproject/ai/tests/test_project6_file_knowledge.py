"""Project6 file access must retain Native identity, source policy and citations."""
import unittest

from gateway.native import NativeError
from gateway.service import Service
from tests import test_allowlisted_file_knowledge as existing


class Project6FileKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture=existing.AllowlistedFileKnowledgeTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.service=self.fixture.service;self.source=self.fixture.source.copy();self.source.update(project_id=6,allowed_roles=['PM','BA'])
        self.service.config['file_sources']['engineering-doc']=self.source
        self.service.config['engineering']={'enabled':True,'actors':{'18':'AI_SYSTEM_OWNER','20':'PM','21':'BA','23':'QA'}}
        self.roles={18:'AI_SYSTEM_OWNER',20:'PM',21:'BA',22:'BE',23:'QA'};self.revoked=set()
        self.tokens={actor:self.fixture.store.issue_token(actor,role,str(actor)) for actor,role in self.roles.items()}
        roles=self.roles;revoked=self.revoked
        class Native:
            def __init__(self,url,credential,project):self.actor=int(credential);self.project=project
            def identity(self,expected):
                if self.actor!=expected or expected in revoked:raise PermissionError('NATIVE_MEMBERSHIP_REVOKED')
                return {'user_id':expected,'role':roles[expected],'capabilities':['AI_SYSTEM_OWNER'] if expected==18 else []}
        self.service.native_factory=Native

    def call(self,actor,action,args,key=None,project=6):
        return self.service.execute(self.tokens[actor],{'action':action,'arguments':args,'idempotency_key':key,'project_id':project})['result']

    def test_project6_ingest_search_read_and_owner_with_exact_citation(self):
        result=self.call(20,'knowledge_file_ingest',{'source_key':'engineering-doc'},'p6-manager')
        self.assertTrue(result['vector_indexed'])
        self.assertEqual(self.call(18,'knowledge_file_ingest',{'source_key':'engineering-doc'},'p6-owner')['document_id'],result['document_id'])
        found=self.call(21,'knowledge_file_search',{'source_key':'engineering-doc','query':'workflow citation'})
        self.assertEqual(found['items'][0]['document_id'],result['document_id'])
        read=self.call(21,'knowledge_file_read',{'source_key':'engineering-doc','document_id':result['document_id']})
        self.assertEqual(read['citation'],'file:engineering-doc#sha256='+self.source['sha256'])
        self.assertIn('verified provenance',read['content'])

    def test_role_identity_cross_project_path_and_stale_source_fail_closed(self):
        for actor in (21,22,23):
            with self.subTest(actor=actor),self.assertRaises(PermissionError):self.call(actor,'knowledge_file_ingest',{'source_key':'engineering-doc'},'denied-'+str(actor))
        for actor in (22,23):
            with self.subTest(actor=actor),self.assertRaises(PermissionError):self.call(actor,'knowledge_file_search',{'source_key':'engineering-doc','query':'workflow'})
        with self.assertRaises(PermissionError):self.call(20,'knowledge_file_search',{'source_key':'workflow-contract','query':'workflow'})
        with self.assertRaises(PermissionError):self.call(20,'knowledge_file_search',{'source_key':'engineering-doc','query':'workflow'},project=7)
        with self.assertRaises(ValueError):self.call(20,'knowledge_file_ingest',{'source_key':'engineering-doc','path':'outside'},'path-denied')
        self.call(20,'knowledge_file_ingest',{'source_key':'engineering-doc'},'before-change')
        self.revoked.add(21)
        with self.assertRaises(PermissionError):self.call(21,'knowledge_file_search',{'source_key':'engineering-doc','query':'workflow'})
        self.revoked.clear();self.fixture.path.write_bytes(b'changed source')
        with self.assertRaisesRegex(NativeError,'FILE_SOURCE_CHECKSUM_CHANGED'):self.call(21,'knowledge_file_search',{'source_key':'engineering-doc','query':'workflow'})

    def test_project6_member_be_cannot_access_file_without_allowed_role(self):
        config={**self.service.config,'project_id':6,'users':{'22':'BE'},'_engineering_scope':True}
        scoped=Service(self.fixture.store,config,self.fixture.root/'workspace-be',self.service.native_factory)
        native,identity=scoped.native_actor(22)
        self.assertEqual((native.project,identity['role']),(6,'BE'))
        with self.assertRaisesRegex(PermissionError,'FILE_SOURCE_ROLE_DENIED'):
            scoped.execute_actor(22,{'action':'knowledge_file_search','arguments':{'source_key':'engineering-doc','query':'workflow'}})
        with self.assertRaises(PermissionError):
            scoped.execute_actor(22,{'action':'knowledge_file_ingest','arguments':{'source_key':'engineering-doc'},'idempotency_key':'be-denied'})


if __name__=='__main__':unittest.main()

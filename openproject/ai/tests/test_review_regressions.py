"""Regression cases found while reviewing Gemini's runtime candidates."""
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from gateway.agent_models import AgentTask, RunScope
from gateway.supervisor import Supervisor
from gateway.knowledge_classifier import KnowledgeDocType, classify_document
from gateway.knowledge_ingestion import KnowledgeIngester, IngestionStatus, chunk_text
from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig


def task_scope():
    now=time.time()
    task=AgentTask(task_id=str(uuid.uuid4()),actor_id=7,project_id=3,conversation_id=str(uuid.uuid4()),
        agent='supervisor',instruction='Phân tích rủi ro sprint',created_at=now,expires_at=now+600)
    scope=RunScope(run_id=str(uuid.uuid4()),task_id=task.task_id,actor_id=7,project_id=3,trace_id=str(uuid.uuid4()))
    return task,scope


class ReviewRegressions(unittest.TestCase):
    def test_supervisor_never_claims_a_provider_call_for_local_handlers(self):
        task,scope=task_scope()
        _,result=Supervisor().execute_task(task,scope,[])
        self.assertFalse(result.model_used)

    def test_supervisor_rejects_cross_actor_scope(self):
        task,scope=task_scope()
        scope=scope.model_copy(update={'actor_id':8})
        with self.assertRaises(PermissionError):Supervisor().execute_task(task,scope,[])

    def test_real_project_size_remains_bounded_and_disclosed(self):
        task,scope=task_scope()
        packages=[{'id':i,'lockVersion':1,'subject':'Fixture '+str(i),'dueDate':None,'_links':{'status':{'title':'NEW'}}} for i in range(1,336)]
        _,result=Supervisor().execute_task(task,scope,packages)
        self.assertLessEqual(len(result.references),50)
        self.assertIn('335',result.summary)
        self.assertIn('10',result.summary)

    def test_same_content_in_different_projects_has_different_identity(self):
        args=dict(doc_type=KnowledgeDocType.ADR,source_id='adr:1',title='Title',content='Shared text')
        a=classify_document(project_id='3',**args)
        b=classify_document(project_id='DEMO',**args)
        self.assertNotEqual(a.source_hash,b.source_hash)

    def test_invalid_chunk_parameters_are_denied(self):
        with self.assertRaises(ValueError):chunk_text('hello',0,0)

    def test_failed_persistence_is_not_reported_created(self):
        storage=KnowledgeStorage(KnowledgeStorageConfig(is_mock=True))
        doc=classify_document(KnowledgeDocType.ADR,'3','adr:1','Title','Text')
        with patch.object(storage,'store_document',return_value=False):
            self.assertEqual(KnowledgeIngester(storage).ingest(doc).status,IngestionStatus.FAILED)

    def test_reopened_index_sees_other_writer_and_source_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg=KnowledgeStorageConfig(db_path=str(Path(tmp)/'knowledge.sqlite'),enable_pgvector=False)
            a=KnowledgeStorage(cfg);b=KnowledgeStorage(cfg)
            first=classify_document(KnowledgeDocType.ADR,'3','adr:1','First','Old text '*100)
            self.assertEqual(KnowledgeIngester(a).ingest(first).status,IngestionStatus.CREATED)
            self.assertEqual(b.count_documents(),1)
            self.assertGreater(KnowledgeIngester(b).count_chunks(first.source_hash),0)
            latest=classify_document(KnowledgeDocType.ADR,'3','adr:1','Latest','New text')
            self.assertEqual(KnowledgeIngester(b).ingest(latest).status,IngestionStatus.UPDATED)
            docs=KnowledgeStorage(cfg).query_documents('3','PM')
            self.assertEqual([d.source_hash for d in docs],[latest.source_hash])

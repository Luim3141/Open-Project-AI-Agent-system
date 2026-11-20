import copy
import json
from sqlite3 import connect as sqlite_connection
from contextlib import closing
from pathlib import Path
import tempfile
from types import SimpleNamespace as N
import unittest
import uuid
from unittest.mock import patch,Mock

from gateway import workflow_commands as commands
from gateway.store import Store,canonical,digest


class WorkflowCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name))
        self.service=N(store=self.store,config={'project_id':6})

    def record(self,actor=20):
        identifier=str(uuid.uuid4());command=N(action='sprint_risks',arguments={})
        result={'report_id':str(uuid.uuid4()),'report_sha256':'a'*64}
        with patch('gateway.integration_events.enqueue',return_value='event') as enqueue:
            response=commands.record(self.service,actor,command,result,identifier)
        self.assertEqual(response['state'],'COMMAND_ACCEPTED')
        return identifier,result,enqueue

    def event(self,identifier):
        with self.store.connect() as db:row=db.execute('select hash from workflow_command_sources where id=?',(identifier,)).fetchone()
        return {'source_id':'ui-command:'+identifier,'source_version':row['hash'],'kind':'UI_RISK_COMPLETED',
                'payload':{'command_id':identifier,'action':'sprint_risks'}}

    def test_real_result_is_persisted_before_observation_and_callback_never_repeats_command(self):
        identifier,result,enqueue=self.record();enqueue.assert_called_once()
        self.service.perform=Mock(return_value={'state':'SNAPSHOT','source_versions_current':True,'sha256':result['report_sha256']})
        native=Mock()
        with patch('gateway.engineering.scoped_service',return_value=self.service),patch('gateway.engineering.authorized',return_value=(native,{'user_id':20})):
            receipt=commands.business(self.service,self.event(identifier))
        self.assertEqual(receipt['state'],'COMMAND_RESULT_VERIFIED');native.call.assert_not_called()
        self.service.perform.assert_called_once_with({'user_id':20},native,'get_report',{'id':result['report_id']})

    def test_report_changed_or_revoked_source_cannot_be_verified_from_old_report_hash(self):
        identifier,_,_=self.record()
        for response in ({'state':'SOURCE_PERMISSION_CHANGED','data_hidden':True},{'state':'SNAPSHOT','source_versions_current':False}):
            self.service.perform=Mock(return_value=response)
            with patch('gateway.engineering.scoped_service',return_value=self.service),patch('gateway.engineering.authorized',return_value=(Mock(),{'user_id':20})):
                self.assertEqual(commands.business(self.service,self.event(identifier))['state'],'SUPERSEDED')

    def test_changed_payload_kind_or_persisted_hash_cannot_claim_verified_result(self):
        identifier,_,_=self.record();base=self.event(identifier)
        for event in ({**base,'kind':'UI_BUG_TRIAGED'},{**base,'source_version':'f'*64},
                      {**base,'payload':{**base['payload'],'action':'delete_work_package'}}):
            with patch('gateway.engineering.scoped_service',return_value=self.service),self.assertRaises(PermissionError):
                commands.business(self.service,event)

    def test_project5_and_unknown_commands_create_no_observation_or_owner_authority(self):
        with patch('gateway.integration_events.enqueue') as enqueue:
            self.service.config['project_id']=5
            self.assertIsNone(commands.record(self.service,18,N(action='sprint_risks',arguments={}),{},str(uuid.uuid4())))
            self.service.config['project_id']=6
            self.assertIsNone(commands.record(self.service,18,N(action='transition',arguments={}),{},str(uuid.uuid4())))
            with self.assertRaises(PermissionError):commands.record(self.service,21,N(action='sprint_risks',arguments={}),{},str(uuid.uuid4()))
            enqueue.assert_not_called()

    def test_crash_between_source_and_outbox_is_recovered_idempotently_by_existing_publisher(self):
        from gateway.integration_events import setup
        identifier=str(uuid.uuid4())
        with self.store.connect() as db:setup(db)
        with patch('gateway.integration_events.enqueue',side_effect=RuntimeError('process-stopped-after-source')):
            with self.assertRaises(RuntimeError):
                commands.record(self.service,20,N(action='sprint_risks',arguments={}),{'report_id':'source'},identifier)
        for _ in range(2):commands.publish(self.store)
        with self.store.connect() as db:
            rows=db.execute('select document from integration_event_outbox').fetchall()
        self.assertEqual(len(rows),1)
        self.assertEqual(json.loads(rows[0]['document'])['correlation_id'],identifier)

    def test_file_callback_requires_complete_actual_sqlite_fts_and_vector_readback(self):
        from gateway.knowledge_classifier import classify_document,KnowledgeDocType
        from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
        from gateway.vector_client import VectorClient
        source=classify_document(KnowledgeDocType.ARCHITECTURE,'6','file:sample','Test title',
            '# Tiếng Việt\nReceipt: YES.\n'+('Second Paragraph! '*70),allowed_roles=['PM'],metadata={'source_key':'sample'})
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.store.root/'knowledge.sqlite')))
        self.assertTrue(storage.store_document(source))
        identifier=str(uuid.uuid4());result={'document_id':source.source_hash,'vector_indexed':True}
        with patch('gateway.integration_events.enqueue'):
            commands.record(self.service,20,N(action='knowledge_file_ingest',arguments={'source_key':'sample'}),result,identifier)
        event=self.event(identifier);event['kind']='UI_FILE_INDEXED';event['payload']['action']='knowledge_file_ingest'
        vector=Mock();vector.deterministic_uuid=lambda x:VectorClient.deterministic_uuid(None,x);vector.verify_points.return_value=True
        with patch('gateway.engineering.scoped_service',return_value=self.service),patch('gateway.engineering.authorized',return_value=(Mock(),{'user_id':20})),patch('gateway.file_knowledge.load_source',return_value=source),patch('gateway.vector_client.VectorClient',return_value=vector):
            self.assertEqual(commands.business(self.service,event)['state'],'COMMAND_RESULT_VERIFIED')
            self.assertGreater(len(vector.verify_points.call_args.args[0]),1)
            vector.verify_points.return_value=False
            with self.assertRaisesRegex(ValueError,'FILE_INDEX_READBACK'):commands.business(self.service,event)
            vector.verify_points.return_value=True
            with closing(sqlite_connection(self.store.root/'knowledge.sqlite')) as db:
                db.execute('DELETE FROM knowledge_chunks WHERE chunk_index=1');db.commit()
            with self.assertRaisesRegex(ValueError,'FILE_INDEX_READBACK'):commands.business(self.service,event)

"""Durable feedback and controlled trusted-source reindex; no Main or Native mutations."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.service import Service
from gateway.store import Store
from tests import test_native_incremental_sync as incremental_fixture


class VerifiedKnowledgeFeedbackTests(unittest.TestCase):
    def setUp(self):
        fixture=incremental_fixture.NativeIncrementalSyncTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.fixture=fixture;self.service=fixture.service;self.store=fixture.store
        self.pm,self.ba=fixture.pm,fixture.ba
        self.other=self.store.issue_token(9,'BA','BA');self.service.config['users']['9']='BA'

    def call(self,token,action,args,key=None):
        return self.service.execute(token,{'action':action,'arguments':args,'idempotency_key':key})['result']

    def submit(self,key='feedback-1'):
        return self.call(self.ba,'knowledge_feedback_submit',{'native_id':12,
            'note':'UNTRUSTED_FEEDBACK_NOTE_MUST_NEVER_BECOME_KNOWLEDGE'},key)

    def test_independent_exact_review_reindexes_only_the_verified_native_source(self):
        feedback=self.submit()
        self.assertEqual(feedback['state'],'pending')
        accepted=self.service.decide_feedback(self.pm,feedback['id'],'accept',feedback['hash'])
        self.assertEqual(accepted['state'],'accepted')
        result=self.call(self.pm,'knowledge_feedback_apply',{'id':feedback['id']},'apply-feedback')
        self.assertEqual(result['state'],'applied')
        self.assertTrue(result['result']['vector_indexed'])
        from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
        docs=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.store.root/'knowledge.sqlite'))).query_documents('5')
        self.assertEqual(len(docs),1)
        self.assertEqual(docs[0].source_id,'op:wp:12')
        self.assertNotIn('UNTRUSTED_FEEDBACK_NOTE',docs[0].content)
        self.assertFalse(result['feedback_content_promoted'])

    def test_no_self_review_wrong_hash_replay_or_unapproved_application(self):
        feedback=self.submit()
        with self.assertRaises(PermissionError):
            self.service.decide_feedback(self.ba,feedback['id'],'accept',feedback['hash'])
        own=self.call(self.pm,'knowledge_feedback_submit',{'native_id':12,'note':'Own request'},'manager-own')
        with self.assertRaisesRegex(PermissionError,'FEEDBACK_SELF_REVIEW_DENIED'):
            self.service.decide_feedback(self.pm,own['id'],'accept',own['hash'])
        from gateway.native import NativeError
        with self.assertRaisesRegex(NativeError,'FEEDBACK_CHANGED_STALE_OR_ALREADY_DECIDED'):
            self.service.decide_feedback(self.pm,feedback['id'],'accept','0'*64)
        with self.assertRaisesRegex(NativeError,'ACCEPTED_CURRENT_FEEDBACK_REQUIRED'):
            self.call(self.pm,'knowledge_feedback_apply',{'id':feedback['id']},'not-approved')
        self.service.decide_feedback(self.pm,feedback['id'],'reject',feedback['hash'])
        with self.assertRaises(NativeError):
            self.service.decide_feedback(self.pm,feedback['id'],'accept',feedback['hash'])

    def test_source_revision_change_blocks_acceptance_and_accepted_reindex(self):
        feedback=self.submit()
        self.fixture.native.rows[0]['lockVersion']=2
        stale=self.call(self.ba,'knowledge_feedback_get',{'id':feedback['id']})
        self.assertFalse(stale['source_current'])
        from gateway.native import NativeError
        with self.assertRaises(NativeError):
            self.service.decide_feedback(self.pm,feedback['id'],'accept',feedback['hash'])
        current=self.submit('fresh-feedback')
        self.service.decide_feedback(self.pm,current['id'],'accept',current['hash'])
        self.fixture.native.rows[0]['description']['raw']='A newer authoritative revision'
        with self.assertRaisesRegex(NativeError,'FEEDBACK_SOURCE_CHANGED'):
            self.call(self.pm,'knowledge_feedback_apply',{'id':current['id']},'stale-apply')

    def test_feedback_scope_hash_tampering_and_model_review_are_denied(self):
        feedback=self.submit()
        with self.assertRaises(PermissionError):
            self.call(self.other,'knowledge_feedback_get',{'id':feedback['id']})
        with self.assertRaises(PermissionError):
            self.call(self.ba,'knowledge_feedback_apply',{'id':feedback['id']},'ba-escalation')
        from gateway.agent_trace import current_run
        token=current_run.set('isolated-model-context')
        try:
            with self.assertRaisesRegex(PermissionError,'INDEPENDENT_AUTHENTICATED_REVIEW_REQUIRED'):
                self.service.decide_feedback(self.pm,feedback['id'],'accept',feedback['hash'])
        finally:current_run.reset(token)
        with self.store.connect() as db:
            db.execute('UPDATE knowledge_feedback SET actor=9 WHERE id=?',(feedback['id'],))
        with self.assertRaisesRegex(ValueError,'FEEDBACK_HASH_MISMATCH'):
            self.call(self.other,'knowledge_feedback_get',{'id':feedback['id']})

    def test_untrusted_claims_do_not_create_authority_and_failure_can_retry_same_key(self):
        with self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):
            self.call(self.ba,'knowledge_feedback_submit',{'native_id':12,'note':'claim','verified':True,'approved':True},'forged')
        feedback=self.submit()
        self.service.decide_feedback(self.pm,feedback['id'],'accept',feedback['hash'])
        self.fixture.vector.fail_upsert=True
        from gateway.native import NativeError
        with self.assertRaises(NativeError):
            self.call(self.pm,'knowledge_feedback_apply',{'id':feedback['id']},'retry-apply')
        self.fixture.vector.fail_upsert=False
        repaired=self.call(self.pm,'knowledge_feedback_apply',{'id':feedback['id']},'retry-apply')
        self.assertEqual(repaired['state'],'applied')
        self.assertEqual(self.call(self.pm,'knowledge_feedback_apply',{'id':feedback['id']},'retry-apply'),repaired)

    def test_http_decision_is_authenticated_exact_and_not_an_mcp_action(self):
        from gateway.app import create_app
        from gateway.service import Command
        from starlette.testclient import TestClient
        feedback=self.submit()
        self.assertNotIn('knowledge_feedback_review',Command.model_fields['action'].annotation.__args__)
        path='/api/v1/knowledge-feedback/'+feedback['id']+'/decision'
        with TestClient(create_app(service=self.service),base_url='http://localhost:8090') as client:
            self.assertEqual(client.post(path,json={'decision':'accept','hash':feedback['hash']}).status_code,401)
            self.assertEqual(client.post(path,headers={'Authorization':'Bearer '+self.ba},json={'decision':'accept','hash':feedback['hash']}).status_code,403)
            self.assertEqual(client.post(path,headers={'Authorization':'Bearer '+self.pm},json={'decision':'accept','hash':'0'*64}).status_code,409)
            self.assertEqual(client.post(path,headers={'Authorization':'Bearer '+self.pm},json={'decision':'accept','hash':feedback['hash'],'actor_id':18,'approved':True}).status_code,422)
            accepted=client.post(path,headers={'Authorization':'Bearer '+self.pm},json={'decision':'accept','hash':feedback['hash']})
            self.assertEqual(accepted.status_code,200)
            self.assertEqual(accepted.json()['result']['state'],'accepted')
            self.assertEqual(client.post(path,headers={'Authorization':'Bearer '+self.pm},json={'decision':'accept','hash':feedback['hash']}).status_code,409)

    def test_lost_submit_receipt_recovers_same_feedback_record_without_duplicate(self):
        with patch.object(self.service.store,'finish',side_effect=RuntimeError('isolated lost metadata receipt')):
            with self.assertRaises(RuntimeError):self.submit('lost-receipt')
        recovered=self.submit('lost-receipt')
        self.assertEqual(recovered['state'],'pending')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_feedback').fetchone()[0],1)

    def test_owner_review_of_file_feedback_never_promotes_the_untrusted_note(self):
        from tests import test_allowlisted_file_knowledge as files
        fixture=files.AllowlistedFileKnowledgeTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        service=fixture.service
        feedback=service.execute(fixture.ba,{'action':'knowledge_feedback_submit','arguments':{
            'source_key':'workflow-contract','note':'UNVERIFIED_NEW_CLAIM_NEVER_INDEX'},'idempotency_key':'file-feedback'})['result']
        service.decide_feedback(fixture.owner,feedback['id'],'accept',feedback['hash'])
        applied=service.execute(fixture.owner,{'action':'knowledge_feedback_apply','arguments':{'id':feedback['id']},
            'idempotency_key':'apply-file-feedback'})['result']
        self.assertEqual(applied['reviewer'],18)
        self.assertTrue(applied['result']['vector_indexed'])
        read=service.execute(fixture.ba,{'action':'knowledge_file_read','arguments':{'source_key':'workflow-contract',
            'document_id':applied['result']['document_id']}})['result']
        self.assertNotIn('UNVERIFIED_NEW_CLAIM',read['content'])


if __name__=='__main__':unittest.main()

"""Full lifecycle at the Service seam, with an isolated Native adapter and vector index."""
import copy
import hashlib
import unittest
from unittest.mock import patch

from gateway.native import NativeError
from gateway.store import canonical
from tests.test_native_bug_lifecycle import NativeBugLifecycleTests,REPORT
from tests.test_rag_recovery import VectorFixture


class BugQaIntegrationTests(unittest.TestCase):
    def test_bug_fix_manual_retest_independent_review_exact_transition_and_cache(self):
        fixture=NativeBugLifecycleTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        service,store,native=fixture.service,fixture.store,fixture.native
        vector=VectorFixture();self.addCleanup(patch.stopall)
        patch('gateway.vector_client.VectorClient',return_value=vector).start()
        syncs=[]
        def approve(p):
            count=len(native.writes)
            with self.assertRaises(ValueError):service.decide_proposal(fixture.tokens[18],p['id'],'approve','0'*64)
            self.assertEqual(len(native.writes),count)
            result=service.decide_proposal(fixture.tokens[18],p['id'],'approve',p['hash'])
            self.assertEqual(len(native.writes),count+1)
            with self.assertRaises(ValueError):service.decide_proposal(fixture.tokens[18],p['id'],'approve',p['hash'])
            syncs.append(result['knowledge_sync']['id'])
            self.assertTrue(service.process_knowledge_sync())
            self.assertEqual(store.knowledge_sync(18,syncs[-1])['state'],'verified')
            return result
        report={**REPORT,'reproduction':REPORT['reproduction']+'\nAC1: Unauthorized requests receive401'}
        self.assertEqual(fixture.call('bug_triage',{'report':report},18)['duplicates'],[])
        proposal=fixture.call('bug_propose',{'operation':'create','source_id':'isolated-reviewed-bug','report':report},18,'create')
        identifier=approve(proposal)['result']['id']
        for op,extra in [('assign',{'assignee_id':21}),('fix',{'text':'Isolated fix reference; not a Main commit'})]:
            approve(fixture.call('bug_propose',{'operation':op,'id':identifier,'lock_version':native.rows[identifier]['lockVersion'],**extra},18,op))
        self.assertIn('NOT_VERIFIED_BY_SYSTEM',fixture.call('bug_triage',{'id':identifier},18)['submitted_evidence'][0]['comment']['raw'])
        # This fixture represents the separately authenticated QA Native comment/attachment producer.
        artifact=b'Isolated test log: expected HTTP401; observed HTTP401.'
        manifest={'schema':'QLDAPM_QA_EVIDENCE_V1','work_package_id':identifier,'source_version':native.rows[identifier]['lockVersion'],
            'criteria':{'AC1':'Unauthorized requests receive401'},'tests':[{'criterion_id':'AC1','reference':'TC-AUTH-1',
            'expected':'HTTP401','actual':'HTTP401','outcome':'PASSED'}],'attachment_id':99,
            'attachment_sha256':hashlib.sha256(artifact).hexdigest(),'related_run_id':None}
        native.activities[identifier].append({'id':4242,'createdAt':'2026-10-25T00:00:00Z','comment':{'raw':canonical(manifest)},
            '_links':{'user':{'href':'/api/v3/users/23'},'workPackage':{'href':f'/api/v3/work_packages/{identifier}'}}})
        original=native.call
        def call(instance,path,method='GET',payload=None,**kwargs):
            if path=='/api/v3/attachments/99':return {'id':99,'fileSize':len(artifact),'_links':{
                'container':{'href':f'/api/v3/work_packages/{identifier}'},'author':{'href':'/api/v3/users/23'}}}
            if path=='/api/v3/attachments/99/content' and kwargs.get('binary'):return artifact
            if path=='/api/v3/statuses/9':return {'id':9,'name':'REVIEW','isClosed':False}
            return original(instance,path,method,payload)
        native.call=call
        e=fixture.call('qa_evidence_capture',{'native_id':identifier,'activity_id':4242},23,'capture')
        self.assertFalse(e['ready'])
        with self.assertRaises(PermissionError):service.decide_qa_evidence(fixture.tokens[21],e['id'],'accept',e['hash'])
        service.decide_qa_evidence(fixture.tokens[18],e['id'],'accept',e['hash'])
        with self.assertRaises(NativeError):service.decide_qa_evidence(fixture.tokens[18],e['id'],'accept',e['hash'])
        with self.assertRaises(NativeError):fixture.call('bug_propose',{'operation':'transition','id':identifier,
            'lock_version':manifest['source_version'],'status_id':9},18,'missing-evidence')
        p=fixture.call('bug_propose',{'operation':'transition','id':identifier,'lock_version':manifest['source_version'],
            'status_id':9,'qa_evidence_id':e['id'],'qa_evidence_hash':e['hash']},18,'reviewed-transition')
        result=approve(p)
        self.assertEqual(result['result']['_links']['status']['href'],'/api/v3/statuses/9')
        self.assertEqual(native.rows[identifier]['_links']['assignee']['href'],'/api/v3/users/21')
        search=fixture.call('knowledge_search',{'query':'Unauthorized requests','native_ids':[identifier]},18)
        self.assertTrue(search['items']);self.assertEqual({i['lock_version'] for i in search['items']},{2})
        self.assertEqual(len(set(syncs)),4)
        self.assertFalse(fixture.call('qa_evidence_get',{'id':e['id']},23)['source_current'])


if __name__=='__main__':unittest.main()

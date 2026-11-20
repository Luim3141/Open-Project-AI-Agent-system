"""Fixed read-only Native assertions produce artifacts, never human QA decisions."""
import copy
import json
import unittest

import test_native_qa_evidence as fixture
from gateway.native import NativeError


class NativeQaRunTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.NativeQaEvidenceTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.service=self.f.service;self.store=self.f.store;self.native=self.f.native
        (self.f.root/'ui.key').write_bytes(b'isolated-native-qa-producer-key')
        self.native.row.update(startDate='2026-10-26',dueDate='2026-10-27')
        self.native.row['description']['raw']='AC1: native.startDate == "2026-10-26"\nAC2: native.dueDate == "2026-10-27"\nAC3: native.assignee_id == 21'

    def call(self,actor,action,args,key=None):return self.f.call(actor,action,args,key)

    def test_actual_native_readback_produces_signed_automated_artifact_without_claiming_review(self):
        result=self.call(18,'qa_test_run',{'native_id':371},'qa-readback-1')
        self.assertEqual(result['verification_kind'],'AUTOMATED_NATIVE_READBACK')
        self.assertEqual(result['verdict'],'PASSED');self.assertEqual(result['actor'],18)
        self.assertEqual(result['project_id'],5);self.assertEqual(result['binding']['version'],1)
        self.assertEqual(len(result['tests']),3);self.assertTrue(result['source_current'])
        self.assertEqual(result['producer']['id'],'qldapm-native-readback-v1')
        self.assertEqual(len(result['producer']['code_sha256']),64)
        self.assertIn('signature',result);self.assertIn('artifact_sha256',result)
        self.assertNotIn('human_approved',result);self.assertNotIn('reviewer',result)
        artifact=json.loads(result['artifact']);self.assertEqual(artifact['tests'],result['tests'])
        self.assertGreaterEqual(result['finished_at'],result['started_at'])
        again=self.call(18,'qa_test_run',{'native_id':371},'qa-readback-1');self.assertEqual(again['id'],result['id'])
        self.assertEqual(self.native.writes,[])
        self.native.row['lockVersion']=2
        current=self.call(18,'qa_test_get',{'id':result['id']});self.assertFalse(current['source_current'])
        self.assertFalse(self.call(18,'qa_test_run',{'native_id':371},'qa-readback-1')['source_current'])

    def test_agent_report_only_comes_from_fresh_authenticated_trusted_run(self):
        from gateway.native_qa_runs import for_agent
        from gateway.qa_agent import evaluate_test_attestation, VerifiedTestReport
        result=self.call(19,'qa_test_run',{'native_id':371},'agent-trusted-run')
        verified=for_agent(self.service,self.f.tokens[23],result['id'])
        summary,_=evaluate_test_attestation(self.native.row,verified)
        self.assertIn('PASSED',summary);self.assertIn('automated Native readback',summary)
        self.assertEqual((verified.actor_id,verified.project_id),(23,5))
        with self.assertRaises(PermissionError):
            VerifiedTestReport(None,23,5,371,1,result['id'],'PASSED','fake',0,'a'*64)
        with self.assertRaises(PermissionError):for_agent(self.service,self.f.tokens[21],result['id'])
        self.native.row['lockVersion']+=1
        with self.assertRaises(NativeError):for_agent(self.service,self.f.tokens[23],result['id'])

    def test_http_runner_and_independent_reviews_preserve_contracts_and_legacy_guard(self):
        from gateway.app import create_app
        from starlette.testclient import TestClient
        with TestClient(create_app(service=self.service),base_url='http://localhost:8090') as client:
            def command(actor,action,args):
                return client.post('/api/v1/commands',headers={'Authorization':'Bearer '+self.f.tokens[actor]},json={
                    'action':action,'arguments':args,'idempotency_key':'http-'+action})
            response=command(19,'qa_test_run',{'native_id':371})
            self.assertEqual(response.status_code,200,response.text)
            run=response.json()['result']
            e=command(19,'qa_evidence_from_run',{'run_id':run['id']}).json()['result']
            path='/api/v1/qa-evidence/'+e['id']+'/decision'
            def decision(actor,fingerprint):
                return client.post(path,headers={'Authorization':'Bearer '+self.f.tokens[actor]},json={'decision':'accept','hash':fingerprint})
            self.assertIn(decision(18,e['hash']).status_code,[401,403])
            self.assertEqual(decision(23,'0'*64).status_code,409)
            self.assertEqual(decision(23,e['hash']).status_code,200)
            self.assertEqual(decision(23,e['hash']).status_code,409)
            self.assertEqual(decision(18,e['hash']).status_code,200)
            self.assertEqual(command(18,'qa_evidence_list',{}).status_code,200)
            self.assertEqual(command(21,'qa_evidence_list',{}).status_code,403)
            self.assertEqual(command(18,'get_gate',{'id':371}).status_code,422)
            self.assertEqual(client.post('/api/v1/commands',json={'action':'qa_evidence_list'}).status_code,401)
        self.assertEqual(self.native.writes,[])

    def test_uncovered_unsupported_forged_or_foreign_inputs_cannot_generate_a_pass(self):
        original=self.native.row['description']['raw']
        for index,description in enumerate([original+'\nAC4: ',original+'\nAC1: native.status_id == 7',
                'AC1: the login UI works', 'AC1: native.url == "http://external.invalid"',
                'AC1: native.status_id == true', 'AC1: native.startDate == {"passed":true}']):
            self.native.row['description']['raw']=description
            with self.assertRaises(ValueError):self.call(18,'qa_test_run',{'native_id':371},'invalid-'+str(index))
        self.native.row['description']['raw']=original
        for actor in [20,21,22]:
            with self.assertRaises(PermissionError):self.call(actor,'qa_test_run',{'native_id':371},'role-'+str(actor))
        for extra in [{'passed':True},{'actor':23},{'file_path':'C:/private'},{'tests':[{'outcome':'PASSED'}]}]:
            with self.assertRaises(ValueError):self.call(18,'qa_test_run',{'native_id':371,**extra},'forged-'+str(len(extra)))
        self.assertEqual(self.native.writes,[])

    def test_failed_assertions_stale_source_and_tampered_artifact_never_become_trusted_passes(self):
        self.native.row['dueDate']='2026-10-28'
        failed=self.call(18,'qa_test_run',{'native_id':371},'failed-readback')
        self.assertEqual(failed['verdict'],'FAILED');self.assertEqual(failed['tests'][1]['outcome'],'FAILED')
        with self.store.connect() as db:
            raw=db.execute('select document from qa_test_runs where id=?',(failed['id'],)).fetchone()[0]
            changed=json.loads(raw);changed['verdict']='PASSED'
            db.execute('update qa_test_runs set document=? where id=?',(json.dumps(changed),failed['id']))
        with self.assertRaisesRegex(ValueError,'INTEGRITY_FAILED'):
            self.call(18,'qa_test_get',{'id':failed['id']})
        self.native.row['dueDate']='2026-10-27'
        original=self.native.package;calls=[]
        def moving(instance,identifier):
            result=original(instance,identifier);calls.append(identifier)
            if len(calls)==4:self.native.row['lockVersion']+=1
            return result
        from unittest.mock import patch
        with patch.object(self.native,'package',moving):
            stale=self.call(18,'qa_test_run',{'native_id':371},'mid-run-change')
        self.assertEqual(stale['verdict'],'BLOCKED');self.assertFalse(stale['source_current'])
        self.assertEqual(self.native.writes,[])

    def test_automated_runs_keep_native_acl_scope_and_do_not_accept_bearer_role_claims(self):
        result=self.call(19,'qa_test_run',{'native_id':371},'pm-source-test')
        self.assertEqual(self.call(23,'qa_test_get',{'id':result['id']})['id'],result['id'])
        for actor in [20,21,22]:
            with self.assertRaises(PermissionError):self.call(actor,'qa_test_get',{'id':result['id']})
        self.native.denied=True
        with self.assertRaises(NativeError):self.call(23,'qa_test_get',{'id':result['id']})
        self.native.denied=False
        from unittest.mock import patch
        with patch.object(self.native,'identity',side_effect=PermissionError('REVOKED_NATIVE_IDENTITY')):
            with self.assertRaises(PermissionError):self.call(18,'qa_test_run',{'native_id':371},'revoked')

    def test_automated_evidence_needs_independent_qa_then_manager_and_separate_native_approval(self):
        run=self.call(19,'qa_test_run',{'native_id':371},'pm-run')
        evidence=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'pm-run-evidence')
        self.assertEqual(evidence['state'],'pending_qa');self.assertFalse(evidence['ready'])
        self.assertEqual(evidence['verification_kind'],'AUTOMATED_NATIVE_READBACK')
        self.assertEqual(evidence['producer'],run['producer']);self.assertEqual(evidence['run_id'],run['id'])
        with self.assertRaises(PermissionError):self.service.decide_qa_evidence(self.f.tokens[18],evidence['id'],'accept',evidence['hash'])
        reviewed=self.service.decide_qa_evidence(self.f.tokens[23],evidence['id'],'accept',evidence['hash'])
        self.assertEqual(reviewed['state'],'qa_accepted');self.assertFalse(reviewed['ready'])
        with self.assertRaises(PermissionError):self.service.decide_qa_evidence(self.f.tokens[19],evidence['id'],'accept',evidence['hash'])
        accepted=self.service.decide_qa_evidence(self.f.tokens[18],evidence['id'],'accept',evidence['hash'])
        self.assertTrue(accepted['ready']);self.assertEqual([r['actor'] for r in accepted['reviews']],[23,18])
        with self.assertRaises(NativeError):self.service.decide_qa_evidence(self.f.tokens[18],evidence['id'],'accept',evidence['hash'])
        p=self.call(18,'qa_transition_prepare',{'id':evidence['id'],'hash':evidence['hash'],'status_id':9},'separate-proposal')
        self.assertEqual(self.native.writes,[])
        result=self.service.decide_proposal(self.f.tokens[18],p['id'],'approve',p['hash'])
        self.assertEqual(len(self.native.writes),1);self.assertEqual(result['result']['lockVersion'],2)
        self.assertFalse(self.call(23,'qa_evidence_get',{'id':evidence['id']})['ready'])

    def test_model_self_review_forged_review_and_wrong_source_cannot_advance_automated_evidence(self):
        run=self.call(19,'qa_test_run',{'native_id':371},'run-for-negative-review')
        with self.assertRaises(PermissionError):self.call(18,'qa_evidence_from_run',{'run_id':run['id']},'foreign-producer')
        evidence=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'negative-evidence')
        from gateway.agent_trace import current_run
        from types import SimpleNamespace
        token=current_run.set((self.store,SimpleNamespace(actor_id=23,project_id=5,run_id='model-run',trace_id='model-trace',task_id=None)))
        try:
            with self.assertRaises(PermissionError):self.service.decide_qa_evidence(self.f.tokens[23],evidence['id'],'accept',evidence['hash'])
        finally:current_run.reset(token)
        with self.assertRaises(NativeError):self.service.decide_qa_evidence(self.f.tokens[23],evidence['id'],'accept','0'*64)
        with self.store.connect() as db:db.execute("update qa_evidence set state='accepted' where id=?",(evidence['id'],))
        self.assertFalse(self.call(18,'qa_evidence_get',{'id':evidence['id']})['ready'])
        with self.store.connect() as db:db.execute("update qa_evidence set state='pending_qa' where id=?",(evidence['id'],))
        self.service.decide_qa_evidence(self.f.tokens[23],evidence['id'],'accept',evidence['hash'])
        with self.store.connect() as db:
            row=db.execute("select document from qa_evidence_reviews where evidence=? and stage='qa'",(evidence['id'],)).fetchone()
            proof=json.loads(row[0]);proof['actor']=21
            db.execute("update qa_evidence_reviews set document=? where evidence=? and stage='qa'",(json.dumps(proof),evidence['id']))
        with self.assertRaisesRegex(ValueError,'PROVENANCE_INVALID'):self.call(18,'qa_evidence_get',{'id':evidence['id']})
        self.assertEqual(self.native.writes,[])

    def test_each_automated_review_stage_has_one_concurrent_winner_and_failed_tests_stay_not_ready(self):
        import concurrent.futures
        import threading
        run=self.call(19,'qa_test_run',{'native_id':371},'concurrent-run')
        e=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'concurrent-evidence')
        for actor in [23,18]:
            barrier=threading.Barrier(2)
            def decide(_):
                barrier.wait()
                try:self.service.decide_qa_evidence(self.f.tokens[actor],e['id'],'accept',e['hash']);return 200
                except NativeError as error:return error.status
            with concurrent.futures.ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(decide,[0,1]))
            self.assertEqual(sorted(outcomes),[200,409])
        self.native.row['dueDate']='2026-10-28'
        run=self.call(19,'qa_test_run',{'native_id':371},'failed-after-review')
        e=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'failed-evidence')
        for actor in [23,18]:self.service.decide_qa_evidence(self.f.tokens[actor],e['id'],'accept',e['hash'])
        self.assertFalse(self.call(18,'qa_evidence_get',{'id':e['id']})['ready'])
        with self.assertRaises(NativeError):self.call(18,'qa_transition_prepare',{'id':e['id'],'hash':e['hash'],'status_id':9},'failed-no-transition')
        self.assertEqual(self.native.writes,[])

    def test_explicit_schedule_acceptance_sentences_are_checked_as_six_real_predicates(self):
        self.native.row['_links']['priority']={'href':'/api/v3/priorities/8','title':'Normal'}
        self.native.row['description']['raw']='Technical schedule/readback test only. Not a completed business task.\n\nAC1: Native startDate is 2026-10-26 and dueDate is 2026-10-27.\nAC2: Normal priority8 and BE21 assignment are preserved.'
        result=self.call(18,'qa_test_run',{'native_id':371},'explicit-schedule-contract')
        self.assertEqual(result['verdict'],'PASSED');self.assertEqual(len(result['tests']),6)
        self.assertEqual(set(result['criteria']),{'AC1','AC2'})
        self.assertEqual(len({r['reference'] for r in result['tests']}),6)
        self.assertEqual(result['binding']['assignee_identity'],{'actor':21,'role':'BE'})
        self.native.row['_links']['priority']['title']='High'
        failed=self.call(18,'qa_test_run',{'native_id':371},'changed-priority-label')
        self.assertEqual(failed['verdict'],'FAILED')

    def test_qa_inbox_is_native_authorized_and_never_exposes_foreign_artifacts_to_developers(self):
        run=self.call(19,'qa_test_run',{'native_id':371},'inbox-run')
        e=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'inbox-evidence')
        for actor in [18,19,23]:
            inbox=self.call(actor,'qa_evidence_list',{})
            self.assertEqual([r['id'] for r in inbox['items']],[e['id']])
            self.assertNotIn('artifact',inbox['items'][0])
        for actor in [20,21,22]:
            with self.assertRaises(PermissionError):self.call(actor,'qa_evidence_list',{})
        with self.assertRaises(ValueError):self.call(23,'qa_evidence_list',{'actor_id':18})
        self.native.denied=True
        self.assertEqual(self.call(23,'qa_evidence_list',{})['items'],[])

    def test_lost_metadata_reply_recovers_same_run_without_replaying_native_write(self):
        from unittest.mock import patch
        from gateway.service import Service
        from gateway.store import Store
        with patch.object(self.store,'finish',side_effect=RuntimeError('lost metadata reply')):
            with self.assertRaises(RuntimeError):self.call(19,'qa_test_run',{'native_id':371},'lost-run')
        self.store=Store(self.f.root)
        self.service=Service(self.store,self.service.config,self.f.root/'workspace',self.native)
        self.f.store=self.store;self.f.service=self.service
        recovered=self.call(19,'qa_test_run',{'native_id':371},'lost-run')
        self.assertEqual(recovered['verdict'],'PASSED')
        with self.store.connect() as db:self.assertEqual(db.execute('select count(*) from qa_test_runs').fetchone()[0],1)
        with patch.object(self.store,'finish',side_effect=RuntimeError('lost evidence reply')):
            with self.assertRaises(RuntimeError):self.call(19,'qa_evidence_from_run',{'run_id':recovered['id']},'lost-evidence')
        e=self.call(19,'qa_evidence_from_run',{'run_id':recovered['id']},'lost-evidence')
        self.assertEqual(e['state'],'pending_qa')
        self.assertEqual(self.native.writes,[])



    def test_revoked_reviewers_invalidate_readiness_without_rewriting_review_history(self):
        from unittest.mock import patch
        run=self.call(19,'qa_test_run',{'native_id':371},'revocation-run')
        e=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'revocation-evidence')
        for actor in [23,18]:self.service.decide_qa_evidence(self.f.tokens[actor],e['id'],'accept',e['hash'])
        original=self.native.identity
        for revoked in [23,18]:
            def identity(client,actor):
                if actor==revoked:raise NativeError(403,'REVIEWER_REVOKED')
                return original(client,actor)
            with patch.object(self.native,'identity',identity):
                result=self.call(19,'qa_evidence_get',{'id':e['id']})
                self.assertFalse(result['ready']);self.assertFalse(result['reviewers_current'])
                self.assertEqual(result['state'],'accepted');self.assertEqual(len(result['reviews']),2)
        self.assertTrue(self.call(19,'qa_evidence_get',{'id':e['id']})['ready'])
        self.assertEqual(self.native.writes,[])

    def test_manager_cannot_accept_after_qa_authorization_changed(self):
        from unittest.mock import patch
        run=self.call(19,'qa_test_run',{'native_id':371},'changed-qa-run')
        e=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'changed-qa-evidence')
        self.service.decide_qa_evidence(self.f.tokens[23],e['id'],'accept',e['hash'])
        original=self.native.identity
        def identity(client,actor):
            if actor==23:raise NativeError(403,'REVIEWER_REVOKED')
            return original(client,actor)
        with patch.object(self.native,'identity',identity):
            with self.assertRaisesRegex(NativeError,'REVIEWER_AUTHORIZATION_CHANGED'):
                self.service.decide_qa_evidence(self.f.tokens[18],e['id'],'accept',e['hash'])
        with self.store.connect() as db:
            self.assertEqual(db.execute('select state from qa_evidence where id=?',(e['id'],)).fetchone()[0],'qa_accepted')
            self.assertEqual(db.execute('select count(*) from qa_evidence_reviews where evidence=?',(e['id'],)).fetchone()[0],1)

    def test_automated_review_and_audit_commit_together_or_both_rollback(self):
        import sqlite3
        run=self.call(19,'qa_test_run',{'native_id':371},'audit-run')
        e=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'audit-evidence')
        with self.store.connect() as db:
            db.execute("CREATE TRIGGER fail_review_audit BEFORE INSERT ON audit WHEN NEW.action='qa_evidence_qa_accept' BEGIN SELECT RAISE(ABORT,'AUDIT_UNAVAILABLE'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.service.decide_qa_evidence(self.f.tokens[23],e['id'],'accept',e['hash'])
        with self.store.connect() as db:
            self.assertEqual(db.execute('select state from qa_evidence where id=?',(e['id'],)).fetchone()[0],'pending_qa')
            self.assertEqual(db.execute('select count(*) from qa_evidence_reviews where evidence=?',(e['id'],)).fetchone()[0],0)
            db.execute('DROP TRIGGER fail_review_audit')
        self.service.decide_qa_evidence(self.f.tokens[23],e['id'],'accept',e['hash'])
        with self.store.connect() as db:
            rows=db.execute("select version from audit where action='qa_evidence_qa_accept' and target=?",(e['id'],)).fetchall()
            self.assertEqual([row[0] for row in rows],[e['hash']])

    def test_review_authorization_dependency_failure_is_not_a_ready_result(self):
        from unittest.mock import patch
        run=self.call(19,'qa_test_run',{'native_id':371},'offline-review-run')
        e=self.call(19,'qa_evidence_from_run',{'run_id':run['id']},'offline-review-evidence')
        for actor in [23,18]:self.service.decide_qa_evidence(self.f.tokens[actor],e['id'],'accept',e['hash'])
        original=self.native.identity
        def identity(client,actor):
            if actor==23:raise NativeError(503,'NATIVE_UNAVAILABLE')
            return original(client,actor)
        with patch.object(self.native,'identity',identity),self.assertRaises(NativeError) as error:
            self.call(19,'qa_evidence_get',{'id':e['id']})
        self.assertEqual(error.exception.status,503)


if __name__=='__main__':unittest.main()

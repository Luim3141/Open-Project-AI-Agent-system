"""Phase artifacts are drafts; only a separate independent human review can accept them."""
import copy
import unittest
from unittest.mock import patch

from gateway.agent_trace import current_run
from gateway.native import NativeError
from tests import test_native_bug_lifecycle as fixtures


class NativePhaseTests(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.NativeBugLifecycleTests();self.h.setUp();self.addCleanup(self.h.doCleanups)
        self.service=self.h.service;self.store=self.h.store;self.tokens=self.h.tokens
        (self.store.root/'ui.key').write_bytes(b'isolated-phase-key')
        self.h.native.rows[39]['description']={'raw':'Story: Preserve registered vectors.\nAC1: Unknown vectors remain quarantined.\nScope: Registered IDs only.\nAnalysis: Persist old point proofs before updating metadata.\n'}
        self.h.native.rows[39]['_links'].update(assignee={'href':'/api/v3/users/21'},priority={'href':'/api/v3/priorities/8','title':'Normal'})
        original=self.h.native.call
        def call(native,path,method='GET',payload=None):
            if path=='/api/v3/qldapm/gates/39':return {'id':39,'lockVersion':self.h.native.rows[39]['lockVersion'],'gate':{'revision':1,'contributors':[]}}
            return original(native,path,method,payload)
        self.h.native.call=call

    def draft(self,actor=20,kind='scope'):
        from gateway.native_phase import create
        return create(self.service,actor,39,kind)

    def review(self,doc,actor=19,decision='accept',fingerprint=None):
        from gateway.native_phase import review
        return review(self.service,actor,doc['id'],decision,fingerprint or doc['hash'])

    def test_missing_ac_and_developer_producer_cannot_create_accepted_facts(self):
        for actor in [21,22,23]:
            with self.assertRaises(PermissionError):self.draft(actor)
        self.h.native.rows[39]['description']['raw']='Story: Missing actual acceptance criteria.\nScope: Unqualified.\n'
        with self.assertRaisesRegex(ValueError,'AC_REQUIRED'):self.draft()
        self.assertEqual(self.h.native.writes,[])

    def test_native_crlf_source_is_supported_without_rewriting_signed_source(self):
        self.h.native.rows[39]['description']['raw']=self.h.native.rows[39]['description']['raw'].replace('\n','\r\n')
        document=self.draft()
        self.assertEqual(document['source']['description'],self.h.native.rows[39]['description']['raw'])
        self.assertEqual(self.review(document)['state'],'accepted')

    def test_blank_native_criterion_is_not_accepted(self):
        self.h.native.rows[39]['description']['raw']=self.h.native.rows[39]['description']['raw'].replace('AC1: Unknown vectors remain quarantined.','AC1:    ')
        with self.assertRaisesRegex(ValueError,'AC_REQUIRED'):self.draft()

    def test_scope_and_analysis_require_explicit_exact_independent_review(self):
        from gateway.native_phase import packet
        for kind,approvals in [('scope',['scope']),('analysis',['scope','analysis'])]:
            doc=self.draft(kind=kind);self.assertEqual(doc['state'],'pending')
            with self.assertRaises(NativeError):packet(self.service,18,doc['id'])
            with self.assertRaises(PermissionError):self.review(doc,20)
            with self.assertRaises(NativeError):self.review(doc,fingerprint='0'*64)
            accepted=self.review(doc);self.assertEqual(accepted['state'],'accepted')
            self.assertEqual(accepted['review']['approvals'],approvals)
            self.assertEqual(set(packet(self.service,18,doc['id'])),{'version','artifact','review'})
            with self.assertRaises(NativeError):self.review(doc)
        self.assertEqual(self.h.native.writes,[])

    def test_rejected_or_stale_wrong_wp_artifact_does_not_become_native_authority(self):
        from gateway.native_phase import get,packet
        doc=self.draft();self.review(doc,decision='reject')
        with self.assertRaises(NativeError):packet(self.service,18,doc['id'])
        self.assertEqual(self.draft()['state'],'rejected')
        self.h.native.rows[39]['lockVersion']+=1;new=self.draft();self.assertNotEqual(new['id'],doc['id'])
        self.h.native.rows[39]['lockVersion']+=1
        self.assertFalse(get(self.service,19,new['id'])['source_current'])
        with self.assertRaises(NativeError):self.review(new)
        with self.store.connect() as db:self.assertEqual(db.execute('select count(*) from native_phase_reviews').fetchone()[0],1)

    def test_model_context_cross_actor_and_lower_role_review_denied(self):
        from gateway.native_phase import get
        doc=self.draft()
        for actor in [21,22,23]:
            with self.assertRaises(PermissionError):get(self.service,actor,doc['id'])
            with self.assertRaises(PermissionError):self.review(doc,actor)
        token=current_run.set('isolated-model-context')
        try:
            with self.assertRaises(PermissionError):self.review(doc)
        finally:current_run.reset(token)
        self.assertEqual(get(self.service,19,doc['id'])['state'],'pending')

    def test_review_and_audit_commit_atomically(self):
        from gateway.native_phase import get
        doc=self.draft()
        with patch.object(self.store,'record',side_effect=RuntimeError('ISOLATED_AUDIT_FAULT')):
            with self.assertRaises(RuntimeError):self.review(doc)
        self.assertEqual(get(self.service,19,doc['id'])['state'],'pending')
        with self.store.connect() as db:self.assertEqual(db.execute('select count(*) from native_phase_reviews').fetchone()[0],0)


if __name__=='__main__':unittest.main()

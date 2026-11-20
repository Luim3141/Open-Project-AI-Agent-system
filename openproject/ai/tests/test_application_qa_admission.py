import unittest
from unittest.mock import patch
from contextlib import ExitStack

from tests import test_application_qa_verify_action as verify_fixture
from gateway.native import NativeError


class ApplicationQaAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = verify_fixture.ApplicationQaVerifyActionTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture.f
        self.proof = self.fixture.proof

    def scope(self):
        stack = ExitStack()
        capabilities = {'project_id': 5, 'enforced': True, 'application_qa_source_sha256': self.proof.sources['core']}
        stack.enter_context(patch.object(self.f.native, 'package', return_value=self.proof.item))
        stack.enter_context(patch.object(self.f.native, 'call', return_value=capabilities))
        stack.enter_context(patch('gateway.application_qa_intake.gateway_sources', return_value=self.proof.sources['gateway']))
        return stack

    def test_admission_is_idempotent_independent_review_and_native_approval_stay_separate(self):
        capabilities = {'project_id': 5, 'enforced': True, 'application_qa_source_sha256': self.proof.sources['core']}
        with patch.object(self.f.native, 'package', return_value=self.proof.item), \
             patch.object(self.f.native, 'call', return_value=capabilities), \
             patch('gateway.application_qa_intake.gateway_sources', return_value=self.proof.sources['gateway']):
            evidence = self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.id}, 'admit-app')
            self.assertEqual(evidence['verification_kind'], 'AUTOMATED_APPLICATION_WBS')
            self.assertEqual(evidence['state'], 'pending_qa')
            self.assertFalse(evidence['ready'])
            self.assertFalse(evidence['native_transition_supported'])
            again = self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.id}, 'admit-app')
            self.assertEqual(again['id'], evidence['id'])
            self.assertEqual(self.f.call(23, 'qa_evidence_get', {'id': evidence['id']})['id'], evidence['id'])
            with self.assertRaises(PermissionError):
                self.f.service.decide_qa_evidence(self.f.tokens[18], evidence['id'], 'accept', evidence['hash'])
            qa = self.f.service.decide_qa_evidence(self.f.tokens[23], evidence['id'], 'accept', evidence['hash'])
            self.assertEqual(qa['state'], 'qa_accepted')
            accepted = self.f.service.decide_qa_evidence(self.f.tokens[19], evidence['id'], 'accept', evidence['hash'])
            self.assertEqual(accepted['state'], 'accepted')
            self.assertTrue(accepted['review_chain_complete'])
            self.assertFalse(accepted['ready'])
            repeated = self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.id}, 'admit-second-request')
            self.assertEqual((repeated['id'], repeated['hash'], repeated['state']),
                             (accepted['id'], accepted['hash'], 'accepted'))
            from gateway.native_qa_runs import for_agent
            from gateway.qa_agent import evaluate_test_attestation
            report = for_agent(self.f.service, self.f.tokens[23], evidence['run_id'])
            summary, _ = evaluate_test_attestation(self.proof.item, report)
            self.assertIn('qualification application WBS', summary)
            self.assertNotIn('automated Native readback', summary)
            with self.assertRaisesRegex(NativeError, 'APPLICATION_QA_NATIVE_TRANSITION_NOT_IMPLEMENTED'):
                self.f.call(18, 'qa_transition_prepare', {'id': evidence['id'], 'hash': evidence['hash'], 'status_id': 9}, 'no-app-native')
            self.assertEqual(self.f.native.writes, [])
            with self.f.store.connect() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM qa_test_runs').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT count(*) FROM qa_evidence').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT count(*) FROM qa_evidence_reviews').fetchone()[0], 2)

    def test_code_or_native_drift_blocks_review_and_invalid_admission_creates_nothing(self):
        with self.scope():
            for actor in (19, 20, 21, 22, 23):
                with self.assertRaises(PermissionError):
                    self.f.call(actor, 'qa_application_proof_admit', {'id': self.fixture.id}, 'foreign-'+str(actor))
            evidence = self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.id}, 'admit-drift')
            changed = {**self.proof.sources['gateway'], 'native_wbs.py': '6' * 64}
            with patch('gateway.application_qa_intake.gateway_sources', return_value=changed):
                stale = self.f.call(23, 'qa_evidence_get', {'id': evidence['id']})
                self.assertFalse(stale['source_current'])
                with self.assertRaises(NativeError):
                    self.f.service.decide_qa_evidence(self.f.tokens[23], evidence['id'], 'accept', evidence['hash'])
            self.proof.item['lockVersion'] += 1
            self.assertFalse(self.f.call(23, 'qa_evidence_get', {'id': evidence['id']})['source_current'])
            with self.assertRaises(ValueError):
                self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.id}, 'changed-native')
            with self.f.store.connect() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM qa_evidence').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT count(*) FROM qa_evidence_reviews').fetchone()[0], 0)
        self.assertEqual(self.f.native.writes, [])

    def test_lost_metadata_ack_recovers_same_records_without_native_replay(self):
        with self.scope():
            with patch.object(self.f.store, 'finish', side_effect=RuntimeError('isolated lost metadata acknowledgment')):
                with self.assertRaises(RuntimeError):
                    self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.id}, 'lost-metadata')
            evidence = self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.id}, 'lost-metadata')
            self.assertEqual(evidence['state'], 'pending_qa')
            with self.f.store.connect() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM qa_test_runs').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT count(*) FROM qa_evidence').fetchone()[0], 1)
        self.assertEqual(self.f.native.writes, [])


if __name__ == '__main__':
    unittest.main()

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import test_native_qa_evidence as native_fixture
from tests import test_application_qa_proof as proof_fixture


class ApplicationQaVerifyActionTests(unittest.TestCase):
    def setUp(self):
        self.f = native_fixture.NativeQaEvidenceTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.proof = proof_fixture.ApplicationQaProofTests('runTest')
        self.proof.setUp()
        (self.f.root / 'ui.key').write_bytes(self.proof.key)
        directory = self.f.root / 'application-proofs'
        directory.mkdir()
        self.id = self.proof.body['id']
        (directory / (self.id + '.json')).write_text(json.dumps(self.proof.bundle()), encoding='utf-8')

    def test_only_owner_can_verify_without_recording_review_or_native_write(self):
        capabilities = {'project_id': 5, 'enforced': True, 'application_qa_source_sha256': self.proof.sources['core']}
        with patch.object(self.f.native, 'package', return_value=self.proof.item), \
             patch.object(self.f.native, 'call', return_value=capabilities), \
             patch('gateway.application_qa_intake.gateway_sources', return_value=self.proof.sources['gateway']):
            result = self.f.call(18, 'qa_application_proof_verify', {'id': self.id})
            self.assertEqual(result['id'], self.id)
            self.assertEqual(result['status'], 'TECHNICAL_PROOF_NOT_REVIEWED')
            self.assertEqual(result['tested_build'], self.proof.body['build'])
            self.assertNotIn('approved', result)
            for actor in (19, 20, 21, 22, 23):
                with self.assertRaises(PermissionError):
                    self.f.call(actor, 'qa_application_proof_verify', {'id': self.id})
            with self.assertRaises(ValueError):
                self.f.call(18, 'qa_application_proof_verify', {'id': self.id, 'approved': True})
            from gateway.agent_trace import current_run
            marker = current_run.set((self.f.store, SimpleNamespace(actor_id=18, project_id=5,
                run_id='isolated-run', trace_id='isolated-trace', task_id=None)))
            try:
                with self.assertRaises(PermissionError):
                    self.f.call(18, 'qa_application_proof_verify', {'id': self.id})
            finally:
                current_run.reset(marker)
        with self.f.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM qa_evidence').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM qa_test_runs').fetchone()[0], 0)
        self.assertEqual(self.f.native.writes, [])


if __name__ == '__main__':
    unittest.main()

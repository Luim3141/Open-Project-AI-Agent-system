import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests import test_application_qa_proof as proof_fixture
from gateway.application_qa_intake import load_verified


class ApplicationQaIntakeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = proof_fixture.ApplicationQaProofTests('runTest')
        self.fixture.setUp()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / 'ui.key').write_bytes(self.fixture.key)
        (root / 'application-proofs').mkdir()
        self.path = root / 'application-proofs' / (self.fixture.body['id'] + '.json')
        self.path.write_text(json.dumps(self.fixture.bundle()), encoding='utf-8')
        self.service = SimpleNamespace(store=SimpleNamespace(root=root), mode='native', config={'project_id': 5})

        class Native:
            def identity(_, identifier):
                assert identifier == 18
                return {'user_id': 18, 'role': 'AI_SYSTEM_OWNER', 'project_id': 5}

            def package(_, identifier):
                assert identifier == 371
                return self.fixture.item

            def call(_, path):
                assert path == '/api/v3/qldapm/capabilities'
                return {'project_id': 5, 'enforced': True, 'application_qa_source_sha256': self.fixture.sources['core']}

        self.native = Native()
        self.who = {'user_id': 18, 'role': 'AI_SYSTEM_OWNER'}

    def load(self, identifier=None, who=None):
        with patch('gateway.application_qa_intake.gateway_sources', return_value=self.fixture.sources['gateway']):
            return load_verified(self.service, who or self.who, self.native, identifier or self.fixture.body['id'])

    def test_signed_current_proof_is_technical_only(self):
        result = self.load()
        self.assertEqual(result['id'], self.fixture.body['id'])
        self.assertEqual(result['verdict'], 'PASSED')
        self.assertNotIn('approved', result)

    def test_foreign_actor_traversal_tampering_and_source_drift_fail(self):
        for who in ({'user_id': 19, 'role': 'PM'}, {'user_id': 20, 'role': 'AI_SYSTEM_OWNER'}):
            with self.assertRaises(PermissionError):
                self.load(who=who)
        with self.assertRaises(ValueError):
            self.load(identifier='../config.json')
        bundle = self.fixture.bundle()
        bundle['signature'] = '0' * 64
        self.path.write_text(json.dumps(bundle), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.load()
        self.path.write_text(json.dumps(self.fixture.bundle()), encoding='utf-8')
        with patch('gateway.application_qa_intake.gateway_sources', return_value={**self.fixture.sources['gateway'], 'native_wbs.py': '6' * 64}):
            with self.assertRaises(ValueError):
                load_verified(self.service, self.who, self.native, self.fixture.body['id'])
        with patch('gateway.application_qa_intake.current_run', SimpleNamespace(get=lambda: object())):
            with self.assertRaises(PermissionError):
                self.load()
        self.fixture.item['lockVersion'] += 1
        with self.assertRaises(ValueError):
            self.load()

    def test_filename_must_match_signed_id_and_missing_capability_fails(self):
        import uuid
        other = str(uuid.uuid4())
        (self.path.parent / (other + '.json')).write_text(json.dumps(self.fixture.bundle()), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'ID_MISMATCH'):
            self.load(identifier=other)
        with patch.object(self.native, 'call', return_value={'project_id': 5, 'enforced': True}):
            with self.assertRaises(ValueError):
                self.load()

    def test_oversized_file_fails_before_parsing(self):
        self.path.write_bytes(b' ' * 1_100_001)
        with self.assertRaisesRegex(ValueError, 'SIZE'):
            self.load()


if __name__ == '__main__':
    unittest.main()

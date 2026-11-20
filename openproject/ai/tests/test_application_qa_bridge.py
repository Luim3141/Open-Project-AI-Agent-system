import unittest
from unittest.mock import patch

from tests import test_application_qa_admission as admission_fixture
from gateway.native import NativeError


class ApplicationQaBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = admission_fixture.ApplicationQaAdmissionTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f, self.proof = self.fixture.f, self.fixture.proof

    def test_qualified_native_capability_allows_only_independently_reviewed_exact_packet(self):
        from gateway.native_qa_bridge import packet, preflight
        with self.fixture.scope():
            evidence = self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.fixture.id}, 'bridge-admit')
            self.assertFalse(evidence['ready'])
            capabilities = {'project_id': 5, 'enforced': True, 'qa_bridge_version': 1,
                            'application_qa_bridge_version': 1, 'application_qa_source_sha256': self.proof.sources['core']}
            with patch.object(self.f.native, 'call', return_value=capabilities):
                with self.assertRaises(NativeError):
                    packet(self.f.service, 18, evidence['id'])
                for actor in (23, 19):
                    accepted = self.f.service.decide_qa_evidence(self.f.tokens[actor], evidence['id'], 'accept', evidence['hash'])
                self.assertTrue(accepted['ready'])
                self.assertTrue(accepted['native_transition_supported'])
                bundle = packet(self.f.service, 18, evidence['id'])
                self.assertEqual(len(bundle['reviews']), 2)
                for actor in (20, 21, 22, 23):
                    with self.assertRaises(PermissionError):
                        packet(self.f.service, actor, evidence['id'])
                args = {'status_id': 9, 'qa_evidence_id': evidence['id'], 'qa_evidence_hash': evidence['hash']}
                native, who = self.f.service.native_actor(18)
                def call(path, *unused):
                    if path.endswith('/capabilities'):
                        return capabilities
                    self.assertEqual(path, '/api/v3/qldapm/qa_transition_forms')
                    return {'valid': True, 'lockVersion': self.proof.item['lockVersion'],
                            'qa_evidence_id': evidence['id'], 'hash': evidence['hash']}
                with patch.object(self.f.native, 'call', side_effect=call):
                    self.assertEqual(preflight(self.f.service, who, native, self.proof.item, args), bundle)
                self.assertNotIn('qa_authorization', bundle)
                self.assertEqual(self.f.native.writes, [])

    def test_unknown_or_disabled_application_bridge_never_falls_back_to_generic_native_write(self):
        from gateway.native_qa_bridge import preflight
        with self.fixture.scope():
            evidence = self.f.call(18, 'qa_application_proof_admit', {'id': self.fixture.fixture.id}, 'bridge-off')
            for actor in (23, 19):
                self.f.service.decide_qa_evidence(self.f.tokens[actor], evidence['id'], 'accept', evidence['hash'])
            for version in (None, 0, 2, True, '1'):
                capabilities = {'project_id': 5, 'enforced': True, 'qa_bridge_version': 1,
                                'application_qa_source_sha256': self.proof.sources['core']}
                if version is not None:
                    capabilities['application_qa_bridge_version'] = version
                with self.subTest(version=version), patch.object(self.f.native, 'call', return_value=capabilities):
                    current = self.f.call(18, 'qa_evidence_get', {'id': evidence['id']})
                    self.assertFalse(current['ready'])
                    self.assertFalse(current['native_transition_supported'])
                    native, who = self.f.service.native_actor(18)
                    with self.assertRaises(NativeError):
                        preflight(self.f.service, who, native, self.proof.item,
                                  {'status_id': 9, 'qa_evidence_id': evidence['id'], 'qa_evidence_hash': evidence['hash']})
            self.assertEqual(self.f.native.writes, [])


if __name__ == '__main__':
    unittest.main()

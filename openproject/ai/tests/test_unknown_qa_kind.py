import unittest
import uuid
import hashlib
import hmac

import test_native_qa_evidence as fixture
from gateway.native import NativeError
from gateway.store import canonical, digest


class UnknownQaKindTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.NativeQaEvidenceTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_future_evidence_is_visible_but_cannot_be_reviewed_or_used(self):
        f = self.fixture
        identifier = str(uuid.uuid4())
        body = {'id': identifier, 'actor': 18, 'project_id': 5, 'verification_kind': 'FUTURE_QA_PROOF',
                'binding': {'native_id': 371, 'version': 1}, 'manifest': {}}
        text = canonical(body)
        with f.store.connect() as db:
            db.execute('INSERT INTO qa_evidence VALUES(?,?,?,?,?,?,?,?)',
                       (identifier, 18, 5, text, digest(text), 'pending', 1, None))
        result = f.call(18, 'qa_evidence_get', {'id': identifier})
        self.assertFalse(result['ready'])
        self.assertFalse(result['source_current'])
        self.assertEqual(result['compatibility'], 'UNSUPPORTED_EVIDENCE_KIND')
        self.assertEqual(f.call(18, 'qa_evidence_list', {})['items'][0]['id'], identifier)
        with self.assertRaises(PermissionError):
            f.service.decide_qa_evidence(f.tokens[19], identifier, 'reject', result['hash'])
        with self.assertRaises(PermissionError):
            f.call(23, 'qa_evidence_get', {'id': identifier})
        with self.assertRaises(NativeError):
            f.call(18, 'qa_transition_prepare', {'id': identifier, 'hash': result['hash'], 'status_id': 9}, 'future')
        f.native.denied = True
        with self.assertRaises(NativeError):
            f.call(18, 'qa_evidence_get', {'id': identifier})
        f.native.denied = False
        with f.store.connect() as db:
            db.execute('UPDATE qa_evidence SET hash=? WHERE id=?', ('0' * 64, identifier))
        with self.assertRaisesRegex(ValueError, 'QA_EVIDENCE_HASH_MISMATCH'):
            f.call(18, 'qa_evidence_get', {'id': identifier})
        self.assertEqual(f.native.writes, [])

    def test_future_run_is_readable_as_unsupported_but_cannot_become_an_agent_attestation(self):
        from gateway.native_qa_runs import DOMAIN, snapshot, for_agent
        f = self.fixture
        key = b'isolated-future-run-signing-key'
        (f.root / 'ui.key').write_bytes(key)
        identifier = str(uuid.uuid4())
        body = {'id': identifier, 'actor': 18, 'project_id': 5, 'verification_kind': 'FUTURE_QA_PROOF',
                'binding': {'native_id': 371, 'version': 1, 'snapshot_sha256': digest(canonical(snapshot(f.native.row)))},
                'artifact': 'future signed technical artifact', 'artifact_sha256': digest('future signed technical artifact')}
        body['signature'] = hmac.new(key, DOMAIN + canonical(body).encode(), hashlib.sha256).hexdigest()
        with f.store.connect() as db:
            db.execute('INSERT INTO qa_test_runs VALUES(?,?,?,?,?)', (identifier, 18, 5, canonical(body), 1))
        result = f.call(18, 'qa_test_get', {'id': identifier})
        self.assertFalse(result['source_current'])
        self.assertEqual(result['compatibility'], 'UNSUPPORTED_RUN_KIND')
        with self.assertRaises(NativeError):
            for_agent(f.service, f.tokens[23], identifier)


if __name__ == '__main__':
    unittest.main()

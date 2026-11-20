"""Native bridge proof export is internal, source-authenticated and never an approval."""
import hashlib
import hmac
import json
import unittest

import test_native_qa_runs as fixture
from gateway.native import NativeError


class NativeQaBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.NativeQaRunTests('runTest');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.service=self.fixture.service;self.store=self.fixture.store
        self.run=self.fixture.call(19,'qa_test_run',{'native_id':371},'bridge-run')
        self.evidence=self.fixture.call(19,'qa_evidence_from_run',{'run_id':self.run['id']},'bridge-evidence')

    def accept(self):
        for actor in [23,18]:self.service.decide_qa_evidence(self.fixture.f.tokens[actor],self.evidence['id'],'accept',self.evidence['hash'])

    def test_internal_packet_needs_accepted_independent_reviews_and_exact_unchanged_source(self):
        from gateway.native_qa_bridge import packet
        with self.assertRaises(NativeError):packet(self.service,19,self.evidence['id'])
        self.accept();proof=packet(self.service,19,self.evidence['id'])
        self.assertEqual(set(proof),{'version','run','evidence_document','reviews'})
        self.assertEqual(proof['version'],1);self.assertEqual(len(proof['reviews']),2)
        key=(self.fixture.f.root/'ui.key').read_bytes()
        for bundle,domain in [(proof['run'],b'qldapm.native-qa-run.v1\0')]+[(r,b'qldapm.native-qa-review.v1\0') for r in proof['reviews']]:
            self.assertEqual(bundle['signature'],hmac.new(key,domain+bundle['document'].encode(),hashlib.sha256).hexdigest())
        self.assertEqual(json.loads(proof['run']['document'])['id'],self.run['id'])
        self.assertEqual(hashlib.sha256(proof['evidence_document'].encode()).hexdigest(),self.evidence['hash'])
        self.assertNotIn(key.decode(),json.dumps(proof))
        self.fixture.native.row['lockVersion']+=1
        with self.assertRaises(NativeError):packet(self.service,19,self.evidence['id'])
        self.assertEqual(self.fixture.native.writes,[])

    def test_packet_export_cannot_be_used_by_non_manager_or_as_an_execution_authorization(self):
        from gateway.native_qa_bridge import packet
        self.accept()
        for actor in [20,21,22,23]:
            with self.assertRaises(PermissionError):packet(self.service,actor,self.evidence['id'])
        proof=packet(self.service,18,self.evidence['id'])
        self.assertNotIn('approved',proof);self.assertNotIn('authorization',proof)
        self.assertNotIn('proposal_id',proof)
        with self.store.connect() as db:db.execute("update qa_evidence set state='pending_qa'")
        with self.assertRaises(NativeError):packet(self.service,18,self.evidence['id'])


if __name__=='__main__':unittest.main()

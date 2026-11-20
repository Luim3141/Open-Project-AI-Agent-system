import unittest
from gateway.engineering_integrity import observed_result


class IntegrityProjectionTests(unittest.TestCase):
    def test_conflicting_success_is_not_projected_as_delivery_or_replayed(self):
        stored = {'status': 'succeeded', 'error': 'KNOWLEDGE_BUSY_RETRY_LATER', 'text': 'success claim'}
        result = observed_result(stored, 'FAILED')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['persisted_status'], 'succeeded')
        self.assertEqual(result['integrity_state'], 'RECONCILIATION_REQUIRED')
        self.assertEqual(stored['status'], 'succeeded')

    def test_consistent_or_missing_agent_evidence_is_preserved(self):
        for status in ['COMPLETED', None]:
            stored = {'status': 'succeeded', 'head_sha': 'a' * 40}
            self.assertEqual(observed_result(stored, status), stored)

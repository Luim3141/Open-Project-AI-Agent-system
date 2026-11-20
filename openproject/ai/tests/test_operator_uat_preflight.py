import unittest

from automation.operator_uat_preflight import LEGACY_POINTS, assess


class OperatorPreflightTests(unittest.TestCase):
    def fixture(self):
        return ({'integrity': {'status': 'PARTIAL_UNMATCHED_POINTS', 'documents': 441,
                    'unmatched_points': [{'id': k, 'source_id': v} for k, v in LEGACY_POINTS.items()]},
                'wp376': ['test2', 0, 'NEW'], 'wp371': [4, 'IN ANALYSIS'], 'qa': 'pending_qa',
                'gateway_quick_check': 'ok', 'pm_token_remaining_seconds': 100},
                [{'code': f'WF{i:02}', 'active': True, 'published': True} for i in range(1, 17)])

    def test_dynamic_document_count_is_not_a_fixed_release_gate(self):
        probe, workflows = self.fixture()
        for count in (441, 442):
            probe['integrity']['documents'] = count
            self.assertTrue(all(assess(probe, workflows).values()))

    def test_drift_and_unregistered_point_changes_fail_closed(self):
        probe, workflows = self.fixture()
        probe['integrity']['status'] = 'DRIFT_DETECTED'
        self.assertFalse(assess(probe, workflows)['registered_knowledge'])
        probe['integrity']['unmatched_points'].pop()
        self.assertFalse(assess(probe, workflows)['protected_legacy_points'])

    def test_expired_pm_token_and_unpublished_workflow_are_not_pass(self):
        probe, workflows = self.fixture()
        probe['pm_token_remaining_seconds'] = -1
        workflows[0]['published'] = False
        checks = assess(probe, workflows)
        self.assertFalse(checks['pm_token_valid'])
        self.assertFalse(checks['workflow_activation'])

    def test_changed_protected_business_state_needs_operator_review(self):
        probe, workflows = self.fixture()
        probe['qa'] = 'accepted'
        probe['wp376'][1] = 1
        checks = assess(probe, workflows)
        self.assertFalse(checks['qa_pending'])
        self.assertFalse(checks['wp376_preserved'])

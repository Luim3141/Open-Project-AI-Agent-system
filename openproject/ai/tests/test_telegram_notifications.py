import copy
import unittest


class TelegramEventTests(unittest.TestCase):
    def snapshot(self):
        return {'task_id': 400, 'project_id': 6, 'task_title': 'Verified task',
                'workflow_status': 'COMPLETED', 'latest_run_id': 'run-1',
                'source_conflicts': [], 'stages': [], 'artifacts': [],
                'acceptance': {'status': 'FULLY_COMPLETED', 'required_gates': [{'name': 'dev', 'passed': True}, {'name': 'owner', 'passed': True}],
                               'missing_gates': [], 'evidence_refs': ['receipt-1']},
                'events': [{'event_id': 'event-1', 'run_id': 'run-1', 'event_type': 'RUN_COMPLETED',
                            'timestamp': 1000, 'source_record_id': 'event-1'}]}

    def test_completed_requires_explicit_all_gates_and_source(self):
        from gateway.telegram_notifications import events
        item = self.snapshot()
        self.assertEqual(events(item)[0]['event_type'], 'TASK_COMPLETED')
        for field, value in [('missing_gates', ['owner']), ('required_gates', []), ('evidence_refs', [])]:
            changed = copy.deepcopy(item); changed['acceptance'][field] = value
            self.assertNotIn('TASK_COMPLETED', [e['event_type'] for e in events(changed)])
        for key, value in [('source_conflicts', ['mismatch']), ('events', [])]:
            changed = copy.deepcopy(item); changed[key] = value
            self.assertNotIn('TASK_COMPLETED', [e['event_type'] for e in events(changed)])
        changed = copy.deepcopy(item); changed['acceptance']['required_gates'][0]['passed'] = False
        self.assertNotIn('TASK_COMPLETED', [e['event_type'] for e in events(changed)])

    def test_run_success_or_pr_does_not_prove_task_completion(self):
        from gateway.telegram_notifications import events
        item = self.snapshot(); item['acceptance']['status'] = 'NOT_RECORDED'
        self.assertEqual(events(item), [])
        item['acceptance']['status'] = 'AWAITING_OWNER_APPROVAL'
        self.assertEqual([e['event_type'] for e in events(item)], ['AWAITING_APPROVAL'])

    def test_qa_failure_and_blocked_are_source_bound_stable_and_payload_is_bounded(self):
        from gateway.telegram_notifications import events
        item = self.snapshot(); item['acceptance']['status'] = 'UNKNOWN'; item['workflow_status'] = 'BLOCKED'
        item['events'][0].update(event_type='AGENT_FAILED', agent_id='qa', error_code='TEST_FAILED', payload={'token': 'SECRET'})
        actual = events(item)
        self.assertEqual({e['event_type'] for e in actual}, {'TASK_BLOCKED', 'QA_FAILED', 'AGENT_FAILED'})
        self.assertEqual(actual, events(item))
        self.assertNotIn('SECRET', str(actual))
        item['events'][0]['event_id'] = ''
        self.assertEqual(events(item), [])

    def test_pr_notification_requires_verified_http_artifact(self):
        from gateway.telegram_notifications import events
        item = self.snapshot(); item['acceptance']['status'] = 'UNKNOWN'
        item['artifacts'] = [{'artifact_id': 'pr-1', 'type': 'github_pr', 'uri': 'https://github.com/o/r/pull/1',
                              'verification_status': 'VERIFIED', 'created_at': 1001, 'run_id': 'run-1'}]
        self.assertEqual(events(item)[0]['event_type'], 'PR_CREATED')
        item['artifacts'][0]['verification_status'] = 'NOT_RECORDED'
        self.assertEqual(events(item), [])


if __name__ == '__main__':
    unittest.main()

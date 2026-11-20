import unittest
from unittest.mock import patch

from gateway.daily_brief import day
from gateway.store import Store
from tests import test_daily_brief as fixture


class WorkflowErrorTests(unittest.TestCase):
    def setUp(self):
        self.daily = fixture.DailyBriefTests()
        self.daily.setUp()
        self.addCleanup(self.daily.doCleanups)

    def event(self):
        return self.daily.command(kind='workflow_error', request_key='error:qldapmDailyBrief:42:' + day())

    def test_fixed_error_metadata_dedup_restart_no_native_provider_and_project_authorized_ui(self):
        with patch.object(self.daily.service, 'native_factory', side_effect=AssertionError('NO_NATIVE_IN_ERROR_EVENT')):
            first = self.daily.post(self.event()).json()['result']
            self.assertEqual(self.daily.post(self.event()).json()['result'], first)
        self.assertEqual((first['state'], first['status'], first['actor_id']), ('COMPLETED', 'WORKFLOW_FAILED', None))
        self.assertFalse(first['native_write_allowed'])
        reopened = Store(self.daily.root)
        self.assertEqual(len(reopened.workflow_alerts(3)), 1)
        self.assertEqual(reopened.workflow_alerts(99), [])
        for actor in self.daily.roles:
            result = self.daily.service.execute_actor(actor, {'action': 'analyze', 'arguments': {}})['result']
            self.assertEqual(len(result['workflow_alerts']), 1)
            self.assertEqual(result['workflow_alerts'][0]['trace_id'], first['trace_id'])
        self.daily.state.roles.pop(7)
        with self.assertRaises(PermissionError):
            self.daily.service.execute_actor(7, {'action': 'analyze', 'arguments': {}})
        with reopened.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 1)
            self.assertEqual(db.execute('select count(*) from gemini_usage').fetchone()[0], 0)

    def test_unknown_workflows_raw_errors_actor_project_and_reserved_namespace_rejected(self):
        for changes in ({'request_key': 'error:otherWorkflow:42:' + day()}, {'request_key': 'error:qldapmDailyBrief:42:2000-01-01'},
                        {'error_message': 'PRIVATE_MUST_NOT_PERSIST'}, {'actor_id': 7}, {'project_id': 99}):
            command = {**self.event(), **changes}
            self.assertEqual(self.daily.post(command).status_code, 422)
        self.assertEqual(self.daily.post({**self.event(), 'kind': 'status'}).status_code, 422)
        with self.daily.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 0)
            self.assertNotIn('PRIVATE_MUST_NOT_PERSIST', '\n'.join(db.iterdump()))

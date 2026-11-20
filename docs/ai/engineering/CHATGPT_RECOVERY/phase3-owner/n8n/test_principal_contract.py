"""Offline contract checks for observed identities; no credentials, Native calls, or mutations."""
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[6] / 'openproject/ai'))
from gateway.daily_brief import collect, day
from gateway.native import Native
from gateway.weekly_report import collect_scheduled, scheduled_week


class PrincipalContractTests(unittest.TestCase):
    def test_actor19_admin_is_denied_before_membership_can_grant_pm(self):
        native = Native('http://localhost:8088', 'synthetic-only', 5)
        native.call = Mock(side_effect=lambda path: {'id': 19, 'login': 'ba-pm', 'admin': True, 'status': 'active'}
                           if path.endswith('/users/me') else {'identifier': 'qldapm-local'})
        native.collection = Mock(return_value=[])
        with self.assertRaisesRegex(PermissionError, 'IDENTITY_MISMATCH_OR_ADMIN_TOKEN'):
            native.identity(19)
        native.collection.assert_not_called()

    def test_login_pm_does_not_promote_actor20_from_actual_ba_membership(self):
        native = Native('http://localhost:8088', 'synthetic-only', 5)
        native.call = Mock(side_effect=lambda path: {'id': 20, 'login': 'pm', 'admin': None, 'status': 'active'}
                           if path.endswith('/users/me') else {'identifier': 'qldapm-local'})
        native.collection = Mock(return_value=[{'_links': {'principal': {'href': '/api/v3/users/20'},
                                  'roles': [{'title': 'QLDAPM BA'}]}}])
        self.assertEqual(native.identity(20)['role'], 'BA')

    def service(self):
        service = Mock()
        service.config = {'project_id': 5, 'users': {'18': 'AI_SYSTEM_OWNER', '19': 'PM', '20': 'BA',
                                                   '21': 'BE', '22': 'FE', '23': 'QA'}}
        service.store.begin_automation.return_value = ({'run_id': 'synthetic-run', 'trace_id': 'synthetic-trace'}, True)
        def actor(actor, **kwargs):
            if actor == 19:
                raise PermissionError('IDENTITY_MISMATCH_OR_ADMIN_TOKEN')
            native = Mock()
            native.summary.return_value = {'count': 0, 'by_status': {}, 'overdue_ids': []}
            return native, {'role': service.config['users'][str(actor)]}
        service.native_actor.side_effect = actor
        return service

    def assert_actor_states(self, reports):
        self.assertEqual(len(reports), 5)
        self.assertEqual({row['actor'] for row in reports}, {19, 20, 21, 22, 23})
        self.assertEqual({row['actor']: row['state'] for row in reports},
                         {19: 'DENIED', 20: 'READY', 21: 'READY', 22: 'READY', 23: 'READY'})

    def test_daily_preserves_all_five_targets_and_denial_does_not_become_ready(self):
        service = self.service()
        issued = time.time()
        collect(service, {'issued_at': issued, 'request_key': 'daily:' + day(issued)})
        self.assertEqual(service.store.begin_automation.call_args.kwargs['targets'], 5)
        self.assert_actor_states(service.store.finish_daily_brief.call_args.args[1])

    def test_weekly_preserves_all_five_targets_and_denial_does_not_become_ready(self):
        service = self.service()
        def report(actor, *args, **kwargs):
            if actor == 19:
                raise PermissionError('IDENTITY_MISMATCH_OR_ADMIN_TOKEN')
            return {'report_id': 'synthetic-report', 'report_sha256': 'a' * 64}
        service.weekly_report.side_effect = report
        issued = time.time()
        collect_scheduled(service, {'issued_at': issued, 'request_key': scheduled_week(issued)[1]})
        self.assertEqual(service.store.begin_automation.call_args.kwargs['targets'], 5)
        self.assert_actor_states(service.store.finish_weekly_summary.call_args.args[1])


if __name__ == '__main__':
    unittest.main()

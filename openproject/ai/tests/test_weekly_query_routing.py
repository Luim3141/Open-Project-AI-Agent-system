import unittest
from unittest.mock import patch

from tests import test_local_queries as fixture
from gateway.gemini import ProviderError
from gateway.local_queries import match_query


class WeeklyQueryRoutingTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.LocalQueryTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.tearDown)

    def test_weekly_question_works_without_model_and_keeps_role_scope_and_freshness(self):
        self.assertEqual(match_query('Báo cáo tuần này'), ('weekly', 'weekly_summary', {}))
        with patch.object(self.f.service.gemini, 'validate_prompt', side_effect=ProviderError('DISABLED')):
            receipt = self.f.start('Báo cáo tuần này', 'weekly', actor=8)
            result = self.f.store.run(8, receipt['result']['id'])['result']
            self.assertFalse(result['model_used'])
            report = result['tools'][0]['result']['result']
            self.assertEqual(report['actor_id'], 8)
            self.assertEqual(report['data_quality'], 'PARTIAL_STATUS_HISTORY_UNAVAILABLE')
            self.assertEqual(set(report['member_breakdown']), {'8'})
            self.assertEqual(self.f.start('Báo cáo tuần này', 'weekly', actor=8), receipt)
            fresh = self.f.service.execute_actor(8, {'action': 'get_ai_run', 'arguments': {'id': receipt['result']['id']}})['result']
            self.assertEqual(fresh['result']['source_fingerprint'], result['source_fingerprint'])
            self.assertFalse(fresh['result'].get('stale', False))
            self.f.state.rows[1]['percentageDone'] = 0
            self.f.state.rows[1]['_links']['status'] = {'href': '/api/v3/statuses/1', 'title': 'NEW'}
            with self.assertRaisesRegex(ValueError, 'STALE_READ_RECEIPT'):
                self.f.start('Báo cáo tuần này', 'weekly', actor=8)
        with self.f.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM gemini_usage').fetchone()[0], 0)

    def test_mixed_write_is_not_classified_as_weekly_read(self):
        self.assertIsNone(match_query('Báo cáo tuần này rồi đóng tất cả task'))

    def test_six_roles_keep_member_scope_and_cross_actor_history_private(self):
        roles = {18: 'AI_SYSTEM_OWNER', 19: 'PM', 20: 'BA', 21: 'BE', 22: 'FE', 23: 'QA'}
        self.f.state.roles.update(roles)
        self.f.config['users'] = {str(actor): role for actor, role in roles.items()}
        self.f.config['project_id'] = 5
        identity = self.f.native_factory.identity
        def native_identity(native, actor):
            result = identity(native, actor)
            if actor == 18:
                result['capabilities'] = ['AI_SYSTEM_OWNER']
            return result
        replacement = patch.object(self.f.native_factory, 'identity', native_identity)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.f.state.rows[0]['_links']['assignee'] = {'href': '/api/v3/users/21', 'title': 'BE fixture'}
        self.f.state.rows[1]['_links']['assignee'] = {'href': '/api/v3/users/22', 'title': 'FE fixture'}
        for actor, role in roles.items():
            with self.subTest(role=role):
                self.f.state.visible[actor] = [1, 2]
                self.f.store.issue_token(actor, role, f'synthetic-native-{actor}')
                receipt = self.f.start('Báo cáo tuần', f'weekly-{actor}', actor)
                run = self.f.service.execute_actor(actor, {'action': 'get_ai_run', 'arguments': {'id': receipt['result']['id']}})['result']
                members = run['result']['tools'][0]['result']['result']['member_breakdown']
                self.assertEqual(set(members), set(map(str, roles)) if actor in {18, 19} else {str(actor)})
                with self.assertRaises(PermissionError):
                    self.f.service.execute_actor(7, {'action': 'get_ai_run', 'arguments': {'id': receipt['result']['id']}})


if __name__ == '__main__':
    unittest.main()

"""Public Gateway commands; synthetic Native responses, no network or Main writes."""
import tempfile
import unittest
from pathlib import Path

from gateway.service import Service
from gateway.store import Store
from tests.test_sprint_accuracy import item, relation


class NativeSprintSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        store = Store(root)
        self.token = store.issue_token(7, 'PM', 'PM')
        self.ba = store.issue_token(8, 'BA', 'BA')
        rows = [item(1), item(2, actor=8), item(3)]
        for row, sprint in zip(rows, (11, 11, 12)):
            row['_links']['sprint'] = {'href': f'/api/v3/sprints/{sprint}'}
        class Native:
            def __init__(self, url, credential, project):
                self.role = credential
            def identity(self, actor):
                return {'user_id': actor, 'role': self.role}
            def packages(self):
                return rows
            def sprints(self):
                return [{'id': 11, 'name': 'S1', 'startDate': '2026-10-05', 'finishDate': '2026-10-16'},
                        {'id': 12, 'name': 'S2'}, {'id': 13, 'name': 'Empty'}]
            def relations(self, packages):
                return [relation(41, 1, 3, 'follows')]
        self.service = Service(store, {'users': {'7': 'PM', '8': 'BA'}, 'project_id': 5,
            'gateway_mode': 'native', 'openproject_url': 'http://127.0.0.1:8088'}, root/'workspace', Native)

    def risk(self, args, token=None):
        return self.service.execute(token or self.token, {'action': 'sprint_risks',
            'arguments': {'as_of_date': '2026-10-24', **args}})['result']

    def test_exact_native_sprint_selection_keeps_cross_sprint_dependencies_and_persisted_readback(self):
        result = self.risk({'sprint_id': 11})
        self.assertEqual(result['report']['summary']['total_packages'], 2)
        self.assertEqual(result['sprint']['id'], 11)
        self.assertEqual(result['report']['dependencies'][0]['prerequisite_ids'], [3])
        readback = self.service.execute(self.token, {'action': 'get_report',
            'arguments': {'id': result['report_id']}})['result']
        self.assertEqual(readback['document']['sprint']['name'], 'S1')
        self.assertTrue(readback['source_versions_current'])

    def test_default_project_scope_empty_sprint_and_role_limits_are_preserved(self):
        self.assertEqual(self.risk({})['report']['summary']['total_packages'], 3)
        empty = self.risk({'sprint_id': 13})
        self.assertEqual(empty['report']['summary']['total_packages'], 0)
        self.assertEqual(empty['sprint']['id'], 13)
        ba = self.risk({'sprint_id': 11}, self.ba)
        self.assertEqual(ba['report']['summary']['total_packages'], 2)
        self.assertEqual(set(ba['report']['workload']), {'8', 'project_totals'})
        self.assertEqual(ba['report']['workload']['8']['package_ids'], [2])
        self.assertEqual(ba['report']['workload']['project_totals']['total_open'], 2)
        self.assertEqual(ba['report']['dependencies'], [])
        self.assertNotIn('Chưa chọn Sprint Native', '\n'.join(ba['report']['limitations']))

    def test_unseen_sprint_and_untrusted_selectors_fail_closed(self):
        with self.assertRaisesRegex(PermissionError, 'NATIVE_SPRINT_NOT_VISIBLE'):
            self.risk({'sprint_id': 999})
        for invalid in (True, False, 0, -1, '11', None, [], {}):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'POSITIVE_NATIVE_SPRINT_ID_REQUIRED'):
                self.risk({'sprint_id': invalid})
        with self.assertRaisesRegex(ValueError, 'INVALID_ARGUMENTS'):
            self.risk({'sprint_id': 11, 'actor_id': 7, 'role': 'PM'})


if __name__ == '__main__':
    unittest.main()

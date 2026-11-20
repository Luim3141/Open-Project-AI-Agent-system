import unittest
from gateway.automation_targets import select
import test_daily_brief as daily_fixture

class SelectedReadersTests(unittest.TestCase):
    def setUp(self):
        self.fixture=daily_fixture.DailyBriefTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
    def test_invalid_admin_path_can_be_excluded_without_granting_new_roles(self):
        f=self.fixture
        f.denied.add(7)
        f.service.config['automation_readers']=[6,8,9,10]
        response=f.post();self.assertEqual(response.status_code,200)
        result=response.json()['result']
        self.assertEqual(result['ready'],4);self.assertEqual(result['targets'],4)
        self.assertEqual(result['target_selection']['excluded_actor_ids'],[7])
        self.assertNotIn(7,f.calls)
        self.assertEqual(f.post().json()['result'],result)
    def test_selector_cannot_create_membership_or_select_owner(self):
        f=self.fixture;f.service.config['automation_readers']=[9999]
        with self.assertRaisesRegex(PermissionError,'SELECTION'):select(f.service,{'request_key':'daily:fixture'})

if __name__=='__main__':unittest.main()

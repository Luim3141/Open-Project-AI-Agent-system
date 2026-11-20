import unittest
from app.tools import context_result

class CheckpointContextTests(unittest.TestCase):
    def test_version_counter_is_not_number_of_completed_steps_even_after_truncation(self):
        for padding in ['', 'x'*30000]:
            result=context_result({'task_id':398,'checkpoint':{'version':27,'completed_steps':['dev-0','review-0','qa-0']},'padding':padding})
            result=result.get('verified_summary',result)
            self.assertEqual(result['checkpoint']['completed_step_count'],3)
            self.assertEqual(result['checkpoint']['version_semantics'],'REVISION_COUNTER_NOT_STEP_COUNT')

    def test_missing_steps_are_not_reported_as_zero(self):
        result=context_result({'checkpoint':{'version':27}})
        self.assertNotIn('completed_step_count',result['checkpoint'])

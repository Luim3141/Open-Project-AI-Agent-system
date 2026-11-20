import unittest

from pydantic import ValidationError

from gateway.engineering_planning import DevelopmentPlan, feedback_base_unit, validate_plan


class EngineeringCatalogLimitTests(unittest.TestCase):
    def catalog(self, count):
        known={f'feedback-{i}':{'base_unit':None} for i in range(count)}
        delivered={key:{'head_sha':'a'*40} for key in known}
        return known,delivered

    def test_completed_thirteen_units_allow_one_more(self):
        known,delivered=self.catalog(13)
        self.assertEqual(feedback_base_unit(known,delivered,'feedback-demo-next'),'feedback-12')

    def test_fourteen_is_still_a_hard_bound(self):
        known,delivered=self.catalog(14)
        with self.assertRaisesRegex(ValueError,'ENGINEERING_UNIT_CATALOG_BUDGET'):
            feedback_base_unit(known,delivered,'feedback-fifteenth')

    def test_existing_feedback_can_resume_at_the_limit(self):
        known,delivered=self.catalog(14)
        self.assertIsNone(feedback_base_unit(known,delivered,'feedback-13'))

    def test_pending_unit_still_blocks_a_new_request(self):
        known,delivered=self.catalog(12)
        delivered.pop('feedback-11')
        with self.assertRaisesRegex(ValueError,'ENGINEERING_PENDING_FEEDBACK_UNIT_REQUIRED'):
            feedback_base_unit(known,delivered,'feedback-demo-next')

    def test_fourteen_assignments_fit_schema_and_plan_validation(self):
        allowed={f'unit-{i}':{'dependencies':[]} for i in range(14)}
        plan=DevelopmentPlan(summary='Existing thirteen plus one approved stabilization demo',
            assignments=[{'unit':key,'priority':1,'objective':'Fixture','dependencies':[]} for key in allowed],
            blockers=[],next_action='One pending unit only')
        self.assertEqual(len(validate_plan(plan,allowed).assignments),14)
        self.assertEqual(DevelopmentPlan.model_json_schema()['properties']['assignments']['maxItems'],14)

    def test_schema_rejects_fifteen_assignments(self):
        with self.assertRaises(ValidationError):
            DevelopmentPlan(summary='Too many',assignments=[{'unit':f'unit-{i}','priority':1,
                'objective':'Fixture','dependencies':[]} for i in range(15)],blockers=[],next_action='Rejected')


if __name__=='__main__':
    unittest.main()

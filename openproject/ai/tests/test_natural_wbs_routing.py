import unittest
import copy
import json
import time
import uuid

from gateway.planner import is_wbs_planning_intent, resolve_target_agents


class NaturalWbsRoutingTests(unittest.TestCase):
    def test_requested_wbs_uses_ba_without_discarding_named_specialists(self):
        for text in ('Phân tích requirement #375 và đề xuất WBS',
                     'Decompose requirement #375 into a WBS',
                     'Lập WBS cho yêu cầu #375, nhờ FE và BE phân tích'):
            self.assertTrue(is_wbs_planning_intent(text))
            self.assertIn('ba', resolve_target_agents(text, 'supervisor'))
        self.assertEqual(resolve_target_agents('Lập WBS cho yêu cầu #375, nhờ FE và BE phân tích', 'supervisor'),
                         ['ba', 'fe', 'be'])

    def test_question_and_explicit_specialist_are_not_rerouted(self):
        self.assertFalse(is_wbs_planning_intent('WBS là gì?'))
        self.assertFalse(is_wbs_planning_intent('Không đề xuất WBS, chỉ phân tích yêu cầu'))
        self.assertEqual(resolve_target_agents('Lập WBS cho yêu cầu #375', 'qa'), ['qa'])

    def test_legacy_markers_still_request_planning(self):
        for text in ('WBS_JSON', 'WBS_NATIVE_RELATIONS explicit lag2'):
            self.assertTrue(is_wbs_planning_intent(text))

    def test_natural_request_yields_cited_structured_v2_without_writes(self):
        from gateway.agent_models import AgentTask, RunScope
        from gateway.live_agents import LiveAgents, LiveConfig
        from tests.test_native_wbs import SPEC

        class MockProvider:
            def structured(self, prompt, schema, **kwargs):
                return schema.model_validate({'summary': 'Fixture draft', 'findings': [], 'recommendations': [],
                    'citations': [39], 'limitations': ['Not executed'], 'proposed_operations': [],
                    'planning': {'schema': 'QLDAPM_WBS_V2', **copy.deepcopy(SPEC), 'relations': []}})

        task = AgentTask(task_id=str(uuid.uuid4()), actor_id=20, project_id=5, conversation_id=str(uuid.uuid4()),
            agent='ba', instruction='Phân tích requirement #39 và đề xuất WBS', created_at=time.time(), expires_at=time.time()+600)
        scope = RunScope(run_id=str(uuid.uuid4()), task_id=task.task_id, actor_id=20, project_id=5, trace_id=str(uuid.uuid4()))
        item = {'id': 39, 'lockVersion': 3}
        provider = LiveAgents(MockProvider(), LiveConfig(enabled=True))
        provider.context = {'native_items': [item], 'retrieved_knowledge': []}
        result = provider.run_agent('ba', task, scope, [item])
        self.assertEqual(json.loads(result.summary)['schema'], 'QLDAPM_WBS_V2')
        self.assertEqual(result.references[0].work_package_id, 39)
        self.assertEqual(provider.operations, [])


if __name__ == '__main__':
    unittest.main()

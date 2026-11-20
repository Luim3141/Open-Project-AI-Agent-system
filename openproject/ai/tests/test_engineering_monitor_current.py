import unittest
from types import SimpleNamespace as N
from unittest.mock import patch
from gateway.engineering_monitor import project

class CurrentStageTests(unittest.TestCase):
    def test_recorded_current_agent_is_running_even_before_result_and_during_rework(self):
        run={'id':'run','state':'running','result':{}}
        agent=N(state='RUNNING',run_id='run',trace_id='trace',created_at=100.,updated_at=110.)
        task=N(references=[],instruction='tests only')
        for completed in [[],['dev-1']]:
            with self.subTest(completed=completed),patch('gateway.engineering_monitor.load',return_value={'completed_steps':completed}),patch('gateway.engineering_observability.describe_run',return_value={'current_agent':'dev'}):
                view=project(N(store=None),{'user_id':18,'role':'AI_SYSTEM_OWNER'},run,task,agent,{'native_id':398,'unit':'demo'},[],[])
                self.assertEqual(next(n for n in view['nodes'] if n['agent']=='dev')['state'],'RUNNING')

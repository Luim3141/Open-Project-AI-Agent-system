import tempfile,unittest
from pathlib import Path
from app.config import Settings
from app.storage import Repository
from app.tools import ToolExecutor,declarations

class GlobalReadTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_observer_queries_are_exposed_with_scope_and_truncation(self):
        class Gateway:
            last_correlation_id='fixture'
            async def command(self,action,args,project):
                self.last=(action,args,project)
                return {'items':[{'task_id':398,'acceptance_status':'AWAITING_OWNER_APPROVAL','artifacts':['x'*50000]},{'task_id':397,'acceptance_status':'FULLY_COMPLETED'}],'truncated':True,'source_limits':{'runs':50}}
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');code=repo.create_pairing(101,[6]);repo.pair(code,101,101);gw=Gateway();tools=ToolExecutor(gw,repo,Settings(project_ids=[6]))
            for name,state in [('get_active_agents','RUNNING'),('get_blocked_tasks','BLOCKED'),('get_pending_approvals','ALL')]:
                self.assertIn(name,{d['name'] for d in declarations()})
                result=await tools.execute(name,{},101,101,6)
                self.assertEqual(gw.last,('observer_active',{'state':state,'limit':50},6))
                self.assertTrue(result['truncated']);self.assertIn('Observer',result['scope_notice'])
                self.assertEqual(result['project_id'],6)
                self.assertNotIn('artifacts',result['items'][0])
                if name=='get_pending_approvals':self.assertEqual([x['task_id'] for x in result['items']],[398])
                self.assertIsNone(repo.memory(101,101).get('current_task_id'))
                with self.assertRaises(PermissionError):await tools.execute(name,{},999,999,6)

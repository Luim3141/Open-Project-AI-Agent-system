import asyncio
import tempfile
import time
import unittest
from pathlib import Path


class SecurityTests(unittest.TestCase):
    def test_notification_type_preferences_are_persistent_and_validated(self):
        code=self.repo.create_pairing(101,[6]);self.repo.pair(code,101,101)
        self.repo.set_notification_types(101,['TASK_COMPLETED','TASK_BLOCKED'])
        self.assertEqual(self.repo.recipients()[0]['notification_types'],['TASK_COMPLETED','TASK_BLOCKED'])
        with self.assertRaises(ValueError):self.repo.set_notification_types(101,['ALL_SECRETS'])
    def setUp(self):
        from app.storage import Repository
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repository(Path(self.tmp.name) / 'bot.sqlite')

    def tearDown(self):
        self.tmp.cleanup()

    def test_pairing_is_bound_to_numeric_user_private_chat_single_use(self):
        code = self.repo.create_pairing(101, [5], ttl=60)
        self.assertFalse(self.repo.pair(code, 102, 102))
        self.assertFalse(self.repo.pair(code, 101, -100))
        self.assertTrue(self.repo.pair(code, 101, 101))
        self.assertFalse(self.repo.pair(code, 101, 101))
        self.assertEqual(self.repo.authorize(101, 101)['project_ids'], [5])
        self.assertIsNone(self.repo.authorize(101, 102))
        self.repo.revoke(101)
        self.assertIsNone(self.repo.authorize(101, 101))

    def test_pairing_attempt_limit_and_expiry(self):
        code = self.repo.create_pairing(101, [5], ttl=-1)
        self.assertFalse(self.repo.pair(code, 101, 101))
        code = self.repo.create_pairing(101, [5])
        for _ in range(5): self.assertFalse(self.repo.pair('wrong', 101, 101))
        self.assertFalse(self.repo.pair(code, 101, 101))

    def test_memory_and_reply_context_survive_restart_and_are_chat_scoped(self):
        from app.storage import Repository
        self.repo.save_memory(101, 101, {'current_task_id': 391, 'current_project_id': 5,
                                      'constraints': ['không merge'], 'recent_messages': []})
        for i in range(30): self.repo.append_message(101, 101, 'user', 'message ' + str(i))
        self.repo.record_notification(101, 88, 392, 6, 'run-1')
        reopened = Repository(self.repo.path)
        memory = reopened.memory(101, 101)
        self.assertEqual(memory['current_task_id'], 391)
        self.assertEqual(memory['constraints'], ['không merge'])
        self.assertLessEqual(len(memory['recent_messages']), 16)
        self.assertTrue(memory['summary'])
        self.assertEqual(reopened.notification_context(101, 88)['task_id'], 392)
        self.assertIsNone(reopened.notification_context(102, 88))

    def test_confirmation_atomic_claim_bound_expiry_and_cancel(self):
        nonce = self.repo.propose(101, 101, {'tool': 'resume_task', 'arguments': {'task_id': 391}, 'fingerprint': 'a'})
        self.assertIsNone(self.repo.claim_confirmation(nonce, 102, 102))
        self.assertIsNotNone(self.repo.claim_confirmation(nonce, 101, 101))
        self.assertIsNone(self.repo.claim_confirmation(nonce, 101, 101))
        expired = self.repo.propose(101, 101, {'tool': 'resume_task'}, ttl=-1)
        self.assertIsNone(self.repo.claim_confirmation(expired, 101, 101))
        fresh = self.repo.propose(101, 101, {'tool': 'resume_task'})
        self.repo.cancel_pending(101, 101)
        self.assertIsNone(self.repo.claim_confirmation(fresh, 101, 101))

    def test_duplicate_update_and_rate_limit(self):
        self.assertTrue(self.repo.claim_update(1))
        self.assertFalse(self.repo.claim_update(1))
        for _ in range(6): self.assertTrue(self.repo.rate_limit(101, limit=6))
        self.assertFalse(self.repo.rate_limit(101, limit=6))

    def test_tool_allowlist_strict_args_and_project_scope(self):
        from app.tools import validate_call
        self.assertEqual(validate_call('get_task_progress', {'task_id': 391})['task_id'], 391)
        for name, args in [('shell', {}), ('get_task_progress', {'task_id': True}),
                           ('get_task_progress', {'task_id': 391, 'url': 'http://evil'}),
                           ('set_execution_mode', {'mode': 'DELETE'})]:
            with self.assertRaises(ValueError): validate_call(name, args)


class ToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_pause_binding_still_rejects_run_stage_checkpoint_or_native_version_changes(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        for change in [{'latest_run_id':'run2'},{'current_stage':'qa'},
                       {'checkpoint':{'version':5}},{'version':2}]:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as folder:
                class Gateway:
                    task={'task_id':400,'project_id':6,'version':1,'latest_run_id':'run1',
                          'current_stage':'dev','checkpoint':{'version':4}}
                    writes=[]
                    async def command(self,action,args,project_id,idempotency_key=None):
                        if action=='observer_task_progress':return dict(self.task)
                        if action=='engineering_status':return {'control':{'state_revision':7}}
                        self.writes.append(action);return {}
                repo=Repository(Path(folder)/'db');repo.pair(repo.create_pairing(101,[6]),101,101)
                gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[6]))
                proposed=await executor.execute('pause_task',{'task_id':400},101,101,6)
                gateway.task={**gateway.task,**change}
                with self.assertRaisesRegex(ValueError,'STATE_CHANGED'):
                    await executor.confirm(proposed['confirmation_id'],101,101)
                self.assertEqual(gateway.writes,[])

    async def test_pause_does_not_expire_only_because_live_heartbeat_changed(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        class Gateway:
            heartbeat_revision='heartbeat-1'
            writes=[]
            async def command(self,action,args,project_id,idempotency_key=None):
                if action=='observer_task_progress':return {'task_id':400,'project_id':6,'version':1,
                    'revision':self.heartbeat_revision,'workflow_status':'RUNNING','latest_run_id':'run1',
                    'current_stage':'dev','current_agent':'dev','checkpoint':{'version':4,'revision':'reviewed-tree'}}
                if action=='engineering_status':return {'control':{'state_revision':7,'desired_mode':'AUTO'}}
                self.writes.append(action);return {'accepted':True}
        with tempfile.TemporaryDirectory() as folder:
            repo=Repository(Path(folder)/'db');repo.pair(repo.create_pairing(101,[6]),101,101)
            gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[6]))
            proposed=await executor.execute('pause_task',{'task_id':400},101,101,6)
            gateway.heartbeat_revision='heartbeat-2'
            await executor.confirm(proposed['confirmation_id'],101,101)
            self.assertEqual(gateway.writes,['engineering_control'])

    async def test_resume_uses_exact_existing_run_and_checkpoint_and_sends_once(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        class Gateway:
            calls=[]
            async def command(self,action,args,project_id,idempotency_key=None):
                self.calls.append((action,args,idempotency_key))
                if action=='observer_task_progress':return {'task_id':400,'project_id':6,'version':1,'revision':'v1',
                    'latest_run_id':'existing-run','resume':{'eligible':True,'checkpoint_version':4}}
                return {'accepted':True,'command_id':'fixture'}
        with tempfile.TemporaryDirectory() as folder:
            repo=Repository(Path(folder)/'db');repo.pair(repo.create_pairing(101,[6]),101,101)
            gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[6]))
            proposed=await executor.execute('resume_task',{'task_id':400,'run_id':'existing-run'},101,101,6)
            self.assertFalse(any(c[0]=='engineering_resume' for c in gateway.calls))
            await executor.confirm(proposed['confirmation_id'],101,101)
            self.assertEqual(gateway.calls[-1][:2],('engineering_resume',{'run_id':'existing-run','checkpoint_version':4}))
            with self.assertRaises(ValueError):await executor.confirm(proposed['confirmation_id'],101,101)
            self.assertEqual(sum(c[0]=='engineering_resume' for c in gateway.calls),1)

    async def test_resume_denies_wrong_run_ineligible_or_missing_checkpoint(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        for latest,eligible,checkpoint in [('other-run',True,4),('run1',False,4),('run1',True,None)]:
            with self.subTest(latest=latest,eligible=eligible,checkpoint=checkpoint),tempfile.TemporaryDirectory() as folder:
                class Gateway:
                    writes=[]
                    async def command(self,action,args,project_id,idempotency_key=None):
                        if action=='observer_task_progress':return {'task_id':400,'project_id':6,'revision':'v1',
                            'latest_run_id':latest,'resume':{'eligible':eligible,'checkpoint_version':checkpoint}}
                        self.writes.append(action);return {}
                repo=Repository(Path(folder)/'db');repo.pair(repo.create_pairing(101,[6]),101,101)
                gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[6]))
                proposal=await executor.execute('resume_task',{'task_id':400,'run_id':'run1'},101,101,6)
                with self.assertRaises(ValueError):await executor.confirm(proposal['confirmation_id'],101,101)
                self.assertEqual(gateway.writes,[])

    async def test_mode_contract_requires_confirmation_for_off_auto_paused_and_run_once(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        for mode in ['OFF','AUTO','PAUSED','RUN_ONCE']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                class Gateway:
                    writes=[]
                    async def command(self,action,args,project_id,idempotency_key=None):
                        if action=='engineering_status':return {'control':{'state_revision':7,'desired_mode':'OFF'}}
                        self.writes.append((action,args,idempotency_key));return {'accepted':True}
                repo=Repository(Path(folder)/'db');repo.pair(repo.create_pairing(101,[6]),101,101)
                gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[6]))
                proposal=await executor.execute('set_execution_mode',{'mode':mode},101,101,6)
                self.assertEqual(gateway.writes,[])
                await executor.confirm(proposal['confirmation_id'],101,101)
                expected=('engineering_run_once',{}) if mode=='RUN_ONCE' else ('engineering_control',{'mode':mode,'expected_revision':7})
                self.assertEqual(gateway.writes[0][:2],expected)
                self.assertTrue(gateway.writes[0][2].startswith('tg:'))

    async def test_pause_confirmation_rejects_changed_project_control_even_when_task_is_unchanged(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        class Gateway:
            revision=7
            writes=[]
            async def command(self,action,args,project_id,idempotency_key=None):
                if action=='observer_task_progress':return {'task_id':400,'project_id':6,'version':1,'revision':'task-unchanged'}
                if action=='engineering_status':return {'control':{'state_revision':self.revision,'desired_mode':'OFF'}}
                self.writes.append(action);return {'accepted':True}
        with tempfile.TemporaryDirectory() as folder:
            repo=Repository(Path(folder)/'db');repo.pair(repo.create_pairing(101,[6]),101,101)
            gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[6]))
            proposal=await executor.execute('pause_task',{'task_id':400},101,101,6)
            gateway.revision=8
            with self.assertRaisesRegex(ValueError,'STATE_CHANGED'):
                await executor.confirm(proposal['confirmation_id'],101,101)
            self.assertEqual(gateway.writes,[])

    async def test_native_write_requires_second_exact_gateway_proposal_confirmation(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        class Gateway:
            approvals=0
            proposal={'id':'00000000-0000-4000-8000-000000000001','hash':'a'*64,'state':'pending',
                      'expires':time.time()+300,'human_confirmation_required':True,
                      'command':{'action':'create_work_package','preview':{'new_work_package':{'subject':'Test'}}}}
            async def command(self,action,args,project_id,idempotency_key=None):
                if action=='get_project_options':return {'types':[{'id':1,'name':'Task'}]}
                if action in {'create_work_package','get_proposal'}:return self.proposal
                raise AssertionError(action)
            async def proposal_decision(self,*args):
                self.approvals+=1;return {'result':{'id':400}}
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');code=repo.create_pairing(101,[5]);repo.pair(code,101,101)
            gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[5]))
            initial=await executor.execute('create_task',{'title':'Test','type_id':1},101,101,5)
            native_preview=await executor.confirm(initial['confirmation_id'],101,101)
            self.assertEqual(native_preview['state'],'CONFIRMATION_REQUIRED')
            self.assertEqual(gateway.approvals,0)
            result=await executor.confirm(native_preview['confirmation_id'],101,101)
            self.assertEqual(gateway.approvals,1)
            self.assertEqual(result['result']['result']['id'],400)
            with self.assertRaises(ValueError):await executor.confirm(native_preview['confirmation_id'],101,101)
    async def test_exact_task_execution_uses_real_gateway_backlog_contract(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        class Gateway:
            calls=[]
            async def command(self,action,args,project_id,idempotency_key=None):
                self.calls.append((action,args))
                if action=='observer_task_progress':return {'task_id':391,'project_id':6,'version':7,'revision':'exact'}
                if action=='engineering_status':return {'backlog':[{'native_id':391,'eligible':True,'unit':'approved-unit'}]}
                return {'accepted':True,'command_id':'real-receipt'}
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');code=repo.create_pairing(101,[6]);repo.pair(code,101,101)
            gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[6]))
            proposal=await executor.execute('request_task_execution',{'task_id':391},101,101,6)
            result=await executor.confirm(proposal['confirmation_id'],101,101)
            self.assertEqual(gateway.calls[-1],('engineering_run_once',{'native_id':391,'lock_version':7,'unit':'approved-unit'}))
            self.assertEqual(result['state'],'GATEWAY_RECEIPT')

    async def test_run_error_and_checkpoint_read_use_monitor_execution_summary(self):
        from app.tools import ToolExecutor
        class Gateway:
            async def command(self,*args,**kwargs):
                return {'run_id':'run1','state':'FAILED','execution_summary':{'checkpoint':{'version':2},
                    'resume':{'eligible':False},'failure':{'category':'TOOL_FAILED','message':'failure','raw_code':'ERROR'}}}
        executor=ToolExecutor(Gateway(),None,None)
        checkpoint=await executor.read('get_checkpoint_status',{'run_id':'run1'},6)
        self.assertEqual(checkpoint['checkpoint'],{'version':2})
        errors=await executor.read('get_run_errors',{'run_id':'run1'},6)
        self.assertEqual(errors['error_code'],'ERROR')
    async def test_model_cannot_execute_write_without_separate_confirmation(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        class Gateway:
            calls = []
            async def command(self, action, args, project_id, idempotency_key=None):
                self.calls.append((action, args))
                if action=='engineering_status':return {'control_state':{'state_revision':3}}
                return {'task_id': 391, 'project_id': project_id, 'lock_version': 7,
                        'latest_run_id': 'run1', 'runs': [{'run_id':'run1','checkpoint':{'version':2}}]}
        with tempfile.TemporaryDirectory() as directory:
            repo = Repository(Path(directory)/'x.sqlite')
            code=repo.create_pairing(101,[5]);repo.pair(code,101,101)
            gateway=Gateway()
            executor=ToolExecutor(gateway,repo,Settings(project_ids=[5]))
            result=await executor.execute('pause_task', {'task_id':391},101,101,5)
            self.assertEqual(result['state'],'CONFIRMATION_REQUIRED')
            self.assertTrue(all(action in {'observer_task_progress','engineering_status'} for action,_ in gateway.calls))
            await executor.confirm(result['confirmation_id'],101,101)
            self.assertEqual(gateway.calls[-1][0],'engineering_control')
            with self.assertRaises(ValueError): await executor.confirm(result['confirmation_id'],101,101)

    async def test_changed_task_rejects_confirmation_before_gateway_write(self):
        from app.tools import ToolExecutor
        from app.storage import Repository
        from app.config import Settings
        class Gateway:
            version=1
            calls=[]
            async def command(self, action,args,project_id,idempotency_key=None):
                self.calls.append(action)
                if action=='engineering_status':return {'control':{'state_revision':3}}
                return {'task_id':391,'project_id':project_id,'lock_version':self.version}
        with tempfile.TemporaryDirectory() as directory:
            repo=Repository(Path(directory)/'x.sqlite')
            code=repo.create_pairing(101,[5]);repo.pair(code,101,101)
            gateway=Gateway();executor=ToolExecutor(gateway,repo,Settings(project_ids=[5]))
            result=await executor.execute('pause_task',{'task_id':391},101,101,5)
            gateway.version=2
            with self.assertRaisesRegex(ValueError,'STATE_CHANGED'):
                await executor.confirm(result['confirmation_id'],101,101)
            self.assertNotIn('engineering_control',gateway.calls)


if __name__ == '__main__': unittest.main()

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


class EngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_503_retries_once_and_counts_every_attempt(self):
        import json
        from unittest.mock import AsyncMock,patch
        from app.engine import GeminiBrain
        from app.storage import Repository
        from app.config import Settings
        class Unavailable(Exception):code=503
        class Models:
            calls=0
            async def generate_content(self,**kwargs):
                self.calls+=1
                if self.calls==1:raise Unavailable('temporary')
                return SimpleNamespace(model_version='gemini-3.5-flash-lite',candidates=[],function_calls=[],usage_metadata=None)
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');models=Models()
            brain=GeminiBrain(Settings(gemini_api_key='key',provider_data_consent=True),repo)
            brain.client=SimpleNamespace(aio=SimpleNamespace(models=models))
            with patch('app.engine.asyncio.sleep',new_callable=AsyncMock):await brain.generate([],[])
            self.assertEqual(models.calls,2)
            with repo.connect() as db:
                self.assertEqual(db.execute('SELECT calls FROM model_budget').fetchone()[0],2)
                self.assertEqual(db.execute('SELECT count(*) FROM command_audit').fetchone()[0],2)
    async def test_exact_task_id_resolves_only_across_paired_allowed_projects(self):
        from app.engine import Commander
        from app.gateway import GatewayError
        from app.storage import Repository
        from app.config import Settings
        class Tools:
            projects=[]
            async def execute(self,name,args,user,chat,project):
                self.projects.append(project)
                if project==5:raise GatewayError('GATEWAY_HTTP_403 WRONG_PROJECT')
                return {'task_id':391,'project_id':6,'workflow_status':'COMPLETED','acceptance_status':'AWAITING_OWNER_APPROVAL'}
        class Brain:
            async def generate(self,*args):return {'calls':[],'text':'Task thuộc project6, đang chờ nghiệm thu.'}
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');code=repo.create_pairing(101,[5,6]);repo.pair(code,101,101)
            tools=Tools();commander=Commander(Settings(project_ids=[5,6]),repo,tools,Brain())
            result=await commander.answer(101,101,'Task #391 tới đâu?',5)
            self.assertIn('project6',result['text'])
            self.assertEqual(tools.projects,[5,6]);self.assertEqual(repo.memory(101,101)['current_project_id'],6)
            code=repo.create_pairing(101,[5]);repo.pair(code,101,101);tools.projects.clear()
            await commander.answer(101,101,'Task #391 tới đâu?',5)
            self.assertEqual(tools.projects,[5])
    async def test_function_call_ids_are_preserved_for_google_manual_calling(self):
        from app.engine import Commander
        from app.storage import Repository
        from app.config import Settings
        class Tools:
            async def execute(self,*args):return {'state':'VERIFIED'}
        class Brain:
            calls=0
            async def generate(self,contents,functions):
                self.calls+=1
                if self.calls==1:return {'content':{'role':'model','parts':[]},'text':'',
                    'calls':[{'id':'call-1','name':'get_system_health','args':{}}]}
                assert contents[-1]['parts'][0]['function_response']['id']=='call-1'
                return {'calls':[],'text':'Đã kiểm tra.'}
        with tempfile.TemporaryDirectory() as tmp:
            commander=Commander(Settings(project_ids=[6]),Repository(Path(tmp)/'db'),Tools(),Brain())
            result=await commander.answer(1,1,'Kiểm tra hệ thống',6)
            self.assertEqual(result['text'],'Đã kiểm tra.')
    async def test_context_is_bounded_and_incoming_secrets_are_not_persisted(self):
        import json
        from app.engine import Commander
        from app.storage import Repository
        from app.config import Settings
        class Tools:
            async def execute(self,*args):return {'task_id':391,'workflow_status':'BLOCKED','logs':'x'*100000}
        class Brain:
            sizes=[]
            async def generate(self,contents,functions):
                self.sizes.append(len(json.dumps(contents)))
                return {'calls':[],'text':'Đã đọc nguồn thật.'}
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');brain=Brain()
            commander=Commander(Settings(project_ids=[6]),repo,Tools(),brain)
            await commander.answer(1,1,'Task #391 api_key=do-not-store',6)
            self.assertNotIn('do-not-store',json.dumps(repo.memory(1,1)))
            self.assertLess(brain.sizes[0],30000)
    async def test_provider_usage_receipt_has_counts_and_no_prompt_or_key(self):
        import json
        from app.engine import GeminiBrain
        from app.storage import Repository
        from app.config import Settings
        class Models:
            async def generate_content(self,**kwargs):
                return SimpleNamespace(model_version='gemini-3.5-flash-lite',candidates=[],function_calls=[],
                    usage_metadata=SimpleNamespace(prompt_token_count=3,candidates_token_count=2,total_token_count=5))
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');brain=GeminiBrain(Settings(gemini_api_key='secret-key',provider_data_consent=True),repo)
            brain.client=SimpleNamespace(aio=SimpleNamespace(models=Models()))
            await brain.generate([{'role':'user','parts':[{'text':'secret-prompt'}]}],[])
            with repo.connect() as db:
                row=db.execute("SELECT document FROM command_audit ORDER BY created DESC LIMIT 1").fetchone()
            self.assertIsNotNone(row)
            receipt=json.loads(row[0]);self.assertEqual(receipt['input_tokens'],3)
            self.assertEqual(receipt['resolved_model_version'],'gemini-3.5-flash-lite')
            self.assertEqual(receipt['output_tokens'],2)
            self.assertIn('latency_seconds',receipt)
            self.assertNotIn('secret',row[0])
    async def test_bound_function_calls_and_memory_live_grounding(self):
        from app.engine import Commander
        from app.storage import Repository
        from app.config import Settings
        class Tools:
            calls=[]
            async def execute(self,name,args,*identity):
                self.calls.append(name)
                return {'task_id':391,'workflow_status':'BLOCKED','freshness':{'status':'FRESH'}}
        class Brain:
            calls=0
            async def generate(self,contents,functions):
                self.calls+=1
                return {'content':{'role':'model','parts':[{'function_call':{'name':'get_task_progress','args':{'task_id':391}}}]},
                        'calls':[{'name':'get_task_progress','args':{'task_id':391}}],'text':''}
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db.sqlite');tools=Tools();brain=Brain()
            engine=Commander(Settings(project_ids=[5],max_tool_rounds=2,max_tool_calls=2),repo,tools,brain)
            result=await engine.answer(1,1,'Task #391 tới đâu?',5)
            self.assertIn('giới hạn',result['text'])
            self.assertLessEqual(brain.calls,2)
            self.assertIn('get_task_progress',tools.calls)
            self.assertEqual(repo.memory(1,1)['current_task_id'],391)

    async def test_model_error_not_leaked_and_no_provider_fallback(self):
        from app.engine import Commander
        from app.storage import Repository
        from app.config import Settings
        class Tools:
            async def execute(self,*args):return {'state':'UNKNOWN'}
        class Brain:
            async def generate(self,*args):raise RuntimeError('secret api key TOKEN')
        with tempfile.TemporaryDirectory() as tmp:
            engine=Commander(Settings(project_ids=[5]),Repository(Path(tmp)/'db'),Tools(),Brain())
            result=await engine.answer(1,1,'Chào',5)
            self.assertIn('chưa xác minh',result['text'])
            self.assertNotIn('TOKEN',result['text'])

    async def test_confirmation_id_generated_by_tools_not_model_text(self):
        from app.engine import Commander
        from app.storage import Repository
        from app.config import Settings
        class Tools:
            async def execute(self,name,args,*identity):
                return {'state':'CONFIRMATION_REQUIRED','confirmation_id':'actual-nonce','tool':name}
        class Brain:
            async def generate(self,*args):
                return {'content':{},'calls':[{'name':'pause_task','args':{'task_id':391}}],'text':''}
        with tempfile.TemporaryDirectory() as tmp:
            engine=Commander(Settings(project_ids=[5]),Repository(Path(tmp)/'db'),Tools(),Brain())
            result=await engine.answer(1,1,'Tạm dừng Task #391',5)
            self.assertEqual(result['confirmation_id'],'actual-nonce')


if __name__=='__main__':unittest.main()

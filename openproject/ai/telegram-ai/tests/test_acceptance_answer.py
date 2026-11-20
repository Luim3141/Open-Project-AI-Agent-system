import tempfile
import unittest
from pathlib import Path
from app.config import Settings
from app.engine import Commander
from app.storage import Repository


class AcceptanceAnswerTests(unittest.IsolatedAsyncioTestCase):
    async def answer(self,snapshot,model_text,question='Vậy đã DONE chưa?'):
        class Tools:
            async def execute(self,*args):return snapshot
        class Brain:
            async def generate(self,*args):return {'calls':[],'text':model_text}
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'db');repo.save_memory(1,1,{'current_task_id':snapshot['task_id'],'recent_messages':[]})
            result=await Commander(Settings(project_ids=[6]),repo,Tools(),Brain()).answer(1,1,question,6)
            self.assertEqual(repo.memory(1,1)['recent_messages'][-1]['text'],result['text'])
            return result['text']

    def snapshot(self,**changes):
        return {'task_id':398,'project_id':6,'workflow_status':'COMPLETED','business_status':'READY FOR RELEASE',
                'acceptance_status':'AWAITING_OWNER_APPROVAL','latest_run_id':'recorded-run','source_conflicts':[],**changes}

    async def test_live_398_unsafe_done_conclusion_is_not_sent_or_remembered(self):
        # Actual live message30 wording, replayed at Commander output boundary.
        answer=await self.answer(self.snapshot(),'Vì vậy task đã làm xong (DONE), hiện chỉ còn chờ approval từ owner.')
        self.assertIn('chưa',answer.lower());self.assertNotIn('đã làm xong (DONE)',answer)
        self.assertIn('AWAITING_OWNER_APPROVAL',answer);self.assertIn('398',answer)

    async def test_done_question_does_not_rely_on_models_conclusion(self):
        answer=await self.answer(self.snapshot(),'Đã hoàn thành toàn bộ và đóng công việc.')
        self.assertIn('chưa',answer.lower());self.assertIn('READY FOR RELEASE',answer)

    async def test_only_canonical_native_done_and_full_acceptance_prove_done(self):
        answer=await self.answer(self.snapshot(task_id=397,business_status='DONE',acceptance_status='FULLY_COMPLETED'),'Chưa xong.')
        self.assertIn('đã',answer.lower());self.assertIn('FULLY_COMPLETED',answer)
        for changed in [{'business_status':'READY FOR RELEASE'},{'source_conflicts':['mismatch']},{'acceptance_status':'NOT_RECORDED'}]:
            answer=await self.answer({**self.snapshot(business_status='DONE',acceptance_status='FULLY_COMPLETED'),**changed},'DONE')
            self.assertIn('chưa',answer.lower())

    async def test_dev_and_qa_evidence_answers_remain_specific(self):
        answer=await self.answer(self.snapshot(),'QA PASS, exit_code0.','QA có pass không?')
        self.assertEqual(answer,'QA PASS, exit_code0.')

    async def test_unprompted_done_claim_is_grounded_too(self):
        answer=await self.answer(self.snapshot(),'Task đã DONE.','Task #398 thế nào?')
        self.assertIn('chưa',answer.lower())

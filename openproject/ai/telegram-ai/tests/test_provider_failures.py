import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.config import Settings
from app.engine import Commander, GeminiBrain
from app.storage import Repository


class ProviderFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_429_and_nonretryable_error_use_one_attempt_and_one_budget_reservation(self):
        for status in (429, 400, 401):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as folder:
                repo = Repository(Path(folder) / 'db')
                error = type('ProviderError', (Exception,), {'code': status})('rejected')
                generate = AsyncMock(side_effect=error)
                brain = GeminiBrain(Settings(gemini_api_key='test', provider_data_consent=True), repo)
                brain.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
                with patch('app.engine.asyncio.sleep', new_callable=AsyncMock) as sleep:
                    with self.assertRaises(type(error)):
                        await brain.generate([], [])
                self.assertEqual(generate.await_count, 1)
                sleep.assert_not_awaited()
                with repo.connect() as db:
                    self.assertEqual(db.execute('SELECT calls FROM model_budget').fetchone()[0], 1)
                    audit = json.loads(db.execute('SELECT document FROM command_audit').fetchone()[0])
                self.assertEqual(audit['http_status'], status)

    async def test_repeated_5xx_is_bounded_to_two_provider_attempts(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Repository(Path(folder) / 'db')
            error = type('Unavailable', (Exception,), {'code': 503})('temporary')
            generate = AsyncMock(side_effect=error)
            brain = GeminiBrain(Settings(gemini_api_key='test', provider_data_consent=True), repo)
            brain.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
            with patch('app.engine.asyncio.sleep', new_callable=AsyncMock) as sleep:
                with self.assertRaises(type(error)):
                    await brain.generate([], [])
            self.assertEqual(generate.await_count, 2)
            sleep.assert_awaited_once_with(2)
            with repo.connect() as db:
                self.assertEqual(db.execute('SELECT calls FROM model_budget').fetchone()[0], 2)

    async def test_model_routing_mismatch_locks_the_brain_without_another_request(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Repository(Path(folder) / 'db')
            generate = AsyncMock(return_value=SimpleNamespace(model_version='gemini-other', usage_metadata=None))
            brain = GeminiBrain(Settings(gemini_api_key='test', provider_data_consent=True), repo)
            brain.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
            with self.assertRaisesRegex(ValueError, 'MODEL_ROUTING_MISMATCH'):
                await brain.generate([], [])
            with self.assertRaisesRegex(ValueError, 'MODEL_ROUTING_MISMATCH_LOCKED'):
                await brain.generate([], [])
            self.assertEqual(generate.await_count, 1)

    async def test_exhausted_local_budget_prevents_provider_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Repository(Path(folder) / 'db'); repo.reserve_model_call(1)
            generate = AsyncMock()
            brain = GeminiBrain(Settings(gemini_api_key='test', provider_data_consent=True, max_daily_model_calls=1), repo)
            brain.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
            with self.assertRaisesRegex(ValueError, 'BUDGET_EXHAUSTED'):
                await brain.generate([], [])
            generate.assert_not_awaited()

    async def test_tool_timeout_and_invalid_call_return_unverified_results_to_model(self):
        for failure in (TimeoutError(), ValueError('TOOL_NOT_ALLOWED')):
            with self.subTest(error=type(failure).__name__), tempfile.TemporaryDirectory() as folder:
                tools = SimpleNamespace(execute=AsyncMock(side_effect=failure))
                async def generate(contents, functions):
                    if len(contents) == 1:
                        return {'content': {'role': 'model', 'parts': []}, 'calls': [{'name': 'get_system_health', 'args': {}}]}
                    value = contents[-1]['parts'][0]['function_response']['response']['result']
                    self.assertEqual(value['state'], 'NOT_VERIFIED')
                    return {'calls': [], 'text': 'Chưa xác minh được dữ liệu.'}
                brain = SimpleNamespace(generate=generate)
                result = await Commander(Settings(project_ids=[6]), Repository(Path(folder) / 'db'), tools, brain).answer(1, 1, 'Chào', 6)
                self.assertIn('Chưa xác minh', result['text'])
                tools.execute.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()

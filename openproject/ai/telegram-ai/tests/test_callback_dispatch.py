import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
from aiogram import Bot
from aiogram.types import Update

from app.config import Settings
from app.engine import Commander
from app.gateway import GatewayClient
from app.handlers import create_dispatcher
from app.storage import Repository
from app.tools import ToolExecutor


class CallbackDispatchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder = tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.repo = Repository(Path(self.folder.name) / 'test.sqlite')
        self.repo.pair(self.repo.create_pairing(10, [6]), 10, 10)
        self.settings = Settings(project_ids=[6], service_credential='fixture')
        self.calls = []; self.revision = 7; self.write_status = 200
        self.gateway = GatewayClient(self.settings)
        await self.gateway.client.aclose()
        def transport(request):
            self.assertEqual(request.url.path, '/api/v1/commands')
            self.assertEqual(request.headers['Authorization'], 'Bearer fixture')
            body = json.loads(request.content); self.calls.append(body)
            self.assertEqual(body['project_id'], 6)
            if body['action'] == 'observer_task_progress':
                result = {'task_id': 400, 'project_id': 6, 'version': 1, 'revision': 'unchanged-task'}
            elif body['action'] == 'engineering_status':
                result = {'control': {'state_revision': self.revision, 'desired_mode': 'OFF'}}
            elif body['action'] == 'engineering_control':
                self.assertEqual(body['arguments'], {'mode': 'PAUSED', 'expected_revision': 7})
                self.assertTrue(body['idempotency_key'].startswith('tg:'))
                if self.write_status != 200:
                    return httpx.Response(self.write_status, json={'error': 'MAINTENANCE'})
                result = {'accepted': True, 'command_id': 'fixture-receipt', 'current_state': 'PAUSED'}
            else:
                raise AssertionError(body['action'])
            return httpx.Response(200, json={'result': result, 'correlation_id': 'fixture-correlation'})
        self.gateway.client = httpx.AsyncClient(base_url=self.settings.gateway_url,
            transport=httpx.MockTransport(transport), trust_env=False)
        self.addAsyncCleanup(self.gateway.close)
        async def generate(*args):
            return {'calls': [{'name': 'pause_task', 'args': {'task_id': 400}}], 'content': {}}
        self.brain = SimpleNamespace(generate=AsyncMock(side_effect=generate))
        engine = Commander(self.settings, self.repo, ToolExecutor(self.gateway, self.repo, self.settings), self.brain)
        self.dispatcher = create_dispatcher(self.repo, self.settings, self.gateway, engine, {})
        self.bot = Bot('123456:' + 'x' * 35)
        self.bot.session = AsyncMock(return_value=SimpleNamespace(message_id=100))

    async def propose_pause(self):
        await self.dispatcher.feed_update(self.bot, Update.model_validate({'update_id': 1, 'message': {
            'message_id': 1, 'date': int(time.time()), 'chat': {'id': 10, 'type': 'private'},
            'from': {'id': 10, 'is_bot': False, 'first_name': 'Owner'}, 'text': 'Tạm dừng Task #400'}}))
        self.assertEqual(self.writes(), [])
        return self.repo.memory(10, 10)['pending_confirmation']

    def writes(self):
        return [v for v in self.calls if v['action'] == 'engineering_control']

    async def callback(self, nonce, update_id, user=10, action='confirm'):
        await self.dispatcher.feed_update(self.bot, Update.model_validate({'update_id': update_id, 'callback_query': {
            'id': str(update_id), 'from': {'id': user, 'is_bot': False, 'first_name': 'Owner'},
            'chat_instance': 'fixture', 'data': action + ':' + nonce,
            'message': {'message_id': 100, 'date': int(time.time()), 'chat': {'id': 10, 'type': 'private'},
                'from': {'id': 123456, 'is_bot': True, 'first_name': 'Bot'}, 'text': 'Confirm pause'}}}))

    async def test_dispatcher_to_http_adapter_requires_click_and_never_replays_consumed_callback(self):
        nonce = await self.propose_pause()
        await self.callback(nonce, 2)
        self.assertEqual(len(self.writes()), 1)
        await self.callback(nonce, 3)
        self.assertEqual(len(self.writes()), 1)
        with self.repo.connect() as db:
            state = db.execute('SELECT state FROM confirmations WHERE id=?', (nonce,)).fetchone()[0]
        self.assertEqual(state, 'DONE')

    async def test_changed_control_and_wrong_user_deny_before_http_write(self):
        nonce = await self.propose_pause()
        await self.callback(nonce, 2, user=11)
        self.assertEqual(self.writes(), [])
        self.revision = 8
        await self.callback(nonce, 3)
        self.assertEqual(self.writes(), [])

    async def test_backend_503_does_not_cause_a_second_business_request(self):
        nonce = await self.propose_pause(); self.write_status = 503
        await self.callback(nonce, 2)
        await self.callback(nonce, 3)
        self.assertEqual(len(self.writes()), 1)

    async def test_expired_confirmation_never_reaches_http_write(self):
        nonce = await self.propose_pause()
        with self.repo.connect() as db:
            db.execute('UPDATE confirmations SET expires=0 WHERE id=?', (nonce,))
        await self.callback(nonce, 2)
        self.assertEqual(self.writes(), [])

    async def test_start_private_auth_and_revoked_user_do_not_invoke_model_or_gateway(self):
        async def message(update, user, text, chat_type='private'):
            chat_id=user if chat_type=='private' else -100
            await self.dispatcher.feed_update(self.bot, Update.model_validate({'update_id':update,'message':{
                'message_id':update,'date':int(time.time()),'chat':{'id':chat_id,'type':chat_type},
                'from':{'id':user,'is_bot':False,'first_name':'Owner'},'text':text}}))
        await message(1,11,'/start')
        self.assertIn('Numeric User ID: 11',self.bot.session.call_args.args[1].text)
        await message(2,10,'/start')
        self.assertIn('sẵn sàng',self.bot.session.call_args.args[1].text)
        sent=self.bot.session.await_count
        await message(3,10,'/start','supergroup')
        self.assertEqual(self.bot.session.await_count,sent)
        await message(4,11,'Task #400 đang ở đâu?')
        self.repo.revoke(10)
        await message(5,10,'/status')
        self.brain.generate.assert_not_awaited()
        self.assertEqual(self.calls,[])


if __name__ == '__main__':
    unittest.main()

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock
from types import SimpleNamespace
import json

from aiogram import Bot
from aiogram.types import Update

from app.config import Settings
from app.handlers import create_dispatcher
from app.storage import Repository


class ReplyDispatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_aiogram_reply_field_overrides_older_conversation_context(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Repository(Path(folder) / 'test.sqlite')
            repo.pair(repo.create_pairing(10, [5, 6]), 10, 10)
            repo.save_memory(10, 10, {'current_project_id': 6, 'current_task_id': 391})
            repo.record_notification(10, 16, 397, 6, 'run397')
            commander = type('Commander', (), {})()
            commander.answer = AsyncMock(return_value={'text': 'Verified reply'})
            dispatcher = create_dispatcher(repo, Settings(project_ids=[5, 6]), None, commander, {})
            bot = Bot('123456:' + 'x' * 35)
            bot.session = AsyncMock(return_value=SimpleNamespace(message_id=18))
            now = int(time.time())
            update = Update.model_validate({'update_id': 1, 'message': {
                'message_id': 17, 'date': now, 'chat': {'id': 10, 'type': 'private'},
                'from': {'id': 10, 'is_bot': False, 'first_name': 'Owner'},
                'text': 'Dev đã làm gì ở Task này?',
                'reply_to_message': {'message_id': 16, 'date': now - 10,
                    'chat': {'id': 10, 'type': 'private'},
                    'from': {'id': 123456, 'is_bot': True, 'first_name': 'Commander'},
                    'text': 'QLDAPM Task #397 completed'}}})
            await dispatcher.feed_update(bot, update)
            commander.answer.assert_awaited_once()
            self.assertEqual(commander.answer.call_args.kwargs['reply_context'],
                {'task_id': 397, 'project_id': 6, 'run_id': 'run397'})
            self.assertEqual(commander.answer.call_args.args[3], 6)
            with repo.connect() as db:
                receipts = [json.loads(r[0]) for r in db.execute('SELECT document FROM command_audit ORDER BY created')]
            incoming = next(r for r in receipts if r.get('event') == 'INCOMING_CONTEXT')
            self.assertEqual(incoming['message_id'], 17)
            self.assertEqual(incoming['reply_to_message_id'], 16)
            self.assertEqual(incoming['notification_context']['task_id'], 397)
            sent = next(r for r in receipts if r.get('event') == 'BOT_REPLY_SENT')
            self.assertEqual(sent['message_id'], 18)
            self.assertEqual(sent['in_reply_to_message_id'], 17)


if __name__ == '__main__':
    unittest.main()

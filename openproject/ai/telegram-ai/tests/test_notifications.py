import contextlib
import json
import time
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


class Repository:
    def __init__(self, root):
        self.path = Path(root) / 'memory.sqlite'
        self.people = [{'user_id': 10, 'chat_id': 10, 'project_ids': [6], 'notifications': True, 'paired_at': 100}]
        self.context = {}

    @contextlib.contextmanager
    def connect(self):
        db = sqlite3.connect(self.path); db.row_factory = sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def recipients(self): return self.people

    def record_notification(self, chat_id, message_id, task_id, project_id, run_id=None):
        self.context[(chat_id, message_id)] = {'task_id': task_id, 'project_id': project_id, 'run_id': run_id}


class NotificationOutboxTests(unittest.TestCase):
    def setUp(self):
        from app.notifications import Outbox
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Repository(self.temp.name); self.outbox = Outbox(self.repo)
        self.event = {'event_id': 'a'*64, 'event_type': 'TASK_BLOCKED', 'task_id': 400, 'project_id': 6,
                      'workflow_run_id': 'run-1', 'source_record_id': 'receipt-1', 'timestamp': 101}

    def enqueue(self): return self.outbox.enqueue(self.event, self.repo.people[0], now=102)

    def test_event_recipient_unique_survives_reopen_and_only_message_ack_marks_sent(self):
        self.enqueue(); self.enqueue()
        from app.notifications import Outbox
        outbox = Outbox(self.repo)
        claimed = outbox.claim(now=103)
        self.assertEqual(outbox.status()['PROCESSING'], 1)
        self.assertIsNone(outbox.claim(now=104))
        outbox.validate(claimed['notification_id'], claimed['lease'], now=104)
        with self.assertRaises(PermissionError): outbox.validate(claimed['notification_id'], claimed['lease'], now=104)
        with self.assertRaises(ValueError): outbox.ack(claimed['notification_id'], claimed['lease'], 0, 10, now=105)
        self.assertEqual(outbox.status()['PROCESSING'], 1)
        ack = outbox.ack(claimed['notification_id'], claimed['lease'], 88, 10, now=105)
        self.assertEqual(ack['status'], 'SENT')
        self.assertEqual(self.repo.context[(10, 88)]['task_id'], 400)
        self.assertEqual(outbox.ack(claimed['notification_id'], claimed['lease'], 88, 10, now=106), ack)

    def test_private_paired_recipient_and_preferences_and_historical_floor(self):
        for field, value in [('notifications', False), ('project_ids', [5]), ('chat_id', -10), ('paired_at', 200)]:
            person = {**self.repo.people[0], field: value}
            self.assertFalse(self.outbox.enqueue(self.event, person, now=102))
        self.assertEqual(self.outbox.status(), {})

    def test_unpaired_or_revoked_recipient_cannot_claim_or_ack(self):
        self.enqueue(); claimed = self.outbox.claim(now=103)
        self.repo.people = []
        with self.assertRaises(PermissionError):
            self.outbox.validate(claimed['notification_id'], claimed['lease'], now=104)
        self.outbox.fail(claimed['notification_id'], claimed['lease'], now=104)
        self.assertIsNone(self.outbox.claim(now=200))
        self.assertEqual(self.outbox.status()['CANCELLED'], 1)

    def test_expired_lease_retries_bounded_and_old_callback_cannot_send(self):
        self.enqueue(); claimed = self.outbox.claim(now=103)
        with self.assertRaises(PermissionError): self.outbox.validate(claimed['notification_id'], claimed['lease'], now=1000)
        next_claim = self.outbox.claim(now=1000)
        self.assertNotEqual(claimed['lease'], next_claim['lease'])
        with self.assertRaises(PermissionError):
            self.outbox.ack(claimed['notification_id'], claimed['lease'], 99, 10, now=1001)
        for tick in range(1, 8):
            self.outbox.fail(next_claim['notification_id'], next_claim['lease'], now=1000*tick)
            next_claim = self.outbox.claim(now=1000*(tick+1))
            if next_claim is None: break
        self.assertEqual(self.outbox.status()['FAILED'], 1)

    def test_payload_unknown_fields_and_callback_cross_chat_denied(self):
        with self.assertRaises(ValueError):
            self.outbox.enqueue({**self.event, 'token': 'SECRET'}, self.repo.people[0], now=102)
        self.enqueue(); claimed = self.outbox.claim(now=103)
        self.outbox.validate(claimed['notification_id'], claimed['lease'], now=103)
        with self.assertRaises(PermissionError):
            self.outbox.ack(claimed['notification_id'], claimed['lease'], 88, 11, now=104)
        self.assertNotIn('SECRET', json.dumps(claimed))


class NotificationHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def test_delivery_check_is_explicit_and_never_claims_task_completion(self):
        event={**self.event,'event_id':'test-delivery','event_type':'DELIVERY_TEST','timestamp':time.time()}
        self.assertTrue(self.outbox.enqueue(event,self.repo.people[0]))
        with self.repo.connect() as db:db.execute("UPDATE telegram_notification_outbox SET status='CANCELLED' WHERE event_id=?",(self.event['event_id'],))
        claimed=self.outbox.claim()
        data=self.outbox.validate(claimed['notification_id'],claimed['lease'])
        self.assertIn('KIỂM THỬ',data['text'])
        self.assertNotIn('TASK HOÀN THÀNH',data['text'])
    async def asyncSetUp(self):
        from aiohttp.test_utils import TestClient, TestServer
        from app.notifications import Outbox, create_app
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Repository(self.temp.name); self.repo.people[0]['paired_at'] = 0
        key_file = Path(self.temp.name) / 'notification.key'; key_file.write_text('k'*64)
        self.outbox = Outbox(self.repo)
        self.event = {'event_id': 'a'*64, 'event_type': 'TASK_BLOCKED', 'task_id': 400, 'project_id': 6,
                      'workflow_run_id': 'run-1', 'source_record_id': 'receipt-1', 'timestamp': 101}
        self.outbox.enqueue(self.event, self.repo.people[0]); self.claimed = self.outbox.claim()
        settings = SimpleNamespace(internal_secret_file=key_file, notifications_enabled=False)
        class Gateway:
            denied = False
            snapshot = {'task_id': 400, 'project_id': 6, 'acceptance_status': 'COMPLETED'}
            async def command(this, action, args, project):
                if this.denied: raise PermissionError('NATIVE_SCOPE_REVOKED')
                return this.snapshot
        self.gateway = Gateway()
        self.client = TestClient(TestServer(create_app(self.repo, settings, self.gateway)))
        await self.client.start_server(); self.addAsyncCleanup(self.client.close)
        self.headers = {'X-QLDAPM-Notification-Key': 'k'*64}
        self.body = {k: self.claimed[k] for k in ('notification_id', 'lease')}

    async def test_http_auth_one_use_send_ack_and_reply_context(self):
        response = await self.client.post('/internal/notifications/validate', json=self.body)
        self.assertEqual(response.status, 403)
        response = await self.client.post('/internal/notifications/validate', json=self.body, headers=self.headers)
        self.assertEqual(response.status, 200); self.assertEqual((await response.json())['chat_id'], 10)
        replay = await self.client.post('/internal/notifications/validate', json=self.body, headers=self.headers)
        self.assertEqual(replay.status, 403)
        ack = {**self.body, 'message_id': 88, 'chat_id': 10}
        response = await self.client.post('/internal/notifications/ack', json=ack, headers=self.headers)
        self.assertEqual(response.status, 200); self.assertEqual((await response.json())['status'], 'SENT')
        self.assertEqual(self.repo.context[(10, 88)]['task_id'], 400)

    async def test_http_ack_revoked_pairing_and_extra_fields_denied(self):
        response = await self.client.post('/internal/notifications/validate', json={**self.body, 'chat_id': 10}, headers=self.headers)
        self.assertEqual(response.status, 403)
        response = await self.client.post('/internal/notifications/validate', json=self.body, headers=self.headers)
        self.assertEqual(response.status, 200)
        self.repo.people = []
        response = await self.client.post('/internal/notifications/ack',
            json={**self.body, 'message_id': 88, 'chat_id': 10}, headers=self.headers)
        self.assertEqual(response.status, 403)
        self.assertEqual(self.outbox.status()['PROCESSING'], 1)

    async def test_native_scope_revocation_after_enqueue_denies_delivery_without_consuming_authorization(self):
        self.gateway.denied = True
        response = await self.client.post('/internal/notifications/validate', json=self.body, headers=self.headers)
        self.assertEqual(response.status, 403)
        self.gateway.denied = False
        response = await self.client.post('/internal/notifications/validate', json=self.body, headers=self.headers)
        self.assertEqual(response.status, 200)

    async def test_current_native_project_and_completion_are_rechecked_before_send(self):
        self.gateway.snapshot = {'task_id': 400, 'project_id': 5, 'acceptance_status': 'COMPLETED'}
        response = await self.client.post('/internal/notifications/validate', json=self.body, headers=self.headers)
        self.assertEqual(response.status, 403)
        event = {**self.event, 'event_type': 'TASK_COMPLETED'}
        with self.repo.connect() as db:
            db.execute('UPDATE telegram_notification_outbox SET payload=? WHERE id=?', (json.dumps(event), self.body['notification_id']))
        self.gateway.snapshot = {'task_id': 400, 'project_id': 6, 'acceptance_status': 'AWAITING_OWNER_APPROVAL'}
        response = await self.client.post('/internal/notifications/validate', json=self.body, headers=self.headers)
        self.assertEqual(response.status, 403)


if __name__ == '__main__': unittest.main()

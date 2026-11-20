import concurrent.futures
import hashlib
import hmac
import json
import time
import unittest
import uuid
from unittest.mock import patch

from starlette.testclient import TestClient
from gateway.app import create_app
from gateway.automation import COMMAND_PATH, HEADER, SIGNATURE_HEADER, signing_key, signing_message
from gateway.store import Store
from tests import test_automation_auth as fixture


class AutomationCommandTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.AutomationAuthTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.client, self.store, self.root = self.fixture.client, self.fixture.store, self.fixture.root

    def payload(self, **changes):
        return {'version': 1, 'kind': 'status', 'request_key': str(uuid.uuid4()), 'nonce': str(uuid.uuid4()),
                'issued_at': int(time.time()), **changes}

    def headers(self, document):
        signature = hmac.new(signing_key(self.fixture.key).encode('ascii'), signing_message(document), hashlib.sha256).hexdigest()
        return {HEADER: self.fixture.key, SIGNATURE_HEADER: signature}

    def post(self, document, headers=None):
        return self.client.post(COMMAND_PATH, json=document, headers=headers or self.headers(document))

    def test_duplicate_and_new_nonce_return_exact_durable_receipt_after_app_reopen(self):
        document = self.payload()
        with patch.object(self.fixture.service, 'execute_actor', side_effect=AssertionError('NO_HUMAN_IMPERSONATION')), \
                patch.object(self.fixture.service.gemini, 'sdk_client', side_effect=AssertionError('NO_PROVIDER')):
            first = self.post(document)
            self.assertEqual(first.status_code, 200)
            self.assertEqual(self.post(document).json(), first.json())
            self.assertEqual(self.post({**document, 'nonce': str(uuid.uuid4())}).json(), first.json())
        self.fixture.service.store = Store(self.root)
        with TestClient(create_app(self.root, self.fixture.service)) as reopened:
            response = reopened.post(COMMAND_PATH, json=document, headers=self.headers(document))
            self.assertEqual(response.json(), first.json())
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 1)
            self.assertEqual(db.execute('select count(*) from automation_nonces').fetchone()[0], 2)
            self.assertEqual(db.execute("select count(*) from audit where action='automation_command'").fetchone()[0], 1)
            self.assertEqual(db.execute('select count(*) from ui_nonces').fetchone()[0], 0)
            self.assertEqual(db.execute('select count(*) from ai_queue').fetchone()[0], 0)

    def test_concurrent_duplicates_create_one_run_and_one_accepted_audit(self):
        document = self.payload()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: self.post(document), range(12)))
        self.assertEqual({r.status_code for r in responses}, {200})
        self.assertEqual(len({r.json()['result']['run_id'] for r in responses}), 1)
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 1)
            self.assertEqual(db.execute('select count(*) from automation_nonces').fetchone()[0], 1)

    def test_expired_future_missing_invalid_signature_and_tamper_are_denied(self):
        document = self.payload()
        now = int(time.time())
        # Keep the 15-second boundary independent of SQLite/file-system latency.
        with patch('gateway.automation.time.time', return_value=now):
            for value in (self.payload(issued_at=now - 61), self.payload(issued_at=now + 16)):
                self.assertEqual(self.post(value).status_code, 403)
        self.assertEqual(self.post(document, {HEADER: self.fixture.key}).status_code, 403)
        self.assertEqual(self.post(document, {**self.headers(document), SIGNATURE_HEADER: 'b' * 64}).status_code, 403)
        self.assertEqual(self.post({**document, 'request_key': str(uuid.uuid4())}, self.headers(document)).status_code, 403)
        self.assertEqual(self.post(document, {**self.headers(document), HEADER: 'b' * 64}).status_code, 401)
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 0)

    def test_reused_nonce_for_changed_command_or_timestamp_cannot_start_another_run(self):
        document = self.payload()
        first = self.post(document).json()
        self.assertEqual(self.post({**document, 'request_key': str(uuid.uuid4())}).status_code, 403)
        self.assertEqual(self.post({**document, 'issued_at': document['issued_at'] + 1}).status_code, 403)
        self.assertEqual(self.post(document).json(), first)
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 1)

    def test_actor_business_kind_extra_fields_wrong_types_and_unbounded_body_denied(self):
        for changes in ({'kind': 'create_work_package'}, {'actor_id': 7}, {'version': True}, {'issued_at': True},
                        {'nonce': 'x\ninjection'}, {'request_key': '../path'}, {'native_write_allowed': True}):
            document = self.payload(**changes)
            # Invalid schema must be rejected even when a known machine presents some signature.
            response = self.post(document, {HEADER: self.fixture.key, SIGNATURE_HEADER: 'a' * 64})
            self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.post(COMMAND_PATH, content='x' * 8193, headers=self.fixture.headers).status_code, 413)
        self.assertEqual(self.client.get(COMMAND_PATH, headers=self.fixture.headers).status_code, 403)
        self.assertEqual(self.client.post(COMMAND_PATH + '?actor=7', json=self.payload(), headers=self.fixture.headers).status_code, 403)

    def test_expired_nonce_housekeeping_never_deletes_receipts_or_reexecutes_status(self):
        document = self.payload()
        first = self.post(document).json()
        with self.store.connect() as db:
            db.execute('update automation_nonces set expires=0')
        fresh = {**document, 'nonce': str(uuid.uuid4())}
        self.assertEqual(self.post(fresh).json(), first)
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 1)
            self.assertEqual(db.execute('select count(*) from automation_nonces').fetchone()[0], 1)

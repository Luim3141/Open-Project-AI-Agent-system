import hashlib
import hmac
import time
import unittest
import uuid
from unittest.mock import patch

from starlette.testclient import TestClient
from gateway.app import create_app
from gateway.automation import COMMAND_PATH, HEADER, SIGNATURE_HEADER, signing_key, signing_message
from gateway.daily_brief import day
from gateway.native import NativeError
from tests import test_local_queries as fixture


class DailyBriefTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.LocalQueryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store, self.service, self.root, self.state = self.fixture.store, self.fixture.service, self.fixture.root, self.fixture.state
        self.roles = {6: 'BA-PM', 7: 'PM', 8: 'BE', 9: 'FE', 10: 'QA'}
        self.state.roles = dict(self.roles)
        self.state.visible = {6: [1], 7: [1, 2], 8: [2], 9: [], 10: [1, 2]}
        self.service.config.update(users={str(actor): role for actor,role in self.roles.items()}, hosts=['testserver'])
        self.tokens = {actor: self.store.issue_token(actor, role, 'synthetic-native-' + str(actor)) for actor,role in self.roles.items()}
        self.calls, self.deadlines, self.offline, self.denied = [], [], set(), set()
        original = self.service.native_factory
        test = self
        class Native(original):
            def summary(self, actor):
                return test.service.perform(self.identity(actor), self, 'analyze', {})
            def packages(self):
                test.calls.append(self.actor)
                test.deadlines.append(getattr(self, 'deadline', None))
                if self.actor in test.offline:
                    raise NativeError(503, 'OPENPROJECT_UNAVAILABLE')
                if self.actor in test.denied:
                    raise NativeError(403, 'OPENPROJECT_DENIED')
                return super().packages()
        self.service.native_factory = Native
        self.key = 'a' * 64
        (self.root / 'automation.key').write_text(self.key)
        self.dispatch = patch.object(self.service, 'start_dispatcher')
        self.dispatch.start()
        self.addCleanup(self.dispatch.stop)
        # Route tests own their Native reads; the real RAG consumer has separate lifecycle tests.
        self.knowledge_worker = patch.object(self.service, 'start_knowledge_worker')
        self.knowledge_worker.start()
        self.addCleanup(self.knowledge_worker.stop)
        self.client = TestClient(create_app(self.root, self.service))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def command(self, **changes):
        return {'version': 1, 'kind': 'daily_brief', 'request_key': 'daily:' + day(), 'nonce': str(uuid.uuid4()),
                'issued_at': int(time.time()), **changes}

    def post(self, document=None):
        document = document or self.command()
        signature = hmac.new(signing_key(self.key).encode(), signing_message(document), hashlib.sha256).hexdigest()
        return self.client.post(COMMAND_PATH, json=document, headers={HEADER: self.key, SIGNATURE_HEADER: signature})

    def read(self, actor):
        return self.service.execute_actor(actor, {'action': 'analyze', 'arguments': {}})['result']['daily_brief']

    def test_five_scoped_native_snapshots_zero_provider_and_same_day_duplicates_do_not_recollect(self):
        with patch.object(self.service.gemini, 'sdk_client', side_effect=AssertionError('NO_PROVIDER')) as sdk:
            result = self.post()
            self.assertEqual(result.status_code, 200)
            receipt = result.json()['result']
            self.assertEqual((receipt['state'], receipt['ready'], receipt['targets']), ('COMPLETED', 5, 5))
            self.assertEqual(self.calls, sorted(self.roles))
            self.assertTrue(all(time.monotonic()-1 < deadline <= time.monotonic()+25 for deadline in self.deadlines))
            self.assertEqual(self.post().json()['result'], receipt)
            self.assertEqual(len(self.calls), 5)
            for actor in self.roles:
                report = self.read(actor)
                self.assertEqual(report['state'], 'READY')
                self.assertEqual(report['snapshot']['count'], len(self.state.visible[actor]))
                self.assertNotIn('by_assignee', report['snapshot'])
                self.assertFalse(report['model_used'])
            sdk.assert_not_called()
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from daily_briefs').fetchone()[0], 5)
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 1)
            self.assertEqual(db.execute('select count(*) from ai_queue').fetchone()[0], 0)
            self.assertEqual(db.execute('select count(*) from gemini_usage').fetchone()[0], 0)

    def test_changed_visibility_yields_stale_without_snapshot_and_other_actor_project_are_not_exposed(self):
        self.assertEqual(self.post().status_code, 200)
        self.state.visible[7] = [2]
        report = self.read(7)
        self.assertEqual(report['state'], 'STALE')
        self.assertNotIn('snapshot', report)
        self.assertEqual(self.read(8)['snapshot']['count'], 1)
        self.assertIsNone(self.store.daily_brief(7, 99, day()))
        with self.assertRaises(ValueError):
            self.service.execute_actor(7, {'action': 'analyze', 'arguments': {'actor_id': 8}})
        self.state.roles.pop(7)
        with self.assertRaises(PermissionError):
            self.read(7)

    def test_role_revocation_and_native_outage_make_per_actor_empty_failures(self):
        self.state.roles[8] = 'PM'
        self.offline.add(9)
        self.denied.add(10)
        result = self.post().json()['result']
        self.assertEqual((result['status'], result['ready'], result['unavailable']), ('PARTIAL', 2, 3))
        for actor, expected in ((8, 'DENIED'), (9, 'OFFLINE'), (10, 'DENIED')):
            report = self.store.daily_brief(actor, 3, day())
            self.assertEqual(report['state'], expected)
            self.assertNotIn('snapshot', report)
        self.offline.clear()
        self.assertEqual(self.read(9)['state'], 'OFFLINE')
        self.assertNotIn('snapshot', self.read(9))

    def test_caller_actor_date_namespace_and_non_five_user_config_denied_before_outbound(self):
        self.assertEqual(self.post(self.command(actor_id=7)).status_code, 422)
        self.assertEqual(self.post(self.command(request_key='daily:2000-01-01')).status_code, 422)
        self.assertEqual(self.post(self.command(kind='status')).status_code, 422)
        self.service.config['users']['10'] = 'INVALID_ROLE'
        self.assertEqual(self.post().status_code, 403)
        self.assertEqual(self.calls, [])
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0], 0)

    def test_startup_marks_incomplete_collection_failed_and_never_replays_native_reads(self):
        document = self.command()
        receipt, created = self.store.begin_automation(document, project=3)
        self.assertTrue(created)
        with TestClient(create_app(self.root, self.service)) as restarted:
            changed = {**document, 'nonce': str(uuid.uuid4())}
            signature = hmac.new(signing_key(self.key).encode(), signing_message(changed), hashlib.sha256).hexdigest()
            result = restarted.post(COMMAND_PATH, json=changed, headers={HEADER: self.key, SIGNATURE_HEADER: signature}).json()['result']
            self.assertEqual(result['run_id'], receipt['run_id'])
            self.assertEqual(result['state'], 'FAILED')
            self.assertTrue(result['reconcile_required'])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.read(7)['state'], 'MISSING')

    def test_unexpected_failure_cannot_leave_partial_reports_or_retry_collection(self):
        with patch.object(self.store, 'finish_daily_brief', side_effect=RuntimeError('controlled-fixture-failure')):
            with self.assertRaises(RuntimeError):
                self.post()
        self.assertEqual(len(self.calls), 5)
        result = self.post().json()['result']
        self.assertEqual(result['state'], 'FAILED')
        self.assertEqual(len(self.calls), 5)
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from daily_briefs').fetchone()[0], 0)

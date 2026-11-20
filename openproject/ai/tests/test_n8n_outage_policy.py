"""P04-10: Outage, restart, missed schedule, and catch-up policy verification for all n8n workflows."""
import copy
import hashlib
import hmac
import json
import time
import unittest
import uuid
from unittest.mock import patch

from starlette.testclient import TestClient

from gateway.app import create_app
from gateway.automation import (
    COMMAND_PATH,
    HEADER,
    SIGNATURE_HEADER,
    signing_key,
    signing_message,
)
from gateway.daily_brief import day
from gateway.store import Store
from n8n_status_workflow import (
    DAILY_SOURCE,
    DAILY_WORKFLOW_ID,
    ERROR_SOURCE,
    ERROR_WORKFLOW_ID,
    SOURCE,
    WORKFLOW_ID,
)
from tests import test_local_queries as fixture


class MockNativeSummary:
    def __init__(self, count=10):
        self._count = count

    def summary(self, actor_id):
        return {'count': self._count, 'by_status': {'open': self._count}, 'overdue_ids': []}


class OutageAndCatchUpPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.LocalQueryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store, self.service, self.root, self.state = (
            self.fixture.store,
            self.fixture.service,
            self.fixture.root,
            self.fixture.state,
        )
        self.roles = {6: 'BA-PM', 7: 'PM', 8: 'BE', 9: 'FE', 10: 'QA'}
        self.state.roles = dict(self.roles)
        self.state.visible = {6: [1], 7: [1, 2], 8: [2], 9: [], 10: [1, 2]}
        self.service.config.update(
            users={str(actor): role for actor, role in self.roles.items()},
            hosts=['testserver'],
        )
        self.key = 'a' * 64
        (self.root / 'automation.key').write_text(self.key)
        self.dispatch = patch.object(self.service, 'start_dispatcher')
        self.dispatch.start()
        self.addCleanup(self.dispatch.stop)
        self.client = TestClient(create_app(self.root, self.service))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def headers(self, command):
        sig = hmac.new(signing_key(self.key).encode('ascii'), signing_message(command), hashlib.sha256).hexdigest()
        return {HEADER: self.key, SIGNATURE_HEADER: sig}

    def post(self, command):
        return self.client.post(COMMAND_PATH, json=command, headers=self.headers(command))

    # --- 1. Workflow Architecture & Trigger Declarations ---

    def test_workflow_catalog_trigger_and_schedule_declarations(self):
        """Every workflow has a strictly validated trigger model matching its outage role."""
        # 1. Manual status: strictly manual, no schedule, inactive
        manual = json.loads(SOURCE.read_text(encoding='utf-8'))
        self.assertEqual(manual['id'], WORKFLOW_ID)
        self.assertFalse(manual['active'])
        types = {n['name']: n['type'] for n in manual['nodes']}
        self.assertIn('Manual status', types)
        self.assertEqual(types['Manual status'], 'n8n-nodes-base.manualTrigger')
        self.assertNotIn('Daily 09:00', types)
        self.assertNotIn('After startup', types)

        # 2. Daily brief: schedule (09:00 Bangkok) + After startup (init catch-up)
        daily = json.loads(DAILY_SOURCE.read_text(encoding='utf-8'))
        self.assertEqual(daily['id'], DAILY_WORKFLOW_ID)
        daily_types = {n['name']: n['type'] for n in daily['nodes']}
        self.assertEqual(daily_types['Daily 09:00'], 'n8n-nodes-base.scheduleTrigger')
        self.assertEqual(daily_types['After startup'], 'n8n-nodes-base.n8nTrigger')
        self.assertEqual(daily['settings']['timezone'], 'Asia/Bangkok')
        schedule_node = next(n for n in daily['nodes'] if n['name'] == 'Daily 09:00')
        self.assertEqual(
            schedule_node['parameters']['rule']['interval'][0]['expression'],
            '0 0 9 * * *'
        )
        startup_node = next(n for n in daily['nodes'] if n['name'] == 'After startup')
        self.assertEqual(startup_node['parameters']['events'], ['init'])

        # 3. Workflow errors: error trigger only, no schedule, no startup trigger
        error_wf = json.loads(ERROR_SOURCE.read_text(encoding='utf-8'))
        self.assertEqual(error_wf['id'], ERROR_WORKFLOW_ID)
        error_types = {n['name']: n['type'] for n in error_wf['nodes']}
        self.assertEqual(error_types['Workflow error'], 'n8n-nodes-base.errorTrigger')
        self.assertNotIn('Daily 09:00', error_types)
        self.assertNotIn('After startup', error_types)

    # --- 2. Outage Catch-up & Idempotency Rules ---

    def test_missed_schedule_startup_catchup_creates_single_daily_receipt(self):
        """When Docker was off at 09:00 and starts up later, catch-up runs once and succeeds."""
        today = day()
        cmd = {
            'version': 1,
            'kind': 'daily_brief',
            'request_key': 'daily:' + today,
            'nonce': 'n8n:qldapmDailyBrief:startup-catchup-1',
            'issued_at': int(time.time()),
        }
        with patch.object(self.service, 'native_actor', return_value=(MockNativeSummary(15), {'role': 'PM'})):
            resp = self.post(cmd)
            self.assertEqual(resp.status_code, 200)
            result = resp.json()['result']
            self.assertEqual(result['kind'], 'daily_brief')
            self.assertEqual(result['state'], 'COMPLETED')
            self.assertEqual(result['ready'], 5)
            self.assertEqual(result['model_calls'], 0)
            self.assertFalse(result['native_write_allowed'])

    def test_multiple_restarts_on_same_day_return_identical_receipt_without_duplication(self):
        """Repeated Docker container restarts throughout the day trigger After startup but never duplicate."""
        today = day()
        cmd_first = {
            'version': 1,
            'kind': 'daily_brief',
            'request_key': 'daily:' + today,
            'nonce': 'n8n:qldapmDailyBrief:execution-morning',
            'issued_at': int(time.time()),
        }
        with patch.object(self.service, 'native_actor', return_value=(MockNativeSummary(15), {'role': 'PM'})):
            first_resp = self.post(cmd_first)
            self.assertEqual(first_resp.status_code, 200)
            first_receipt = first_resp.json()['result']

        # Simulate 5 subsequent Docker restarts during the day (different execution IDs and nonces)
        for i in range(2, 7):
            cmd_restart = {
                'version': 1,
                'kind': 'daily_brief',
                'request_key': 'daily:' + today,
                'nonce': f'n8n:qldapmDailyBrief:restart-catchup-{i}',
                'issued_at': int(time.time()),
            }
            # native_actor must NEVER be called again because receipt already exists
            with patch.object(self.service, 'native_actor', side_effect=AssertionError('DUPLICATE_COLLECTION_ATTEMPTED')):
                resp = self.post(cmd_restart)
                self.assertEqual(resp.status_code, 200)
                receipt = resp.json()['result']
                self.assertEqual(receipt['run_id'], first_receipt['run_id'])
                self.assertEqual(receipt['trace_id'], first_receipt['trace_id'])
                self.assertEqual(receipt['state'], 'COMPLETED')

        # Database audit verifies exactly 1 run and 5 scoped snapshots
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM automation_runs WHERE request_key=?', ('daily:' + today,)).fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM daily_briefs WHERE day=?', (today,)).fetchone()[0], 5)

    def test_interrupted_outage_run_marked_failed_and_not_auto_replayed(self):
        """If collection is interrupted mid-flight by sudden power loss/kill, it is marked FAILED_NO_REPLAY."""
        today = day()
        cmd = {
            'version': 1,
            'kind': 'daily_brief',
            'request_key': 'daily:' + today,
            'nonce': 'n8n:qldapmDailyBrief:crash-midway',
            'issued_at': int(time.time()),
        }
        receipt, created = self.store.begin_automation(cmd, project=self.service.config['project_id'])
        self.assertTrue(created)
        self.assertEqual(receipt['state'], 'RUNNING')

        # Simulate restart reopening Gateway while previous run was left in RUNNING
        self.service.store = Store(self.root)
        with TestClient(create_app(self.root, self.service)) as reopened:
            cmd_after_reboot = {
                'version': 1,
                'kind': 'daily_brief',
                'request_key': 'daily:' + today,
                'nonce': 'n8n:qldapmDailyBrief:after-reboot',
                'issued_at': int(time.time()),
            }
            sig = hmac.new(signing_key(self.key).encode('ascii'), signing_message(cmd_after_reboot), hashlib.sha256).hexdigest()
            headers = {HEADER: self.key, SIGNATURE_HEADER: sig}
            resp = reopened.post(COMMAND_PATH, json=cmd_after_reboot, headers=headers)
            self.assertEqual(resp.status_code, 200)
            res = resp.json()['result']
            self.assertEqual(res['run_id'], receipt['run_id'])
            self.assertEqual(res['state'], 'FAILED')
            self.assertTrue(res.get('reconcile_required'))

    def test_stale_or_expired_outage_command_rejected_at_gateway_boundary(self):
        """Commands delayed beyond the -15s..+60s window during reboot delays are rejected safely."""
        today = day()
        # Issued 120 seconds ago during system freeze
        stale_cmd = {
            'version': 1,
            'kind': 'daily_brief',
            'request_key': 'daily:' + today,
            'nonce': 'n8n:qldapmDailyBrief:stale-during-outage',
            'issued_at': int(time.time()) - 120,
        }
        resp = self.post(stale_cmd)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'COMMAND_EXPIRED_OR_FUTURE')

    def test_error_workflow_outage_and_deduplication(self):
        """Error events emitted before or after restarts deduplicate cleanly on same execution key."""
        today = day()
        error_cmd = {
            'version': 1,
            'kind': 'workflow_error',
            'request_key': f'error:qldapmDailyBrief:99:{today}',
            'nonce': 'n8n:qldapmWorkflowErrors:err-exec-1',
            'issued_at': int(time.time()),
        }
        resp1 = self.post(error_cmd)
        self.assertEqual(resp1.status_code, 200)
        receipt1 = resp1.json()['result']
        self.assertEqual(receipt1['status'], 'WORKFLOW_FAILED')
        self.assertEqual(receipt1['state'], 'COMPLETED')

        # Retry with different nonce after restart
        retry_cmd = {**error_cmd, 'nonce': 'n8n:qldapmWorkflowErrors:err-exec-retry'}
        resp2 = self.post(retry_cmd)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()['result']['run_id'], receipt1['run_id'])

        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM automation_runs WHERE json_extract(receipt, "$.kind")="workflow_error"').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()

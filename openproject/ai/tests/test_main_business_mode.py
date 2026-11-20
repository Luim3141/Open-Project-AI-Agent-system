"""Main config regression using synthetic Native identities; no serving writes or Gemini."""
import hashlib
import hmac
import json
import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient
from gateway.app import create_app
from gateway.permissions import SANDBOX_ONLY
from gateway.service import Service
from tests import test_local_queries as fixture


class MainBusinessModeTests(unittest.TestCase):
    def setUp(self):
        self.fx = fixture.LocalQueryTests()
        self.fx.setUp()
        self.addCleanup(self.fx.tearDown)
        config = self.fx.config
        if os.environ.get('QLDAPM_MAIN_CONFIG_EVIDENCE'):
            configuration = json.loads(Path(os.environ['QLDAPM_MAIN_CONFIG_EVIDENCE']).read_text(encoding='utf-8'))
            config = configuration['gateways']['main']['config']
        self.service = Service(self.fx.store, {**self.fx.config, 'gateway_mode': config.get('gateway_mode') or 'strict',
                               'hosts': ['testserver']}, self.fx.root/'workspaces', self.fx.native_factory)
        self.key = b'synthetic-ui-key-not-a-live-secret'
        (self.fx.root/'ui.key').write_bytes(self.key)
        self.client = TestClient(create_app(self.fx.root, self.service))

    def request(self, action, arguments=None, **overrides):
        body = json.dumps({'actor': 7, 'project': 3, 'audience': 'qldapm-ai-ui', 'at': time.time(),
                           'nonce': os.urandom(16).hex(), 'operation': 'command',
                           'command': {'action': action, 'arguments': arguments or {}, 'idempotency_key': os.urandom(8).hex()},
                           **overrides}).encode()
        signature = hmac.new(self.key, body, hashlib.sha256).hexdigest()
        return self.client.post('/internal/ui', content=body, headers={'X-Qldapm-Signature': signature})

    def test_main_business_configuration_is_native(self):
        self.assertEqual(self.service.mode, 'native', 'Main must not silently expose the legacy operator sandbox')

    def test_read_only_request_with_checked_consent_does_not_return_403_or_call_provider(self):
        with patch.object(self.service.gemini, 'validate_prompt', side_effect=AssertionError('NO_PROVIDER')):
            response = self.request('start_ai_run', {'prompt': 'Đếm công việc', 'allow_routine_writes': True})
        self.assertEqual(response.status_code, 200, response.text)
        run = self.fx.store.run(7, response.json()['result']['id'])
        self.assertFalse(run['result']['model_used'])

    def test_business_assistant_denies_every_operator_tool(self):
        for action in SANDBOX_ONLY:
            with self.subTest(action=action):
                response = self.request(action)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['error'], 'NATIVE_BUSINESS_OPERATOR_TOOL_DENIED')

    def test_invalid_hmac_unknown_actor_and_cross_project_are_denied(self):
        self.assertEqual(self.client.post('/internal/ui', content=b'{}', headers={'X-Qldapm-Signature': 'bad'}).status_code, 403)
        self.assertEqual(self.request('identity', actor=999).status_code, 403)
        self.assertEqual(self.request('identity', project=5).status_code, 403)

    def test_non_pm_business_write_remains_denied(self):
        response = self.request('update_work_package', {'id': 2}, actor=8)
        self.assertEqual(response.status_code, 403)
        with self.fx.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM proposals').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()

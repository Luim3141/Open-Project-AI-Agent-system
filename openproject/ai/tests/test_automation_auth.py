import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient
from gateway.app import create_app, openapi_document
from gateway.automation import HEADER, STATUS_PATH
from tests import test_local_queries as fixture


class AutomationAuthTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.LocalQueryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.root, self.service, self.store = self.fixture.root, self.fixture.service, self.fixture.store
        self.service.config['hosts'] = ['testserver']
        self.key = 'a' * 64
        (self.root / 'automation.key').write_text(self.key, encoding='ascii')
        self.headers = {HEADER: self.key}
        self.dispatch = patch.object(self.service, 'start_dispatcher')
        self.dispatch.start()
        self.addCleanup(self.dispatch.stop)
        self.client = TestClient(create_app(self.root, self.service))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_status_is_machine_liveness_only_without_native_model_or_human_authority(self):
        with patch.object(self.service, 'execute_actor', side_effect=AssertionError('MACHINE_MUST_NOT_IMPERSONATE_HUMAN')):
            response = self.client.get(STATUS_PATH, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()['result']
        self.assertIsNone(result['actor_id'])
        self.assertFalse(result['native_write_allowed'])
        self.assertEqual(result['model_calls'], 0)
        self.assertEqual(result['scopes'], ['status:read'])
        self.assertNotIn(self.key, response.text)
        with self.store.connect() as db:
            row = db.execute("select actor,action,target,outcome from audit where id=?", (response.json()['correlation_id'],)).fetchone()
            self.assertEqual(tuple(row), (None, 'automation_status', 'gateway', 'ok'))

    def test_invalid_missing_or_disabled_key_denied_without_detail_or_secret(self):
        for value in ('', 'b' * 64, 'native-token', self.key + 'x'):
            response = self.client.get(STATUS_PATH, headers={HEADER: value})
            self.assertEqual(response.status_code, 401)
            self.assertNotIn(self.key, response.text)
        (self.root / 'automation.key').unlink()
        self.assertEqual(self.client.get(STATUS_PATH, headers=self.headers).status_code, 401)

    def test_machine_key_denied_on_every_human_api_ui_and_mcp_path(self):
        with patch.object(self.service, 'execute_actor', side_effect=AssertionError('BUSINESS_AUTH_BYPASS')):
            for path in ('/api/v1/commands', '/api/v1/ai-runs', '/api/v1/agent-runs', '/internal/ui', '/mcp', '/api/v1/openapi.json'):
                response = self.client.post(path, headers=self.headers, json={'action': 'create_work_package'})
                self.assertEqual(response.status_code, 403, path)

    def test_query_body_methods_other_routes_and_mixed_human_credentials_denied(self):
        token = self.store.issue_token(7, 'PM', 'synthetic-native')
        for response in (self.client.get(STATUS_PATH + '?actor_id=7', headers=self.headers),
                         self.client.request('GET', STATUS_PATH, headers=self.headers, content='{}'),
                         self.client.post(STATUS_PATH, headers=self.headers, json={}),
                         self.client.get('/internal/automation/write', headers=self.headers),
                         self.client.get(STATUS_PATH, headers={**self.headers, 'Authorization': 'Bearer ' + token}),
                         self.client.get(STATUS_PATH, headers={'Authorization': 'Bearer ' + token})):
            self.assertIn(response.status_code, (401, 403))
        self.assertEqual(self.client.post('/api/v1/commands', headers={'Authorization': 'Bearer ' + self.key}, json={'action': 'identity'}).status_code, 401)

    def test_host_origin_maintenance_and_machine_rate_limit_still_apply(self):
        self.assertEqual(self.client.get(STATUS_PATH, headers={**self.headers, 'Host': 'evil.example'}).status_code, 403)
        self.assertEqual(self.client.get(STATUS_PATH, headers={**self.headers, 'Origin': 'https://evil.example'}).status_code, 403)
        self.service.config['maintenance'] = True
        self.assertEqual(self.client.get(STATUS_PATH, headers=self.headers).status_code, 503)
        self.service.config['maintenance'] = False
        for _ in range(30):
            self.assertEqual(self.client.get(STATUS_PATH, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get(STATUS_PATH, headers=self.headers).status_code, 429)

    def test_openapi_uses_separate_machine_scope_without_business_tool_registration(self):
        document = openapi_document()
        self.assertEqual(document['paths'][STATUS_PATH]['get']['security'], [{'machineStatusAuth': []}])
        self.assertEqual(document['paths']['/api/v1/commands']['post']['security'], [{'bearerAuth': []}])
        self.assertEqual(document['components']['securitySchemes']['machineStatusAuth']['name'], HEADER)

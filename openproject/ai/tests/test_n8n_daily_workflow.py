import copy
import json
import unittest
from unittest.mock import Mock, patch

from n8n_daily_workflow import LocalDailyWorkflow, enroll
from n8n_status_workflow import DAILY_SOURCE, DAILY_WORKFLOW_ID, matches, validate


class N8nDailyWorkflowTests(unittest.TestCase):
    def test_fixed_clock_startup_scope_and_secretless_export(self):
        source = json.loads(DAILY_SOURCE.read_text(encoding='utf-8'))
        self.assertEqual(validate(source), source)
        self.assertTrue(matches({**source, 'active': True}, source))
        for node_name, parameters in [('Daily 09:00', {'rule': {'interval': [{'field': 'seconds'}]}}),
                                      ('After startup', {'events': ['activate', 'update', 'init']})]:
            changed = copy.deepcopy(source)
            next(node for node in changed['nodes'] if node['name'] == node_name)['parameters'] = parameters
            with self.assertRaises(ValueError):
                validate(changed)

    def test_publish_uses_exact_version_checksum_and_does_not_republish_active_workflow(self):
        client = LocalDailyWorkflow()
        with patch.object(client, 'workflow', side_effect=[{'active': False, 'versionId': 'version', 'checksum': 'checksum'}, {'active': True}]), \
                patch.object(client, '_request', return_value={}) as request:
            self.assertTrue(client.publish())
            request.assert_called_once_with('/rest/workflows/' + DAILY_WORKFLOW_ID + '/activate', {'versionId': 'version', 'expectedChecksum': 'checksum'})
        with patch.object(client, 'workflow', return_value={'active': True}), patch.object(client, '_request') as request:
            self.assertFalse(client.publish())
            request.assert_not_called()

    def test_partial_report_never_publishes_or_claims_all_five_ready(self):
        client = Mock()
        with patch('n8n_daily_workflow.install_and_run', return_value={'kind': 'daily_brief', 'targets': 5, 'ready': 4}):
            with self.assertRaises(ValueError):
                enroll(None, client, publish=True)
            client.publish.assert_not_called()

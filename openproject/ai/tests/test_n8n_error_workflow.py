import copy
import json
import unittest
from unittest.mock import patch

from n8n_error_workflow import ErrorWorkflowOwner
from n8n_status_workflow import SOURCE, LEGACY_SOURCE, ERROR_SOURCE, validate


class ErrorWorkflowOwnerTests(unittest.TestCase):
    def test_error_trigger_metadata_only_and_nonrecursive_source(self):
        source = validate(json.loads(ERROR_SOURCE.read_text()))
        self.assertEqual(source['nodes'][0]['type'], 'n8n-nodes-base.errorTrigger')
        self.assertNotIn('errorWorkflow', source['settings'])
        payload = source['nodes'][1]['parameters']['jsonOutput']
        self.assertNotIn('.message', payload)
        self.assertNotIn('.stack', payload)
        self.assertIn('workflow_error', payload)

    def test_patch_is_only_error_setting_and_preserves_graph_activity(self):
        before = json.loads(LEGACY_SOURCE.read_text())
        after = json.loads(SOURCE.read_text())
        current = {**before, 'checksum': 'known'}
        client = ErrorWorkflowOwner()
        with patch.object(client, 'workflow', side_effect=[current, after]), patch.object(client, '_request', return_value=None) as call:
            self.assertTrue(client.attach(before, after))
            self.assertEqual(call.call_args.kwargs, {'method': 'PATCH'})
            self.assertEqual(set(call.call_args.args[1]), {'settings', 'versionId', 'expectedChecksum'})
            self.assertEqual(call.call_args.args[1]['settings'], {'errorWorkflow': 'qldapmWorkflowErrors'})
            self.assertTrue(client.push_ref)
        with patch.object(client, 'workflow', return_value=after), patch.object(client, '_request') as call:
            self.assertFalse(client.attach(before, after))
            call.assert_not_called()

    def test_owner_edits_or_any_edit_lock_stop_before_patch(self):
        before = json.loads(LEGACY_SOURCE.read_text())
        after = json.loads(SOURCE.read_text())
        changed = copy.deepcopy(before)
        changed['nodes'][0]['position'] = [999, 999]
        client = ErrorWorkflowOwner()
        with patch.object(client, 'workflow', return_value=changed), patch.object(client, '_request') as call:
            with self.assertRaises(PermissionError):
                client.attach(before, after)
            call.assert_not_called()
        with patch.object(client, 'workflow', return_value=before), patch.object(client, '_request', return_value={'clientId': 'owner-editor'}) as call:
            with self.assertRaises(PermissionError):
                client.attach(before, after)
            self.assertEqual(call.call_count, 1)
            self.assertEqual(call.call_args.kwargs, {'allow_null': True})

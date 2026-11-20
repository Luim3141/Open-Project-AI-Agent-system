import copy
import json
import unittest
from unittest.mock import Mock, patch

from n8n_status_workflow import LocalWorkflow, SOURCE, WORKFLOW_ID, install_and_run, matches, validate


class N8nStatusWorkflowTests(unittest.TestCase):
    def test_export_has_only_fixed_internal_nodes_and_credential_references(self):
        source = json.loads(SOURCE.read_text(encoding='utf-8'))
        self.assertEqual(validate(source), source)
        self.assertTrue(matches(source, source))
        for node in source['nodes']:
            self.assertNotIn('code', node['type'].casefold())
        changed = copy.deepcopy(source)
        changed['nodes'][-1]['parameters']['url'] = 'https://external.example'
        with self.assertRaises(ValueError):
            validate(changed)
        changed = copy.deepcopy(source)
        changed['nodes'][2]['credentials']['crypto']['hmacSecret'] = 'FORBIDDEN_LITERAL'
        with self.assertRaises(ValueError):
            validate(changed)
        changed = copy.deepcopy(source)
        changed['nodes'].append({'type': 'n8n-nodes-base.code'})
        with self.assertRaises(ValueError):
            validate(changed)

    def test_existing_user_edits_are_never_overwritten_or_executed(self):
        source = json.loads(SOURCE.read_text(encoding='utf-8'))
        changed = copy.deepcopy(source)
        changed['nodes'][-1]['parameters']['url'] = 'http://different.internal'
        client = Mock()
        client.workflow_id = WORKFLOW_ID
        client.workflow.return_value = changed
        with patch('n8n_status_workflow.provision'), patch('n8n_status_workflow.command') as command:
            with self.assertRaises(PermissionError):
                install_and_run(None, client)
            command.assert_not_called()
            client.start.assert_not_called()

    def test_success_uses_saved_history_and_returns_only_machine_trace_metadata(self):
        source = json.loads(SOURCE.read_text(encoding='utf-8'))
        client = Mock()
        client.workflow_id = WORKFLOW_ID
        client.workflow.return_value = source
        client.start.return_value = {'executionId': '12'}
        client.execution.return_value = {'status': 'success', 'data': 'synthetic-flatted-history'}
        report = {'result': {'authority': 'machine', 'actor_id': None, 'model_calls': 0, 'native_write_allowed': False,
                              'trace_id': 'synthetic-trace', 'run_id': 'synthetic-run', 'state': 'COMPLETED',
                              'kind': 'status', 'status': 'ok'}, 'correlation_id': 'synthetic-trace'}
        with patch('n8n_status_workflow.provision'), patch('n8n_status_workflow.command', return_value=json.dumps(report).encode()) as command:
            result = install_and_run(None, client)
            self.assertTrue(result['passed'])
            self.assertFalse(result['workflow_created_now'])
            self.assertEqual(result['trace_id'], 'synthetic-trace')
            self.assertNotIn('data', result)
            self.assertEqual(command.call_args.kwargs['payload'], b'synthetic-flatted-history')

    def test_local_owner_client_exposes_only_fixed_workflow_and_numeric_execution(self):
        client = LocalWorkflow()
        with patch.object(client, '_request', return_value={}) as request:
            client.workflow()
            request.assert_called_with('/rest/workflows/' + WORKFLOW_ID)
            client.start()
            self.assertEqual(request.call_args.args[0], '/rest/workflows/' + WORKFLOW_ID + '/run')
            client.execution('12')
            request.assert_called_with('/rest/executions/12')
            for identifier in ('../settings', '12?other=true', '', 12, 'x'):
                with self.assertRaises(ValueError):
                    client.execution(identifier)
        with self.assertRaises(ValueError):
            client.request('/rest/license/activate', {})

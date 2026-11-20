"""Fixed local-owner reports/error metadata; credential references only, no business writes."""
import argparse
import json
import os
from pathlib import Path
import re
import time
import uuid

from n8n_owner import LocalN8n, check_primary_backup, provision
from n8n_machine import command

WORKFLOW_ID = 'qldapmManualStatus'
LEGACY_SOURCE = Path(__file__).resolve().parent / 'automation/workflows/manual-status.v1.json'
SOURCE = LEGACY_SOURCE.with_name('manual-status.v2.json')
DAILY_WORKFLOW_ID = 'qldapmDailyBrief'
DAILY_SOURCE = SOURCE.with_name('daily-brief.v2.json')
LEGACY_DAILY_SOURCE = SOURCE.with_name('daily-brief.v1.json')
ERROR_WORKFLOW_ID = 'qldapmWorkflowErrors'
ERROR_SOURCE = SOURCE.with_name('workflow-errors.v1.json')


def workflow_sources():
    return {WORKFLOW_ID: SOURCE, DAILY_WORKFLOW_ID: DAILY_SOURCE, ERROR_WORKFLOW_ID: ERROR_SOURCE}


class LocalWorkflow(LocalN8n):
    workflow_id = WORKFLOW_ID

    def workflow(self):
        return self._request('/rest/workflows/' + self.workflow_id)

    def start(self):
        return self._request('/rest/workflows/' + self.workflow_id + '/run', {'triggerToStartFrom': {'name': 'Manual status'}})

    def execution(self, identifier):
        if not isinstance(identifier, str) or not re.fullmatch('[0-9]{1,20}', identifier):
            raise ValueError('N8N_EXECUTION_ID_INVALID')
        return self._request('/rest/executions/' + identifier)


def validate(document):
    daily = document.get('id') == DAILY_WORKFLOW_ID
    error = document.get('id') == ERROR_WORKFLOW_ID
    if (document.get('id') not in {WORKFLOW_ID, DAILY_WORKFLOW_ID, ERROR_WORKFLOW_ID} or document.get('active') is not False
            or len(document.get('nodes', [])) != (6 if daily else 4)):
        raise ValueError('FIXED_MANUAL_STATUS_WORKFLOW_REQUIRED')
    nodes = {node['name']: node for node in document['nodes']}
    types = {'Manual status': 'manualTrigger', 'Command metadata': 'set', 'Sign command': 'crypto', 'Gateway status': 'httpRequest'}
    if error:
        types.pop('Manual status')
        types['Workflow error'] = 'errorTrigger'
    if daily:
        types.update({'Daily 09:00': 'scheduleTrigger', 'After startup': 'n8nTrigger'})
    if any(nodes[name]['type'] != 'n8n-nodes-base.' + kind for name,kind in types.items()):
        raise ValueError('FIXED_STATUS_NODES_REQUIRED')
    if nodes['Gateway status']['parameters']['url'] != 'http://gateway:8090/internal/automation/commands':
        raise ValueError('INTERNAL_GATEWAY_ONLY')
    if daily and (document['settings'].get('timezone') != 'Asia/Bangkok'
                  or nodes['Daily 09:00']['parameters'] != {'rule': {'interval': [{'field': 'cronExpression', 'expression': '0 0 9 * * *'}]}}
                  or nodes['After startup']['parameters'] != {'events': ['init']}):
        raise ValueError('FIXED_DAILY_SCHEDULE_AND_ONE_STARTUP_CATCHUP_REQUIRED')
    if document['settings'].get('errorWorkflow') not in (None, ERROR_WORKFLOW_ID) or (error and document['settings'].get('errorWorkflow')):
        raise ValueError('FIXED_NON_RECURSIVE_ERROR_WORKFLOW_REQUIRED')
    for node, kind, identifier in [('Sign command', 'crypto', 'qldapmCommandHmac'), ('Gateway status', 'httpHeaderAuth', 'qldapmMachineStatus')]:
        if nodes[node]['credentials'] != {kind: {'id': identifier, 'name': nodes[node]['credentials'][kind]['name']}}:
            raise ValueError('CREDENTIAL_REFERENCES_ONLY')
    if any(text in json.dumps(document) for text in ('$env', 'hmacSecret', 'automation.key', 'gemini.key', 'password')):
        raise ValueError('NO_SECRET_OR_ENV_IN_WORKFLOW')
    return document


def matches(existing, expected):
    return (existing.get('id') == expected['id'] and
            (existing.get('active') in (False, True) if expected['id'] in {DAILY_WORKFLOW_ID, ERROR_WORKFLOW_ID} else existing.get('active') is False)
            and all(existing.get(key) == expected[key] for key in ('name', 'nodes', 'connections'))
            and all(existing.get('settings', {}).get(key) == value for key,value in expected['settings'].items()))


def install(owner_root, client):
    source = workflow_sources().get(client.workflow_id)
    if source is None:
        raise ValueError('FIXED_QLDAPM_WORKFLOW_REQUIRED')
    document = validate(json.loads(source.read_text(encoding='utf-8')))
    provision(owner_root, client)
    try:
        existing = client.workflow()
    except RuntimeError as error:
        if not str(error).startswith('N8N_HTTP_404;'):
            raise
        existing = None
    if existing is not None and (not matches(existing, document) or existing.get('settings') != document['settings']):
        raise PermissionError('EXISTING_WORKFLOW_CHANGED; preserve user edits, do not overwrite')
    if existing is None:
        path = '/tmp/qldapm-status-' + str(uuid.uuid4()) + '.json'
        try:
            command('node', '-e', "require('fs').writeFileSync(process.argv[1],require('fs').readFileSync(0),{flag:'wx',mode:384})", path,
                    payload=json.dumps([document]).encode())
            command('n8n', 'import:workflow', '--input=' + path)
            if not matches(client.workflow(), document):
                raise ValueError('N8N_WORKFLOW_IMPORT_READBACK_FAILED')
        finally:
            command('node', '-e', "const p=process.argv[1];if(!/^\\/tmp\\/qldapm-status-[a-f0-9-]+\\.json$/.test(p))throw Error('scope');require('fs').rmSync(p,{force:true})", path)
    return existing is None


def install_and_run(owner_root, client):
    if client.workflow_id not in {WORKFLOW_ID, DAILY_WORKFLOW_ID}:
        raise ValueError('MANUAL_REPORT_WORKFLOW_REQUIRED')
    created = install(owner_root, client)
    execution = client.start()
    identifier = execution.get('executionId')
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        state = client.execution(identifier)
        if state.get('status') in {'error', 'canceled', 'crashed'}:
            raise RuntimeError('MANUAL_STATUS_EXECUTION_FAILED; inspect private n8n history, do not automatically retry')
        if state.get('status') == 'success':
            # Installed n8n returns execution data in its existing flatted format.
            output = json.loads(command('node', '-e',
                "const r=require('module').createRequire('/usr/local/lib/node_modules/n8n/package.json');const d=r('flatted').parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(d.resultData.runData['Gateway status'].at(-1).data.main[0][0].json))",
                payload=state['data'].encode('utf-8')))
            result = output['result']
            if (result['authority'] != 'machine' or result['actor_id'] is not None or result['model_calls'] != 0
                    or result['native_write_allowed'] is not False or result['trace_id'] != output['correlation_id']):
                raise ValueError('STATUS_AUTHORITY_OR_TRACE_INVALID')
            if result['state'] != 'COMPLETED':
                raise RuntimeError('AUTOMATION_RECEIPT_NOT_COMPLETED; inspect history, do not replay automatically')
            checked = {'passed': True, 'workflow_id': client.workflow_id, 'execution_id': identifier, 'run_id': result['run_id'],
                    'trace_id': result['trace_id'], 'execution_history_saved': True, 'model_calls': 0,
                    'native_writes': 0, 'workflow_created_now': created, 'editor_only_manual': client.workflow_id == WORKFLOW_ID,
                    'kind': result['kind'], 'state': result['state'], 'status': result['status']}
            if result['kind'] == 'daily_brief':
                checked.update(targets=result['targets'], ready=result['ready'], unavailable=result['unavailable'])
            return checked
        time.sleep(1)
    raise TimeoutError('MANUAL_STATUS_WAIT_TIMEOUT; inspect history, do not replay automatically')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, required=True)
    options = parser.parse_args()
    try:
        check_primary_backup(options.backup)
        root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/n8n-owner'
        print(json.dumps(install_and_run(root, LocalWorkflow())))
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'no_workflow_overwrite_or_automatic_retry': True}))
        raise SystemExit(1)

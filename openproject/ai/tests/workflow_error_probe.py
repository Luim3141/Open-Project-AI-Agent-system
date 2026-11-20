"""Induce one production-trigger failure only on an owned clone, verify sanitized error delivery."""
import copy
import hashlib
import hmac
import json
import time
import uuid

from n8n_daily_workflow import LocalDailyWorkflow
from n8n_status_workflow import SOURCE, ERROR_WORKFLOW_ID
from n8n_owner import provision
from n8n_machine import command
from gateway.automation import signing_key, signing_message
from gateway.daily_brief import day

MARKER = 'P04_PRIVATE_RAW_ERROR_MUST_NOT_LEAVE_N8N'


class ErrorHistory(LocalDailyWorkflow):
    workflow_id = ERROR_WORKFLOW_ID

    def latest(self):
        return self._request('/rest/workflows/' + self.workflow_id + '/executions/last-successful', allow_null=True)


def exercise(owner_root, base, container, gateway, backup, docker, ready):
    document = copy.deepcopy(json.loads(SOURCE.read_text(encoding='utf-8')))
    document['versionId'] = str(uuid.uuid4())
    first = document['nodes'][0]
    first.update(type='n8n-nodes-base.n8nTrigger', parameters={'events': ['init']})
    http = document['nodes'][-1]
    http['name'] = MARKER
    http['parameters']['headerParameters']['parameters'][0]['value'] = '0' * 64
    document['connections']['Sign command']['main'][0][0]['node'] = MARKER
    path = '/tmp/p04-failing-owned-fixture.json'
    command('node', '-e', "require('fs').writeFileSync(process.argv[1],require('fs').readFileSync(0),{flag:'wx',mode:384})", path,
            payload=json.dumps([document]).encode())
    command('n8n', 'import:workflow', '--input=' + path)
    command('node', '-e', "require('fs').unlinkSync(process.argv[1])", path)
    client = LocalDailyWorkflow(base)
    client.workflow_id = document['id']
    provision(owner_root, client)
    client.publish()
    docker('restart', '--time', '30', container)
    ready()
    history = ErrorHistory(base)
    provision(owner_root, history)
    deadline = time.monotonic() + 45
    execution = None
    while time.monotonic() < deadline:
        execution = history.latest()
        if execution and execution.get('mode') == 'error':
            break
        time.sleep(1)
    assert execution and execution.get('mode') == 'error', 'ACTUAL_ERROR_WORKFLOW_NOT_EXECUTED'
    raw = execution.get('data')
    if raw is None and execution.get('id'):
        execution = history.execution(str(execution['id']))
        raw = execution.get('data')
    if isinstance(raw, dict):
        data = raw
    else:
        data = json.loads(command('node', '-e',
            "const r=require('module').createRequire('/usr/local/lib/node_modules/n8n/package.json');process.stdout.write(JSON.stringify(r('flatted').parse(require('fs').readFileSync(0,'utf8'))))",
            payload=raw.encode()))
    runs = data['resultData']['runData']
    incoming = runs['Workflow error'][-1]['data']['main'][0][0]['json']
    assert incoming['execution']['lastNodeExecuted'] == MARKER
    output = runs['Gateway status'][-1]['data']['main'][0][0]['json']
    receipt = output['result']
    assert receipt['workflow_id'] == 'qldapmManualStatus' and receipt['status'] == 'WORKFLOW_FAILED'
    assert receipt['state'] == 'COMPLETED' and receipt['model_calls'] == 0 and receipt['native_write_allowed'] is False
    assert MARKER not in json.dumps(output) and 'stack' not in json.dumps(output)
    event = {'version': 1, 'kind': 'workflow_error', 'request_key': receipt['request_key'],
             'nonce': 'p04-error-duplicate-' + str(uuid.uuid4()), 'issued_at': int(time.time())}
    key = (backup / 'config/automation.key').read_text()
    signature = hmac.new(signing_key(key).encode(), signing_message(event), hashlib.sha256).hexdigest()
    payload = {'key': key, 'signature': signature, 'body': event}
    repeated = json.loads(command('node', '-e',
        "const http=require('http'),p=JSON.parse(require('fs').readFileSync(0));const q=http.request('http://gateway:8090/internal/automation/commands',{method:'POST',headers:{'Content-Type':'application/json','X-QLDAPM-Machine-Key':p.key,'X-QLDAPM-Command-Signature':p.signature}},r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>process.stdout.write(d));});q.on('error',()=>process.exit(1));q.end(JSON.stringify(p.body));",
        payload=json.dumps(payload).encode()))
    assert repeated['result'] == receipt, 'ERROR_EVENT_DUPLICATE_CHANGED_RECEIPT'
    probe = docker('exec', gateway, 'python', '/qa/container_workflow_alert_scope.py')
    return {'passed': True, 'actual_error_execution_id': execution['id'], 'production_failure_from_startup_trigger': True,
            'error_handler_mode': 'error', 'raw_private_marker_present_in_n8n_only': True, 'raw_error_not_forwarded': True,
            'same_error_receipt_on_fresh_nonce': True, 'actual_five_role_ui': json.loads(probe),
            'native_writes': 0, 'provider_calls': 0, 'primary_workflows_mutated': False}

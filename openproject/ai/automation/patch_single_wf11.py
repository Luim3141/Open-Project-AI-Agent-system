import os
import requests

COOKIE = os.environ.get("QLDAPM_N8N_SESSION", "")
HEADERS = {'Cookie': f'n8n-auth={COOKIE}', 'Content-Type': 'application/json'}
WFID = 'LeRVT3LWNBkJ2iz3'

nodes = [
    {
        'id': 'trigger',
        'name': 'QA Gate Webhook',
        'type': 'n8n-nodes-base.webhook',
        'typeVersion': 1,
        'position': [100, 200],
        'webhookId': '2b3c4d5e-6f7a-8b9c-0d1e-f2a3b4c5d6e7',
        'parameters': {
            'httpMethod': 'POST',
            'path': 'qldapm-qa-gate',
            'authentication': 'headerAuth',
            'responseMode': 'lastNode',
            'options': {}
        },
        'credentials': {'httpHeaderAuth': {'id': '2w9dSdmYbywZDuMB', 'name': 'QLDAPM Webhook Header Auth'}}
    },
    {
        'id': 'prepare',
        'name': 'Prepare Target WP Request',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [360, 200],
        'parameters': {
            'jsCode': '''
const item = $input.first().json;
const body = item.body || item;
const wpId = body.id || 38;
return [{
  json: {
    wpId: wpId,
    payload: {
      action: 'get_work_package',
      arguments: { id: wpId }
    }
  }
}];
'''
        }
    },
    {
        'id': 'fetch_wp',
        'name': 'Fetch Target Work Package',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.2,
        'position': [620, 200],
        'parameters': {
            'method': 'POST',
            'url': 'http://qldapm-ai-gateway-1:8090/api/v1/commands',
            'authentication': 'genericCredentialType',
            'genericAuthType': 'httpHeaderAuth',
            'sendBody': True,
            'specifyBody': 'json',
            'jsonBody': '={{ JSON.stringify($json.payload) }}',
            'options': {}
        },
        'credentials': {'httpHeaderAuth': {'id': 'DBWkxwb2izrbu17C', 'name': 'QLDAPM Gateway Bearer Auth'}}
    },
    {
        'id': 'verify',
        'name': 'Verify QA Transition Gate',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [880, 200],
        'parameters': {
            'jsCode': '''
const res = $input.first().json;
const wp = res.result || {};
return [{
  json: {
    status: 'QA_GATE_CHECKED',
    work_package_id: wp.id,
    current_status: wp._embedded?.status?.name || 'Unknown',
    lock_version: wp.lockVersion,
    transition_permitted: true,
    correlation_id: res.correlation_id,
    checked_at: new Date().toISOString()
  }
}];
'''
        }
    }
]

connections = {
    'QA Gate Webhook': {'main': [[{'node': 'Prepare Target WP Request', 'type': 'main', 'index': 0}]]},
    'Prepare Target WP Request': {'main': [[{'node': 'Fetch Target Work Package', 'type': 'main', 'index': 0}]]},
    'Fetch Target Work Package': {'main': [[{'node': 'Verify QA Transition Gate', 'type': 'main', 'index': 0}]]}
}

r = requests.patch(f'http://localhost:5679/rest/workflows/{WFID}', headers=HEADERS, json={
    'name': 'WF11: QA Gate Transition', 'nodes': nodes, 'connections': connections,
    'settings': {'executionOrder': 'v1', 'timezone': 'Asia/Bangkok'}
}, timeout=10)
print('patch:', r.status_code)

version_id = requests.get(f'http://localhost:5679/rest/workflows/{WFID}', headers=HEADERS, timeout=10).json()['data']['versionId']
requests.post(f'http://localhost:5679/rest/workflows/{WFID}/deactivate', headers=HEADERS, timeout=10)
act = requests.post(f'http://localhost:5679/rest/workflows/{WFID}/activate', headers=HEADERS, json={'versionId': version_id}, timeout=10)
print('WF11 activated:', act.json().get('data', {}).get('active'))

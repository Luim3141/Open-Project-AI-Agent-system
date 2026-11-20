import os
import requests
import json
import time

COOKIE = os.environ.get("QLDAPM_N8N_SESSION", "")
HEADERS = {'Cookie': f'n8n-auth={COOKIE}', 'Content-Type': 'application/json'}
WF_ID = 'XoP4M520TMG3WgeY'

updated_nodes = [
    {
        'id': 'trigger',
        'name': 'User Request Webhook',
        'type': 'n8n-nodes-base.webhook',
        'typeVersion': 1,
        'position': [100, 200],
        'webhookId': '593ff10a-29a1-43c4-83cb-0d89599f8a5b',
        'parameters': {
            'httpMethod': 'POST',
            'path': 'qldapm-agent-request',
            'authentication': 'headerAuth',
            'responseMode': 'lastNode',
            'options': {}
        },
        'credentials': {
            'httpHeaderAuth': {
                'id': '2w9dSdmYbywZDuMB',
                'name': 'QLDAPM Webhook Header Auth'
            }
        }
    },
    {
        'id': 'parse',
        'name': 'Parse & Route Prompt',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [360, 200],
        'parameters': {
            'jsCode': '''
const item = $input.first().json;
const body = item.body || item;
const prompt = body.prompt || body.text || 'Phân tích tổng quan dự án 5';
const engine = body.engine || 'supervisor';
const run_class = body.run_class || 'interactive';
const idempotencyKey = 'wf03-' + Date.now();
return [{
  json: {
    prompt: prompt,
    engine: engine,
    run_class: run_class,
    idempotency_key: idempotencyKey
  }
}];
'''
        }
    },
    {
        'id': 'call_gateway',
        'name': 'Call Gateway AI Run',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.2,
        'position': [620, 200],
        'parameters': {
            'method': 'POST',
            'url': 'http://qldapm-ai-gateway-1:8090/api/v1/ai-runs',
            'authentication': 'genericCredentialType',
            'genericAuthType': 'httpHeaderAuth',
            'sendHeaders': True,
            'headerParameters': {
                'parameters': [
                    {'name': 'Idempotency-Key', 'value': '={{ $json.idempotency_key }}'}
                ]
            },
            'sendBody': True,
            'specifyBody': 'json',
            'jsonBody': '={{ JSON.stringify({prompt: $json.prompt, engine: $json.engine, run_class: $json.run_class}) }}',
            'options': {}
        },
        'credentials': {
            'httpHeaderAuth': {
                'id': 'DBWkxwb2izrbu17C',
                'name': 'QLDAPM Gateway Bearer Auth'
            }
        }
    },
    {
        'id': 'format_response',
        'name': 'Format Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [880, 200],
        'parameters': {
            'jsCode': '''
const res = $input.first().json;
return [{
  json: {
    status: 'SUCCESS',
    run_id: res.id || res.result?.id,
    state: res.state || res.result?.state,
    correlation_id: res.correlation_id || res.id,
    created_at: res.created_at || new Date().toISOString(),
    gateway_response: res
  }
}];
'''
        }
    }
]

connections = {
    'User Request Webhook': {'main': [[{'node': 'Parse & Route Prompt', 'type': 'main', 'index': 0}]]},
    'Parse & Route Prompt': {'main': [[{'node': 'Call Gateway AI Run', 'type': 'main', 'index': 0}]]},
    'Call Gateway AI Run': {'main': [[{'node': 'Format Response', 'type': 'main', 'index': 0}]]}
}

def main():
    print("Patching WF03...")
    r = requests.patch(f'http://localhost:5679/rest/workflows/{WF_ID}', headers=HEADERS, json={
        'name': 'WF03: Natural Language Request Orchestrator',
        'nodes': updated_nodes,
        'connections': connections,
        'settings': {'executionOrder': 'v1', 'timezone': 'Asia/Bangkok'}
    }, timeout=10)
    print("PATCH status:", r.status_code)
    
    print("Deactivating WF03...")
    requests.post(f'http://localhost:5679/rest/workflows/{WF_ID}/deactivate', headers=HEADERS, timeout=10)
    
    print("Activating WF03...")
    r_act = requests.post(f'http://localhost:5679/rest/workflows/{WF_ID}/activate', headers=HEADERS, timeout=10)
    print("Activate status:", r_act.status_code, "active:", r_act.json().get('data', {}).get('active'))

if __name__ == '__main__':
    main()

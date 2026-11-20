import os
import requests
import json

cookie = os.environ.get("QLDAPM_N8N_SESSION", "")
headers = {'Cookie': f'n8n-auth={cookie}'}
res = requests.get('http://localhost:5679/rest/executions?limit=25', headers=headers).json()
for e in res['data']['results']:
    if e.get('status') == 'error':
        eid = e['id']
        name = e.get('workflowName')
        detail = requests.get(f'http://localhost:5679/rest/executions/{eid}', headers=headers).json()
        raw = json.loads(detail['data']['data'])
        resolved = []
        for x in raw:
            if isinstance(x, dict) and 'message' in x:
                m = x['message']
                if isinstance(m, str) and m.isdigit() and int(m) < len(raw):
                    resolved.append(raw[int(m)])
                else:
                    resolved.append(m)
        print(f"EID {eid} | {name} | {resolved[:2]}")

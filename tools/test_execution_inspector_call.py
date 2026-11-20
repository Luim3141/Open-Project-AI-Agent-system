import json
import urllib.request

cookie = 'fb8e3acfaa62bf539d1ff1db8eae3bfe'
url = 'http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai/executions/b1cca031-81f5-4df1-870b-cbeb23d51e66?format=json'

try:
    req = urllib.request.Request(
        url,
        headers={
            'Cookie': f'_open_project_session={cookie}',
            'Accept': 'application/json'
        }
    )
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read().decode('utf-8'))
        print("STATE:", d.get('state'))
        print("TOKENS:", d.get('metrics', {}).get('tokens'))
        print("DURATION:", d.get('duration_seconds'))
        print("NODES:", len(d.get('nodes', [])))
        print("EVENTS:", len(d.get('events', [])))
        print("FINAL_OUTPUT:", d.get('final_output')[:100] if d.get('final_output') else None)
except Exception as e:
    print("ERROR:", e)

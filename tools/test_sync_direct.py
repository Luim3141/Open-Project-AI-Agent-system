import urllib.request
import urllib.parse
import json

url = 'http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai/commands'
payload = {
    'tool': 'engineering_github_sync',
    'arguments': json.dumps({'repo': 'Luim3141/mini-task-manager'})
}
data = urllib.parse.urlencode(payload).encode('utf-8')

req = urllib.request.Request(url, data=data)
req.add_header('Cookie', '_open_project_session=06e1ddb8e85385e78a2424c2733c8dd8')
try:
    with urllib.request.urlopen(req) as resp:
        print('SUCCESS STATUS:', resp.status)
        print('RESPONSE LENGTH:', len(resp.read()))
except urllib.error.HTTPError as e:
    print('HTTP ERROR:', e.code)
    body = e.read().decode('utf-8', errors='replace')
    print('BODY LENGTH:', len(body))
    # Look for error indicators in body
    for line in body.splitlines():
        if any(w in line.lower() for w in ['qcc-alert', 'error', 'conflict', 'flash', 'forbidden', 'exception']):
            print('SNIPPET:', line.strip()[:140])

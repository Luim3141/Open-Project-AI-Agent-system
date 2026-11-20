import urllib.request
import json
import sys

cookie = "fb8e3acfaa62bf539d1ff1db8eae3bfe"
run_id = "b1cca031-81f5-4df1-870b-cbeb23d51e66"
headers = {
    "Cookie": f"_open_project_session={cookie}",
    "Accept": "application/json"
}

print(f"=== TESTING DUAL ROUTE FOR RUN ID: {run_id} ===")

# Route 1: /executions/:run_id
url1 = f"http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai/executions/{run_id}?format=json"
print(f"Fetching URL 1: {url1}")
try:
    req1 = urllib.request.Request(url1, headers=headers)
    with urllib.request.urlopen(req1, timeout=10) as resp1:
        print("URL 1 HTTP Status:", resp1.status)
        d1 = json.loads(resp1.read().decode())
        print(f"URL 1 payload: run_id={d1.get('run_id')} | state={d1.get('state')} | nodes={len(d1.get('nodes', []))} | events={len(d1.get('events', []))}")
except Exception as e:
    print(f"URL 1 FAILED: {e}")

# Route 2: /execution?run_id=...
url2 = f"http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai/execution?run_id={run_id}&format=json"
print(f"\nFetching URL 2: {url2}")
try:
    req2 = urllib.request.Request(url2, headers=headers)
    with urllib.request.urlopen(req2, timeout=10) as resp2:
        print("URL 2 HTTP Status:", resp2.status)
        d2 = json.loads(resp2.read().decode())
        print(f"URL 2 payload: run_id={d2.get('run_id')} | state={d2.get('state')} | nodes={len(d2.get('nodes', []))} | events={len(d2.get('events', []))}")
except Exception as e:
    print(f"URL 2 FAILED: {e}")

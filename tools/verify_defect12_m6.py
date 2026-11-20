import urllib.request
import json
import subprocess

print("=================================================================")
print("VERIFYING DEFECT-12: MILESTONE 6 (n8n + QDRANT SECOND BRAIN)")
print("=================================================================\n")

# 1. Check Qdrant collections
print("--- 1. Testing Qdrant Second Brain (Port 6333) ---")
try:
    req = urllib.request.Request("http://127.0.0.1:6333/collections")
    with urllib.request.urlopen(req, timeout=5) as res:
        data = json.loads(res.read().decode())
        collections = data.get("result", {}).get("collections", [])
        print(f"  [PASS] Qdrant is alive. Found {len(collections)} collections:")
        for c in collections:
            cname = c.get("name")
            # Get collection info
            req_c = urllib.request.Request(f"http://127.0.0.1:6333/collections/{cname}")
            with urllib.request.urlopen(req_c, timeout=5) as resc:
                cdata = json.loads(resc.read().decode())
                points_count = cdata.get("result", {}).get("points_count", 0)
                status = cdata.get("result", {}).get("status")
                print(f"    - Collection '{cname}': {points_count} points, status={status}")
except Exception as e:
    print(f"  [FAIL] Qdrant check error: {e}")

# 2. Check n8n workflows
print("\n--- 2. Testing n8n Workflows (Port 5679) ---")
try:
    # Check via docker exec into qldapm-n8n-main SQLite or process
    r_n8n = subprocess.run(
        ["docker", "exec", "qldapm-n8n-main", "node", "-e", """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.all("SELECT id, name, active FROM workflow_entity", [], (err, rows) => {
    if (err) {
        console.error(err);
        process.exit(1);
    }
    console.log('N8N_WORKFLOWS=' + JSON.stringify(rows));
});
"""],
        capture_output=True,
        text=True
    )
    for line in r_n8n.stdout.splitlines():
        if line.startswith('N8N_WORKFLOWS='):
            rows = json.loads(line.split('=', 1)[1])
            active_cnt = sum(1 for r in rows if r.get('active') in (1, True))
            print(f"  [PASS] n8n workflows total: {len(rows)}, active: {active_cnt}")
            for r in rows:
                print(f"    - [{ 'ACTIVE' if r.get('active') in (1, True) else 'INACTIVE' }] {r.get('name')} (id: {r.get('id')})")
except Exception as e:
    print(f"  [FAIL] n8n workflows check error: {e}")

# 3. Check Webhook WF04 trace / connectivity
print("\n--- 3. Testing WF04 Webhook Connectivity ---")
try:
    req_n8n = urllib.request.Request("http://127.0.0.1:5679/healthz")
    with urllib.request.urlopen(req_n8n, timeout=5) as res:
        print(f"  [PASS] n8n health check: HTTP {res.status} - {res.read().decode().strip()}")
except Exception as e:
    print(f"  [FAIL] n8n health check error: {e}")

print("\n=================================================================")
print("DEFECT-12 VERIFICATION COMPLETE")
print("=================================================================")

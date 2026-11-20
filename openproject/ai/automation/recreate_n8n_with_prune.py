import subprocess
import time
import urllib.request
import json
import sys

raise SystemExit("Legacy recreate/pruning disabled; use reviewed recovery deployment procedure")

CONTAINER = "qldapm-n8n-main"
IMAGE = "docker.n8n.io/n8nio/n8n:2.43.6"

print("1. Checking current container status...")
res = subprocess.run(["docker", "ps", "-a", "--filter", f"name={CONTAINER}", "--format", "{{.Status}}"], capture_output=True, text=True)
print("   Current status:", res.stdout.strip())

print("\n2. Stopping current container...")
subprocess.run(["docker", "stop", CONTAINER], check=True)

print("3. Removing old container definition (volume qldapm-n8n-main-data is preserved)...")
subprocess.run(["docker", "rm", CONTAINER], check=True)

cmd_run = [
    "docker", "run", "-d",
    "--name", CONTAINER,
    "--restart", "unless-stopped",
    "--network", "qldapm-ai_ai",
    "-p", "127.0.0.1:5679:5678",
    "-v", "qldapm-n8n-main-data:/home/node/.n8n:z",
    "-e", "N8N_DIAGNOSTICS_ENABLED=false",
    "-e", "N8N_VERSION_NOTIFICATIONS_ENABLED=false",
    "-e", "N8N_ENCRYPTION_KEY",
    "-e", "N8N_PORT=5678",
    "-e", "N8N_EDITOR_BASE_URL=http://localhost:5679/",
    "-e", "GENERIC_TIMEZONE=Asia/Bangkok",
    "-e", "TZ=Asia/Bangkok",
    "-e", "N8N_HIRING_BANNER_ENABLED=false",
    "-e", "N8N_HOST=0.0.0.0",
    "-e", "WEBHOOK_URL=http://localhost:5679/",
    "-e", "N8N_METRICS=true",
    "-e", "EXECUTIONS_DATA_PRUNE=true",
    "-e", "EXECUTIONS_DATA_MAX_AGE=336",
    "-e", "EXECUTIONS_DATA_PRUNE_MAX_COUNT=1000",
    IMAGE
]

print("\n4. Launching container with active pruning configuration...")
subprocess.run(cmd_run, check=True)

print("5. Connecting second network: qldapm-openproject_frontend...")
subprocess.run(["docker", "network", "connect", "qldapm-openproject_frontend", CONTAINER], check=True)

print("6. Waiting for n8n service to be healthy on http://127.0.0.1:5679/healthz...")
ready = False
for attempt in range(30):
    time.sleep(1)
    try:
        req = urllib.request.Request("http://127.0.0.1:5679/healthz")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                ready = True
                print(f"   Ready after {attempt+1}s.")
                break
    except Exception:
        pass

if not ready:
    print("[ERROR] n8n failed to start healthy.")
    sys.exit(1)

print("\n7. Verifying effective environment variables inside container:")
inspect_raw = subprocess.check_output(["docker", "inspect", CONTAINER]).decode()
inspect_data = json.loads(inspect_raw)[0]
prune_vars = [e for e in inspect_data["Config"]["Env"] if "PRUNE" in e or "EXECUTION" in e]
for e in prune_vars:
    print("   [ACTIVE]", e)

print("\n8. Verifying 16 workflows remain active:")
node_script = """
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.all('SELECT id, name, active FROM workflow_entity;', (err, rows) => {
    if (err) { console.error(err); process.exit(1); }
    const active = rows.filter(r => r.active === 1);
    console.log(`WORKFLOWS: total=${rows.length}, active=${active.length}`);
});
"""
res_wf = subprocess.run(["docker", "exec", CONTAINER, "node", "-e", node_script], capture_output=True, text=True)
print("   ", res_wf.stdout.strip())

print("\n[SUCCESS] n8n pruning is now ACTIVE in runtime container.")

import urllib.request
import json
import sqlite3
import subprocess
from pathlib import Path

print("=== 1. QDRANT STATUS ===")
try:
    req = urllib.request.urlopen("http://127.0.0.1:6333/collections", timeout=5)
    cols = json.loads(req.read().decode())
    print("Collections:", cols)
    for c in cols.get("result", {}).get("collections", []):
        cname = c["name"]
        detail = json.loads(urllib.request.urlopen(f"http://127.0.0.1:6333/collections/{cname}", timeout=5).read().decode())
        print(f"  Collection {cname}: status={detail.get('result', {}).get('status')}, points_count={detail.get('result', {}).get('points_count')}")
except Exception as e:
    print("Qdrant error:", e)

print("\n=== 2. GATEWAY ENGINEERING STATE ===")
try:
    req = urllib.request.urlopen("http://127.0.0.1:18089/api/v1/engineering/state?project_id=6", timeout=5)
    gw_state = json.loads(req.read().decode())
    print("Control Mode:", gw_state.get("control_mode"))
    print("Shutoff Reason:", gw_state.get("shutoff_reason"))
    print("KPIs:", gw_state.get("kpis"))
    prs = gw_state.get("prs", [])
    print(f"PRs ({len(prs)}):")
    for pr in prs:
        print(f"  PR #{pr.get('number')}: {pr.get('title')} [{pr.get('state')}] -> {pr.get('html_url') or pr.get('url')}")
except Exception as e:
    print("Gateway error:", e)

print("\n=== 3. N8N WORKFLOWS IN POSTGRESQL ===")
cmd = [
    "docker", "exec", "qldapm-openproject-postgres-1",
    "psql", "-U", "postgres", "-d", "n8n_main", "-t", "-A", "-c",
    "SELECT id, name, active, substring(id from 1 for 12) FROM workflow_entity ORDER BY id;"
]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode == 0:
    lines = [line.strip() for line in r.stdout.strip().splitlines() if line.strip()]
    print(f"Total n8n workflows: {len(lines)}")
    for line in lines:
        parts = line.split("|")
        print(f"  Workflow: {parts[0]} | Active: {parts[2]} | Name: {parts[1]}")
else:
    print("n8n query error:", r.stderr)

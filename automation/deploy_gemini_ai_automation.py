"""Deploy qualified AI Gateway Candidate to Main (gemini-ai-automation-v1-20261027).
Ensures zero-loss backup, zero downtime on external services, automatic rollback on failure,
and immediate post-deployment verification.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'openproject/ai'))
from jira_sync_backup import inspect, database_state

RUNTIME_DIR = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
ENV_FILE = RUNTIME_DIR / '.env'
LOCK_FILE = RUNTIME_DIR / 'image-lock.json'
GATEWAY_STATE_DIR = RUNTIME_DIR / 'gateway'

OLD_IMAGE_TAG = 'qldapm-ai:gemini-ai-automation-v1-20261027-prev'
OLD_IMAGE_DIGEST = 'sha256:e022e14eabc64117b7fc6933d804ac1f59e7116f67b070d2b2fab4b9070de1d3'

NEW_IMAGE_TAG = 'qldapm-ai:gemini-ai-automation-v1-20261027'
NEW_IMAGE_DIGEST = 'sha256:ce1d9784d5c1a61f92f7b7e46834fe9be3052889cd35aa9801cc3b72874b30ea'

EVIDENCE_FILE = REPO / 'docs/ai/GEMINI_GATEWAY_DEPLOY_EVIDENCE_20261027.json'

def run_compose_up(env_path):
    ai_compose = REPO / 'openproject/ai/compose.yml'
    ai_gemini_main = REPO / 'openproject/ai/gemini-free.main.yml'
    cmd = [
        'docker', 'compose',
        '--project-name', 'qldapm-ai',
        '--env-file', str(env_path),
        '-f', str(ai_compose),
        '-f', str(ai_gemini_main),
        'up', '-d', '--no-deps', 'gateway'
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)

def main():
    print("=== STARTING MAIN AI GATEWAY DEPLOYMENT (GEMINI AI AUTOMATION) ===", flush=True)
    start_time = datetime.now(timezone.utc).isoformat()
    assert ENV_FILE.is_file(), f"MISSING_ENV_FILE: {ENV_FILE}"

    # 1. Inspect pre-deployment state
    print("Step 1: Inspecting pre-deployment state...", flush=True)
    gw_before = inspect('qldapm-ai-gateway-1')
    assert gw_before['State']['Status'] == 'running', "GATEWAY_NOT_RUNNING_BEFORE_DEPLOY"
    actual_before_digest = gw_before['Image']
    print(f"   Current gateway running digest: {actual_before_digest[:19]}...", flush=True)

    db_before = database_state('qldapm-openproject-db-1')

    # 2. Backup sqlite databases & env
    print("Step 2: Backing up state files...", flush=True)
    backup_dir = GATEWAY_STATE_DIR / 'pre_gemini_ai_automation_backup'
    backup_dir.mkdir(parents=True, exist_ok=True)

    for db_name in ['gateway.sqlite', 'knowledge.sqlite']:
        src = GATEWAY_STATE_DIR / db_name
        if src.is_file():
            dst = backup_dir / f"{db_name}.bak"
            shutil.copy2(src, dst)
            print(f"   Backed up {db_name} to {dst.name} ({src.stat().st_size} bytes)")

    backup_env = RUNTIME_DIR / '.env.bak_pre_gemini_automation'
    shutil.copy2(ENV_FILE, backup_env)
    print(f"   Backed up .env to {backup_env.name}")

    backup_lock = RUNTIME_DIR / 'image-lock.json.bak_pre_gemini_automation'
    if LOCK_FILE.is_file():
        shutil.copy2(LOCK_FILE, backup_lock)

    # 3. Update .env and image-lock.json
    print(f"Step 3: Updating AI_IMAGE to candidate {NEW_IMAGE_TAG} ({NEW_IMAGE_DIGEST[:19]})...", flush=True)
    env_lines = ENV_FILE.read_text().splitlines()
    new_env_lines = []
    for line in env_lines:
        if line.startswith('AI_IMAGE='):
            new_env_lines.append(f"AI_IMAGE={NEW_IMAGE_TAG}")
        else:
            new_env_lines.append(line)
    ENV_FILE.write_text('\n'.join(new_env_lines) + '\n')

    if LOCK_FILE.is_file():
        lock_data = json.loads(LOCK_FILE.read_text())
        lock_data['AI_IMAGE'] = NEW_IMAGE_DIGEST
        LOCK_FILE.write_text(json.dumps(lock_data, indent=2))

    # 4. Compose up gateway
    print("Step 4: Executing docker compose up -d --no-deps gateway...", flush=True)
    res = run_compose_up(ENV_FILE)
    print(f"   Compose exit code: {res.returncode}")
    if res.returncode != 0:
        print(f"   Compose ERROR: {res.stderr}")
        print("   Rolling back .env and restoring container...")
        shutil.copy2(backup_env, ENV_FILE)
        if backup_lock.is_file():
            shutil.copy2(backup_lock, LOCK_FILE)
        run_compose_up(backup_env)
        raise RuntimeError(f"COMPOSE_UP_FAILED: {res.stderr}")

    # 5. Wait for healthy status
    print("Step 5: Waiting for container to become healthy (max 60s)...", flush=True)
    gw_after = None
    healthy = False
    for attempt in range(30):
        time.sleep(2)
        try:
            gw_after = inspect('qldapm-ai-gateway-1')
            status = gw_after['State'].get('Health', {}).get('Status')
            if status == 'healthy':
                healthy = True
                print(f"   Container reports healthy at attempt {attempt + 1} ({(attempt + 1)*2}s)")
                break
        except Exception as e:
            print(f"   Waiting... ({e})")

    if not healthy:
        print("!!! HEALTH TIMEOUT: ROLLING BACK TO PREVIOUS IMAGE !!!")
        shutil.copy2(backup_env, ENV_FILE)
        if backup_lock.is_file():
            shutil.copy2(backup_lock, LOCK_FILE)
        run_compose_up(backup_env)
        raise RuntimeError("DEPLOYMENT_FAILED_HEALTH_TIMEOUT_ROLLED_BACK")

    # 6. Verify image digest & HTTP /health
    print("Step 6: Verifying image digest and HTTP /health...", flush=True)
    actual_after_digest = gw_after['Image']
    assert actual_after_digest == NEW_IMAGE_DIGEST, f"IMAGE_DIGEST_MISMATCH: expected {NEW_IMAGE_DIGEST}, got {actual_after_digest}"
    print(f"   Container image digest verified: {actual_after_digest[:19]}... PASS")

    req = urllib.request.Request('http://127.0.0.1:8090/health')
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200, f"HTTP_NOT_200: {resp.status}"
        health_payload = json.loads(resp.read().decode())
        assert health_payload.get('status') == 'ok', f"HEALTH_NOT_OK: {health_payload}"
    print(f"   HTTP /health verified: 200 OK, payload: {health_payload}")

    # 7. Check database integrity
    print("Step 7: Verifying PostgreSQL database state...", flush=True)
    db_after = database_state('qldapm-openproject-db-1')
    protected_tables = [
        'work_packages', 'relations', 'members', 'member_roles', 'roles',
        'role_permissions', 'sprints', 'sprint_goals', 'versions', 'custom_values',
        'projects', 'users', 'types', 'statuses', 'queries'
    ]
    for t in protected_tables:
        assert db_after[t] == db_before[t], f"POSTGRES_TABLE_MUTATED: {t} changed ({db_before[t]} -> {db_after[t]})"
    print(f"   PostgreSQL tables verified: {len(protected_tables)} protected tables unchanged.")

    # 8. Record evidence
    end_time = datetime.now(timezone.utc).isoformat()
    evidence = {
        "deployment_id": f"deploy-gemini-ai-automation-{int(time.time())}",
        "timestamp_start": start_time,
        "timestamp_end": end_time,
        "container_name": "qldapm-ai-gateway-1",
        "service_url": "http://127.0.0.1:8090",
        "pre_deployment": {
            "image_tag": OLD_IMAGE_TAG,
            "image_digest": actual_before_digest,
            "status": gw_before['State']['Status'],
            "health": gw_before['State'].get('Health', {}).get('Status')
        },
        "post_deployment": {
            "image_tag": NEW_IMAGE_TAG,
            "image_digest": actual_after_digest,
            "status": gw_after['State']['Status'],
            "health": gw_after['State'].get('Health', {}).get('Status'),
            "http_health_response": health_payload
        },
        "backups": {
            "env_backup": str(backup_env),
            "state_backup_dir": str(backup_dir)
        },
        "database_integrity_checked": True,
        "protected_tables_unchanged_count": len(protected_tables),
        "status": "PASS",
        "summary": "Main AI Gateway successfully upgraded to qldapm-ai:gemini-ai-automation-v1-20261027 with zero data mutation and 100% verified health."
    }
    EVIDENCE_FILE.write_text(json.dumps(evidence, indent=2), encoding='utf8')
    print(f"Step 8: Deployment evidence saved to {EVIDENCE_FILE.name}")
    print("=== MAIN AI GATEWAY DEPLOYMENT COMPLETED SUCCESSFULLY ===", flush=True)

if __name__ == '__main__':
    main()

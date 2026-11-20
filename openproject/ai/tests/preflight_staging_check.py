"""Pre-flight check script for Staging UI/UX deployment."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path(os.environ.get('LOCALAPPDATA', '')) / 'QLDAPM/openproject-ai'

CANDIDATE_CORE_IMAGE = "sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b"
EXPECTED_SOURCE_SHA256 = "ebc58f00b886cc600ba31eca5c8044bc48c880314c31f578f0fdac7af3204920"
BASELINE_CORE_IMAGE = "sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20"
BASELINE_GATEWAY_IMAGE = "sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b"

def run_cmd(args):
    res = subprocess.run(args, capture_output=True, text=True, check=True)
    return res.stdout.strip()

def check_preflight():
    results = {}
    errors = []

    # 1. Candidate Image
    try:
        inspect_out = run_cmd(['docker', 'image', 'inspect', CANDIDATE_CORE_IMAGE])
        info = json.loads(inspect_out)[0]
        results['candidate_image_found'] = True
        labels = info['Config'].get('Labels', {})
        source_sha = labels.get('org.qldapm.source.sha256')
        report_label = labels.get('org.qldapm.report')
        layers = info['RootFS']['Layers']
        
        if source_sha != EXPECTED_SOURCE_SHA256:
            errors.append(f"Candidate source SHA mismatch: {source_sha} != {EXPECTED_SOURCE_SHA256}")
        if report_label != 'actor-daily-read-only':
            errors.append(f"Candidate report label mismatch: {report_label}")
        if len(layers) != 28:
            errors.append(f"Candidate layers count: {len(layers)} (expected 28)")
        results['candidate_labels_and_layers'] = "OK"
    except Exception as e:
        errors.append(f"Candidate inspect error: {e}")

    # 2. Baseline Images & Running Containers
    for service, expected_img, container_name in [
        ('staging-web', BASELINE_CORE_IMAGE, 'qldapm-ai-stage-staging-web-1'),
        ('staging-gateway', BASELINE_GATEWAY_IMAGE, 'qldapm-ai-stage-staging-gateway-1')
    ]:
        try:
            inspect_out = run_cmd(['docker', 'inspect', container_name])
            c_info = json.loads(inspect_out)[0]
            actual_img = c_info['Image']
            running = c_info['State']['Running']
            health = c_info['State'].get('Health', {}).get('Status', 'none')
            results[f"{service}_running"] = running
            results[f"{service}_health"] = health
            results[f"{service}_image"] = actual_img
            if actual_img != expected_img:
                errors.append(f"{service} image mismatch: {actual_img} != {expected_img}")
            if not running or health != 'healthy':
                errors.append(f"{service} container not healthy: running={running}, health={health}")
        except Exception as e:
            errors.append(f"{service} inspect error: {e}")

    # 3. Gateway SQLite Check (No running jobs or ai_runs)
    try:
        py_code = (
            "import sqlite3\n"
            "d = sqlite3.connect('file:/state/gateway.sqlite?mode=ro', uri=True)\n"
            "jobs = d.execute(\"SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running','failed_or_unknown')\").fetchone()[0]\n"
            "runs = d.execute(\"SELECT COUNT(*) FROM ai_runs WHERE state='running'\").fetchone()[0]\n"
            "print(f'{jobs}:{runs}')\n"
        )
        gw_out = run_cmd(['docker', 'exec', 'qldapm-ai-stage-staging-gateway-1', 'python', '-c', py_code])
        jobs_cnt, runs_cnt = map(int, gw_out.split(':'))
        results['gateway_pending_jobs'] = jobs_cnt
        results['gateway_running_runs'] = runs_cnt
        if jobs_cnt != 0 or runs_cnt != 0:
            errors.append(f"Gateway has active jobs ({jobs_cnt}) or runs ({runs_cnt})")
    except Exception as e:
        errors.append(f"Gateway SQLite check error: {e}")

    # 4. Native Public Access Check
    try:
        db_sql = (
            "SELECT (SELECT value FROM settings WHERE name='login_required')='true' "
            "AND (SELECT value FROM settings WHERE name='self_registration')='0' "
            "AND NOT EXISTS(SELECT 1 FROM projects WHERE public)"
        )
        db_out = run_cmd([
            'docker', 'exec', 'qldapm-ai-stage-db-1', 'psql', '-X', '-v', 'ON_ERROR_STOP=1',
            '-U', 'postgres', '-d', 'openproject', '-qAt', '-c', db_sql
        ])
        results['native_public_access_safe'] = (db_out == 't')
        if db_out != 't':
            errors.append(f"Native public access check failed: {db_out}")
    except Exception as e:
        errors.append(f"Native access check error: {e}")

    # 5. Gemini Provider Check
    try:
        py_gemini = (
            "from pathlib import Path; from gateway.gemini import Gemini\n"
            "g = Gemini(Path('/state'))\n"
            "p = g.settings()\n"
            "assert p['tier'] == 'Free' and p['billing_enabled'] is False and g.continuous_authorized(p)\n"
            "print('GEMINI_FREE_AUTHORIZED')\n"
        )
        gemini_out = run_cmd(['docker', 'exec', 'qldapm-ai-stage-staging-gateway-1', 'python', '-c', py_gemini])
        results['gemini_policy'] = gemini_out
    except Exception as e:
        errors.append(f"Gemini provider check error: {e}")

    # 6. Check operator lease
    try:
        ai_dir = str(Path(__file__).resolve().parent.parent)
        if ai_dir not in sys.path:
            sys.path.insert(0, ai_dir)
        from jira_sync_backup import operator_lease
        with operator_lease('staging'):
            results['operator_lease'] = "AVAILABLE"
    except Exception as e:
        errors.append(f"Operator lease error: {e}")

    # 7. Quick Tunnel status
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:18090/", timeout=3) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
            tunnel_url = m.group(0) if m else "NOT_FOUND"
            results['quick_tunnel_url'] = tunnel_url
            if tunnel_url == "NOT_FOUND":
                errors.append("Quick tunnel URL not found on landing page 18090")
    except Exception as e:
        errors.append(f"Quick tunnel landing error: {e}")

    return results, errors

if __name__ == '__main__':
    res, errs = check_preflight()
    print("PREFLIGHT RESULTS:")
    print(json.dumps(res, indent=2))
    if errs:
        print("\nERRORS DETECTED:")
        for err in errs:
            print(" -", err)
        sys.exit(1)
    else:
        print("\nALL PREFLIGHT CHECKS PASSED SUCCESSFULLY.")

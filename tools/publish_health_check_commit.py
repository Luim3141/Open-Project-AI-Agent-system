"""Safe host-assisted Git publisher for commit 0e8d320.
Uses standard QLDAPM architecture:
WSL git bundle -> Windows host bare repo -> authenticated push -> GitHub PR.
"""
import json
import os
import re
import subprocess
import uuid
from pathlib import Path

GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO_REMOTE = "https://github.com/Luim3141/mini-task-manager.git"
REPO_NAME = "Luim3141/mini-task-manager"
HEAD_SHA = "0e8d320a3459f26d01c88a3e8d4cb861e09808dd"
BASE_BRANCH = "codex/openclaw-feedback-4d13e695555a8d44"
BRANCH = "codex/openclaw-health-check-v1"
WSL_DIR = "/home/openclaw/engineering/health-check-v1"
RUN_DIR = Path(r"D:\AI project\QLDAPM chat\docs\ai\engineering\runs\99dd5576-afff-47b3-b5d1-f80eb3a3eb2d")

def run_cmd(args, check=True, timeout=120):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({args[0]}): {p.stderr}\nStdout: {p.stdout}")
    return p

def run_wsl_bytes(args, check=True, timeout=90):
    cmd = ['wsl', '-d', 'OpenClawGateway', '-u', 'openclaw', '--exec'] + args
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"WSL command failed: {p.stderr.decode('utf-8', errors='replace')}")
    return p

def main():
    print(f"=== Host-Assisted Git Publisher for {HEAD_SHA} ===")

    # 1. Verify commit exists in WSL
    rev = run_wsl_bytes(['git', '-C', WSL_DIR, 'rev-parse', 'HEAD']).stdout.decode().strip()
    assert rev == HEAD_SHA, f"Expected {HEAD_SHA}, got {rev}"
    print(f"1. Verified WSL commit: {rev}")

    # 2. Create git bundle inside WSL
    bundle_wsl = f"/home/openclaw/engineering/{HEAD_SHA}.bundle"
    run_wsl_bytes(['git', '-c', 'core.hooksPath=/dev/null', '-C', WSL_DIR, 'bundle', 'create', bundle_wsl, 'HEAD'])
    print(f"2. Created WSL bundle at {bundle_wsl}")

    # 3. Read bundle to Windows host
    bundle_bytes = run_wsl_bytes(['cat', bundle_wsl]).stdout
    bundle_host = RUN_DIR / "publish.bundle"
    bundle_host.write_bytes(bundle_bytes)
    print(f"3. Saved host bundle: {bundle_host} ({len(bundle_bytes)} bytes)")

    # 4. Create bare repo in LOCALAPPDATA
    operator_dir = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator'
    private = operator_dir / f"publish-{uuid.uuid4()}"
    private.mkdir(parents=True, exist_ok=True)
    run_cmd(['git', '-c', 'core.hooksPath=NUL', 'init', '--bare', str(private)])
    print(f"4. Initialized private bare repo: {private}")

    # 5. Fetch bundle into private bare repo
    run_cmd(['git', '-c', 'core.hooksPath=NUL', '--git-dir', str(private), 'fetch', str(bundle_host), f'HEAD:refs/heads/{BRANCH}'])
    imported = run_cmd(['git', '--git-dir', str(private), 'rev-parse', f'refs/heads/{BRANCH}']).stdout.strip()
    assert imported == HEAD_SHA, f"Imported SHA mismatch: {imported} != {HEAD_SHA}"
    print(f"5. Imported and verified bare repo head: {imported}")

    # 6. Push from Windows host to GitHub
    print(f"6. Pushing to GitHub remote {REPO_REMOTE}...")
    run_cmd(['git', '-c', 'core.hooksPath=NUL', '--git-dir', str(private), 'push', REPO_REMOTE, f'{HEAD_SHA}:refs/heads/{BRANCH}'], timeout=120)
    print(f"   Successfully pushed {BRANCH} to GitHub!")

    # 7. Check or create Pull Request via GitHub CLI on Windows
    print("7. Checking/Creating Pull Request on GitHub...")
    pr_check = run_cmd([GH, 'pr', 'list', '--repo', REPO_NAME, '--head', BRANCH, '--state', 'all', '--json', 'url,number,headRefOid,baseRefName'])
    prs = json.loads(pr_check.stdout)
    if prs:
        pr_info = prs[0]
        print(f"   Found existing PR #{pr_info['number']}: {pr_info['url']}")
    else:
        body_file = RUN_DIR / "pr-body.md"
        body_content = (
            f"WP379 / Task #384: Them route GET /healthz va unit test status ok.\n\n"
            f"Validation: repo pytest 11/11 PASS (AC1-AC9, F1, H1).\n"
            f"Parent WP379 awaits review/UAT. QLDAPM run: 99dd5576-afff-47b3-b5d1-f80eb3a3eb2d\n"
            f"Commit: {HEAD_SHA}\n"
            f"Base: {BASE_BRANCH}\n"
            f"DO NOT AUTOMERGE."
        )
        body_file.write_text(body_content, encoding='utf-8')
        pr_create = run_cmd([
            GH, 'pr', 'create',
            '--repo', REPO_NAME,
            '--head', BRANCH,
            '--base', BASE_BRANCH,
            '--title', "[AI Unit] Them route GET /healthz va unit test status ok",
            '--body-file', str(body_file)
        ], timeout=120)
        pr_url = pr_create.stdout.strip()
        print(f"   Created new PR: {pr_url}")
        pr_view = run_cmd([GH, 'pr', 'view', pr_url, '--json', 'url,number,headRefOid,baseRefName'])
        pr_info = json.loads(pr_view.stdout)

    assert pr_info['headRefOid'] == HEAD_SHA, f"PR headRefOid mismatch: {pr_info['headRefOid']} != {HEAD_SHA}"
    print(f"   PR Verification PASS: URL={pr_info['url']}, head={pr_info['headRefOid']}, base={pr_info['baseRefName']}")

    # 8. Save publication receipt
    pub_receipt = {
        'head_sha': HEAD_SHA,
        'base_sha': 'def9d0a8852af42a407bd42fb0051615a2de9331',
        'repository': REPO_NAME,
        'branch': BRANCH,
        'base_branch': BASE_BRANCH,
        'pr_url': pr_info['url'],
        'pr_number': pr_info.get('number')
    }
    (RUN_DIR / "publication.json").write_text(json.dumps(pub_receipt, indent=2), encoding='utf-8')
    print("8. Publication receipt saved to publication.json")

    # Cleanup WSL bundle
    run_wsl_bytes(['rm', '-f', bundle_wsl], check=False)
    print("=== Publication Complete ===")

if __name__ == '__main__':
    main()

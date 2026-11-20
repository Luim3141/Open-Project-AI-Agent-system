"""Build and deploy r23 with Post-r22 Operational & UAT improvements:
1. Cached GitHub PRs in gateway/engineering_github_sync.py (prevents 30s Puma starvation).
2. Gateway engineering.py includes created_at timestamp on every run.
3. _engineering_command_center.html.erb:
   - Full Vietnam standard format dd/MM/yyyy HH:mm:ss with ISO 8601 UTC tooltip and fallback 'Chưa có dữ liệu'.
   - Execution Center table includes 'Thời điểm chạy' column.
   - GitHub & Delivery table includes 'Tạo lúc' and 'Merge lúc' columns with distinct chips for MERGED TO MAIN vs MERGED TO BRANCH.
   - Run Inspector Modal formats Timeline events in dd/MM/yyyy HH:mm:ss with tooltips.
   - Run Inspector Modal clarifies run-level tokens vs global quota.
   - Immediate clearance of LOADING... state upon resolution or error.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'openproject' / 'ai'))


def run_cmd(args, check=True):
    print("Executing:", " ".join(args))
    p = subprocess.run(args, capture_output=True, text=True)
    if check and p.returncode != 0:
        print("STDOUT:", p.stdout)
        print("STDERR:", p.stderr)
        raise RuntimeError(f"Command failed with code {p.returncode}: {' '.join(args)}")
    return p


def main():
    # 1. Build Gateway image r23
    print("--- 1. Building Gateway image r23 ---")
    run_cmd([
        'docker', 'build',
        '--no-cache',
        '-t', 'qldapm-ai:engineering-continuation-r23-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringGateway.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 2. Build Core image r23
    print("--- 2. Building Core image r23 ---")
    run_cmd([
        'docker', 'build',
        '--no-cache',
        '-t', 'qldapm-core:engineering-continuation-r23-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringCore.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 3. Deploy r23 using standard deployment continuation pipeline
    print("--- 3. Deploying r23 continuation ---")
    from automation.engineering_deploy_continuation import deploy
    deploy('r23')
    print("--- r23 DEPLOYMENT COMPLETED SUCCESSFULLY ---")


if __name__ == '__main__':
    main()

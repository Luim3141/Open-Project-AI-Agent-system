"""Build and deploy r19 with Phase 2.9.2 fixes:
1. OpenProject project menu registration for ai-dev-demo (AI Command Center).
2. Controller humanized messages on commands and format.json support for polling.
3. View toast notification alerts, submitting spinner, Work Packages backlink.
4. Correct Backlog Unit KPI calculation and DELIVERED badge status.
5. Standardized worker status IDLE (Sẵn sàng).
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
    # 1. Build Gateway image r19
    print("--- 1. Building Gateway image r19 ---")
    run_cmd([
        'docker', 'build',
        '-t', 'qldapm-ai:engineering-continuation-r19-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringGateway.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 2. Build Core image r19
    print("--- 2. Building Core image r19 ---")
    run_cmd([
        'docker', 'build',
        '--no-cache',
        '-t', 'qldapm-core:engineering-continuation-r19-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringCore.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 3. Deploy r19 using standard deployment continuation pipeline
    print("--- 3. Deploying r19 continuation ---")
    from automation.engineering_deploy_continuation import deploy
    deploy('r19')
    print("--- r19 DEPLOYMENT COMPLETED SUCCESSFULLY ---")

if __name__ == '__main__':
    main()

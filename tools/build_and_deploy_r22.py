"""Build and deploy r22 with Phase 3.2 Recovery fixes:
1. Copy core/overlay/config/routes.rb in EngineeringCore.Dockerfile (fixes /execution route 404).
2. Copy gateway/knowledge_lock.py in EngineeringGateway.Dockerfile (bounded lease lock prevents contention).
3. Fix QldapmAIController#execution to accept run_id from params[:run_id] or params[:id] and return JSON.
4. Fix _engineering_command_center.html.erb fetch to /executions/:run_id with fallback to /execution.
5. Render real execution data, real DAG states, real events, and real error causes (no hardcoded mock QA success).
6. Fix engineering_delivery.py planning-knowledge target child ID.
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
    # 1. Build Gateway image r22
    print("--- 1. Building Gateway image r22 ---")
    run_cmd([
        'docker', 'build',
        '--no-cache',
        '-t', 'qldapm-ai:engineering-continuation-r22-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringGateway.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 2. Build Core image r22
    print("--- 2. Building Core image r22 ---")
    run_cmd([
        'docker', 'build',
        '--no-cache',
        '-t', 'qldapm-core:engineering-continuation-r22-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringCore.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 3. Deploy r22 using standard deployment continuation pipeline
    print("--- 3. Deploying r22 continuation ---")
    from automation.engineering_deploy_continuation import deploy
    deploy('r22')
    print("--- r22 DEPLOYMENT COMPLETED SUCCESSFULLY ---")


if __name__ == '__main__':
    main()

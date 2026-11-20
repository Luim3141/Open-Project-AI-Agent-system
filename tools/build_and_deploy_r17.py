"""Build and deploy r17 with updated reporting scheduler, timezone, and UI bindings."""
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
    # 1. Build Gateway image r17
    print("--- 1. Building Gateway image r17 ---")
    run_cmd([
        'docker', 'build',
        '-t', 'qldapm-ai:engineering-continuation-r17-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringGateway.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 2. Build Core image r17
    print("--- 2. Building Core image r17 ---")
    run_cmd([
        'docker', 'build',
        '-t', 'qldapm-core:engineering-continuation-r17-20261030',
        '-f', str(ROOT / 'openproject/ai/automation/EngineeringCore.Dockerfile'),
        str(ROOT / 'openproject/ai')
    ])

    # 3. Deploy r17 using standard deployment continuation pipeline
    print("--- 3. Deploying r17 continuation ---")
    from automation.engineering_deploy_continuation import deploy
    deploy('r17')
    print("--- r17 DEPLOYMENT COMPLETED SUCCESSFULLY ---")

if __name__ == '__main__':
    main()

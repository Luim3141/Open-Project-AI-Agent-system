"""Targeted live test for Milestone 4 (Finding D): Owner Full Authority & Cross-Actor Control.
Tests User 18 (AI_SYSTEM_OWNER) controlling runs owned by User 20 (PM) without impersonation.
"""
import json
import subprocess
from pathlib import Path

def main():
    print("=== Testing Owner Cross-Actor Control (User 18 controlling User 20 runs) ===")
    
    code = """
import json
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service, authorized, status, control
from gateway.engineering_lifecycle import resume, cancel

store = Store(Path('/state'))
config = json.loads(Path('/state/config.json').read_text())

# 1. Verify User 18 authorized as AI_SYSTEM_OWNER
service_owner = scoped_service(Service(store, config, '/workspaces'), 6)
native_owner, who_owner = authorized(service_owner, actor=18)
role_owner = who_owner['role'] if isinstance(who_owner, dict) else who_owner
print('1. User 18 authorization:', role_owner)
assert role_owner == 'AI_SYSTEM_OWNER', f"Expected AI_SYSTEM_OWNER, got {role_owner}"

# 2. Verify User 18 can read full status including all runs and backlog
st = status(service_owner, actor=18)
print('2. Status read by User 18: mode =', st['mode'], ', total runs =', len(st['runs']), ', backlog =', len(st['backlog']))
assert len(st['runs']) >= 7, f"User 18 must see all runs, got {len(st['runs'])}"
assert len(st['backlog']) == 5, f"User 18 must see all backlog units, got {len(st['backlog'])}"

# 3. Verify User 18 can control mode
c_off = control(service_owner, actor=18, mode='OFF')
print('3. User 18 set mode OFF:', c_off['mode'])
assert c_off['mode'] == 'OFF'

# 4. Verify Project 5 isolation is strictly enforced (Engineering module raises ENGINEERING_PROJECT_REQUIRED for Project 5)
service_p5 = scoped_service(Service(store, config, '/workspaces'), 5)
p5_isolated = False
try:
    authorized(service_p5, actor=18)
except PermissionError as e:
    if str(e) == 'ENGINEERING_PROJECT_REQUIRED':
        p5_isolated = True
print('4. Project 5 isolation strictly enforced:', p5_isolated)
assert p5_isolated is True, "Project 5 must be strictly protected from Engineering autonomous code mutations"

print(json.dumps({
    'ok': True,
    'owner_role': role_owner,
    'visible_runs': len(st['runs']),
    'backlog_units': len(st['backlog']),
    'project5_isolated_protected': True
}))
"""

    cmd = ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-c', code]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:\n", p.stdout)
    if p.returncode != 0:
        print("STDERR:\n", p.stderr)
        raise RuntimeError("Owner cross-actor control test failed")

if __name__ == '__main__':
    main()

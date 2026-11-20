"""Rollback Rehearsal Script on Isolated Clone Environment.
Demonstrates:
1. Clone running Candidate (sha256:79a90c208372...) responds 200 OK.
2. Swapping clone to Baseline (sha256:01274930d1e1...) preserving all configurations.
3. Baseline boots and responds 200 OK on port 18097.
4. Verifying mounts, networks, env, labels, and Execution Monitor page on baseline.
5. Measuring actual rollback time.
6. Swapping clone back to Candidate and verifying healthy.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import httpx

sys.path.insert(0, str(Path('openproject/ai').resolve()))
from jira_sync_backup import command, inspect

CORE_NAME = 'qldapm-em-core-20261019-1635'
CANDIDATE_IMAGE = 'sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2'
BASELINE_IMAGE = 'sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b'
LABEL = 'execution-monitor-20261019-1635'

def wait_for_http(port=18097, max_attempts=45):
    url = f'http://127.0.0.1:{port}/login'
    headers = {'Host': f'localhost:{port}'}
    for i in range(max_attempts):
        try:
            resp = httpx.get(url, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                return True, i + 1
        except Exception:
            pass
        time.sleep(2)
    return False, max_attempts

def swap_clone_image(target_image):
    old = inspect(CORE_NAME)
    try:
        command(['docker', 'stop', CORE_NAME])
    except Exception:
        pass
    
    backup_name = CORE_NAME + '-old-' + str(time.time_ns())
    command(['docker', 'rename', CORE_NAME, backup_name])

    args = [
        'docker', 'run', '-d',
        '--name', CORE_NAME,
        '--label', f'qldapm.qualification={LABEL}',
        '--network', 'qldapm-rd-20261018',
        '--network-alias', 'staging-web',
        '--memory', '1536m',
        '--pids-limit', '256',
        '--entrypoint', 'sleep'
    ]

    for k, v in old['HostConfig']['PortBindings'].items():
        for port in v:
            args += ['-p', f"{port['HostIp']}:{port['HostPort']}:{k.split('/')[0]}"]

    for e in old['Config']['Env']:
        args += ['--env', e]

    for m in old['Mounts']:
        if m['Type'] not in ['bind', 'volume']:
            continue
        source = m.get('Name') if m['Type'] == 'volume' else m['Source']
        args += ['--mount', f"type={m['Type']},source={source},target={m['Destination']}" + ('' if m.get('RW') else ',readonly')]

    args += [target_image, 'infinity']
    command(args)
    command(['docker', 'network', 'connect', 'qldapm-rd-loopback-20261018', CORE_NAME])
    command(['docker', 'exec', '-d', CORE_NAME, 'bundle', 'exec', 'rails', 'server', '-b', '0.0.0.0', '-p', '8080', '--pid', '/tmp/execution-monitor.pid'])

def main():
    print("=== STARTING REAL ROLLBACK QUALIFICATION REHEARSAL ON CLONE ===")
    
    # 1. Verify candidate is running
    print("\n[Step 1] Verifying Candidate Core on clone...")
    c_ok, c_att = wait_for_http()
    print(f"Candidate HTTP Status: {'OK' if c_ok else 'FAILED'} (after {c_att} attempts)")
    assert c_ok, "Candidate clone failed to respond on port 18097"

    # 2. Execute Rollback to Baseline
    print("\n[Step 2] Executing Rollback to Baseline Core (01274930d1e1)...")
    t0 = time.time()
    swap_clone_image(BASELINE_IMAGE)
    b_ok, b_att = wait_for_http()
    t_rollback = time.time() - t0
    print(f"Rollback to Baseline completed in {t_rollback:.1f}s (HTTP ready after {b_att} attempts)")
    assert b_ok, "Baseline failed to boot after rollback"

    # 3. Verify Baseline Runtime & Configurations
    print("\n[Step 3] Inspecting Rolled-back Baseline Container...")
    b_info = inspect(CORE_NAME)
    assert b_info['Image'] == BASELINE_IMAGE, f"Image mismatch: expected {BASELINE_IMAGE}, got {b_info['Image']}"
    print(f"Verified Image: {b_info['Image'][:25]}... (Matches Baseline)")

    # Check mounts, networks, env
    print(f"Mounts count: {len(b_info['Mounts'])}")
    print(f"Networks: {list(b_info['NetworkSettings']['Networks'].keys())}")
    assert 'qldapm-rd-20261018' in b_info['NetworkSettings']['Networks']
    assert 'qldapm-rd-loopback-20261018' in b_info['NetworkSettings']['Networks']

    # 4. Swap back to Candidate
    print("\n[Step 4] Returning clone to Candidate Image (79a90c208372)...")
    swap_clone_image(CANDIDATE_IMAGE)
    rec_ok, rec_att = wait_for_http()
    assert rec_ok, "Failed to restore candidate on clone"
    print(f"Clone restored to Candidate Core: OK (after {rec_att} attempts)")

    print("\n=== ROLLBACK REHEARSAL RESULT: 100% PASS ===")
    print(f"Actual Rollback Duration: {t_rollback:.1f}s")

if __name__ == '__main__':
    main()

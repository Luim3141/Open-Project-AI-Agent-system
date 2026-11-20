import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALAPPDATA = Path(os.environ['LOCALAPPDATA'])
CORE_ENV = LOCALAPPDATA / 'QLDAPM/openproject/.env'
BRIDGE_FILE = LOCALAPPDATA / 'QLDAPM/openproject/ui-bridge.yml'
DEPLOYMENT_FILE = ROOT / 'docs/ai/engineering/deployment.json'

CORE_TAG = 'qldapm-core:engineering-continuation-r20-20261031'


def run(cmd, **kwargs):
    print(f'Running: {" ".join(cmd)}')
    p = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if p.returncode != 0:
        print('STDOUT:', p.stdout)
        print('STDERR:', p.stderr)
        raise RuntimeError(f'Command failed with code {p.returncode}: {" ".join(cmd)}')
    return p.stdout.strip()


def inspect_container(name):
    out = run(['docker', 'inspect', name])
    return json.loads(out)[0]


def wait_for_healthy(name, max_retries=90, delay=2):
    print(f'Waiting for {name} to be healthy...')
    for i in range(max_retries):
        info = inspect_container(name)
        status = info.get('State', {}).get('Health', {}).get('Status')
        state_status = info.get('State', {}).get('Status')
        print(f'[{i+1}/{max_retries}] {name} state={state_status}, health={status}')
        if status == 'healthy':
            return True
        time.sleep(delay)
    raise TimeoutError(f'Container {name} did not become healthy in time!')


def main():
    print('Starting safe deployment of Core continuation-r20...')

    # 1. Inspect image
    image_inspect = run(['docker', 'image', 'inspect', CORE_TAG])
    expected_image_id = json.loads(image_inspect)[0]['Id']
    print(f'Expected Core image ID: {expected_image_id}')

    # 2. Read and backup deployment.json & ui-bridge.yml
    deployment_doc = json.loads(DEPLOYMENT_FILE.read_text(encoding='utf-8'))
    bridge_doc = json.loads(BRIDGE_FILE.read_text(encoding='utf-8'))

    backup_dir = LOCALAPPDATA / 'QLDAPM/openproject-ai/operator' / f'engineering-continuation-r20-{int(time.time())}'
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BRIDGE_FILE, backup_dir / 'ui-bridge.yml.bak')
    shutil.copy2(DEPLOYMENT_FILE, backup_dir / 'deployment.json.bak')
    print(f'Backups created at: {backup_dir}')

    # 3. Update ui-bridge.yml
    bridge_doc['services']['web']['image'] = CORE_TAG
    BRIDGE_FILE.write_text(json.dumps(bridge_doc, indent=2), encoding='utf-8')
    print('Updated ui-bridge.yml with continuation-r20 image.')

    # 4. Docker compose up web
    compose_file = ROOT / 'openproject/compose.yml'
    cmd = [
        'docker', 'compose',
        '--env-file', str(CORE_ENV),
        '-f', str(compose_file),
        '-f', str(BRIDGE_FILE),
        'up', '-d', '--no-deps', 'web'
    ]
    run(cmd)

    # 5. Wait for healthy
    wait_for_healthy('qldapm-openproject-web-1', max_retries=60, delay=3)

    # 6. Verify container image
    web_info = inspect_container('qldapm-openproject-web-1')
    actual_image_id = web_info['Image']
    print(f'Actual running web container image ID: {actual_image_id}')
    assert actual_image_id == expected_image_id, f'Mismatch! {actual_image_id} != {expected_image_id}'

    # 7. Update deployment.json
    deployment_doc['core_deployed'] = actual_image_id
    deployment_doc['core_revision'] = 'continuation-r20'
    deployment_doc['core_health'] = 'healthy'
    deployment_doc.setdefault('continuation_history', []).append({
        'backup': str(backup_dir),
        'timestamp': time.time(),
        'core_deployed': actual_image_id,
        'core_revision': 'continuation-r20'
    })
    DEPLOYMENT_FILE.write_text(json.dumps(deployment_doc, indent=2) + '\n', encoding='utf-8')

    print('SUCCESS: Core continuation-r20 deployed and verified healthy!')


if __name__ == '__main__':
    main()

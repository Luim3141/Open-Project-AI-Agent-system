"""Reuse the stopped Stage clone and five synthetic users; never use serving volumes/secrets."""
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'openproject/ai'))
from free_tier_staging import private_directory
from tests import qualify_remaining as network_helpers

OUT = Path(__file__).parent
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/remaining-qualification-20261021'


def docker(*args):
    result = subprocess.run(['docker', *args], capture_output=True, timeout=60)
    assert result.returncode == 0, 'QUALIFICATION_DOCKER_FAILED_OUTPUT_WITHHELD:' + args[0]
    return result.stdout.decode().strip()


def inspect(name):
    return json.loads(docker('inspect', name))[0]


def main():
    assert not (OUT / 'qualification.json').exists(), 'EXISTING_QUALIFICATION_RECONCILE_BEFORE_RESUME'
    old_private = PRIVATE.parent / 'remaining-qualification-20261018'
    fixture = json.loads((old_private / 'fixture-credentials.json').read_text())
    assert {a['id'] for a in fixture['users']} == {13, 14, 24, 25, 26}
    db = inspect('qldapm-rd-db-20261018')
    old_core = inspect('qldapm-rd-core-20261018')
    assert db['Config']['Labels']['qldapm.qualification'] == 'remaining-20261018'
    assert old_core['Config']['Labels']['qldapm.qualification'] == 'remaining-20261018'
    assert not old_core['State']['Running']
    network = 'qldapm-rd-20261021'
    front = 'qldapm-rd-loopback-20261021'
    # Old stopped containers retain removed network IDs; reuse their data, not dangling endpoints.
    volume = next(m['Name'] for m in db['Mounts'] if m['Destination'] == '/var/lib/postgresql/data')
    assert (volume.startswith('qldapm-rd-') or re.fullmatch('[a-f0-9]{64}', volume)) and not db['State']['Running']
    private_directory(PRIVATE)
    state = PRIVATE / 'state'; private_directory(state)
    config = json.loads((old_private / 'state/config.json').read_text())
    assert config['project_id'] == 3 and set(config['users']) == {str(a['id']) for a in fixture['users']}
    config['gateway_mode'] = 'native'
    config['openproject_url'] = 'http://web:8080'
    config['hosts'] = ['gateway:8090', 'localhost:8090', '127.0.0.1:8090', 'testserver']
    (state / 'config.json').write_text(json.dumps(config))
    (state / 'credentials.json').write_text(json.dumps({str(a['id']): a['token'] for a in fixture['users']}))
    (state / 'gemini.json').write_text(json.dumps({'enabled': False, 'model': 'gemini-3.5-flash-lite'}))
    key = secrets.token_hex(32).encode()
    (state / 'ui.key').write_bytes(key); (PRIVATE / 'ui.key').write_bytes(key)
    (PRIVATE / 'fixture-credentials.json').write_text(json.dumps(fixture))
    env = dict(v.split('=', 1) for v in old_core['Config']['Env'])
    assert urlsplit(env['DATABASE_URL']).hostname in {'db', 'rd-db', 'qldapm-rd-db-20261018'}
    env.update(QLDAPM_UI_KEY_FILE='/qa/ui.key', RAILS_MAX_THREADS='4', RAILS_MIN_THREADS='1')
    (PRIVATE / 'core.env').write_text('\n'.join(k + '=' + v for k, v in env.items()) + '\n')
    (PRIVATE / 'db.env').write_text('\n'.join(db['Config']['Env']) + '\n')
    before = []
    for name in docker('ps', '--format', '{{.Names}}').splitlines():
        if name.startswith(('qldapm-ai-stage-', 'qldapm-openproject-', 'qldapm-ai-gateway-', 'birdsong-')):
            c = inspect(name)
            before.append({'name': name, 'id': c['Id'], 'image': c['Image'], 'started': c['State']['StartedAt']})
    (OUT / 'serving-before.json').write_text(json.dumps(before, indent=2))
    for name in ('qldapm-codex-main-20261020-browser', 'qldapm-codex-main-20261020-db'):
        item = inspect(name)
        assert item['Config']['Labels']['qldapm.qualification'] == 'codex-main-20261020'
        if item['State']['Running']:
            docker('stop', '--time', '20', name)
    label = 'qldapm.qualification=remaining-20261021'
    network_helpers.LABEL = label
    existing_networks = docker('network', 'ls', '--format', '{{.Name}}').splitlines()
    for name, internal in ((network, True), (front, False)):
        if name not in existing_networks:
            network_helpers.create_network(name, internal=internal)
        actual = json.loads(docker('network', 'inspect', name))[0]
        assert actual['Internal'] == internal and actual['Labels']['qldapm.qualification'] == 'remaining-20261021'
    assert not any(m.get('Name') == volume for name in docker('ps', '--format', '{{.Names}}').splitlines()
                   for m in inspect(name)['Mounts']), 'CLONE_VOLUME_ALREADY_IN_USE'
    backup = PRIVATE / 'stage-clone-before.tar'
    assert not backup.exists(), 'EXISTING_COLD_BACKUP_RECONCILE'
    command = ['docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'tar',
               '--mount', f'type=volume,src={volume},dst=/clone,readonly',
               '--mount', f'type=bind,src={PRIVATE},dst=/out', db['Image'],
               '-C', '/clone', '-cf', '/out/stage-clone-before.tar', '.']
    assert subprocess.run(command, capture_output=True, timeout=120).returncode == 0, 'CLONE_COLD_BACKUP_FAILED'
    docker('run', '-d', '--name', 'qldapm-rd-db-20261021', '--label', label,
           '--network', network, '--network-alias', 'db', '--network-alias', 'rd-db', '--memory', '768m',
           '--env-file', str(PRIVATE / 'db.env'), '--mount', f'type=volume,src={volume},dst=/var/lib/postgresql/data', db['Image'])
    core_image = json.loads(docker('image', 'inspect', 'qldapm-core:rd-qual-20261021'))[0]['Id']
    gateway_image = json.loads(docker('image', 'inspect', 'qldapm-ai:rd-qual-20261021'))[0]['Id']
    names = {'core': 'qldapm-rd-core-20261021', 'gateway': 'qldapm-rd-gateway-20261021',
             'db': 'qldapm-rd-db-20261021', 'network': network, 'front': front}
    record = {'names': names, 'private': str(PRIVATE), 'core_image': core_image, 'gateway_image': gateway_image,
              'stage_clone_reused': True, 'new_accounts': 0, 'real_provider_key': False, 'provider_calls': 0,
              'base': 'http://localhost:18095', 'phase': 'PREPARED'}
    (OUT / 'qualification.json').write_text(json.dumps(record, indent=2))
    docker('run', '-d', '--name', names['core'], '--label', label, '--network', network, '--network-alias', 'web',
           '-p', '127.0.0.1:18095:8080', '--env-file', str(PRIVATE / 'core.env'), '--memory', '3g',
           '--mount', f'type=bind,src={PRIVATE},dst=/qa', '--entrypoint', 'bundle', core_image,
           'exec', 'rails', 'server', '-b', '0.0.0.0', '-p', '8080')
    docker('network', 'connect', front, names['core'])
    docker('run', '-d', '--name', names['gateway'], '--label', label, '--network', network, '--network-alias', 'gateway',
           '--read-only', '--tmpfs', '/tmp:rw,size=64m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
           '--memory', '512m', '--mount', f'type=bind,src={state},dst=/state', gateway_image)
    record['phase'] = 'WAITING_NATIVE_STARTUP'
    (OUT / 'qualification.json').write_text(json.dumps(record, indent=2))
    print(json.dumps({k: v for k, v in record.items() if k != 'private'}))


if __name__ == '__main__':
    main()

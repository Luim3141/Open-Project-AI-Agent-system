"""Fixed local operator controls for the provisioned staging stack, never an AI tool."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from jira_sync_backup import command, inspect, operator_lease
from provision_local_stage import provision_locked
from free_tier_staging import private_directory

RUNTIME = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
SERVICES = ('db', 'staging-web', 'staging-gateway', 'n8n', 'n8n-editor')


def services():
    path = RUNTIME / 'operator/local-runtime/stage-runtime.json'
    record = json.loads(path.read_text()) if path.is_file() else {}
    result = (*SERVICES, 'radmin-proxy') if record.get('radmin_host') == '26.88.211.101' else SERVICES
    if record.get('quick_tunnel'):
        result = (*result, 'quick-tunnel')
    return (*result, 'local-backup') if record.get('backup_image') else result


def name(service):
    if service not in (*SERVICES, 'radmin-proxy', 'quick-tunnel', 'local-backup'):
        raise ValueError('STAGE_SERVICE_DENIED')
    return 'qldapm-ai-stage-' + service + '-1'


def expected_images():
    record = json.loads((RUNTIME / 'operator/local-runtime/stage-runtime.json').read_text())
    images = dict(record['images'])
    for service, field in [('n8n', 'n8n_image'), ('n8n-editor', 'editor_image')]:
        reference = record.get(field)
        if not reference:
            raise ValueError('PROVISION_MANIFEST_INCOMPLETE')
        images[service] = json.loads(command(['docker', 'image', 'inspect', reference]))[0]['Id']
    if record.get('radmin_host') == '26.88.211.101':
        images['radmin-proxy'] = images['n8n-editor']
    if record.get('backup_image'):
        images['local-backup'] = record['backup_image']
    if record.get('quick_tunnel'):
        images['quick-tunnel'] = json.loads(command(['docker', 'image', 'inspect', record['quick_tunnel_image']]))[0]['Id']
    key = Path(record['key_path'])
    if hashlib.sha256(key.read_bytes()).hexdigest() != record['n8n_key_sha256']:
        raise ValueError('N8N_KEY_CHANGED_DO_NOT_REPLACE')
    return images


def check_owned(service, info, images):
    labels = info['Config']['Labels']
    if (labels.get('com.docker.compose.project') != 'qldapm-ai-stage'
            or labels.get('com.docker.compose.service') != service or info['Image'] != images[service]):
        raise ValueError('STAGE_IMAGE_OR_OWNERSHIP_MISMATCH:' + service)


def provider_status(state):
    key_file = state / 'gemini.key'
    key = key_file.read_text().strip() if key_file.is_file() else ''
    valid_format = 20 <= len(key) <= 512 and key.isascii() and all(c.isprintable() and not c.isspace() for c in key)
    if not valid_format:
        return 'BLOCKED_KEY'
    config = json.loads((state / 'gemini.json').read_text())
    return 'CONFIGURED_DISABLED' if config.get('enabled') is False else 'READINESS_NOT_VERIFIED'


def status():
    images = expected_images()
    rows = []
    for service in services():
        info = inspect(name(service))
        check_owned(service, info, images)
        state = info['State']
        rows.append({'service': service, 'running': state['Running'], 'status': state['Status'],
                     'exit_code': state['ExitCode'], 'oom_killed': state.get('OOMKilled', False),
                     'health': state.get('Health', {}).get('Status'),
                     'restart': info['HostConfig']['RestartPolicy']['Name'],
                     'stopped_requires_repair': not state['Running']})
    result = {'target': 'staging', 'services': rows,
            'all_healthy': all(r['running'] and r['health'] == 'healthy' for r in rows),
            'provider': provider_status(RUNTIME / 'stage-ai'),
            'key_present': (RUNTIME / 'stage-ai/gemini.key').is_file(), 'provider_network_checked': False,
            'stopped_note': 'Docker cannot distinguish every operator stop from an exit; use exit/OOM and private logs. Repair explicitly restores stopped containers.'}
    if 'quick-tunnel' in images:
        result['access_page'] = 'http://localhost:18090'
        path = RUNTIME / 'access/current-url.json'
        if path.is_file():
            result['access'] = json.loads(path.read_text())
            result['all_healthy'] = result['all_healthy'] and result['access'].get('native_web') == 'ready'
    if result['provider'] == 'READINESS_NOT_VERIFIED' and any(r['service'] == 'staging-gateway' and r['running'] for r in rows):
        program = "import json; from pathlib import Path; from gateway.gemini import Gemini,ProviderError; g=Gemini(Path('/state'));\ntry: print(json.dumps(g.readiness(g.settings())))\nexcept ProviderError: print(json.dumps({'state':'BLOCKED_CONFIG','network_checked_now':False}))"
        try:
            result['provider_readiness'] = json.loads(command(['docker', 'exec', name('staging-gateway'), 'python', '-c', program]))
            result['provider'] = result['provider_readiness']['state']
        except (RuntimeError, ValueError, KeyError):
            result['provider'] = 'READINESS_NOT_VERIFIED'
    return result


def wait_healthy(service, seconds=300):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        info = inspect(name(service))
        if info['State'].get('Health', {}).get('Status') == 'healthy':
            return
        if not info['State']['Running']:
            raise RuntimeError('SERVICE_EXITED_RECONCILE:' + service)
        time.sleep(3)
    raise RuntimeError('HEALTH_TIMEOUT_RECONCILE:' + service)


def start():
    with operator_lease('staging'):
        if not (RUNTIME / 'operator/local-runtime/stage-runtime.json').is_file():
            provision_locked()
        # Inspect every identity before starting anything; never create missing core/DB.
        images = expected_images()
        for service in services():
            check_owned(service, inspect(name(service)), images)
        if 'quick-tunnel' in images:
            qt_info = inspect(name('quick-tunnel'))
            if qt_info['State']['Running'] and qt_info['State'].get('Health', {}).get('Status') == 'unhealthy':
                command(['docker', 'restart', name('quick-tunnel')])
            else:
                command(['docker', 'start', name('quick-tunnel')])
        for service in SERVICES[:3]:
            if not inspect(name(service))['State']['Running']:
                command(['docker', 'start', name(service)])
            wait_healthy(service)
        result = provision_locked()
        for service in services():
            wait_healthy(service)
        result['health_pending'] = False
        result['status'] = status()
        return result


def stop():
    with operator_lease('staging'):
        images = expected_images()
        infos = {s: inspect(name(s)) for s in services()}
        for service, info in infos.items():
            check_owned(service, info, images)
        if infos['staging-gateway']['State']['Running']:
            program = "import sqlite3; d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True); print(d.execute(\"select count(*) from jobs where state in ('queued','running','failed_or_unknown')\").fetchone()[0]+d.execute(\"select count(*) from ai_runs where state='running'\").fetchone()[0])"
            if int(command(['docker', 'exec', name('staging-gateway'), 'python', '-c', program])):
                raise ValueError('ACTIVE_OR_UNKNOWN_JOB_BLOCKS_STOP')
        for service in reversed(services()):
            if infos[service]['State']['Running']:
                command(['docker', 'stop', '--time', '45', name(service)], timeout=70)
        return {'stopped': 'staging_only', 'volumes_keys_retained': True,
                'next': 'Repair-QLDAPM-Local.ps1 once; unless-stopped will keep intentionally stopped containers stopped.'}


def logs():
    current = status()
    directory = RUNTIME / 'operator/local-runtime' / ('logs-' + str(time.time_ns()))
    private_directory(directory)
    for service in services():
        # Container logs can contain user data; never forward them to chat/source artifacts.
        result = subprocess.run(['docker', 'logs', '--tail', '200', name(service)], capture_output=True, timeout=20)
        if result.returncode:
            raise RuntimeError('PRIVATE_LOG_CAPTURE_FAILED')
        (directory / (service + '.log')).write_bytes(result.stdout + result.stderr)
    return {'private_logs': str(directory), 'raw_logs_not_printed': True, 'status': current}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'repair', 'status', 'stop', 'logs'])
    args = parser.parse_args()
    try:
        action = {'status': status, 'start': start, 'repair': start, 'stop': stop, 'logs': logs}[args.action]
        print(json.dumps(action(), indent=2))
    except Exception as error:
        print(json.dumps({'failed': True, 'error_type': type(error).__name__,
                          'message': str(error) if isinstance(error, (ValueError, RuntimeError)) else 'LOCAL_RUNTIME_FAILED',
                          'no_automatic_retry': True, 'main_changed': False}))
        raise SystemExit(1)

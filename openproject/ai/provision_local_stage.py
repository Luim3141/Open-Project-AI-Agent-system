"""One-time local staging provisioning, never a business tool or a main deployment."""
import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import subprocess
import time

from free_tier_staging import private_directory
from jira_sync_backup import command, inspect, operator_lease

ROOT = Path(__file__).resolve().parent
SERVICES = ('db', 'staging-web', 'staging-gateway')


def pinned_images(infos, lock, baseline):
    result = {}
    for service in SERVICES:
        info = infos[service]
        expected = lock.get(service, baseline.get(service))
        if (not expected or info['Config']['Labels'].get('com.docker.compose.project') != 'qldapm-ai-stage'
                or not info['State']['Running'] or info['Image'] != expected):
            raise ValueError('STAGE_IMAGE_OR_OWNERSHIP_MISMATCH:' + service)
        result[service] = expected
    return result


def provision(enable_radmin=False, backup_image=None, enable_quick=False, gateway_image=None, core_image=None, application_only=False, gateway_only=False, core_only=False):
    with operator_lease('staging'):
        return provision_locked(enable_radmin=enable_radmin, backup_image=backup_image, enable_quick=enable_quick,
                                gateway_image=gateway_image, core_image=core_image, application_only=application_only, gateway_only=gateway_only, core_only=core_only)


def selected_services(application_only, radmin, quick, backup_image, core_image, gateway_only=False, core_only=False):
    if core_only:
        return ['staging-web']
    if gateway_only:
        return ['staging-gateway']
    if application_only:
        return ['staging-web', 'staging-gateway']
    services = ['staging-gateway', 'n8n', 'n8n-editor']
    if radmin:
        services = ['staging-web', *services, 'radmin-proxy']
    if quick:
        services = ['quick-tunnel', 'staging-web', *services]
    if backup_image:
        services += ['local-backup']
    if core_image and 'staging-web' not in services:
        services.insert(0, 'staging-web')
    return services


def free_only_gateway(candidate, previous):
    layers = previous['RootFS']['Layers']
    if (not re.fullmatch(r'sha256:[a-f0-9]{64}', candidate['Id']) or
            (candidate['Config'].get('Labels') or {}).get('org.qldapm.policy') != 'FREE_ONLY' or
            candidate['RootFS']['Layers'][:len(layers)] != layers):
        raise ValueError('FREE_ONLY_GATEWAY_BASE_OR_POLICY_MISMATCH')
    return candidate['Id']


def daily_report_core(candidate, previous):
    layers = previous['RootFS']['Layers']
    cand_layers = candidate['RootFS']['Layers']
    forward_match = (len(cand_layers) >= len(layers) and cand_layers[:len(layers)] == layers)
    rollback_match = (len(cand_layers) <= len(layers) and layers[:len(cand_layers)] == cand_layers)
    if (not re.fullmatch(r'sha256:[a-f0-9]{64}', candidate['Id'])
            or (candidate['Config'].get('Labels') or {}).get('org.qldapm.report') != 'actor-daily-read-only'
            or not (forward_match or rollback_match)):
        raise ValueError('DAILY_REPORT_CORE_BASE_OR_SCOPE_MISMATCH')
    return candidate['Id']


def backup_base(built, core, audited):
    # Report API/views add no schema or PostgreSQL CLI changes to the qualified backup base.
    layers = audited['RootFS']['Layers']
    if ((built['Config'].get('Labels') or {}).get('org.qldapm.operator') != 'local-backup'
            or built['RootFS']['Layers'][:len(layers)] != layers
            or core['RootFS']['Layers'][:len(layers)] != layers):
        raise ValueError('BACKUP_IMAGE_BASE_OR_OPERATOR_MISMATCH')


def check_provider_configuration(state):
    enabled = json.loads((state / 'gemini.json').read_text()).get('enabled')
    if type(enabled) is not bool:
        raise ValueError('PROVIDER_ENABLED_MUST_BE_BOOLEAN')
    if enabled:
        program = "from pathlib import Path; from gateway.gemini import Gemini; g=Gemini(Path('/state')); p=g.settings(); assert p['tier']=='Free' and p['billing_enabled'] is False and g.continuous_authorized(p)"
        command(['docker', 'exec', 'qldapm-ai-stage-staging-gateway-1', 'python', '-c', program])
    return enabled


def provision_locked(enable_radmin=False, backup_image=None, enable_quick=False, gateway_image=None, core_image=None, application_only=False, gateway_only=False, core_only=False):
    if gateway_only and (application_only or core_only or enable_radmin or enable_quick or backup_image or core_image or not gateway_image):
        raise ValueError('GATEWAY_ONLY_REQUIRES_ONE_IMAGE_AND_NO_OTHER_SERVICE_CHANGES')
    if core_only and (application_only or gateway_only or enable_radmin or enable_quick or backup_image or gateway_image or not core_image):
        raise ValueError('CORE_ONLY_REQUIRES_ONE_CORE_IMAGE_AND_NO_OTHER_SERVICE_CHANGES')
    if application_only and (enable_radmin or enable_quick or not gateway_image or not core_image):
        raise ValueError('APPLICATION_ONLY_REQUIRES_BOTH_IMAGES_AND_NO_ACCESS_CHANGES')
    runtime = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
    state = runtime / 'stage-ai'
    lock = json.loads((runtime / 'stage-image-lock.json').read_text())
    # Older locks omitted DB; accept it only when it matches the actual P00 audit.
    observed = json.loads((ROOT.parents[1] / 'docs/ai-multi-agent-upgrade/artifacts/P00-runtime-after.json').read_text())
    baseline = {row['name'].removeprefix('qldapm-ai-stage-').removesuffix('-1'): row['image']
                for row in observed['containers'] if row['project'] == 'qldapm-ai-stage'}
    infos = {s: inspect('qldapm-ai-stage-' + s + '-1') for s in SERVICES}
    images = pinned_images(infos, lock, baseline)
    provider_enabled = check_provider_configuration(state)
    if gateway_image:
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', gateway_image):
            raise ValueError('IMMUTABLE_GATEWAY_IMAGE_REQUIRED')
        candidate = json.loads(command(['docker', 'image', 'inspect', gateway_image]))[0]
        previous_image = json.loads(command(['docker', 'image', 'inspect', images['staging-gateway']]))[0]
        images['staging-gateway'] = free_only_gateway(candidate, previous_image)
    if core_image:
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', core_image):
            raise ValueError('IMMUTABLE_CORE_IMAGE_REQUIRED')
        candidate = json.loads(command(['docker', 'image', 'inspect', core_image]))[0]
        previous_image = json.loads(command(['docker', 'image', 'inspect', images['staging-web']]))[0]
        images['staging-web'] = daily_report_core(candidate, previous_image)
    operator = runtime / 'operator/local-runtime'
    private_directory(operator)
    manifest_path = operator / 'stage-runtime.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    quick = enable_quick or (previous.get('quick_tunnel') is True and not enable_radmin)
    radmin = not quick and (enable_radmin or previous.get('radmin_host') == '26.88.211.101')
    if radmin:
        private_directory(runtime / 'radmin-caddy')
    if quick:
        private_directory(runtime / 'access')
    backup_image = backup_image or previous.get('backup_image')
    if backup_image:
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', backup_image) or not (radmin or quick):
            raise ValueError('BACKUP_IMAGE_OR_ACCESS_NOT_READY')
        built = json.loads(command(['docker', 'image', 'inspect', backup_image]))[0]
        core = json.loads(command(['docker', 'image', 'inspect', images['staging-web']]))[0]
        audited = json.loads(command(['docker', 'image', 'inspect', baseline['staging-web']]))[0]
        backup_base(built, core, audited)
        private_directory(runtime / 'operator/local-backups')
        private_directory(runtime / 'operator/n8n-owner')
    backup = operator / ('before-provision-' + str(time.time_ns()))
    private_directory(backup)
    if manifest_path.is_file():
        shutil.copy2(manifest_path, backup / 'stage-runtime-before.json')
    if quick:
        safety = command(['docker', 'exec', 'qldapm-ai-stage-db-1', 'psql', '-X', '-v', 'ON_ERROR_STOP=1',
            '-U', 'postgres', '-d', 'openproject', '-qAt', '-c', "SELECT (SELECT value FROM settings WHERE name='login_required')='true' AND (SELECT value FROM settings WHERE name='self_registration')='0' AND NOT EXISTS(SELECT 1 FROM projects WHERE public)"]).decode().strip()
        if safety != 't':
            raise ValueError('NATIVE_PUBLIC_ACCESS_PREFLIGHT_FAILED')
    program = """import sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
assert d.execute("select count(*) from jobs where state in ('queued','running','failed_or_unknown')").fetchone()[0]+d.execute("select count(*) from ai_runs where state='running'").fetchone()[0]==0
d.backup(sqlite3.connect('/tmp/p01-before.sqlite'))
"""
    gateway = 'qldapm-ai-stage-staging-gateway-1'
    command(['docker', 'exec', gateway, 'python', '-c', program])
    # Docker cp cannot read this tmpfs on Desktop; stream the completed backup via exec.
    snapshot = command(['docker', 'exec', gateway, 'python', '-c',
                        "import sys; from pathlib import Path; sys.stdout.buffer.write(Path('/tmp/p01-before.sqlite').read_bytes())"])
    with (backup / 'gateway.sqlite').open('xb') as stream:
        stream.write(snapshot)
    files = ('config.json', 'credentials.json', 'gemini.json', 'gemini.key', 'ui.key')
    if (state / 'automation.key').exists():
        files += ('automation.key',)
    hashes = {}
    for name in files:
        shutil.copy2(state / name, backup / name)
        hashes[name] = hashlib.sha256((state / name).read_bytes()).hexdigest()
    for name in ('.env', 'stage-image-lock.json'):
        shutil.copy2(runtime / name, backup / name)
    keydir = runtime / 'n8n-stage'
    private_directory(keydir)
    key = keydir / 'encryption.key'
    if not key.exists():
        with key.open('x', encoding='utf-8') as stream:
            stream.write(secrets.token_hex(32))
    if not key.is_file() or len(key.read_text()) != 64:
        raise ValueError('PRIVATE_N8N_KEY_INVALID_DO_NOT_REPLACE')
    env = {**os.environ, 'AI_RUNTIME': runtime.as_posix(), 'AI_IMAGE': images['staging-gateway'],
           'CORE_IMAGE': images['staging-web'], 'POSTGRES_IMAGE': images['db'], 'QLDAPM_N8N_KEY_PATH': key.as_posix()}
    if backup_image:
        env['LOCAL_BACKUP_IMAGE'] = backup_image
    if quick and previous.get('quick_tunnel_image'):
        env['QUICK_TUNNEL_IMAGE'] = previous['quick_tunnel_image']
    argv = ['docker', 'compose', '--project-name', 'qldapm-ai-stage', '--env-file', str(runtime / '.env')]
    for name in ('stage.yml', 'deep-ai.stage.yml', 'gemini-free.stage.yml', 'local-runtime.stage.yml'):
        argv += ['-f', str(ROOT / name)]
    if radmin:
        argv += ['-f', str(ROOT / 'radmin.stage.yml')]
    if quick:
        argv += ['-f', str(ROOT / 'quick.stage.yml')]
    if backup_image:
        argv += ['-f', str(ROOT / 'backup.stage.yml')]

    def compose(arguments):
        result = subprocess.run(argv + arguments, env=env, capture_output=True, timeout=120)
        if result.returncode:
            (backup / 'compose-error.log').write_bytes(result.stdout + result.stderr)
            raise RuntimeError('STAGE_COMPOSE_FAILED_RECONCILE_PRIVATE_LOG_NO_MAIN_CHANGE')
        return result.stdout

    config = json.loads(compose(['config', '--format', 'json']))
    if any(config['services'][s]['image'] != images[s] for s in SERVICES):
        raise ValueError('COMPOSE_PIN_MISMATCH')
    manifest = {'images': images, 'n8n_image': config['services']['n8n']['image'], 'key_path': str(key),
                'editor_image': config['services']['n8n-editor']['image'],
                'radmin_host': '26.88.211.101' if radmin else None,
                'quick_tunnel': quick,
                'quick_tunnel_image': config['services']['quick-tunnel']['image'] if quick else None,
                'backup_image': backup_image,
                'n8n_key_sha256': hashlib.sha256(key.read_bytes()).hexdigest(),
                'gateway_files_before': hashes, 'backup': str(backup)}
    (operator / 'stage-runtime.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (backup / 'compose.json').write_bytes(json.dumps(config, indent=2).encode())
    services = selected_services(application_only, radmin, quick, backup_image, core_image, gateway_only=gateway_only, core_only=core_only)
    if enable_quick and previous.get('radmin_host'):
        retired = inspect('qldapm-ai-stage-radmin-proxy-1')
        if (retired['Config']['Labels'].get('com.docker.compose.project') != 'qldapm-ai-stage'
                or retired['Image'] != json.loads(command(['docker', 'image', 'inspect', manifest['editor_image']]))[0]['Id']):
            raise ValueError('RETIRED_PROXY_OWNERSHIP_MISMATCH')
        command(['docker', 'stop', '--time', '30', 'qldapm-ai-stage-radmin-proxy-1'])
    compose(['up', '-d', '--no-deps', '--no-build', '--pull', 'never', *services])
    if application_only and backup_image:
        # Reload the already-qualified optional knowledge snapshot in the mounted operator source.
        compose(['restart', 'local-backup'])
    if any(hashlib.sha256((state / name).read_bytes()).hexdigest() != checksum for name, checksum in hashes.items()):
        raise ValueError('STAGE_CONFIGURATION_CHANGED_RECONCILE')
    # Bring the existing resume lock to the same fully observed DB/core/gateway set.
    temporary = runtime / 'stage-image-lock.json.tmp'
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump({**lock, **images}, stream, indent=2)
    temporary.replace(runtime / 'stage-image-lock.json')
    return {'provisioned': services, 'same_stage_images': gateway_image is None,
            'gateway_image_changed': images['staging-gateway'] != infos['staging-gateway']['Image'],
            'core_image_changed': images['staging-web'] != infos['staging-web']['Image'],
            'gateway_config_credentials_key_unchanged': True, 'private_key_persisted': True,
            'main_unchanged': True, 'provider_enabled': provider_enabled, 'health_pending': True, 'backup': str(backup)}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    access = parser.add_mutually_exclusive_group()
    access.add_argument('--radmin', action='store_true', help='Enable the owner-approved fixed Radmin HTTPS overlay')
    access.add_argument('--quick-tunnel', action='store_true', help='Owner-authorized public OpenProject Quick Tunnel only')
    parser.add_argument('--backup-image', help='Enable the separately built and checked backup operator by immutable image ID')
    parser.add_argument('--gateway-image', help='Staging only: Free-only source image derived from the current audited Gateway')
    parser.add_argument('--core-image', help='Staging only: qualified read-only report native image derived from the current audited core')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--application-only', action='store_true', help='Owner-approved Core/Gateway replacement plus existing backup watcher reload; never restart access/n8n/DB services')
    mode.add_argument('--gateway-only', action='store_true', help='Owner-approved Gateway replacement only; preserve Core/access/n8n/DB/backup services')
    mode.add_argument('--core-only', action='store_true', help='Owner-approved Core replacement only; preserve Gateway/access/n8n/DB/backup services')
    args = parser.parse_args()
    try:
        print(json.dumps(provision(enable_radmin=args.radmin, backup_image=args.backup_image, enable_quick=args.quick_tunnel,
                                   gateway_image=args.gateway_image, core_image=args.core_image, application_only=args.application_only, gateway_only=args.gateway_only, core_only=args.core_only)))
    except Exception as error:
        print(json.dumps({'failed': True, 'error_type': type(error).__name__,
                          'message': str(error) if isinstance(error, (ValueError, RuntimeError)) else 'PROVISION_FAILED',
                          'no_automatic_retry': True}))
        raise SystemExit(1)

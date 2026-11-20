"""Qualified, Owner-authorized Main Core-only apply; no migrations or business/provider writes."""
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from rehearse_rollback import verify_image_source
OUT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'openproject/ai'))
from free_tier_staging import private_directory, save
from jira_sync_backup import command, inspect, database_state, verify_archive
from gateway.native import Native

def health():
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request('http://127.0.0.1:8088/health_checks/default', headers={'Host': 'localhost:8088'})
            with urllib.request.urlopen(request, timeout=2) as response:
                if response.status == 200: return
        except (OSError, TimeoutError): pass
        time.sleep(1)
    raise RuntimeError('MAIN_CORE_HEALTH_TIMEOUT')

def main():
    result_path = OUT / 'main-gantt-core-deployment.json'
    assert not result_path.exists(), 'DEPLOYMENT_EXISTS_RECONCILE_NO_BLIND_RETRY'
    for file in ('gantt-clone-qualification.json', 'native-views-clone-qualification.json', 'fresh-backup-restore.json'):
        assert json.loads((OUT / file).read_text())['passed'], 'QUALIFICATION_NOT_PASS:' + file
    build = json.loads((OUT / 'gantt-candidate-build.json').read_text()); candidate = build['image']; previous = build['base_image']
    assert verify_image_source(candidate) == 47
    assert inspect('qldapm-codex-main-20261020-browser')['Image'] == candidate
    backup = json.loads((OUT / 'backup-receipt.json').read_text()); verify_archive(backup['directory'], backup['hashes'])
    assert json.loads((OUT / 'fresh-backup-restore.json').read_text())['backup_directory'] == backup['directory']
    for service in ('web', 'worker', 'cron'):
        assert inspect('qldapm-openproject-' + service + '-1')['Image'] == previous
    root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM'; native = root / 'openproject'; ai = root / 'openproject-ai'
    private = ai / 'operator/codex-main-completion/deployment-gantt-20261021'; assert not private.exists()
    private_directory(private)
    for source, target in [(native / '.env', 'core.env'), (ai / 'image-lock.json', 'image-lock.json')]: shutil.copy2(source, private / target)
    args = ['docker', 'compose', '--project-name', 'qldapm-openproject', '--env-file', str(native / '.env'), '-f', str(REPO / 'openproject/compose.yml')]
    for file in ('active-volumes.yml', 'ui-bridge.yml'):
        if (native / file).is_file(): args += ['-f', str(native / file)]
    targets = {'qldapm-openproject-' + s + '-1' for s in ('web', 'worker', 'cron')}
    names = command(['docker', 'ps', '--format', '{{.Names}}']).decode().splitlines()
    untouched = {name: {key: inspect(name)[key] for key in ('Id', 'Image')} for name in names if name not in targets and not name.startswith('qldapm-codex-main-')}
    protected = [ai / 'gateway' / f for f in ('credentials.json', 'ui.key', 'gemini.key', 'gemini.json', 'gemini-readiness.json', 'config.json')]
    protected += [ai / 'stage-ai' / f for f in ('ui.key', 'gemini.key', 'gemini.json')]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    before = database_state('qldapm-openproject-db-1')
    result = {'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'phase': 'PREPARED', 'candidate': candidate, 'previous': previous, 'backup': backup['directory'], 'provider_calls': 0, 'business_writes': 0}
    def checkpoint(phase):
        result['phase'] = phase; result_path.write_text(json.dumps(result, indent=2))
    checkpoint('PREPARED')
    try:
        lines = (native / '.env').read_text().splitlines(); assert sum(line.startswith('OP_IMAGE=') for line in lines) == 1
        save(native / '.env', '\n'.join('OP_IMAGE=' + candidate if line.startswith('OP_IMAGE=') else line for line in lines) + '\n')
        lock = json.loads((ai / 'image-lock.json').read_text()); lock['CORE_IMAGE'] = candidate; save(ai / 'image-lock.json', json.dumps(lock, indent=2))
        checkpoint('ENV_SAVED_APPLYING_TARGETED_CORE')
        command(args + ['up', '-d', '--no-deps', '--no-build', 'web', 'worker', 'cron'], timeout=120)
        health()
        manifest = build['overlay_manifest']
        runtime_hashes = command(['docker', 'exec', 'qldapm-openproject-web-1', 'sha256sum', *('/app/' + name for name in manifest)]).decode().splitlines()
        actual_hashes = {line.split(maxsplit=1)[1].strip().removeprefix('/app/'): line.split(maxsplit=1)[0] for line in runtime_hashes}
        assert actual_hashes == manifest, 'MAIN_SOURCE_IMAGE_RUNTIME_DRIFT'
        credentials = json.loads((ai / 'gateway/credentials.json').read_text())
        identities = [Native('http://127.0.0.1:8088', credentials[str(i)], 5).identity(i) for i in range(19, 24)]
        assert [x['role'] for x in identities] == ['PM', 'BA', 'BE', 'FE', 'QA']
        after = database_state('qldapm-openproject-db-1')
        tables = ['work_packages', 'relations', 'members', 'member_roles', 'roles', 'role_permissions', 'two_factor_authentication_devices']
        assert all(before[t] == after[t] for t in tables), 'MAIN_PROTECTED_TABLE_DRIFT'
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == value for p, value in hashes.items()), 'PROTECTED_FILE_DRIFT'
        assert all(all(inspect(name)[key] == value for key, value in expected.items()) for name, expected in untouched.items()), 'UNRELATED_CONTAINER_DRIFT'
        assert all(inspect(name)['Image'] == candidate for name in targets)
        result.update(passed=True, native_identities=[{'id': x['user_id'], 'role': x['role']} for x in identities],
                      protected_tables_unchanged=tables, protected_files_unchanged=True, untouched_serving_containers=len(untouched), source_image_runtime_files_matched=len(actual_hashes))
        build['deployed_main'] = True; (OUT / 'gantt-candidate-build.json').write_text(json.dumps(build, indent=2))
        checkpoint('CORE_HEALTH_NATIVE_IDENTITIES_PASS_NATIVE_VIEWS_PENDING')
    except Exception as error:
        result['failure_type'] = type(error).__name__; checkpoint('ROLLBACK_STARTING')
        shutil.copy2(private / 'core.env', native / '.env'); shutil.copy2(private / 'image-lock.json', ai / 'image-lock.json')
        command(args + ['up', '-d', '--no-deps', '--no-build', 'web', 'worker', 'cron'], timeout=120); health()
        checkpoint('ROLLED_BACK_CORE_DATA_PRESERVED'); raise
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()

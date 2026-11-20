"""Fixed host-only backup/restore verification for the two approved sync targets."""
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
import shutil
import tarfile
from contextlib import contextmanager
from pathlib import Path


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_archive(directory, manifest):
    root = Path(directory).resolve()
    if not manifest:
        raise ValueError('BACKUP_MANIFEST_REQUIRED')
    for relative, checksum in manifest.items():
        path = root / relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts or not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError('BACKUP_PATH_DENIED')
        if not path.is_file() or digest(path) != checksum:
            raise ValueError('BACKUP_HASH_MISMATCH')
    return True


SPECS = {
    'live': {'project': 5, 'label': 'qldapm-openproject', 'db': 'qldapm-openproject-db-1',
             'web': 'qldapm-openproject-web-1', 'gateway': 'qldapm-ai-gateway-1',
             'gateway_label': 'qldapm-ai', 'runtime': 'openproject',
             'writers': ['qldapm-ai-gateway-1', 'qldapm-openproject-web-1',
                         'qldapm-openproject-worker-1', 'qldapm-openproject-cron-1', 'qldapm-openproject-hocuspocus-1']},
    'staging': {'project': 3, 'label': 'qldapm-ai-stage', 'db': 'qldapm-ai-stage-db-1',
                'web': 'qldapm-ai-stage-staging-web-1', 'gateway': 'qldapm-ai-stage-staging-gateway-1',
                'gateway_label': 'qldapm-ai-stage', 'runtime': 'openproject-ai/stage',
                'writers': ['qldapm-ai-stage-staging-gateway-1', 'qldapm-ai-stage-staging-web-1']}}


@contextmanager
def operator_lease(name):
    import msvcrt
    from free_tier_staging import private_directory
    if name not in SPECS:
        raise ValueError('TARGET_NOT_ALLOWED')
    directory = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/jira-sync'
    private_directory(directory)
    with (directory / (name + '-operator.lock')).open('a+b') as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise ValueError('ANOTHER_SYNC_OPERATOR_IS_RUNNING') from None
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def command(argv, data=None, timeout=180):
    try:
        result = subprocess.run(argv, input=data, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError('BACKUP_DOCKER_TIMEOUT_RECONCILE_BEFORE_RETRY') from None
    if result.returncode:
        # stderr may contain database/config credentials; never forward it.
        reason = 'PERMISSION' if b'Permission denied' in result.stderr or b'Operation not permitted' in result.stderr else 'FAILED'
        raise RuntimeError('BACKUP_DOCKER_' + reason)
    return result.stdout


def inspect(name):
    return json.loads(command(['docker', 'inspect', name]))[0]


def database_state(container):
    return read_database_state(lambda sql: command(['docker', 'exec', '-i', container, 'psql', '-X',
        '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'openproject', '-qAt'], sql.encode()))


def read_database_state(query):
    """Same read-only fingerprints for host restore drills and the isolated backup operator."""
    tables = query("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").decode().splitlines()
    if not tables or any(not re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9]*', name) for name in tables):
        raise ValueError('DATABASE_TABLE_SCOPE_INVALID')
    sql = 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n' + '\n'.join(
        "SELECT json_build_object('table','" + name + "','rows',count(*),'sha256',encode(sha256(convert_to("
        "coalesce(string_agg(to_jsonb(t)::text,E'\\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex')) "
        'FROM "' + name + '" t;' for name in tables) + '\nCOMMIT;'
    sql = sql.replace('\nCOMMIT;', "\nSELECT json_build_object('table','$sequences','rows',count(*),'sha256',encode(sha256(convert_to(coalesce(string_agg(to_jsonb(t)::text,E'\\n' ORDER BY to_jsonb(t)::text),''),'UTF8')),'hex')) FROM pg_sequences t WHERE schemaname='public';\nCOMMIT;")
    output = query(sql)
    return {row['table']: {'rows': row['rows'], 'sha256': row['sha256']}
            for row in map(json.loads, output.decode().splitlines())}


def asset_command(image, volume, arguments, writable=False):
    mount = f'type=volume,source={volume},target=/assets' + ('' if writable else ',readonly')
    return command(['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '--mount', mount,
        '--entrypoint', arguments[0], image] + arguments[1:])


def assets_state(image, volume):
    links = asset_command(image, volume, ['find', '/assets', '-type', 'l', '-print'])
    if links.strip():
        raise ValueError('ASSET_SYMLINK_REQUIRES_MANUAL_REVIEW')
    output = asset_command(image, volume, ['sh', '-c', 'cd /assets && find . -type f -exec sha256sum {} +'])
    return sorted(output.decode().splitlines())


def create_backup(name):
    with operator_lease(name):
        return create_backup_locked(name)


def create_backup_locked(name):
    from jira_sync import private_save
    from free_tier_staging import private_directory
    if name not in SPECS:
        raise ValueError('TARGET_NOT_ALLOWED')
    spec = SPECS[name]
    infos = {key: inspect(spec[key]) for key in ('web', 'db', 'gateway')}
    for key, info in infos.items():
        label = spec['gateway_label'] if key == 'gateway' else spec['label']
        if info['Config']['Labels'].get('com.docker.compose.project') != label or not info['State']['Running']:
            raise ValueError('BACKUP_TARGET_NOT_RUNNING_OR_LABEL_MISMATCH')
    volume = [row['Name'] for row in infos['web']['Mounts'] if row['Type'] == 'volume' and row['Destination'] == '/var/openproject/assets']
    if len(volume) != 1:
        raise ValueError('BACKUP_ASSET_VOLUME_MISMATCH')
    # Read only in Linux: do not construct Store or open its WAL on Windows.
    busy_program = "import sqlite3; d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True); print(d.execute(\"select count(*) from jobs where state in ('queued','running','failed_or_unknown')\").fetchone()[0]+d.execute(\"select count(*) from ai_runs where state='running'\").fetchone()[0])"
    if int(command(['docker', 'exec', spec['gateway'], 'python', '-c', busy_program]).decode().strip()):
        raise ValueError('ACTIVE_OR_UNKNOWN_JOB_BLOCKS_BACKUP')
    writers = []
    for container in spec['writers']:
        info = inspect(container)
        expected = spec['gateway_label'] if container == spec['gateway'] else spec['label']
        if info['Config']['Labels'].get('com.docker.compose.project') != expected:
            raise ValueError('BACKUP_WRITER_SCOPE_MISMATCH')
        if info['State']['Running']:
            writers.append(container)
    root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM'
    directory = root / 'openproject-ai/operator/jira-sync/backups' / str(uuid.uuid4())
    private_directory(directory)
    stopped = []
    try:
        for container in writers:
            command(['docker', 'stop', '--time', '45', container], timeout=70)
            stopped.append(container)
        state = database_state(spec['db'])
        assets = assets_state(infos['web']['Image'], volume[0])
        with (directory / 'database.dump').open('xb') as stream:
            dump = subprocess.run(['docker', 'exec', spec['db'], 'pg_dump', '-U', 'postgres', '-Fc', 'openproject'], stdout=stream, stderr=subprocess.PIPE, timeout=180)
            if dump.returncode:
                raise RuntimeError('DATABASE_DUMP_FAILED')
        with (directory / 'assets.tar').open('xb') as stream:
            stream.write(asset_command(infos['web']['Image'], volume[0], ['tar', '-cf', '-', '-C', '/assets', '.']))
        with tarfile.open(directory / 'assets.tar') as archive:
            if any(row.issym() or row.islnk() or row.isdev() or Path(row.name).is_absolute() or '..' in Path(row.name).parts for row in archive):
                raise ValueError('ASSET_ARCHIVE_PATH_DENIED')
        config = directory / 'config'
        private_directory(config)
        private_save(config / 'deployment.json', {key: {'Image': info['Image'], 'Config': info['Config'],
            'HostConfig': info['HostConfig'], 'Mounts': info['Mounts'], 'Networks': info['NetworkSettings']['Networks']}
            for key, info in infos.items()})
        for path in (root / spec['runtime']).iterdir():
            if path.is_file() and not path.is_symlink() and path.name not in {'operator.lock', 'release.lock'}:
                shutil.copy2(path, config / path.name)
        if name == 'staging':
            for filename in ('config.json', 'credentials.json', 'ui.key'):
                shutil.copy2(root / 'openproject-ai/stage-ai' / filename, config / ('ai-' + filename))
            shutil.copy2(root / 'openproject-ai/.env', config / 'ai-runtime.env')
        else:
            for filename in ('.env', 'image-lock.json', 'gateway/config.json', 'gateway/credentials.json', 'gateway/ui.key'):
                path = root / 'openproject-ai' / filename
                if path.is_file():
                    shutil.copy2(path, config / ('ai-' + filename.replace('/', '-').lstrip('.')))
        for path in (Path(__file__).resolve().parent.parent / 'compose.yml', Path(__file__).resolve().parent / 'stage.yml'):
            if path.exists():
                shutil.copy2(path, config / path.name)
        for path in Path(__file__).resolve().parent.glob('*stage.yml'):
            shutil.copy2(path, config / path.name)
        if database_state(spec['db']) != state or assets_state(infos['web']['Image'], volume[0]) != assets:
            raise ValueError('SOURCE_CHANGED_DURING_BACKUP')
        private_save(directory / 'database-state.json', state)
        private_save(directory / 'assets-state.json', assets)
        manifest = {path.relative_to(directory).as_posix(): digest(path) for path in directory.rglob('*') if path.is_file()}
        verify_archive(directory, manifest)
        metadata = {'schema': 1, 'target': name, 'project_id': spec['project'], 'at': time.time(),
                    'core_image': infos['web']['Image'], 'postgres_image': infos['db']['Image'],
                    'asset_volume': volume[0], 'manifest': manifest, 'tables': len(state)}
        private_save(directory / 'backup.json', metadata)
        return directory
    finally:
        for container in reversed(stopped):
            command(['docker', 'start', container])


def rehearse_backup(directory, exercise=None, core_image=None, *, data_only=False):
    from jira_sync import private_save
    from free_tier_staging import private_directory
    if data_only and (exercise is not None or core_image is not None):
        raise ValueError('DATA_RESTORE_CANNOT_QUALIFY_IMPORT_OR_IMAGE')
    directory = Path(directory).resolve()
    metadata = json.loads((directory / 'backup.json').read_text())
    if metadata.get('target') not in SPECS or metadata['project_id'] != SPECS[metadata['target']]['project']:
        raise ValueError('BACKUP_TARGET_MISMATCH')
    verify_archive(directory, metadata['manifest'])
    for name in ('core_image', 'postgres_image'):
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', metadata[name]):
            raise ValueError('PINNED_BACKUP_IMAGE_REQUIRED')
    tested_image = core_image or metadata['core_image']
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', tested_image) or (metadata['target'] == 'live' and tested_image != metadata['core_image']):
        raise ValueError('REHEARSAL_IMAGE_SCOPE_DENIED')
    expected = json.loads((directory / 'database-state.json').read_text())
    assets = json.loads((directory / 'assets-state.json').read_text())
    identifier = str(uuid.uuid4())
    label = 'org.qldapm.sync-restore=' + identifier
    name = 'qldapm-sync-restore-' + identifier
    network, database, volume = name + '-net', name + '-db', name + '-assets'
    created = []
    rehearsal = None
    try:
        command(['docker', 'network', 'create', '--internal', '--label', label, network])
        created.append(('network', network))
        command(['docker', 'volume', 'create', '--label', label, volume])
        created.append(('volume', volume))
        # A fresh Docker volume is root-owned; the pinned image runs as app.
        # Ownership is changed only on this newly allocated, labelled volume.
        command(['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
            '--user', '0:0', '--cap-drop', 'ALL', '--cap-add', 'CHOWN', '--security-opt', 'no-new-privileges:true',
            '--mount', f'type=volume,source={volume},target=/assets', '--entrypoint', 'chown',
            metadata['core_image'], '1000:1000', '/assets'])
        command(['docker', 'run', '-d', '--rm', '--pull', 'never', '--name', database, '--label', label,
            '--network', network, '--network-alias', 'restored-db', '--user', 'postgres', '--read-only',
            '--tmpfs', '/tmp:size=768m,mode=1777', '--tmpfs', '/var/run/postgresql:mode=1777',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '--memory', '1g', '--pids-limit', '128',
            '-e', 'PGDATA=/tmp/postgres', '-e', 'POSTGRES_DB=openproject', '-e', 'POSTGRES_HOST_AUTH_METHOD=trust', metadata['postgres_image']])
        created.append(('container', database))
        for _ in range(60):
            ready = subprocess.run(['docker', 'exec', database, 'pg_isready', '-U', 'postgres', '-d', 'openproject'], capture_output=True, timeout=10)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('RESTORE_DATABASE_TIMEOUT')
        with (directory / 'database.dump').open('rb') as stream:
            result = subprocess.run(['docker', 'exec', '-i', database, 'pg_restore', '-U', 'postgres', '--no-owner', '--exit-on-error', '-d', 'openproject'], stdin=stream, capture_output=True, timeout=180)
            if result.returncode:
                raise RuntimeError('RESTORE_DATABASE_FAILED')
        if database_state(database) != expected:
            raise ValueError('RESTORED_DATABASE_HASH_MISMATCH')
        command(['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges:true', '--mount', f'type=bind,source={directory},target=/backup,readonly',
            '--mount', f'type=volume,source={volume},target=/assets', '--entrypoint', 'tar', metadata['core_image'],
            '--no-same-owner', '--no-same-permissions', '-xf', '/backup/assets.tar', '-C', '/assets'])
        if assets_state(metadata['core_image'], volume) != assets:
            raise ValueError('RESTORED_ASSETS_HASH_MISMATCH')
        rehearsal = directory / ('restore-' + identifier)
        private_directory(rehearsal)
        shutil.copytree(directory / 'config', rehearsal / 'config')
        config_manifest = {key[7:]: value for key, value in metadata['manifest'].items() if key.startswith('config/')}
        verify_archive(rehearsal / 'config', config_manifest)
        if data_only:
            # A restore drill cannot stand in for Jira import or release qualification.
            result = {'passed': True, 'target': metadata['target'], 'at': time.time(),
                      'backup_hash': digest(directory / 'backup.json'), 'restored_tables': len(expected),
                      'database_assets_config': True, 'configuration_transaction': False,
                      'purpose': 'data-restore-only', 'core_image': metadata['core_image'],
                      'temporary_id': identifier, 'import_exercise': None}
            private_save(rehearsal / 'result.json', result)
            return result
        # Fixed operator-owned code only. No credentials, actor code, live
        # volumes, Internet, published port or Docker socket are mounted.
        core = Path(__file__).resolve().parent / 'core'
        args = ['docker', 'run', '--rm', '--pull', 'never', '--name', name, '--label', label,
            '--network', network, '--user', '1000:1000', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
            '--memory', '4g', '--cpus', '2', '--pids-limit', '256', '--tmpfs', '/tmp:size=128m,mode=1777',
            '--tmpfs', '/app/tmp:size=128m,mode=1777', '--tmpfs', '/app/log:size=32m,mode=1777',
            '-e', 'QLDAPM_TEST_ONLY=true', '-e', f"QLDAPM_SYNC_PROJECT_ID={metadata['project_id']}",
            '-e', 'RAILS_ENV=production', '-e', 'DATABASE_URL=postgres://postgres@restored-db/openproject',
            '-e', 'SECRET_KEY_BASE=operator-disposable-restore-only-' + '0' * 96, '-e', 'OPENPROJECT_HOST__NAME=localhost:8088',
            '-e', 'OPENPROJECT_RAILS__CACHE__STORE=file_store', '--mount', f'type=bind,source={core},target=/trusted,readonly',
            '--entrypoint', 'bundle', tested_image, 'exec', 'rails', 'runner', '/trusted/jira_sync_configuration_test.rb']
        output = command(args, timeout=180).decode()
        if 'Jira sync configuration PASS' not in output:
            raise ValueError('CONFIGURATION_REHEARSAL_NOT_VERIFIED')
        imported = None
        if exercise is not None:
            alias = 'staging-web' if metadata['target'] == 'staging' else 'web'
            base = args[:args.index('--entrypoint')]
            base[2:2] = ['-d']
            command(base + ['--network-alias', alias, '-e', 'OPENPROJECT_HTTPS=false',
                '-e', 'OPENPROJECT_WEB_WORKERS=1', '-e', 'RAILS_MIN_THREADS=1', '-e', 'RAILS_MAX_THREADS=2',
                '--entrypoint', 'bundle', tested_image, 'exec', 'rails', 'server', '-b', '0.0.0.0', '-p', '8080'])
            created.append(('container', name))
            imported = exercise(metadata['target'], network, name, identifier, rehearsal, tested_image)
        result = {'passed': True, 'target': metadata['target'], 'at': time.time(), 'backup_hash': digest(directory / 'backup.json'),
                  'restored_tables': len(expected), 'database_assets_config': True, 'configuration_transaction': True,
                  'core_image': metadata['core_image'], 'tested_core_image': tested_image,
                  'configuration_source_hash': digest(core / 'jira_sync_configuration.rb'),
                  'temporary_id': identifier, 'import_exercise': imported}
        private_save(rehearsal / 'result.json', result)
        return result
    except Exception as error:
        if rehearsal is not None:
            private_save(rehearsal / 'failure.json', {'passed': False, 'target': metadata['target'],
                'at': time.time(), 'error_type': type(error).__name__, 'primary_sync_applied': False})
        raise
    finally:
        # Only disposable names allocated here, with ownership checked again.
        for kind, resource in reversed(created):
            if kind == 'container':
                remaining = command(['docker', 'ps', '-a', '--filter', 'label=' + label, '--format', '{{.Names}}']).decode().splitlines()
                if resource not in remaining:
                    continue # --rm containers may already be gone after a controlled stop.
                info = inspect(resource)
                if info['Config']['Labels'].get('org.qldapm.sync-restore') != identifier:
                    raise ValueError('RESTORE_CLEANUP_SCOPE_MISMATCH')
                command(['docker', 'rm', '-f', resource])
            else:
                info = json.loads(command(['docker', kind, 'inspect', resource]))[0]
                if info.get('Labels', {}).get('org.qldapm.sync-restore') != identifier:
                    raise ValueError('RESTORE_CLEANUP_SCOPE_MISMATCH')
                command(['docker', kind, 'rm', resource])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['backup', 'rehearse'])
    parser.add_argument('--target', choices=list(SPECS))
    parser.add_argument('--backup', type=Path)
    parser.add_argument('--data-only', action='store_true', help='Verify DB/assets/config restore only; never qualifies an import or release')
    options = parser.parse_args()
    try:
        if options.action == 'backup':
            if options.data_only:
                parser.error('--data-only requires rehearse')
            if not options.target:
                parser.error('backup requires --target')
            print(json.dumps({'backup': str(create_backup(options.target)), 'target': options.target}))
        else:
            if not options.backup:
                parser.error('rehearse requires --backup')
            print(json.dumps(rehearse_backup(options.backup, data_only=options.data_only)))
    except Exception as error:
        code = str(error) if isinstance(error, (ValueError, RuntimeError)) and re.fullmatch(r'[A-Z_]{1,100}', str(error)) else 'BACKUP_OR_RESTORE_FAILED'
        print(json.dumps({'failed': True, 'code': code, 'no_sync_apply': True}))
        raise SystemExit(1)

"""Private local backup operator: read-only inputs, no business API or Docker socket."""
import argparse
from contextlib import closing, contextmanager
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time
import uuid

from jira_sync_backup import read_database_state

OUTPUT = Path('/backup')


def active_work(database):
    busy = database.execute("select count(*) from jobs where state in ('queued','running','failed_or_unknown')").fetchone()[0]
    if database.execute("select 1 from sqlite_master where type='table' and name='ai_queue'").fetchone():
        # Never-started intents are safe to snapshot, including a whole day waiting for Free quota.
        busy += database.execute("select count(*) from ai_runs where state='running' and id not in (select id from ai_queue where state='queued')").fetchone()[0]
    else:
        busy += database.execute("select count(*) from ai_runs where state='running'").fetchone()[0]
    return busy


def run(argv, data=None):
    result = subprocess.run(argv, input=data, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError('BACKUP_COMMAND_FAILED')
    return result.stdout


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def files(root, exclude=()):
    if not root.is_dir():
        raise ValueError('BACKUP_INPUT_DIRECTORY_MISSING')
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('BACKUP_SYMLINK_DENIED')
        relative = path.relative_to(root)
        excluded = relative.parent == Path('.') and any(path.name.startswith(prefix) for prefix in exclude)
        if path.is_file() and not excluded:
            result[relative.as_posix()] = digest(path)
    return result


def archive(root, destination, exclude=()):
    before = files(root, exclude)
    with tarfile.open(destination, 'w') as stream:
        for relative in before:
            stream.add(root / relative, arcname='./' + relative, recursive=False)
    if files(root, exclude) != before:
        raise ValueError('FILES_CHANGED_DURING_BACKUP')
    return sorted(checksum + '  ./' + relative for relative, checksum in before.items())


def sqlite_snapshot(source, destination):
    if destination.exists():
        raise ValueError('BACKUP_TARGET_EXISTS')
    def inputs():
        result = {}
        for path in (source, source.with_name(source.name + '-wal')):
            if path.is_symlink():
                raise ValueError('BACKUP_SYMLINK_DENIED')
            if path.is_file():
                result[path.name] = digest(path)
        if source.name not in result:
            raise ValueError('SQLITE_SOURCE_MISSING')
        return result

    with tempfile.TemporaryDirectory(prefix='ql-sqlite-') as directory:
        temporary = Path(directory)
        expected = inputs()
        for name in expected:
            shutil.copyfile(source.parent / name, temporary / name)
        if inputs() != expected or any(digest(temporary / name) != value for name, value in expected.items()):
            raise ValueError('SQLITE_SOURCE_CHANGED_DURING_COPY')
        # SQLite may create SHM only in the private copy, never on the read-only source mount.
        with closing(sqlite3.connect(temporary / source.name, timeout=10)) as incoming:
            incoming.execute('PRAGMA query_only=ON')
            with closing(sqlite3.connect(destination)) as outgoing:
                incoming.backup(outgoing)
                outgoing.execute('PRAGMA journal_mode=DELETE')
                if outgoing.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('SQLITE_BACKUP_CORRUPT')
                return hashlib.sha256('\n'.join(outgoing.iterdump()).encode()).hexdigest()


def backup_n8n_owner(source, destination, snapshot):
    with closing(sqlite3.connect(snapshot.as_uri() + '?mode=ro&immutable=1', uri=True)) as database:
        claimed = database.execute("select value from settings where key='userManagement.isInstanceOwnerSetUp'").fetchone()
    if not source.exists():
        if claimed and claimed[0] == 'true':
            raise ValueError('N8N_OWNER_CREDENTIAL_BACKUP_REQUIRED')
        return False
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 8192:
        raise ValueError('N8N_OWNER_BACKUP_SOURCE_INVALID')
    before = source.read_bytes()
    owner = json.loads(before)
    if (owner.get('schema_version') != 1 or owner.get('endpoint') != 'http://localhost:5678'
            or not isinstance(owner.get('password'), str) or not 8 <= len(owner['password']) <= 64):
        raise ValueError('N8N_OWNER_BACKUP_SOURCE_INVALID')
    with destination.open('xb') as output:
        output.write(before)
    if source.read_bytes() != before:
        raise ValueError('N8N_OWNER_CHANGED_DURING_BACKUP')
    return True


def backup_machine_key(source, destination):
    if not source.exists():
        return False
    if source.is_symlink() or source.stat().st_size != 64:
        raise ValueError('MACHINE_BACKUP_KEY_INVALID')
    before = source.read_bytes()
    if not re.fullmatch(b'[a-f0-9]{64}', before):
        raise ValueError('MACHINE_BACKUP_KEY_INVALID')
    with destination.open('xb') as output:
        output.write(before)
    if source.read_bytes() != before:
        raise ValueError('MACHINE_KEY_CHANGED_DURING_BACKUP')
    return True


@contextmanager
def lease():
    import fcntl
    # All scheduler/manual runs share this Linux tmpfs lock; no stale lock after restart.
    with Path('/tmp/ql-local-backup.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def once():
    with lease(), tempfile.TemporaryDirectory(prefix='ql-gateway-backup-') as temporary:
        if shutil.disk_usage(OUTPUT).free < 5 * 1024**3:
            raise ValueError('BACKUP_DISK_BELOW_5GIB')
        gateway = Path(temporary) / 'gateway.sqlite'
        gateway_hash = sqlite_snapshot(Path('/gateway/gateway.sqlite'), gateway)
        with closing(sqlite3.connect(gateway.as_uri() + '?mode=ro', uri=True)) as database:
            if active_work(database):
                raise ValueError('ACTIVE_OR_UNKNOWN_JOB_BLOCKS_BACKUP')
        directory = OUTPUT / str(uuid.uuid4())
        directory.mkdir(mode=0o700)
        try:
            config = directory / 'config'
            config.mkdir(mode=0o700)
            query = lambda sql: run(['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-qAt'], sql.encode())
            expected = read_database_state(query)
            run(['pg_dump', '-Fc', '--no-password', '-f', str(directory / 'database.dump')])
            assets = archive(Path('/assets'), directory / 'assets.tar')
            shutil.copyfile(gateway, config / 'gateway.sqlite')
            sqlite_hashes = {'gateway': gateway_hash,
                             'n8n': sqlite_snapshot(Path('/n8n/database.sqlite'), config / 'n8n.sqlite')}
            knowledge = Path('/gateway/knowledge.sqlite')
            if knowledge.exists():
                sqlite_hashes['knowledge'] = sqlite_snapshot(knowledge, config / 'knowledge.sqlite')
            owner_backed_up = backup_n8n_owner(Path('/n8n-owner/owner.json'), config / 'n8n-owner.json', config / 'n8n.sqlite')
            machine_backed_up = backup_machine_key(Path('/gateway/automation.key'), config / 'automation.key')
            for filename in ('config.json', 'credentials.json', 'ui.key', 'gemini.json', 'gemini.key'):
                shutil.copyfile(Path('/gateway') / filename, config / ('ai-' + filename))
            shutil.copyfile('/secrets/n8n.key', config / 'n8n.key')
            shutil.copyfile('/secrets/provider-proof.json', config / 'provider-proof.json')
            if Path('/provider-policy').is_dir():
                archive(Path('/provider-policy'), config / 'provider-policy.tar')
            readiness = Path('/gateway/gemini-readiness.json')
            if readiness.is_file():
                shutil.copyfile(readiness, config / 'gemini-readiness.json')
            shutil.copyfile('/secrets/runtime.env', config / 'runtime.env')
            archive(Path('/n8n'), config / 'n8n-files.tar', ('database.sqlite', 'n8nEventLog', 'crash.journal'))
            archive(Path('/native-private'), config / 'native-private.tar')
            archive(Path('/radmin'), config / 'radmin-private.tar')
            record = json.loads(Path('/secrets/stage-runtime.json').read_text())
            if digest(Path('/secrets/n8n.key')) != record['n8n_key_sha256']:
                raise ValueError('N8N_BACKUP_KEY_MISMATCH')
            shutil.copyfile('/secrets/stage-runtime.json', config / 'stage-runtime.json')
            if read_database_state(query) != expected:
                raise ValueError('NATIVE_DATABASE_CHANGED_DURING_BACKUP')
            if sorted(c + '  ./' + p for p, c in files(Path('/assets')).items()) != assets:
                raise ValueError('ASSETS_CHANGED_DURING_BACKUP')
            save(directory / 'database-state.json', expected)
            save(directory / 'assets-state.json', assets)
            save(directory / 'sqlite-state.json', sqlite_hashes)
            manifest = files(directory)
            save(directory / 'backup.json', {'schema': 1, 'target': 'staging', 'project_id': 3,
                 'at': time.time(), 'core_image': record['images']['staging-web'],
                 'postgres_image': record['images']['db'], 'asset_volume': 'qldapm-ai-stage_stage-assets',
                 'manifest': manifest, 'tables': len(expected), 'purpose': 'data-restore-only'})
            save(OUTPUT / 'last-success.json', {'at': time.time(), 'id': directory.name})
            return {'passed': True, 'id': directory.name, 'tables': len(expected),
                    'sqlite_checked': sorted(sqlite_hashes), 'n8n_owner_credential_backed_up': owner_backed_up,
                    'machine_key_backed_up': machine_backed_up,
                    'private_output_only': True}
        except Exception:
            save(directory / 'failure.json', {'passed': False, 'at': time.time(), 'partial_do_not_restore': True})
            raise


def watch():
    time.sleep(120)
    while True:
        path = OUTPUT / 'last-success.json'
        previous = json.loads(path.read_text()).get('at', 0) if path.is_file() else 0
        if time.time() - previous >= 86400:
            try:
                print(json.dumps(once()), flush=True)
            except Exception as error:
                print(json.dumps({'passed': False, 'at': dt.datetime.now(dt.timezone.utc).isoformat(),
                                  'code': str(error) if isinstance(error, ValueError) else type(error).__name__}), flush=True)
        # One due backup, never replay every missed day or delete old user backups.
        time.sleep(3600)


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['once', 'watch'])
    options = parser.parse_args()
    if options.action == 'once':
        print(json.dumps(once()))
    else:
        watch()

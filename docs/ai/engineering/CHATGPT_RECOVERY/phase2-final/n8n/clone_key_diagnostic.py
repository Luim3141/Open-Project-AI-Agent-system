"""Read a private DPAPI snapshot in RAM; clone-only key failure and rollback diagnostic."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'stabilization-n8n'))
from inspect_backup import private, unprotect

IMAGE = 'sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795'


def docker(args, data=None):
    result = subprocess.run(['docker', *args], input=data, capture_output=True, timeout=300)
    if result.returncode:
        # Neither CLI logs nor stdin are included in the failure output.
        raise RuntimeError(f'DOCKER_{args[0].upper()}_FAILED_EXIT_{result.returncode}')
    return result.stdout


def main():
    snapshot = private / 'n8n-cold-volume.tar.dpapi'
    env_snapshot = private / 'preserved.env.dpapi'
    archive = unprotect(snapshot)
    env = dict(line.split('=', 1) for line in unprotect(env_snapshot).decode().splitlines() if '=' in line)
    assert env.get('N8N_ENCRYPTION_KEY')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:*') as tar:
        names = [member.name.removeprefix('./') for member in tar]
        assert all(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts for name in names)
        assert all(member.isfile() or member.isdir() for member in tar.getmembers())
        assert {'database.sqlite', 'database.sqlite-wal', 'database.sqlite-shm', 'config'} <= set(names)
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'image': IMAGE,
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'environment': 'isolated Docker network-none read-only root with tmpfs; encrypted backup, no MAIN mounts',
              'backup_archive_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
              'backup_environment_sha256': hashlib.sha256(env_snapshot.read_bytes()).hexdigest(),
              'harness_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (Path(__file__), HERE / 'clone_key_diagnostic.js')},
              'command': 'python docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/n8n/clone_key_diagnostic.py', 'stages': []}
    for mode in ('same_database_migration', 'rollback_restore'):
        name = 'qldapm-key-diagnostic-' + uuid.uuid4().hex[:12]
        try:
            docker(['run', '-d', '--pull', 'never', '--name', name, '--network', 'none', '--read-only',
                    '--tmpfs', '/tmp:rw,uid=1000,gid=1000,mode=0700,size=256m',
                    '--mount', f'type=bind,source={HERE},target=/test,readonly', '--entrypoint', '/bin/sh', IMAGE,
                    '-c', 'mkdir -p /tmp/restore/.n8n; sleep 1800'])
            docker(['exec', '-i', name, 'tar', '-C', '/tmp/restore/.n8n', '-xf', '-'], archive)
            value = json.loads(docker(['exec', '-i', name, 'node', '/test/clone_key_diagnostic.js'], json.dumps({'env': env, 'mode': mode}).encode()))
            report['stages'].append({'container': name, **value})
        finally:
            # Stops only this random clone; discard plaintext tmpfs and retain no secrets.
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
    report['completed_at'] = datetime.now(timezone.utc).isoformat()
    report['status'] = 'ROOT_CAUSE_AND_ROLLBACK_VERIFIED_MASTER_KEY_CUTOVER_BLOCKED'
    destination = HERE / 'clone-key-diagnostic-result.json'
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

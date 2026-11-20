"""Restore private SQLite backup copies into disposable Linux tmpfs, never runtime WAL."""
import argparse
import json
from pathlib import Path
import subprocess

from jira_sync_backup import command, digest, verify_archive

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('backup', type=Path)
args = parser.parse_args()
directory = args.backup.resolve()
metadata = json.loads((directory / 'backup.json').read_text())
assert metadata['target'] == 'staging' and metadata['project_id'] == 3
verify_archive(directory, metadata['manifest'])
image = json.loads((directory / 'config/stage-runtime.json').read_text())['backup_image']
program = '''import hashlib,json,sqlite3,tarfile
from contextlib import closing
from pathlib import Path
expected=json.loads(Path('/backup/sqlite-state.json').read_text())
for name,checksum in expected.items():
 assert name in ('gateway','n8n','knowledge')
 # Verified cold backup only: immutable avoids creating WAL/SHM on readonly media.
 with closing(sqlite3.connect('file:/backup/config/'+name+'.sqlite?mode=ro&immutable=1',uri=True)) as source:
  with closing(sqlite3.connect('/tmp/'+name+'.sqlite')) as target:
   source.backup(target)
   assert target.execute('PRAGMA quick_check').fetchone()[0]=='ok'
   assert hashlib.sha256('\\n'.join(target.iterdump()).encode()).hexdigest()==checksum
for name in ('n8n-files','radmin-private','native-private'):
 target=Path('/tmp')/name
 target.mkdir()
 with tarfile.open('/backup/config/'+name+'.tar') as archive:
  archive.extractall(target,filter='data')
print(json.dumps({'passed':True,'restored_sqlite':sorted(expected),'logical_hashes_equal':True,
 'private_archives_extracted_in_tmpfs':True,'runtime_wal_opened':False,'network':'none'}))
'''
result = subprocess.run(['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
                  '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '--user', '1000:1000',
                  '--memory', '256m', '--pids-limit', '32', '--tmpfs', '/tmp:size=128m,mode=1777',
                  '--mount', f'type=bind,source={directory},target=/backup,readonly',
                  '--entrypoint', 'python3', image, '-c', program], capture_output=True, timeout=90)
if result.returncode:
    (directory / 'sqlite-restore-error.log').write_bytes(result.stdout + result.stderr)
    lines = result.stderr.decode(errors='replace').splitlines()
    print(json.dumps({'failed': True, 'private_error_log': str(directory / 'sqlite-restore-error.log'),
                      'exception_type': lines[-1].split(':', 1)[0] if lines else 'DockerFailure'}))
    raise SystemExit(1)
print(result.stdout.decode().strip())

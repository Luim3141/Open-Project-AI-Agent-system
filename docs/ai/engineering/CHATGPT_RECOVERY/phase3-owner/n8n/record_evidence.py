"""Record bounded, sanitized Phase3 n8n source/ciphertext/clone checks."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
IMAGE = 'sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795'


def main():
    commands = [
        ('ciphertext-and-principal-unit', [sys.executable, '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_*.py', '-v']),
        ('original-local-ciphertext-bytes', [sys.executable, str(HERE / 'verify_ciphertext_copy.py'), '--ciphertext-dir',
          str(Path.home() / 'AppData/Local/QLDAPM/openproject-ai/operator/portable-n8n-recovery-8a61c9795ada/ciphertext')]),
        ('vendor-real-filesystem-retention-blocker', ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
          '--memory', '512m', '--memory-swap', '512m', '--pids-limit', '128',
          '--tmpfs', '/tmp:rw,uid=1000,gid=1000,mode=0700,size=32m', '--mount', f'type=bind,source={HERE},target=/tests,readonly',
          '--entrypoint', 'node', IMAGE, '/tests/persistence_filesystem_canary.js']),
    ]
    records = []
    for name, command in commands:
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=90)
        records.append({'name': name, 'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
                        'command': command, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
                        'interpretation': 'EXPECTED_BLOCKER_REPRODUCED_NOT_SECURITY_PASS' if 'retention-blocker' in name else 'CHECK_RESULT'})
    report = {'python': platform.python_version(), 'image': IMAGE, 'records': records,
              'source_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in HERE.iterdir() if path.suffix in ('.py', '.js')},
              'main_mutations': 0, 'retention_enabled': False, 'key_cutover': 'BLOCKED', 'offhost_copy': 'NOT_PERFORMED'}
    (HERE / 'checks.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'records': len(records), 'nonzero_exits': [r['name'] for r in records if r['exit']],
                      'retention': 'BLOCKED_EXPECTED_LEAKS_REPRODUCED', 'offhost': 'OWNER_ACTION_PENDING'}))
    raise SystemExit(int(any(r['exit'] for r in records)))


if __name__ == '__main__':
    main()

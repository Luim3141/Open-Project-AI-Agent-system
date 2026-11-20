"""Offline staged/tracked publication checks. Prints paths and rule names, never secrets."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'google_api_key': re.compile(rb'\bAIza[0-9A-Za-z_-]{35}\b'),
    'github_token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'telegram_token': re.compile(rb'\b\d{8,12}:[A-Za-z0-9_-]{35}\b'),
    'aws_access_key': re.compile(rb'\bAKIA[0-9A-Z]{16}\b'),
    'private_key_block': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\r?\n'),
}
FORBIDDEN_PARTS = {'.codex-local', '.codex', '.venv', '.venv-jira-admin', 'node_modules', '__pycache__', 'backups', 'model-cache'}


def violations(path, data):
    result = [name for name, regex in RULES.items() if regex.search(data)]
    if FORBIDDEN_PARTS.intersection(path.parts):
        result.append('private_or_generated_directory')
    if path.name == '.env' or (path.name.startswith('.env.') and path.name != '.env.example'):
        result.append('private_environment')
    if path.suffix.lower() in {'.key', '.pem', '.token', '.sqlite', '.sqlite3', '.db'}:
        result.append('private_runtime_file')
    if len(data) > 50 * 1024 * 1024:
        result.append('oversize_file')
    return result


def main():
    # In Git, inspect exact indexed bytes, including staged deletions/renames.
    listing = [entry for entry in subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT).split(b'\0') if entry]
    if not listing:
        raise RuntimeError('No indexed files; stage the reviewed snapshot before checking')
    entries = []
    for entry in listing:
        metadata, name = entry.split(b'\t', 1)
        mode, object_id, stage = metadata.split()
        if stage != b'0':
            raise RuntimeError('Resolve merge conflicts before publication')
        entries.append((object_id, name.decode('utf8')))
    batch = subprocess.run(['git', 'cat-file', '--batch'], input=b''.join(oid+b'\n' for oid, _ in entries), cwd=ROOT, capture_output=True, check=True).stdout
    failures = []
    offset = 0
    for object_id, name in entries:
        end = batch.index(b'\n', offset)
        returned_id, object_type, size = batch[offset:end].split()
        if returned_id != object_id or object_type != b'blob':
            raise RuntimeError(f'Unsupported index object: {name}')
        offset = end+1
        data = batch[offset:offset+int(size)]
        offset += int(size)+1
        for rule in violations(Path(name), data):
            failures.append((name, rule))
    for name, rule in failures:
        print(f'{name}: {rule}')
    print(f'Publication check: {len(listing)} indexed files, {len(failures)} violations')
    return bool(failures)


if __name__ == '__main__':
    sys.exit(main())

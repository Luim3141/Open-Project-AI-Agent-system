"""Explicit source allowlist to a private local Git snapshot; no remote or live data."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[5]
RUN = Path(__file__).parent
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator' / ('phase2-source-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
REPO = PRIVATE / 'source'
REPO.mkdir(parents=True)
allowed = {'.py', '.rb', '.erb', '.js', '.css', '.scss', '.json', '.yml', '.yaml', '.sh', '.ps1', '.txt', '.md', '.toml'}
paths = []
for folder in ['openproject/ai/gateway', 'openproject/ai/core/overlay', 'openproject/ai/automation', 'openproject/ai/tests', 'openproject/ai/engineering_skills']:
    paths += [p for p in (ROOT / folder).rglob('*') if p.is_file()
              and (p.suffix in allowed or 'Dockerfile' in p.name)
              and not any(v in p.parts for v in ['__pycache__', 'node_modules', '.venv'])]
paths += [ROOT / p for p in ['AGENTS.md', 'architecture.md', 'openproject/ai/.dockerignore', 'openproject/ai/requirements.txt', 'openproject/ai/requirements.lock.txt', 'openproject/ai/compose.yml', 'openproject/ai/gemini-free.main.yml']]
patterns = [r'AIza[0-9A-Za-z_-]{30,}', r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{40,}',
            r'_open_project_session=[A-Za-z0-9_-]{24,}']
included, quarantined = [], []
for path in sorted(set(paths)):
    relative = path.relative_to(ROOT)
    if path.name.lower().startswith(('.env', 'credentials', 'config.private')):
        quarantined.append({'path': str(relative), 'reason': 'private configuration name'}); continue
    content = path.read_bytes()
    if any(re.search(pattern, content.decode('utf-8', errors='replace')) for pattern in patterns):
        quarantined.append({'path': str(relative), 'reason': 'credential-shaped literal; no value exported'}); continue
    target = REPO / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    included.append({'path': str(relative), 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)})
assert all(Path(v['path']).suffix not in {'.sqlite', '.db', '.dump', '.token', '.key'} for v in included)
def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], stderr=subprocess.PIPE).decode().strip()
git('init', '-b', 'codex/recovery-phase2-source')
spec = PRIVATE / 'source-pathspec.nul'
spec.write_bytes(b''.join(Path(v['path']).as_posix().encode() + b'\0' for v in included))
git('add', '--pathspec-from-file=' + str(spec), '--pathspec-file-nul')
git('-c', 'user.name=Codex Recovery Snapshot', '-c', 'user.email=codex@localhost',
    'commit', '-m', 'Snapshot authorized QLDAPM Phase2 source; private data excluded')
inventory = {}
for name, args in [('tracked', ['ls-files']), ('untracked', ['ls-files', '--others', '--exclude-standard']),
                   ('ignored_paths', ['ls-files', '--others', '--ignored', '--exclude-standard', '--directory'])]:
    lines = subprocess.check_output(['git', *args], cwd=ROOT).decode().splitlines()
    inventory[name] = {'count': len(lines), 'paths': lines}
result = {'private_source_root': str(REPO), 'commit': git('rev-parse', 'HEAD'),
          'remote': git('remote', '-v'), 'included': included, 'quarantined': quarantined,
          'inventory': inventory, 'scope': 'source only; no credentials/DB/backups/artifacts; no public remote'}
(RUN / 'source-versioning-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'commit': result['commit'], 'private_source_root': str(REPO),
                  'source_files': len(included), 'quarantined': quarantined,
                  'original_repo_counts': {k: v['count'] for k, v in inventory.items()}}, indent=2))

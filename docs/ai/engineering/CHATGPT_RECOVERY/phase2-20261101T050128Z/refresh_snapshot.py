"""Refresh previously scanned allowlist only, local Git only; retain immutable old commits."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess
RUN=Path(__file__).parent;ROOT=RUN.parents[4]
m=json.loads((RUN/'source-versioning-manifest.json').read_text());repo=Path(m['private_source_root'])
changed=[]
for relative in ['openproject/ai/tests/test_engineering_delivery_recovery.py','openproject/ai/tests/test_n8n_lifecycle_adapter.py']:
    if not any(Path(row['path']).as_posix()==relative for row in m['included']):
        m['included'].append({'path':str(Path(relative)),'sha256':'','bytes':0})
for row in m['included']:
    source=ROOT/row['path'];data=source.read_bytes()
    if hashlib.sha256(data).hexdigest()==row['sha256']:continue
    assert not re.search(r'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',data.decode(errors='replace'))
    (repo/row['path']).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,repo/row['path']);changed.append(row['path'])
    row.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
if changed:
    subprocess.run(['git','-C',str(repo),'add','--',*changed],check=True)
    subprocess.run(['git','-C',str(repo),'-c','user.name=Codex Recovery Snapshot','-c','user.email=codex@localhost','commit','-m','Complete reviewed worker resume and lifecycle adapter contracts'],check=True)
m['commit']=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip()
(RUN/'source-versioning-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({'commit':m['commit'],'refreshed':changed},indent=2))

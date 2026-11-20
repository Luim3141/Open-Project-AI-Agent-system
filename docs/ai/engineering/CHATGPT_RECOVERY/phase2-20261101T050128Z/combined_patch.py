"""Reviewable exact source changes, pinned serving images and host before snapshots."""
from pathlib import Path
import difflib,hashlib,json,re,subprocess
RUN=Path(__file__).parent;ROOT=RUN.parents[4]
parity=json.loads((RUN/'candidate-final-parity.json').read_text());entries=[];patch=[]
def add(relative,before,label):
    after=(ROOT/'openproject/ai'/relative).read_bytes()
    assert not re.search(rb'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',before+after)
    if before==after:return
    patch.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='before/'+relative,tofile='after/'+relative))
    entries.append({'path':'openproject/ai/'+relative,'baseline':label,'before_sha256':hashlib.sha256(before).hexdigest() if before else None,'after_sha256':hashlib.sha256(after).hexdigest()})
for row in parity:
    relative=row['file']
    if relative.startswith('gateway/'):
        image='sha256:fcb44c49afb99efd85b4a00297a58e7c5a59d36ab2f2b78e15a6a6d135f5e93e';path='/app/'+relative
    elif relative.startswith('core/overlay/'):
        image='sha256:a4fa8150728bc5fc50f8afed22fce898cc52065a55ff0fdb53b803a81d9e1c6b';path='/app/'+relative.removeprefix('core/overlay/')
    else:add(relative,b'','new source');continue
    p=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','cat',image,path],capture_output=True,timeout=20)
    add(relative,p.stdout if p.returncode==0 else b'','pinned r24 serving image')
for relative,old in [('automation/engineering_worker.py',RUN.parent/'backups/core/engineering_worker.before.py'),
                     ('automation/engineering_delivery.py',RUN/'backups/engineering_delivery.before-rework-resume.py'),
                     ('automation/main_native_clone.py',RUN/'backups/root/main_native_clone.before.py')]:
    add(relative,old.read_bytes(),'host before snapshot; loaded process bytecode not verified')
for name in ['n8n_lifecycle_adapter.py','patch_n8n_storage.js','N8nRedacted.Dockerfile','GatewayRecovery.Dockerfile','CoreRecovery.Dockerfile']:
    add('automation/'+name,b'','new source')
(RUN/'recovery-final.patch').write_text(''.join(patch),encoding='utf-8')
(RUN/'changed-source-files.json').write_text(json.dumps(entries,indent=2)+'\n')
print(json.dumps({'changed_runtime_host_build_files':len(entries),'patch_bytes':(RUN/'recovery-final.patch').stat().st_size}))

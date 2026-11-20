"""Read-only old/candidate image rehearsal against the owned clone. Never restore Main."""
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

OUT=Path(__file__).parent
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'openproject/ai'))
from gateway.native import Native
from jira_sync_backup import command

OLD='sha256:bfda82ceec573e5104a797b517e497ec6d6b68a25e3f29a322c3879e1320754c'

def docker(*args):return command(['docker',*args],timeout=90).decode().strip()

def wait(port):
    for _ in range(90):
        try:
            request=urllib.request.Request(f'http://127.0.0.1:{port}/health_checks/default',headers={'Host':'localhost:18088'})
            with urllib.request.urlopen(request,timeout=2) as response:
                if response.status==200:return
        except (OSError,TimeoutError):pass
        time.sleep(1)
    raise RuntimeError('CLONE_IMAGE_HEALTH_TIMEOUT')

def fingerprint(db):
    sql="BEGIN READ ONLY; SELECT md5(string_agg(to_jsonb(w)::text,E'\\n' ORDER BY id)) FROM work_packages w WHERE project_id=5; COMMIT;"
    return docker('exec',db,'psql','-XqAt','-U','postgres','-d','openproject','-c',sql).strip()

def verify_image_source(image):
    root=REPO/'openproject/ai/core/overlay'
    files=[p for p in root.rglob('*') if p.is_file()]
    paths=['/app/'+p.relative_to(root).as_posix() for p in files]
    lines=docker('run','--rm','--network','none','--read-only','--entrypoint','sha256sum',image,*paths).splitlines()
    actual={line.split(maxsplit=1)[1].strip():line.split(maxsplit=1)[0] for line in lines}
    assert all(actual.get(path)==hashlib.sha256(p.read_bytes()).hexdigest() for p,path in zip(files,paths)), 'CANDIDATE_SOURCE_DRIFT'
    return len(files)

def main():
    clone=json.loads((OUT/'clone.json').read_text());names=clone['names'];private=Path(clone['private'])
    result={'at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'scope':'OWNED_CLONE_ONLY','provider_calls':0,'main_mutations':0}
    candidate=docker('image','inspect','qldapm-openproject:codex-main-20261020','--format','{{.Id}}')
    assert candidate==clone['image'];result['source_files_matched']=verify_image_source(candidate)
    before=fingerprint(names['db'])
    account=next(a for a in json.loads((private/'browser-accounts.json').read_text())['users'] if a['role']=='PM')
    rollback='qldapm-codex-main-20261020-rollback'
    if subprocess.run(['docker','inspect',rollback],capture_output=True,timeout=10).returncode==0:
        raise RuntimeError('ROLLBACK_CONTAINER_EXISTS_RECONCILE')
    docker('run','-d','--name',rollback,'--label',clone['label'],'--network',names['network'],
           '-p','127.0.0.1:18087:8080','--env-file',str(private/'browser.env'),'--memory','3g',
           '--mount',f'type=bind,src={private},dst=/qa-private','--entrypoint','bundle',OLD,
           'exec','rails','server','-b','0.0.0.0','-p','8080')
    docker('network','connect',names['front'],rollback)
    try:
        wait(18087)
        who=Native('http://127.0.0.1:18087',account['token'],5).identity(account['id'])
        assert who['role']=='PM'
        result['old_image']={'image':docker('inspect',rollback,'--format','{{.Image}}'),'health':'PASS','native_identity':'PASS'}
    finally:
        info=json.loads(docker('inspect',rollback))[0]
        assert info['Config']['Labels'].get('qldapm.qualification')=='codex-main-20261020'
        docker('stop','--time','30',rollback)
    docker('start',names['browser'])
    wait(18088)
    who=Native('http://127.0.0.1:18088',account['token'],5).identity(account['id'])
    assert who['role']=='PM'
    result['candidate_image']={'image':docker('inspect',names['browser'],'--format','{{.Image}}'),'health':'PASS','native_identity':'PASS'}
    assert result['candidate_image']['image']==candidate
    assert fingerprint(names['db'])==before,'CLONE_WORK_PACKAGES_CHANGED'
    result.update(passed=True,work_packages_unchanged=True,rollback_container_retained_stopped=True)
    (OUT/'rollback-rehearsal.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

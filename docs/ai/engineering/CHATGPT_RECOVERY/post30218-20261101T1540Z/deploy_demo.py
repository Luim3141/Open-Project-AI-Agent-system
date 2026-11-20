import hashlib, io, json, os, sqlite3, subprocess, tarfile, time, urllib.request
from pathlib import Path

sha='0498ceeda97cd3e856a975129129e71f6c94a3dd'
old='def9d0a8852af42a407bd42fb0051615a2de9331'
root=Path('/home/openclaw/engineering'); repo=Path('/home/openclaw/workspaces/mini-task-manager')
wrapper=root/'mini-task-manager-server.py'; db=root/'demo-data/tasks.sqlite'
private=root/'operator'/'post30218-demo-20261101'; private.mkdir(parents=True,exist_ok=False)
release=root/'releases'/sha
assert not release.exists()
original=wrapper.read_bytes(); assert original.count(old.encode())==2
(private/'server-original.py').write_bytes(original)
subprocess.run(['git','-C',str(repo),'cat-file','-e',sha+'^{commit}'],check=True)
archive=subprocess.check_output(['git','-C',str(repo),'archive',sha])
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    for m in tar.getmembers():
        p=Path(m.name)
        assert not p.is_absolute() and '..' not in p.parts and (m.isfile() or m.isdir()), m.name
    release.mkdir(); tar.extractall(release,filter='data')
with sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True) as source, sqlite3.connect(private/'tasks-before.sqlite') as backup:
    source.backup(backup)
    assert backup.execute('pragma integrity_check').fetchone()[0]=='ok'
    schema=backup.execute("select type,name,sql from sqlite_master order by type,name").fetchall()
    before=backup.execute('select * from tasks order by id').fetchall()
env=os.environ.copy();env['NODE_BINARY']='/home/openclaw/.openclaw/tools/node-v24.22.2/bin/node'
test=subprocess.run([str(root/'feedback-4d13e695555a8d44/.venv/bin/python'),'-m','pytest','-q','tests','-o','cache_dir=/tmp/qldapm-demo-release-pytest'],cwd=release,env=env,capture_output=True,text=True)
(private/'pytest.log').write_text(test.stdout+test.stderr)
assert test.returncode==0,'Candidate tests failed'
changed=original.replace(old.encode(),sha.encode())
tmp=wrapper.with_suffix('.candidate'); tmp.write_bytes(changed); tmp.chmod(wrapper.stat().st_mode); tmp.replace(wrapper)
try:
    subprocess.run(['systemctl','--user','restart','qldapm-mini-task-manager'],check=True,timeout=60)
    for _ in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1:18791/healthz',timeout=2) as response:
                assert response.status==200 and response.headers['X-QLDAPM-Revision']==sha
            with urllib.request.urlopen('http://127.0.0.1:18791/tasks/summary',timeout=2) as response: assert response.status==200
            break
        except Exception: time.sleep(1)
    else: raise RuntimeError('Demo readiness timeout')
    with sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True) as check:
        assert check.execute('pragma integrity_check').fetchone()[0]=='ok'
        assert check.execute("select type,name,sql from sqlite_master order by type,name").fetchall()==schema
        assert check.execute('select * from tasks order by id').fetchall()==before
    print(json.dumps({'status':'READY','sha':sha,'old_sha':old,'test':'PASS','health':200,'summary':200,'schema_unchanged':True,'rows_unchanged':True,'backup_sha256':hashlib.sha256((private/'tasks-before.sqlite').read_bytes()).hexdigest()}))
except Exception:
    tmp.write_bytes(original); tmp.chmod(wrapper.stat().st_mode); tmp.replace(wrapper)
    subprocess.run(['systemctl','--user','restart','qldapm-mini-task-manager'],check=True,timeout=60)
    raise

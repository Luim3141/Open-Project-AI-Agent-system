"""Deploy an exact unmerged integration commit to the loopback demo; retain rollback."""
import base64,datetime,hashlib,json,os,re,subprocess,sys,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.engineering_worker import python as linux_python,wsl,write_linux

OUT=Path(__file__).parent;SOURCE=ROOT/'.codex-local/demo-release-candidate'
URL='http://127.0.0.1:18791';DATA='/home/openclaw/engineering/demo-data/tasks.sqlite'
UNIT='qldapm-mini-task-manager.service';SERVER='/home/openclaw/engineering/mini-task-manager-server.py'
SYSTEMCTL=['/usr/bin/env','XDG_RUNTIME_DIR=/run/user/1000','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus','/usr/bin/systemctl','--user']
def systemctl(*args):return wsl(SYSTEMCTL+list(args),timeout=60)
def get(path):
 try:response=urllib.request.urlopen(URL+path,timeout=10)
 except urllib.error.HTTPError as error:response=error
 with response:return response.status,dict(response.headers),response.read()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE).decode().strip()
assert re.fullmatch('[a-f0-9]{40}',head)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=SOURCE).strip()
final=json.loads((OUT/'final.json').read_text());assert final['exit_code']==0
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('integration-demo-release-'+stamp)
private.mkdir(parents=True,exist_ok=False)
before_program=wsl(['/usr/bin/cat',SERVER]).stdout.decode()
before_unit=wsl(['/usr/bin/cat','/home/openclaw/.config/systemd/user/'+UNIT]).stdout.decode()
(private/'server.before.py').write_text(before_program);(private/'unit.before.service').write_text(before_unit)
old_service=(ROOT/'docs/ai/engineering/demo-service.json').read_bytes();(private/'demo-service.before.json').write_bytes(old_service)
release='/home/openclaw/engineering/releases/'+head
archive=subprocess.check_output(['git','archive','--format=zip',head],cwd=SOURCE)
metadata={'revision':head,'type':'UNMERGED_INTEGRATION_TEST_RELEASE','included_prs':[6,7,8,9,10]}
prepare=r'''
from pathlib import Path,PurePosixPath
import base64,io,zipfile,hashlib,sqlite3
root=Path(document['release']);root.mkdir(parents=True,exist_ok=True)
archive=base64.b64decode(document['archive']);assert hashlib.sha256(archive).hexdigest()==document['archive_sha256']
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 assert len(z.infolist())<200 and sum(i.file_size for i in z.infolist())<2097152
 for info in z.infolist():
  name=PurePosixPath(info.filename);assert not name.is_absolute() and '..' not in name.parts
  if info.is_dir():continue
  path=root.joinpath(*name.parts);path.parent.mkdir(parents=True,exist_ok=True);data=z.read(info)
  if path.exists():assert path.read_bytes()==data
  else:path.write_bytes(data)
def logical(db):
 return {'schema':db.execute("select type,name,tbl_name,sql from sqlite_master where name not like 'sqlite_autoindex%' order by type,name").fetchall(),'tasks':db.execute('select id,title,status from tasks order by id').fetchall(),'sequences':db.execute('select * from sqlite_sequence order by name').fetchall()}
with sqlite3.connect(document['data']) as source:
 before=logical(source)
 backup=Path('/home/openclaw/engineering/demo-data/backups')/('integration-'+document['stamp']+'.sqlite');backup.parent.mkdir(exist_ok=True)
 with sqlite3.connect(backup) as destination:source.backup(destination)
print(json.dumps({'sqlite_backup':str(backup),'logical_sha256':hashlib.sha256(json.dumps(before,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'task_count':len(before['tasks']),'schema_sha256':hashlib.sha256(json.dumps(before['schema']).encode()).hexdigest()}))
'''
before=json.loads(linux_python(prepare,{'release':release,'archive':base64.b64encode(archive).decode(),'archive_sha256':hashlib.sha256(archive).hexdigest(),'data':DATA,'stamp':stamp}).stdout)
backup=wsl(['/usr/bin/cat',before['sqlite_backup']]).stdout;(private/'tasks.before.sqlite').write_bytes(backup)
server='import sys\nsys.path.insert(0,'+repr(release)+')\nfrom task_manager.app import create_app\nimport uvicorn\napp=create_app('+repr(DATA)+',release='+repr(metadata)+')\nuvicorn.run(app,host="127.0.0.1",port=18791,access_log=False)\n'
unit='''[Unit]
Description=QLDAPM unmerged integration test release
After=network.target
[Service]
Type=simple
WorkingDirectory='''+release+'''
ExecStart=/home/openclaw/engineering/feedback-2ec52f6742aa972f/.venv/bin/python '''+SERVER+'''
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
UMask=0077
MemoryMax=256M
CPUQuota=50%
[Install]
WantedBy=default.target
'''
changed=False
try:
 systemctl('stop',UNIT)
 changed=True;write_linux(SERVER,server);write_linux('/home/openclaw/.config/systemd/user/'+UNIT,unit)
 systemctl('daemon-reload');systemctl('start',UNIT)
 for _ in range(30):
  try:
   code,headers,body=get('/healthz')
   if code==200 and headers.get('x-qldapm-revision',headers.get('X-QLDAPM-Revision'))==head:break
  except OSError:pass
  time.sleep(1)
 else:raise ValueError('INTEGRATION_RELEASE_NOT_READY')
 assert json.loads(get('/release')[2])==metadata
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'DEPLOYED_INTEGRATION_TEST_RELEASE','head_sha':head,'branch':'codex/demo-integration-20261103','included_prs':[6,7,8,9,10],'main_merged':False,'source':'UNMERGED_INTEGRATION','url':URL,'release':release,'database':DATA,'service':UNIT,'before':before,'backup':str(private),'archive_sha256':hashlib.sha256(archive).hexdigest(),'tests_passed':True,'source_revision_header':head}
 verify=r'''
import sqlite3,hashlib
with sqlite3.connect(document['data']) as db:
 data={'schema':db.execute("select type,name,tbl_name,sql from sqlite_master where name not like 'sqlite_autoindex%' order by type,name").fetchall(),'tasks':db.execute('select id,title,status from tasks order by id').fetchall(),'sequences':db.execute('select * from sqlite_sequence order by name').fetchall()}
print(json.dumps({'logical_sha256':hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'task_count':len(data['tasks'])}))
'''
 after=json.loads(linux_python(verify,{'data':DATA}).stdout);assert after['logical_sha256']==before['logical_sha256']
 result['after']=after;result['data_preserved']=True
 (OUT/'deployment.json').write_text(json.dumps(result,indent=2)+'\n')
 (ROOT/'docs/ai/engineering/demo-service.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
except Exception:
 if changed:
  write_linux(SERVER,before_program);write_linux('/home/openclaw/.config/systemd/user/'+UNIT,before_unit)
  systemctl('daemon-reload');systemctl('restart',UNIT)
 raise

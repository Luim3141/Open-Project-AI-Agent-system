"""Install the verified demo commit as one loopback user service; preserve its data."""
import base64
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request
import uuid
import argparse
import datetime

from automation.engineering_worker import operator,wsl,python,write_linux,save,ROOT

WORK='/home/openclaw/engineering/crud-search-web-v1'
DATA='/home/openclaw/engineering/demo-data/tasks.sqlite'
UNIT='qldapm-mini-task-manager.service'
URL='http://127.0.0.1:18791'


def systemctl(*args):
    return wsl(['/usr/bin/env','XDG_RUNTIME_DIR=/run/user/1000','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus',
        '/usr/bin/systemctl','--user',*args])


def request(path,method='GET',body=None):
    data=json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(URL+path,data=data,method=method,
        headers={'Content-Type':'application/json'}),timeout=10) as response:
        content=response.read()
        return response.status,json.loads(content) if 'application/json' in response.headers.get('Content-Type','') and content else content.decode()


def install(run_id=None,update=False):
    global WORK
    status=operator('status')
    if status['mode']!='OFF':raise ValueError('ENGINEERING_OFF_REQUIRED')
    selected=next(r for r in status['runs'] if r['id']==run_id) if run_id else next(r for r in status['runs'] if r['unit']=='crud-search-web-v1')
    if run_id:
        if not re.fullmatch('[a-z0-9][a-z0-9-]{1,79}',selected['unit']):raise ValueError('UNIT_PATH_INVALID')
        WORK='/home/openclaw/engineering/'+selected['unit']
    result=selected['result'];head=result.get('head_sha','')
    if result['status']!='succeeded' or not re.fullmatch('[a-f0-9]{40}',head):raise ValueError('VERIFIED_HEAD_REQUIRED')
    previous=None
    server_path='/home/openclaw/engineering/mini-task-manager-server.py'
    unit_path='/home/openclaw/.config/systemd/user/'+UNIT
    if update:
        previous=json.loads((ROOT/'docs/ai/engineering/demo-service.json').read_text())
        if previous['database']!=DATA or previous['service']!=UNIT:raise ValueError('DEMO_BASELINE_CHANGED')
        before_program=wsl(['/usr/bin/cat',server_path]).stdout.decode();before_unit=wsl(['/usr/bin/cat',unit_path]).stdout.decode()
        save(ROOT/'docs/ai/engineering','demo-service-before-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json',previous)
    else:python("import socket\ns=socket.socket();s.bind(('127.0.0.1',18791));s.close()")
    if wsl(['/usr/bin/git','-C',WORK,'rev-parse','HEAD']).stdout.decode().strip()!=head:raise ValueError('HEAD_CHANGED')
    archive=wsl(['/usr/bin/git','-C',WORK,'archive','--format=zip',head]).stdout
    release='/home/openclaw/engineering/releases/'+head
    python('''from pathlib import Path,PurePosixPath
import io,zipfile,base64,hashlib,stat
root=Path(document['release']);root.mkdir(parents=True,exist_ok=True)
data=base64.b64decode(document['archive'])
if hashlib.sha256(data).hexdigest()!=document['sha256']:raise ValueError('ARCHIVE_CHANGED')
with zipfile.ZipFile(io.BytesIO(data)) as z:
 if len(z.infolist())>200 or sum(i.file_size for i in z.infolist())>2097152:raise ValueError('ARCHIVE_BOUND')
 for info in z.infolist():
  name=PurePosixPath(info.filename)
  if name.is_absolute() or '..' in name.parts or stat.S_ISLNK(info.external_attr>>16):raise ValueError('ARCHIVE_PATH')
  path=root.joinpath(*name.parts)
  if info.is_dir():path.mkdir(parents=True,exist_ok=True);continue
  content=z.read(info);path.parent.mkdir(parents=True,exist_ok=True)
  if path.exists() and path.read_bytes()!=content:raise ValueError('EXISTING_RELEASE_CHANGED')
  if not path.exists():path.write_bytes(content)
Path('/home/openclaw/engineering/demo-data').mkdir(mode=0o700,exist_ok=True)
''',{'release':release,'archive':base64.b64encode(archive).decode(),'sha256':hashlib.sha256(archive).hexdigest()})
    server="import sys\nsys.path.insert(0,"+repr(release)+")\nfrom task_manager.app import create_app\nimport uvicorn\napp=create_app("+repr(DATA)+")\n@app.middleware('http')\nasync def revision_header(request,call_next):\n response=await call_next(request);response.headers['X-QLDAPM-Revision']="+repr(head)+";return response\nuvicorn.run(app,host='127.0.0.1',port=18791,access_log=False)\n"
    write_linux('/home/openclaw/engineering/mini-task-manager-server.py',server)
    service='''[Unit]
Description=QLDAPM verified Mini Task Manager demo
After=network.target
[Service]
Type=simple
WorkingDirectory='''+release+'''
ExecStart='''+WORK+'''/.venv/bin/python /home/openclaw/engineering/mini-task-manager-server.py
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
    write_linux('/home/openclaw/.config/systemd/user/'+UNIT,service)
    try:
        systemctl('daemon-reload');systemctl('enable','--now',UNIT);systemctl('restart',UNIT)
        for _ in range(15):
            try:
                if request('/')[0]==200:break
            except OSError:time.sleep(1)
        else:raise ValueError('DEMO_NOT_READY')
    except Exception:
        if update:
            write_linux(server_path,before_program);write_linux(unit_path,before_unit)
            systemctl('daemon-reload');systemctl('restart',UNIT)
        raise
    if systemctl('is-active',UNIT).stdout.decode().strip()!='active':raise ValueError('DEMO_SERVICE_NOT_ACTIVE')
    if update:
        with urllib.request.urlopen(URL,timeout=10) as response:
            if response.headers.get('X-QLDAPM-Revision')!=head:raise ValueError('DEMO_REVISION_HEADER_MISMATCH')
        evidence={'url':URL,'head_sha':head,'release':release,'database':DATA,'service':UNIT,'http_html':200,
            'prior_head_sha':previous['head_sha'],'run_id':run_id,'update':'VERIFIED_RELEASE_PROMOTED','data_preserved':True,
            'manual_browser_uat':'DEFERRED_BY_USER','source_revision_header':head,'service_status':systemctl('show',UNIT,'--property=ActiveState,SubState,MainPID').stdout.decode().strip()}
        save(ROOT/'docs/ai/engineering','demo-service.json',evidence);print(json.dumps(evidence));return
    # One clearly owned fixture exercises the running server and persistence.
    marker='QLDAPM terminal smoke '+uuid.uuid4().hex[:10]
    code,created=request('/tasks','POST',{'title':marker})
    if code!=201:raise ValueError('DEMO_CREATE_FAILED')
    path='/tasks/'+str(created['id']);edited=marker+' edited'
    code,item=request(path,'PATCH',{'title':edited,'status':'done'})
    if code!=200 or item['title']!=edited:raise ValueError('DEMO_EDIT_FAILED')
    systemctl('restart',UNIT)
    for _ in range(15):
        try:
            if request('/tasks')[0]==200:break
        except OSError:time.sleep(1)
    rows=request('/tasks')[1]
    if not any(r['id']==item['id'] and r['title']==edited and r['status']=='done' for r in rows):raise ValueError('DEMO_PERSISTENCE_FAILED')
    if request(path,'DELETE')[0]!=204:raise ValueError('DEMO_OWN_FIXTURE_DELETE_FAILED')
    evidence={'url':URL,'head_sha':head,'release':release,'database':DATA,'service':UNIT,
        'http_html':request('/')[0],'create_edit_status_restart_persistence_delete':'PASS',
        'fixture_id':item['id'],'fixture_removed':True,'manual_browser_uat':'NOT_RUN_USER_WILL_TEST',
        'service_status':systemctl('show',UNIT,'--property=ActiveState,SubState,MainPID').stdout.decode().strip()}
    save(ROOT/'docs/ai/engineering','demo-service.json',evidence)
    print(json.dumps(evidence))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--update-run');args=parser.parse_args()
    install(args.update_run,bool(args.update_run))

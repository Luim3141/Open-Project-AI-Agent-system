"""Disposable n8n canary + real lifecycle HTTP delivery; no MAIN mounts or ports."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'openproject/ai'))
from automation.n8n_lifecycle_adapter import attach_lifecycle_adapter, RETENTION_SETTINGS

RUN = Path(__file__).parent
IDENTIFIER = str(uuid.uuid4())
LABEL = 'org.qldapm.phase2=' + IDENTIFIER
N8N_IMAGE = os.environ.get('QLDAPM_N8N_TEST_IMAGE', 'qldapm-n8n:recovery-phase2-redacted-r1')
PREFIX = 'qldapm-recovery-p2-' + IDENTIFIER[:8]
NETWORK, N8N, GATEWAY = PREFIX + '-net', PREFIX + '-n8n', PREFIX + '-gateway'
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator' / PREFIX
PRIVATE.mkdir()
KEY = uuid.uuid4().hex + uuid.uuid4().hex
CANARIES = [uuid.uuid4().hex for _ in range(3)]
created = []
result = {'status': 'RUNNING', 'private_path': str(PRIVATE), 'network': NETWORK, 'n8n_image': N8N_IMAGE}


def docker(*args, data=None, check=True, timeout=90):
    p = subprocess.run(['docker', *args], input=data, capture_output=True, timeout=timeout)
    if check and p.returncode:
        error = (p.stdout + p.stderr).decode(errors='replace')
        for secret in [KEY, *CANARIES]: error = error.replace(secret, '[CANARY_REDACTED]')
        (RUN / 'n8n-clone-error.log').write_text(error)
        raise RuntimeError('CLONE_COMMAND_FAILED: ' + args[0])
    return p


def node(code, payload=None, check=True):
    return docker('exec', '-i', N8N, 'node', '-e', code,
                  data=json.dumps(payload).encode() if payload is not None else None, check=check)


def wait_ready(name, code):
    for _ in range(75):
        if docker('exec', name, *code, check=False, timeout=10).returncode == 0: return
        time.sleep(1)
    raise RuntimeError('CLONE_READINESS_TIMEOUT')


gateway_source = '''import json,os,threading,time,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from types import SimpleNamespace
from gateway.store import Store
from gateway.execution_events import append
from gateway.n8n_lifecycle_outbox import observe,deliver_pending,ensure_schema
store=Store('/tmp/state');key=os.environ['CLONE_SIGNING_KEY']
scope=SimpleNamespace(run_id=str(uuid.uuid4()),trace_id=str(uuid.uuid4()),actor_id=20,project_id=6)
with store.connect() as db:ensure_schema(db)
def tick():
 while True:
  deliver_pending(store,{'enabled':True,'webhook_url':'http://n8n:5678/webhook/qldapm-lifecycle','signing_key':key})
  time.sleep(.2)
threading.Thread(target=tick,daemon=True).start()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,body,status=200):
  b=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  with store.connect() as db:
   self.reply({'outbox':[list(r) for r in db.execute('SELECT state,attempts FROM n8n_lifecycle_outbox')],'observations':db.execute('SELECT count(*) FROM n8n_lifecycle_observations').fetchone()[0],'executions':[r[0] for r in db.execute('SELECT execution_id FROM n8n_lifecycle_execution_metadata')]})
 def do_POST(self):
  if self.path=='/emit':
   with store.connect() as db:append(db,scope,'AGENT_STARTED',agent='dev',status='RUNNING',key='clone-agent-start')
   return self.reply({'emitted':True},202)
  if self.path!='/internal/automation/lifecycle-observation':return self.reply({},404)
  try:self.reply(observe(store,json.loads(self.rfile.read(int(self.headers['Content-Length']))),key,self.headers.get('X-QLDAPM-N8N-Execution')))
  except Exception:self.reply({'error':'OBSERVATION_DENIED'},403)
ThreadingHTTPServer(('0.0.0.0',8090),Handler).serve_forever()
'''
(PRIVATE / 'gateway_fixture.py').write_text(gateway_source)
gateway_source = '''import json,os,uuid,uvicorn
from pathlib import Path
from types import SimpleNamespace
from gateway.store import Store
from gateway.service import Service
from gateway.app import create_app
from gateway.execution_events import append
store=Store('/tmp/state');key=os.environ['CLONE_SIGNING_KEY']
scope=SimpleNamespace(run_id=str(uuid.uuid4()),trace_id=str(uuid.uuid4()),actor_id=20,project_id=6)
with store.connect() as db:append(db,scope,'AGENT_STARTED',agent='dev',status='RUNNING',key='clone-agent-start')
config={'project_id':6,'users':{},'hosts':['gateway:8090','localhost:8090'],
 'engineering':{'enabled':False},'openproject_url':'http://127.0.0.1:9',
 'n8n_lifecycle':{'enabled':True,'webhook_url':'http://n8n:5678/webhook/qldapm-lifecycle','signing_key':key}}
service=Service(store,config,Path('/tmp/workspaces'))
uvicorn.run(create_app('/tmp/state',service),host='0.0.0.0',port=8090)
'''
(PRIVATE / 'gateway_fixture.py').write_text(gateway_source)
adapter = attach_lifecycle_adapter({'id': 'p2Lifecycle', 'name': 'Isolated WF04 lifecycle observation',
                                    'nodes': [], 'connections': {}, 'settings': {}}, 'http://gateway:8090')
workflows = [adapter]
for kind in ['success', 'error', 'manual']:
    trigger = {'id': 'trigger', 'name': 'Trigger', 'typeVersion': 2 if kind != 'manual' else 1,
               'type': 'n8n-nodes-base.webhook' if kind != 'manual' else 'n8n-nodes-base.manualTrigger',
               'position': [0, 0], 'parameters': {'httpMethod': 'POST', 'path': 'canary-' + kind,
                   'responseMode': 'lastNode', 'options': {}} if kind != 'manual' else {}}
    if kind != 'manual': trigger['webhookId'] = 'p2-canary-' + kind
    code = "throw new Error('SYNTHETIC_ERROR');" if kind == 'error' else 'return [{json:{status:"ok"}}];'
    if kind == 'manual': code = 'return [{json:{headers:{authorization:' + json.dumps('Basic ' + CANARIES[2]) + '}}}];'
    workflows.append({'id': 'p2Canary' + kind, 'name': 'Canary ' + kind, 'nodes': [trigger,
        {'id': 'code', 'name': 'Code', 'type': 'n8n-nodes-base.code', 'typeVersion': 2,
         'position': [240, 0], 'parameters': {'jsCode': code}}],
        'connections': {'Trigger': {'main': [[{'node': 'Code', 'type': 'main', 'index': 0}]]}},
        'settings': RETENTION_SETTINGS})
    if kind == 'manual':
        workflows[-1]['nodes'].append({'id':'header-fixture','name':'Disabled Header Fixture','disabled':True,
            'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[500,300],
            'parameters':{'url':'http://gateway:8090/','sendHeaders':True,'headerParameters':{'parameters':[
                {'name':'X-QLDAPM-Webhook-Token','value':CANARIES[2]},
                {'name':'Authorization','value':'Basic '+CANARIES[2]}]}}})
(PRIVATE / 'workflows.json').write_text(json.dumps(workflows))

try:
    docker('network', 'create', '--internal', '--label', LABEL, NETWORK); created.append(('network', NETWORK))
    args = ['run', '-d', '--pull', 'never', '--name', N8N, '--label', LABEL, '--network', NETWORK,
            '--network-alias', 'n8n', '--mount', f'type=bind,source={PRIVATE},target=/fixtures,readonly',
            '--tmpfs', '/home/node/.n8n:rw,uid=1000,gid=1000,mode=0700', '--memory', '1g',
            '--entrypoint', '/bin/sh']
    for key, value in {'EXECUTIONS_DATA_SAVE_ON_SUCCESS': 'none', 'EXECUTIONS_DATA_SAVE_ON_ERROR': 'none',
        'EXECUTIONS_DATA_SAVE_ON_PROGRESS': 'false', 'EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS': 'false',
        'N8N_DIAGNOSTICS_ENABLED': 'false', 'N8N_VERSION_NOTIFICATIONS_ENABLED': 'false',
        'N8N_TEMPLATES_ENABLED': 'false', 'N8N_SECURE_COOKIE': 'false'}.items(): args += ['-e', key + '=' + value]
    docker(*args, N8N_IMAGE, '-c', 'sleep 1800'); created.append(('container', N8N))
    docker('exec', N8N, 'n8n', 'user-management:reset')
    docker('exec', N8N, 'n8n', 'import:workflow', '--input=/fixtures/workflows.json')
    for workflow in workflows[:3]: docker('exec', N8N, 'n8n', 'publish:workflow', '--id=' + workflow['id'])
    docker('exec', '-d', N8N, '/bin/sh', '-c', 'n8n start > /tmp/n8n.log 2>&1 & echo $! > /tmp/n8n.pid; wait')
    wait_ready(N8N, ['node', '-e', "fetch('http://localhost:5678/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"])
    docker('run', '-d', '--pull', 'never', '--name', GATEWAY, '--label', LABEL, '--network', NETWORK,
        '--network-alias', 'gateway', '--read-only', '--tmpfs', '/tmp:rw,size=64m',
        '--mount', f'type=bind,source={ROOT / "openproject/ai"},target=/src,readonly',
        '--mount', f'type=bind,source={PRIVATE},target=/fixtures,readonly',
        '-e', 'PYTHONPATH=/src', '-e', 'QLDAPM_AI_RUNTIME=', '-e', 'PYTHONDONTWRITEBYTECODE=1',
        '-e', 'CLONE_SIGNING_KEY=' + KEY, '--entrypoint', 'python',
        'qldapm-ai:chatgpt-recovery-20261101-r2', '/fixtures/gateway_fixture.py')
    created.append(('container', GATEWAY))
    request = "const p=JSON.parse(require('fs').readFileSync(0,'utf8'));fetch(p.url,{method:p.method||'GET',headers:p.headers||{},body:p.body}).then(async r=>console.log(JSON.stringify({status:r.status,body:await r.text()}))).catch(()=>process.exit(1))"
    for _ in range(60):
        response = node(request, {'url': 'http://gateway:8090/health'}, check=False)
        if response.returncode == 0: break
        time.sleep(1)
    else: raise RuntimeError('GATEWAY_FIXTURE_TIMEOUT')
    for _ in range(60):
        stats="import sqlite3,json;d=sqlite3.connect('file:/tmp/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'outbox':d.execute('SELECT state,attempts FROM n8n_lifecycle_outbox').fetchall(),'observations':d.execute('SELECT count(*) FROM n8n_lifecycle_observations').fetchone()[0],'executions':[r[0] for r in d.execute('SELECT execution_id FROM n8n_lifecycle_execution_metadata')]}))"
        status = docker('exec',GATEWAY,'python','-c',stats,check=False)
        if status.returncode:time.sleep(1);continue
        observed = json.loads(status.stdout)
        if observed['observations'] == 1 and observed['outbox'][0][0] == 'ACKED': break
        time.sleep(1)
    else: raise RuntimeError('LIFECYCLE_NOT_ACKED')
    assert observed['executions'] and all(str(v).isdigit() for v in observed['executions'])
    result['automatic_event_delivery'] = observed
    result['gateway_runtime']='actual ASGI lifespan + Service background publisher + signed observation route'
    result['canary_http'] = {}
    for kind, secret in zip(['success', 'error'], CANARIES):
        raw = json.loads(node(request, {'url': 'http://localhost:5678/webhook/canary-' + kind, 'method': 'POST',
            'headers': {'Authorization': ('Basic ' if kind == 'error' else 'Bearer ') + secret, 'X-QLDAPM-Webhook-Token': secret,
                        'Content-Type': 'application/json'}, 'body': '{}'}).stdout)
        result['canary_http'][kind] = raw['status']
    assert result['canary_http'] == {'success': 200, 'error': 500}
    # CLI execute starts its own broker; stop only this disposable clone's server first.
    node("process.kill(Number(require('fs').readFileSync('/tmp/n8n.pid','utf8')),'SIGTERM')")
    for _ in range(30):
        gone = node("try{process.kill(Number(require('fs').readFileSync('/tmp/n8n.pid','utf8')),0);process.exit(1)}catch{process.exit(0)}", check=False)
        if gone.returncode == 0: break
        time.sleep(1)
    manual = docker('exec', N8N, 'n8n', 'execute', '--id=p2Canarymanual', check=False)
    manual_log = (manual.stdout + manual.stderr).decode(errors='replace')
    for secret in [KEY, *CANARIES]: manual_log = manual_log.replace(secret, '[CANARY_REDACTED]')
    (RUN / 'n8n-manual-redacted.log').write_text(manual_log)
    result['manual_exit_code'] = manual.returncode
    assert manual.returncode == 0
    # Inspect data tables and daemon log; workflow definitions intentionally contain a synthetic manual fixture.
    scan = """const p=JSON.parse(require('fs').readFileSync(0,'utf8'));const sqlite=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));const db=new sqlite.Database('/home/node/.n8n/database.sqlite',sqlite.OPEN_READONLY);db.all(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'execution_%'\",(e,t)=>{if(e)throw e;Promise.all(t.map(v=>new Promise((resolve,reject)=>db.all('SELECT * FROM '+v.name,(err,rows)=>err?reject(err):resolve({table:v.name,rows:rows.length,leaked:p.some(s=>JSON.stringify(rows).includes(s))}))))).then(r=>{const log=require('fs').readFileSync('/tmp/n8n.log','utf8');console.log(JSON.stringify({tables:r,log_leaked:p.some(s=>log.includes(s))}));db.close();});});"""
    time.sleep(2)
    retention = json.loads(node(scan, CANARIES).stdout)
    result['retention'] = retention
    assert not retention['log_leaked'] and not any(t['leaked'] for t in retention['tables'])
    result['status'] = 'CLONE_EVENT_AND_RETENTION_VERIFIED'
finally:
    (RUN / 'n8n-clone-result.json').write_text(json.dumps(result, indent=2) + '\n')
    for kind, name in reversed(created):
        command = ['network', 'inspect'] if kind == 'network' else ['inspect']
        data = json.loads(docker(*command, name).stdout)[0]
        labels = data['Labels'] if kind == 'network' else data['Config']['Labels']
        assert labels.get('org.qldapm.phase2') == IDENTIFIER and name.startswith(PREFIX)
        docker('network', 'rm', name) if kind == 'network' else docker('rm', '-f', name)
print(json.dumps({'status': result['status'], 'automatic_event_delivery': result.get('automatic_event_delivery'),
                  'canary_http': result.get('canary_http'), 'manual_exit_code': result.get('manual_exit_code')}, indent=2))

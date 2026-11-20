"""Replay MAIN's published n8n adapters on an internal, disposable network.

Synthetic Gateway responses exercise adapter contracts, not Native/provider/RAG correctness.
No MAIN business requests, secret export, production mounts, or production mutations.
"""
from pathlib import Path
import copy
import hashlib
import json
import os
import subprocess
import time
import uuid

ROOT = Path.cwd()
OUT = Path(__file__).parent
IMAGE = 'sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795'
GATEWAY_IMAGE = 'sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb'
IDENT = uuid.uuid4().hex[:10]
PREFIX = 'qldapm-business-' + IDENT
NETWORK, N8N, GATEWAY = [PREFIX + '-' + value for value in ('net', 'n8n', 'gateway')]
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator' / PREFIX
created = []
result = {'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
          'command': 'openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/workflows/qualify_published.py',
          'environment': 'isolated n8n actual published definitions + synthetic HTTP Gateway; internal Docker network',
          'n8n_image': IMAGE, 'gateway_fixture_image': GATEWAY_IMAGE, 'tests': [],
          'production_business_writes': 0, 'status': 'RUNNING'}


def docker(*args, data=None, check=True, timeout=120):
    p = subprocess.run(['docker', *args], input=data, capture_output=True, timeout=timeout)
    if check and p.returncode:
        (OUT / 'clone-error.log').write_bytes(p.stdout + p.stderr)
        raise RuntimeError('CLONE_COMMAND_FAILED: ' + args[0])
    return p


def node(code, data=None):
    return json.loads(docker('exec', '-i', N8N, 'node', '-e', code,
                            data=json.dumps(data).encode() if data is not None else None).stdout)


def wait_ready(container, url):
    for _ in range(75):
        p = docker('exec', container, 'node', '-e',
                   "fetch(" + json.dumps(url) + ").then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))", check=False)
        if not p.returncode:
            return
        time.sleep(1)
    raise RuntimeError('READINESS_TIMEOUT')


READ = """const s=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));
const d=new s.Database('/home/node/.n8n/database.sqlite',s.OPEN_READONLY);
d.all('SELECT w.id,w.name,w.activeVersionId,w.versionId,w.settings,h.nodes,h.connections FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId ORDER BY w.name',(e,r)=>{if(e)throw e;console.log(JSON.stringify(r));d.close()});"""
FETCH = """const p=JSON.parse(require('fs').readFileSync(0,'utf8'));fetch(p.url,{method:p.method||'GET',headers:p.headers||{},body:p.body,signal:AbortSignal.timeout(20000)}).then(async r=>console.log(JSON.stringify({status:r.status,body:await r.text()}))).catch(e=>{console.error(e.message);process.exit(1)})"""

FIXTURE = r'''import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
calls=[]
mode='ready'
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):self.handle_request()
 def do_POST(self):self.handle_request()
 def handle_request(self):
  global mode
  payload=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or '{}')
  if self.path=='/fixture/mode':
   mode=payload['mode'];calls.clear();response={'mode':mode};status=200
  elif self.path=='/fixture/calls':response=calls;status=200
  else:
   calls.append({'method':self.command,'path':self.path,'payload':payload,'authorization':self.headers.get('Authorization'),'signature_present':bool(self.headers.get('X-QLDAPM-Command-Signature'))})
   status=403 if mode=='denied' else 200
   if status==403:response={'error':'FIXTURE_FORBIDDEN','correlation_id':'fixture-correlation'}
   elif self.path=='/internal/automation/commands':response={'result':{'state':'COMPLETED','status':'PARTIAL' if mode=='partial' else 'READY','targets':5,'ready':4 if mode=='partial' else 5}}
   elif self.path=='/internal/automation/monitor':response={'status':'HEALTHY','fixture':True}
   elif '/proposals/' in self.path:response={'result':{'id':'11111111-1111-4111-8111-111111111111','hash':'a'*64,'state':'pending','lifecycle':'PENDING'},'correlation_id':'fixture-correlation'}
   else:response={'result':{'fixture':True,'items':[{'event_id':'fixture-event'}]},'correlation_id':'fixture-correlation'}
  data=json.dumps(response).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
ThreadingHTTPServer(('0.0.0.0',8090),Handler).serve_forever()
'''

PAYLOADS = {
 'WF01': {'source_key':'fixture-doc','operation':'search','query':'fixture query'},
 'WF02': {'operation':'status'}, 'WF03': {'operation':'status','run_id':'11111111-1111-4111-8111-111111111111'},
 'WF04': {'run_id':'11111111-1111-4111-8111-111111111111'},
 'WF05': {'proposal_id':'11111111-1111-4111-8111-111111111111'},
 'WF06': {'proposal_id':'11111111-1111-4111-8111-111111111111','decision':'reject','hash':'a'*64},
 'WF07': {}, 'WF08': {'as_of_date':'2026-11-02'}, 'WF09': {'id':389},
 'WF10': {'operation':'get','id':'11111111-1111-4111-8111-111111111111'},
 'WF11': {'id':389}, 'WF12': {'as_of_date':'2026-11-02'},
 'WF13': {'operation':'feedback_get','feedback_id':'11111111-1111-4111-8111-111111111111'},
 'WF14': {'job_id':'11111111-1111-4111-8111-111111111111'}, 'WF15': {}, 'WF16': {},
}
ACTIONS = dict(zip(['WF01','WF02','WF03','WF08','WF09','WF10','WF11','WF12','WF13','WF14','WF15'],
 ['knowledge_file_search','knowledge_incremental_status','get_ai_run','sprint_risks','get_work_package','wbs_get','qa_evidence_list','weekly_summary','knowledge_feedback_get','knowledge_sync_status','knowledge_integrity']))


def fixture(mode):
    node(FETCH, {'url':'http://gateway:8090/fixture/mode','method':'POST',
                 'headers':{'Content-Type':'application/json'},'body':json.dumps({'mode':mode})})


def webhook(path, payload, authenticated=True):
    headers={'Content-Type':'application/json','Authorization':'Bearer synthetic-actor'}
    if authenticated:
        headers['X-QLDAPM-Webhook-Token']='synthetic-transport'
    return node(FETCH, {'url':'http://localhost:5678/webhook/'+path,'method':'POST',
                       'headers':headers,'body':json.dumps(payload)})


def calls():
    return json.loads(node(FETCH, {'url':'http://gateway:8090/fixture/calls'})['body'])


def check(name, action):
    record={'name':name,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    try:
        action(record)
        record['outcome']='PASS'
    except Exception as error:
        record.update(outcome='FAIL',error=str(error))
    result['tests'].append(record)


def assert_equal(actual, expected):
    assert actual==expected, {'actual':actual,'expected':expected}


try:
    OUT.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir()
    rows=json.loads(docker('exec','qldapm-n8n-main','node','-e',READ).stdout)
    assert len(rows)==16
    (OUT/'published-definitions.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    result['published_snapshot_sha256']=hashlib.sha256((OUT/'published-definitions.json').read_bytes()).hexdigest()
    result['source_git_head']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    workflows=[]
    for row in rows:
        nodes=json.loads(row['nodes']); code=row['name'][:4]
        for n in nodes:
            if n['type']=='n8n-nodes-base.scheduleTrigger':n['disabled']=True
            if n['type']=='n8n-nodes-base.httpRequest':
                p=n['parameters'];p['url']=p['url'].replace('http://qldapm-ai-gateway-1:8090','http://gateway:8090').replace('http://host.docker.internal:18089','http://gateway:8090')
        workflows.append({'id':row['id'],'name':row['name'],'nodes':nodes,
            'connections':json.loads(row['connections']),
            'settings':{**json.loads(row['settings']),'saveDataErrorExecution':'none','saveDataSuccessExecution':'none','saveManualExecutions':False,'saveExecutionProgress':False}})
        if code=='WF12':
            trigger=copy.deepcopy(next(n for n in nodes if n['type']=='n8n-nodes-base.webhook'))
            trigger.update(id='clone-weekly-trigger',name='Clone Weekly Branch Trigger',webhookId='clone-weekly-trigger')
            trigger['parameters'].update(path='clone-weekly-schedule',responseMode='lastNode')
            nodes.append(trigger)
            metadata=next(n for n in nodes if n['id']=='weekly_metadata')
            workflows[-1]['connections'][trigger['name']]={'main':[[{'node':metadata['name'],'type':'main','index':0}]]}
    creds=[]
    for workflow in workflows:
        for n in workflow['nodes']:
            for kind,c in n.get('credentials',{}).items():
                data={'hmacSecret':'synthetic-signing'} if kind=='crypto' else {'name':'X-QLDAPM-Webhook-Token','value':'synthetic-transport'} if c['id']=='2w9dSdmYbywZDuMB' else {'name':'X-QLDAPM-Machine','value':'synthetic-machine'}
                if c['id'] not in [v['id'] for v in creds]:creds.append({'id':c['id'],'name':c['name'],'type':kind,'data':data})
    (PRIVATE/'workflows.json').write_text(json.dumps(workflows),encoding='utf-8')
    (PRIVATE/'credentials.json').write_text(json.dumps(creds),encoding='utf-8')
    (PRIVATE/'gateway_fixture.py').write_text(FIXTURE,encoding='utf-8')
    docker('network','create','--internal','--label','org.qldapm.business='+IDENT,NETWORK);created.append(('network',NETWORK))
    docker('run','-d','--pull','never','--name',GATEWAY,'--network',NETWORK,'--network-alias','gateway',
           '--label','org.qldapm.business='+IDENT,'--read-only','--tmpfs','/tmp:size=64m',
           '--mount',f'type=bind,source={PRIVATE},target=/fixtures,readonly','--entrypoint','python',GATEWAY_IMAGE,'/fixtures/gateway_fixture.py');created.append(('container',GATEWAY))
    docker('run','-d','--pull','never','--name',N8N,'--network',NETWORK,
           '--label','org.qldapm.business='+IDENT,'--tmpfs','/home/node/.n8n:rw,uid=1000,gid=1000,mode=0700',
           '--mount',f'type=bind,source={PRIVATE},target=/fixtures,readonly',
           '-e','N8N_DIAGNOSTICS_ENABLED=false','-e','N8N_VERSION_NOTIFICATIONS_ENABLED=false',
           '-e','N8N_TEMPLATES_ENABLED=false','-e','N8N_SECURE_COOKIE=false','--entrypoint','/bin/sh',IMAGE,'-c','sleep 1800');created.append(('container',N8N))
    docker('exec',N8N,'n8n','user-management:reset')
    docker('exec',N8N,'n8n','import:credentials','--input=/fixtures/credentials.json')
    docker('exec',N8N,'n8n','import:workflow','--input=/fixtures/workflows.json')
    for workflow in workflows:
        docker('exec',N8N,'n8n','publish:workflow','--id='+workflow['id'])
    docker('exec','-d',N8N,'/bin/sh','-c','n8n start > /tmp/business.log 2>&1')
    wait_ready(N8N,'http://localhost:5678/healthz')
    wait_ready(N8N,'http://gateway:8090/health')
    for _ in range(30):
        if webhook('qldapm-ingest',{},False)['status']==403:break
        time.sleep(1)
    else:raise RuntimeError('WEBHOOK_REGISTRATION_TIMEOUT')
    for w in workflows:
        code=w['name'][:4];trigger=next(n for n in w['nodes'] if n['type']=='n8n-nodes-base.webhook');path=trigger['parameters']['path']
        def exercise(record,code=code,path=path):
            fixture('ready');response=webhook(path,PAYLOADS[code]);observed=calls()
            record.update(http=response['status'],response=json.loads(response['body']) if response['body'].startswith('{') else response['body'],calls=observed)
            assert_equal(response['status'],200);assert_equal(len(observed),1)
            call=observed[0]
            if code in ACTIONS:assert_equal(call['payload'].get('action'),ACTIONS[code])
            if code not in {'WF07','WF16'}:assert_equal(call['authorization'],'Bearer synthetic-actor')
            if code=='WF07':assert_equal(call['signature_present'],True);assert_equal(call['payload']['kind'],'daily_brief')
            if code=='WF06':assert_equal(call['payload'],{'decision':'reject','hash':'a'*64})
        check(code+'_published_adapter',exercise)
        def reject(record,path=path,code=code):
            fixture('ready');response=webhook(path,PAYLOADS[code],False)
            record['http']=response['status'];assert_equal(response['status'],403);assert_equal(calls(),[])
        check(code+'_transport_denied',reject)
        if code not in {'WF07','WF16'}:
            def denied(record,path=path,code=code):
                fixture('denied');response=webhook(path,PAYLOADS[code]);record['http']=response['status'];assert_equal(response['status'],403)
            check(code+'_gateway_denied_preserved',denied)
    daily=next(w for w in workflows if w['name'].startswith('WF07'))
    path=next(n['parameters']['path'] for n in daily['nodes'] if n['type']=='n8n-nodes-base.webhook')
    def partial(record):
        fixture('partial');response=webhook(path,{})
        record['http']=response['status'];assert_equal(response['status'],500)
    check('WF07_HTTP200_PARTIAL_is_failure',partial)
    def weekly_schedule(record):
        fixture('ready');response=webhook('clone-weekly-schedule',{})
        record['http']=response['status'];record['calls']=calls()
        assert_equal(response['status'],200)
        assert_equal(record['calls'][0]['payload']['kind'],'weekly_summary')
        assert_equal(record['calls'][0]['signature_present'],True)
    check('WF12_published_scheduled_branch_via_clone_trigger',weekly_schedule)
    def weekly_partial(record):
        fixture('partial');response=webhook('clone-weekly-schedule',{})
        record['http']=response['status'];assert_equal(response['status'],500)
    check('WF12_HTTP200_PARTIAL_is_failure',weekly_partial)
    result['status']='PASS_WITH_FIXTURE_LIMITS' if all(v['outcome']=='PASS' for v in result['tests']) else 'FAILED'
except BaseException as error:
    result.update(status='FAILED',fatal_error=type(error).__name__)
    raise
finally:
    result['completed_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    result['harness_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT/'clone-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for kind,name in reversed(created):
        data=json.loads(docker(*(['network','inspect'] if kind=='network' else ['inspect']),name).stdout)[0]
        labels=data['Labels'] if kind=='network' else data['Config']['Labels']
        assert labels.get('org.qldapm.business')==IDENT and name.startswith(PREFIX)
        docker('network','rm',name) if kind=='network' else docker('rm','-f',name)
print(json.dumps({'status':result['status'],'tests':len(result['tests']),'failed':[t['name'] for t in result['tests'] if t['outcome']!='PASS']}))

"""Post-publish positive Project6 paths; normal worker delivers all observer events."""
import datetime
import json
import subprocess
import time
import uuid
from pathlib import Path

OUT=Path(__file__).parent


def docker(args,data):
    p=subprocess.run(['docker',*args],input=data,text=True,capture_output=True,timeout=150)
    assert p.returncode==0,'MAIN_BUSINESS_COMMAND_FAILED: '+p.stderr[-300:]
    return json.loads(p.stdout)


def py(code):return docker(['exec','-i','qldapm-ai-gateway-1','python','-'],code)


context=py("""import json,uuid,datetime
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service
r=Path('/state');store=Store(r);config=json.load(open(r/'config.json'));s=scoped_service(Service(store,config,'/workspaces'),6)
with store.connect() as d:
 assert d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]=='OFF'
 assert not d.execute("SELECT 1 FROM ai_queue WHERE state IN ('queued','executing')").fetchone()
native,who=s.native_actor(20);assert who['role']=='PM'
marker='P6-FUNCTIONAL-'+uuid.uuid4().hex[:12];past=(datetime.date.today()-datetime.timedelta(days=7)).isoformat()
item=native.call('/api/v3/work_packages','POST',{'subject':'[Bug] '+marker,config['source_field']:marker,
 'description':{'raw':'Controlled noncoding Project6 bug/risk qualification. Reproduction: overdue fixture remains open. Expected: risk report cites this source. Actual test evidence is separate; no QA pass or approval claim.'},
 'startDate':past,'dueDate':past,'_links':{'project':{'href':'/api/v3/projects/6'},'type':{'href':'/api/v3/types/1'}}})
assert item['dueDate']<datetime.date.today().isoformat()
secret=json.load(open(r/'webhook_secret.json'))
print(json.dumps({'token':store.issue_token(20,'PM',store.credential(20),ttl=900),
 'webhook':secret.get('webhook_token') or secret.get('secret'),'native_id':item['id'],'native_version':item['lockVersion'],
 'subject':item['subject'],'due_date':item['dueDate']}))
""")

fetch="const p=JSON.parse(require('fs').readFileSync(0,'utf8'));fetch('http://localhost:5678/webhook/'+p.path,{method:'POST',headers:p.headers,body:JSON.stringify(p.body),signal:AbortSignal.timeout(115000)}).then(async r=>console.log(JSON.stringify({status:r.status,body:await r.text()}))).catch(()=>process.exit(1))"
paths={'WF01':'qldapm-ingest','WF08':'qldapm-sprint-risk','WF09':'qldapm-bug-lifecycle','WF10':'qldapm-task-orchestration'}


def request(workflow,payload):
    data={'path':paths[workflow],'headers':{'Content-Type':'application/json','X-QLDAPM-Webhook-Token':context['webhook'],
        'Authorization':'Bearer '+context['token']},'body':payload}
    response=docker(['exec','-i','qldapm-n8n-main','node','-e',fetch],json.dumps(data))
    assert response['status']==200,'HUMAN_WORKFLOW_HTTP_'+str(response['status'])
    body=json.loads(response['body'])
    assert body.get('automation',{}).get('event_id'),'COMMAND_OBSERVER_NOT_RECORDED'
    return body


result={'status':'RUNNING','environment':'MAIN','actor':20,'project':6,
    'route':'authenticated n8n human hooks → same Gateway business commands used by Command Center → normal durable outbox → n8n machine observations',
    'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'fixture':{k:v for k,v in context.items() if k not in {'token','webhook'}},'native_business_creates':1,
    'native_status_transitions':0,'native_deletes':0,'coding_tasks_created':0,'provider_calls':0,'browser_uat':'NOT_PERFORMED'}
output=OUT/'final-completion-main-business-readback.json'
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')

risk=request('WF08',{'project_id':6,'as_of_date':datetime.date.today().isoformat()})
assert any(item['id']==context['native_id'] for item in risk['result']['report']['overdue'])
bug=request('WF09',{'project_id':6,'operation':'triage','id':context['native_id']})
assert bug['result']['native_id']==context['native_id'] and bug['result']['native_mutations'] is False
payload={'project_id':6,'operation':'draft','request_id':str(uuid.uuid4()),
    'requirements':[{'id':'R1','text':'Project6 qualification must preserve exact source identity and approval boundaries.'}],
    'nodes':[{'key':'epic','kind':'Epic','subject':'Functional qualification draft','requirement_ids':['R1']},
             {'key':'task','kind':'Task','parent':'epic','subject':'Source-bound acceptance draft','requirement_ids':['R1']}]}
wbs=request('WF10',payload);repeat=request('WF10',payload);assert wbs==repeat
file=request('WF01',{'project_id':6,'source_key':'project6-integration-qualification','operation':'ingest','request_id':str(uuid.uuid4())})
responses={'WF08':risk,'WF09':bug,'WF10':wbs,'WF01':file}
events={wf:body['automation']['event_id'] for wf,body in responses.items()}
result['commands']={wf:{'correlation_id':body['correlation_id'],'event_id':events[wf],
    'result':body['result']} for wf,body in responses.items()}
for _ in range(36):
    observed=py("""import json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
identifiers="""+repr(list(events.values()))+"""
rows=[]
for identifier in identifiers:
 r=d.execute('SELECT o.id,o.workflow,o.state,o.error,r.execution_id,r.document FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id WHERE o.id=?',(identifier,)).fetchone()
 rows.append({'event_id':r['id'],'workflow':r['workflow'],'state':r['state'],'error':r['error'],'execution_id':r['execution_id'],
 'business':json.loads(r['document'])['business_result'] if r['document'] else None})
print(json.dumps(rows))
""")
    if all(row['state']=='ACKED' and row['business']['state']=='COMMAND_RESULT_VERIFIED' for row in observed):break
    time.sleep(5)
else:
    result.update(status='INCOMPLETE',events=observed);output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    raise SystemExit('MAIN_COMMAND_OBSERVER_READBACK_INCOMPLETE')
result['events']=observed
verification=py("""import json
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service
from gateway.native_wbs import load
r=Path('/state');s=scoped_service(Service(Store(r),json.load(open(r/'config.json')),'/workspaces'),6);n,w=s.native_actor(20)
native=n.package("""+repr(context['native_id'])+""")
report=s.store.report(20,6,"""+repr(risk['result']['report_id'])+""")
draft=load(s,"""+repr(wbs['result']['id'])+""")
assert report['sha256']=="""+repr(risk['result']['report_sha256'])+"""
assert draft['hash']=="""+repr(wbs['result']['hash'])+""" and draft['project_id']==6
assert native['lockVersion']=="""+repr(context['native_version'])+"""
with s.store.connect() as d:
 notifications=d.execute('SELECT count(*) FROM notification_delivery WHERE source_id=?',(report['id'],)).fetchone()[0] if d.execute("SELECT 1 FROM sqlite_master WHERE name='notification_delivery'").fetchone() else None
print(json.dumps({'native_id':native['id'],'native_version':native['lockVersion'],'report_id':report['id'],'report_sha256':report['sha256'],
 'wbs_id':draft['id'],'wbs_hash':draft['hash'],'native_unchanged_after_triage':True,'report_notification_rows':notifications}))
""")
result['business_readback']=verification
result.update(status='MAIN_P6_RISK_BUG_WBS_FILE_COMMANDS_AND_N8N_RECEIPTS_VERIFIED',
    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    limits=['No browser interaction claim; same Gateway business backend was exercised.',
            'Bug triage is read-only. MAIN Bug transition and WF05/WF06 approval remain PENDING_OWNER_ACTION.',
            'WBS draft/get/replay does not approve or materialize a Native hierarchy.'])
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['status'],'native_id':context['native_id'],'execution_ids':{r['workflow']:r['execution_id'] for r in observed}}))

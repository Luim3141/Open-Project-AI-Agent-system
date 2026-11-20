"""Read-only restart invariants; credentials/row documents never enter public evidence."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
OUT=Path(__file__).parent
label=sys.argv[1]
assert label.replace('-','').isalnum()
code=r'''
import hashlib,json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row;d.execute('BEGIN')
tables={r[0] for r in d.execute("SELECT name FROM sqlite_master WHERE type='table'")}
names=['engineering_control','engineering_owner_revision','ai_queue','ai_runs','engineering_checkpoints','engineering_unit_definitions','engineering_plans','delegated_control','gemini_usage','gemini_blocks','gemini_recovery','gemini_call_receipts']
pins={}
for name in names:
 if name not in tables:continue
 rows=[dict(r) for r in d.execute('SELECT * FROM '+name)]
 data=sorted(json.dumps(r,sort_keys=True,ensure_ascii=False) for r in rows)
 pins[name]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(data).encode()).hexdigest()}
unknown=[dict(r) for r in d.execute("SELECT * FROM requests WHERE state NOT IN ('done','rejected')")]
pins['unknown_requests']={'count':len(unknown),'sha256':hashlib.sha256(json.dumps(sorted(json.dumps(r,sort_keys=True) for r in unknown)).encode()).hexdigest()}
mode=dict(d.execute('SELECT * FROM engineering_control WHERE project=6').fetchone())
revision=d.execute('SELECT revision FROM engineering_owner_revision WHERE project=6').fetchone()[0]
delegation=d.execute('SELECT enabled FROM delegated_control WHERE project=6').fetchone()[0]
active=d.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]
outbox={r[0]:r[1] for r in d.execute('SELECT state,count(*) FROM n8n_lifecycle_outbox GROUP BY state')}
runs=[{'id':r[0],'state':r[1],'result_status':json.loads(r[2] or '{}').get('status')} for r in d.execute("SELECT q.id,q.state,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id IN ('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6','301dbdd8-6f6f-4df4-b6c6-b5ca3f073795')")]
print(json.dumps({'pins':pins,'mode':mode,'revision':revision,'delegation':bool(delegation),'queue_active':active,'outbox':outbox,'protected_runs':runs}))
'''
state=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=30))
assert state['mode']['mode']=='PAUSED' and state['queue_active']==0 and state['delegation'] is False
assert len(state['protected_runs'])==2 and all(r['result_status']=='succeeded' and r['state']=='finished' for r in state['protected_runs'])
state['containers']={}
for name in subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines():
 info=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
 state['containers'][name]={'id':info['Id'],'image':info['Image'],'started_at':info['State']['StartedAt'],'restart':info['HostConfig']['RestartPolicy'],'health':info['State'].get('Health',{}).get('Status'),'project':info['Config'].get('Labels',{}).get('com.docker.compose.project'),'mounts':[{'type':m['Type'],'source':m['Source'],'destination':m['Destination']} for m in info['Mounts']]}
meta="import json;v=json.load(open('/state/n8n-workflow-status.json'));print(json.dumps([{k:w.get(k) for k in ['code','id','active','published_version_id','definition_sha256']} for w in v['workflows']]))"
state['workflow_pins']=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',meta]))
state['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
path=OUT/(label+'.json');assert not path.exists(),path
path.write_text(json.dumps(state,indent=2),encoding='utf-8')
if label!='baseline':
 baseline=json.loads((OUT/'baseline.json').read_text())
 assert state['pins']==baseline['pins'],'DURABLE_STATE_CHANGED: compare captured evidence before any action'
 assert state['workflow_pins']==baseline['workflow_pins'],'PUBLISHED_WORKFLOWS_CHANGED'
 assert all(state['containers'][k]['id']==v['id'] and state['containers'][k]['started_at']==v['started_at'] for k,v in baseline['containers'].items() if not k.startswith('qldapm')),'UNRELATED_DOCKER_WORKLOAD_CHANGED'
print(json.dumps({'label':label,'mode':state['mode']['mode'],'revision':state['revision'],'queue':state['queue_active'],'provider_receipts':state['pins']['gemini_call_receipts']['count'],'unknown_writes':state['pins']['unknown_requests']['count'],'workflow_pins':len(state['workflow_pins']),'status':'BASELINE' if label=='baseline' else 'INVARIANTS_PASS'}))

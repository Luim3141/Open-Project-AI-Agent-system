"""Bounded real-clone automation/restart qualification. Never starts a Main writer or copies provider keys."""
import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from automation.comment_sync_qualification import run
from automation.main_native_clone import main_native_clone
from automation.main_operations import private_path
from automation.deploy_real_n8n_workflows import build_workflows, WEBHOOK_CRED_ID
from gateway.automation import signing_key

N8N_STATE=r"""const {DatabaseSync}=require('node:sqlite'),fs=require('fs');const db=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
console.log(JSON.stringify({workflows:db.prepare('SELECT id,name,active,activeVersionId FROM workflow_entity').all(),executions:db.prepare('SELECT id,workflowId,mode,status,finished,startedAt,stoppedAt FROM execution_entity ORDER BY id').all(),bytes:fs.statSync('/home/node/.n8n/database.sqlite').size,integrity:db.prepare('PRAGMA quick_check').get()}));db.close();"""
PRELUDE="""import json,time,uuid,sqlite3,os,httpx
from pathlib import Path
from gateway.native import Native
root=Path('/state');fixture=Path('/qualification');c=json.load(open(root/'config.json'));keys=json.load(open(root/'credentials.json'))
assert os.environ.get('QLDAPM_AUTOMATION_CLONE')==json.load(open(fixture/'clone.json'))['id'] and c['project_id']==5
n=Native('http://web:8080',keys['18'],5)
def q(sql,params=()):
 with sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True) as d:
  d.row_factory=sqlite3.Row;return [dict(x) for x in d.execute(sql,params)]
def cmd(action,args={},actor='18',key=None):
 tokens=json.load(open(fixture/'bearers.json'))
 with httpx.Client(timeout=115,trust_env=False) as client:
  response=client.post('http://qldapm-ai-gateway-1:8090/api/v1/commands',headers={'Authorization':'Bearer '+tokens[actor]},json={'action':action,'arguments':args,'idempotency_key':key or str(uuid.uuid4())})
  if response.status_code!=200:raise RuntimeError('CLONE_COMMAND_'+str(response.status_code)+':'+response.text[:180])
  return response.json()['result']
"""


SNAPSHOT = r"""w=n.package(FIXTURE_ID)
jobs=q('select id,state,attempts,error,lease_until from knowledge_sync where native_id=?',(FIXTURE_ID,))
with sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True) as d:
 d.row_factory=sqlite3.Row
 docs=[dict(x) for x in d.execute("select source_id,source_hash,content,metadata from knowledge_documents where json_extract(metadata,'$.native_id')=?",(FIXTURE_ID,))]
 fts=d.execute('select count(*) from knowledge_fts where source_hash in (select source_hash from knowledge_documents where json_extract(metadata,?)=?)',('$.native_id',FIXTURE_ID)).fetchone()[0]
print(json.dumps(dict(version=w['lockVersion'],jobs=jobs,documents=docs,fts=fts,scanner=q('select generation,document from native_index_scans where actor=18 and project=5'))))"""


def qualify(output,image,baseline):
    output=private_path(output);output.mkdir(exist_ok=False)
    start=time.time();trace=str(uuid.uuid4());image=json.loads(run('image','inspect',image))[0]['Id']
    with main_native_clone(output/'native') as clone:
        label='org.qldapm.automation-clone='+clone['id'];prefix='qldapm-automation-'+clone['id']
        gateway,n8n,vector,proxy=[prefix+'-'+x for x in ['gateway','n8n','vector','proxy']]
        network=prefix+'-embedding';created=[];paused=False
        state=output/'state';fixture=output/'fixture';state.mkdir();fixture.mkdir();(output/'n8n-data').mkdir()
        baseline=private_path(baseline)
        with sqlite3.connect(baseline.as_uri()+'?mode=ro&immutable=1',uri=True) as source,sqlite3.connect(state/'knowledge.sqlite') as target:
            assert source.execute('pragma quick_check').fetchone()[0]=='ok';source.backup(target)
        config=json.loads(run('exec','qldapm-ai-gateway-1','python','-c',"import json;c=json.load(open('/state/config.json'));print(json.dumps({k:c[k] for k in ['project_id','gateway_mode','users','source_field','type_ids','status_ids']}))"))
        config.update(openproject_url='http://web:8080',hosts=['qldapm-ai-gateway-1:8090'],native_incremental_sync={'enabled':True,'actor':18})
        (state/'config.json').write_text(json.dumps(config));(fixture/'clone.json').write_text(json.dumps(clone))
        ruby="require 'json';puts JSON.generate("+json.dumps([int(a) for a in config['users']])+".to_h{|id|[id,Token::API.create_and_return_value(User.find(id))]})"
        keys=json.loads(run('exec','--user','app',clone['web'],'bundle','exec','rails','runner',ruby).decode().splitlines()[-1]);(state/'credentials.json').write_text(json.dumps(keys))
        machine=secrets.token_hex(32);webhook=secrets.token_hex(32);(state/'automation.key').write_text(machine)
        creds=[{'id':'qldapmMachineStatus','name':'Clone machine','type':'httpHeaderAuth','data':{'name':'X-QLDAPM-Machine-Key','value':machine}},
            {'id':'qldapmCommandHmac','name':'Clone HMAC','type':'crypto','data':{'hmacSecret':signing_key(machine)}},
            {'id':WEBHOOK_CRED_ID,'name':'Clone webhook','type':'httpHeaderAuth','data':{'name':'X-QLDAPM-Webhook-Token','value':webhook}}]
        (fixture/'credentials.json').write_text(json.dumps(creds));(fixture/'dependency-mode').write_text('online')
        for name in ['automation_dependency_proxy.py','automation_schedule_setup.js','automation_provider_and_trace_probe.js']:shutil.copy2(Path(__file__).parents[1]/'tests'/name,fixture/name)
        definitions=build_workflows();specs=[]
        for code in ['WF07','WF12','WF16','WF04']:
            spec=copy.deepcopy(definitions[code]);spec['settings'].update(saveDataSuccessExecution='all',saveDataErrorExecution='all',saveExecutionProgress=True)
            for node in spec['nodes']:
                if node['type']=='n8n-nodes-base.scheduleTrigger':node['parameters']['rule']['interval'][0]['expression']='0 * * * * *'
            specs.append(spec)
        for variant in ['old','candidate']:
            spec=copy.deepcopy(specs[0]);spec['name']='Daily Partial Contract '+variant
            trigger=next(n for n in spec['nodes'] if n['type']=='n8n-nodes-base.webhook');trigger['parameters']['path']='daily-partial-'+variant
            report=next(n for n in spec['nodes'] if n['id']=='report');report['parameters']['url']='http://fixture-embedding:11434/partial-daily'
            schedules=[n for n in spec['nodes'] if n['type']=='n8n-nodes-base.scheduleTrigger']
            for node in schedules:spec['connections'].pop(node['name'],None);spec['nodes'].remove(node)
            if variant=='old':
                final=next(n for n in spec['nodes'] if n['id']=='daily_business_result');spec['nodes'].remove(final);spec['connections'].pop(report['name'],None)
            specs.append(spec)
        (fixture/'workflows.json').write_text(json.dumps(specs));(fixture/'owner.json').write_text(json.dumps({'email':'automation-clone@qldapm.local','firstName':'Clone','lastName':'Operator','password':'Aa9!'+secrets.token_urlsafe(24)}))
        (fixture/'n8n.env').write_text('N8N_ENCRYPTION_KEY='+secrets.token_hex(32)+'\nN8N_SECURE_COOKIE=false\nGENERIC_TIMEZONE=Asia/Bangkok\nN8N_DIAGNOSTICS_ENABLED=false\n')
        def py(code):
            compile(PRELUDE+code,'clone-probe','exec')
            return json.loads(run('exec',gateway,'python','-c',PRELUDE+code).decode().splitlines()[-1])
        def wait(check,seconds=200):
            until=time.monotonic()+seconds
            while time.monotonic()<until:
                value=check()
                if value:return value
                time.sleep(2)
            raise AssertionError('CLONE_CONDITION_TIMEOUT')
        evidence={'trace_id':trace,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stages':[],'faults':[],'metrics':[]}
        def record(kind,data):
            row={'kind':kind,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),**data};evidence['stages'].append(row)
            (output/'progress.json').write_text(json.dumps(evidence,indent=2));print(kind,flush=True);return row
        def metrics(phase):
            rows=[json.loads(x) for x in run('stats','--no-stream','--format','{{json .}}',gateway,n8n,vector).decode().splitlines()]
            evidence['metrics'].append({'phase':phase,'at':time.time(),'containers':rows,'n8n':json.loads(run('exec',n8n,'node','-e',N8N_STATE))})
        try:
            run('network','create','--label',label,network)
            for name,container_image,args in [
                (vector,json.loads(run('inspect','qldapm-qdrant'))[0]['Image'],['--network-alias','qldapm-qdrant','--tmpfs','/qdrant/storage:size=256m,mode=1777','--tmpfs','/qdrant/snapshots:size=64m,mode=1777','--memory','384m','-e','QDRANT__TELEMETRY_DISABLED=true']),
                (proxy,image,['--network-alias','fixture-embedding','--memory','128m','--mount',f'type=bind,source={fixture},target=/qualification'])]:
                cmd=['run','-d','--pull','never','--name',name,'--label',label,'--network',clone['network'],'--read-only','--tmpfs','/tmp:size=64m,mode=1777','--cap-drop','ALL','--security-opt','no-new-privileges:true',*args,container_image]
                if name==proxy:cmd+=['python','/qualification/automation_dependency_proxy.py']
                run(*cmd);created.append(name)
            run('network','connect',network,proxy)
            proxy_ip=json.loads(run('inspect',proxy))[0]['NetworkSettings']['Networks'][clone['network']]['IPAddress']
            run('run','-d','--pull','never','--name',gateway,'--label',label,'--network',clone['network'],'--network-alias','qldapm-ai-gateway-1',
                '--add-host','host.docker.internal:'+proxy_ip,'--read-only','--tmpfs','/tmp:size=128m,mode=1777','--memory','384m','--cpus','1','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges:true',
                '-e','PYTHONPATH=/app','-e','QLDAPM_AI_RUNTIME=/state','-e','QLDAPM_AUTOMATION_CLONE='+clone['id'],'-e','QLDAPM_QDRANT_URL=http://qldapm-qdrant:6333','-e','QLDAPM_OLLAMA_URL=http://host.docker.internal:11434',
                '--mount',f'type=bind,source={state},target=/state','--mount',f'type=bind,source={fixture},target=/qualification',image,'python','-m','uvicorn','gateway.app:app','--host','0.0.0.0','--port','8090');created.append(gateway)
            wait(lambda:json.loads(run('inspect',gateway))[0]['State']['Status']=='running',30)
            for _ in range(45):
                try:
                    if py("print(json.dumps(httpx.get('http://qldapm-ai-gateway-1:8090/health',trust_env=False).json()))").get('status')=='ok':break
                except RuntimeError:time.sleep(1)
            else:raise RuntimeError('CLONE_GATEWAY_NOT_READY')
            py("from gateway.store import Store;s=Store(root);tokens={a:s.issue_token(int(a),role,keys[a]) for a,role in c['users'].items()};(fixture/'bearers.json').write_text(json.dumps(tokens));print(json.dumps({'actors':len(tokens)}))")
            py("from gateway.vector_client import VectorClient;v=VectorClient();assert v.ensure_collection();v.close();print('{}')")
            run('run','-d','--pull','never','--name',n8n,'--label',label,'--network',clone['network'],'--read-only','--tmpfs','/tmp:size=128m,mode=1777','--tmpfs','/home/node/.cache:size=64m,mode=1777',
                '--memory','1536m','--cpus','1.5','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges:true','--env-file',str(fixture/'n8n.env'),
                '--mount',f'type=bind,source={output/"n8n-data"},target=/home/node/.n8n','--mount',f'type=bind,source={fixture},target=/qualification',json.loads(run('inspect','qldapm-n8n-main'))[0]['Image']);created.append(n8n)
            run('exec',n8n,'node','/qualification/automation_schedule_setup.js',timeout=240)
            record('SCHEDULES_PUBLISHED',{'workflows':json.loads((fixture/'published.json').read_text())});metrics('initial')
            # Reproduce HTTP-200/PARTIAL false success, then prove the same response fails with the candidate boundary.
            for variant in ['old','candidate']:
                js="(async()=>{const r=await fetch('http://localhost:5678/webhook/daily-partial-"+variant+"',{method:'POST',headers:{'content-type':'application/json','X-QLDAPM-Webhook-Token':"+json.dumps(webhook)+"},body:'{}'});console.log(JSON.stringify({http:r.status,body:await r.text()}));})()"
                response=json.loads(run('exec',n8n,'node','-e',js));record('DAILY_PARTIAL_'+variant.upper(),response)
                assert response['http']==(200 if variant=='old' else 500),response
            nonce='automationnonce'+uuid.uuid4().hex
            created_wp=py("w=n.call('/api/v3/work_packages','POST',{'subject':'Automation stability isolated fixture',c['source_field']:'AUTOMATION-"+trace+"','description':{'raw':'"+nonce+"v1'},'_links':{'project':{'href':'/api/v3/projects/5'},'type':{'href':'/api/v3/types/1'}}});print(json.dumps({'id':w['id'],'version':w['lockVersion']}))")
            identifier=created_wp['id'];assert identifier>376
            def snapshot():
                return py(SNAPSHOT.replace('FIXTURE_ID',str(identifier)))
            def synced(marker,seconds=210):
                def check():
                    s=snapshot()
                    return s if len(s['documents'])==2 and s['jobs'] and all(j['state']=='verified' for j in s['jobs']) and all(marker in d['content'] for d in s['documents']) else None
                s=wait(check,seconds);return record('AUTOMATIC_INDEX_'+marker[-2:],s)
            def update(marker):
                return py("w=n.package("+str(identifier)+");r=n.call('/api/v3/work_packages/"+str(identifier)+"','PATCH',{'lockVersion':w['lockVersion'],'description':{'raw':'"+marker+"'}});print(json.dumps({'id':r['id'],'version':r['lockVersion']}))")
            synced(nonce+'v1');changed_at=time.time();update(nonce+'v2');stage=synced(nonce+'v2');stage['index_latency_seconds']=time.time()-changed_at
            retrieval=py("print(json.dumps(cmd('knowledge_search',{'query':'"+nonce+"v2','native_ids': ["+str(identifier)+"]})))")
            assert retrieval['items'] and all(nonce+'v1' not in h['snippet'] for h in retrieval['items']);record('LATEST_RAG',retrieval)
            supervisor=py("print(json.dumps(cmd('start_ai_run',{'engine':'supervisor','prompt':'Phân tích tiến độ công việc #"+str(identifier)+", chỉ đọc, không tạo đề xuất.','allow_routine_writes':False},key='"+trace+"')))" )
            run_id=supervisor['id'];final=wait(lambda:(lambda x:x if x['state']=='done' else None)(py("print(json.dumps(cmd('get_ai_run',{'id':'"+run_id+"'})))")),120)
            record('LOCAL_SUPERVISOR_FINAL',{'run_id':run_id,'final':final,'provider':'NOT_CONFIGURED_NO_PRODUCTION_SECRET_COPIED'})
            (fixture/'trace-target.json').write_text(json.dumps({'run_id':run_id,'parent_trace_id':trace,'native_id':identifier}))
            provider_spec=build_workflows()['WF03'];provider_spec['settings'].update(saveDataErrorExecution='all',saveDataSuccessExecution='all')
            (fixture/'WF03-probe.json').write_text(json.dumps(provider_spec))
            run('exec',n8n,'node','/qualification/automation_provider_and_trace_probe.js',timeout=160)
            record('PROVIDER_AND_TRACE_BOUNDARY',json.loads((fixture/'provider-trace-result.json').read_text()))
            activity=py("r=n.call('/api/v3/work_packages/"+str(identifier)+"/activities','POST',{'comment':{'raw':'"+nonce+"comment'}});print(json.dumps({'id':r['id']}))")
            s=wait(lambda:(lambda x:x if any(nonce+'comment' in d['content'] for d in x['documents']) and all(j['state']=='verified' for j in x['jobs']) else None)(snapshot()))
            denied=py("print(json.dumps(cmd('knowledge_search',{'query':'"+nonce+"comment','native_ids': ["+str(identifier)+"]},actor='19')))" )
            record('COMMENT_READ_AS_PM',{'items':denied['items']})
            # A related authorized canonical hit is valid; Owner snapshot/content must never be returned.
            assert all(h['source_id']!=f'actor:18:wp:{identifier}' and nonce+'comment' not in h['snippet'] for h in denied['items'])
            record('COMMENT_ACTOR_BOUND',{'activity':activity,'snapshot':s,'authorized_pm_hits':len(denied['items'])})
            # Natural Ollama failure: disable only this clone proxy, leave the actual Main daemon untouched.
            for dependency in ['ollama','qdrant']:
                began=time.time()
                if dependency=='ollama':(fixture/'dependency-mode').write_text('offline')
                else:run('pause',vector);paused=True
                update(nonce+dependency)
                fault=wait(lambda:(lambda x:x if x['jobs'] and any(j['state'] in {'retry','dlq'} for j in x['jobs']) else None)(snapshot()),200)
                assert any(j['error'] for j in fault['jobs']);record('FAULT_'+dependency.upper(),fault)
                if dependency=='ollama':(fixture/'dependency-mode').write_text('online')
                else:run('unpause',vector);paused=False
                recovered=synced(nonce+dependency);evidence['faults'].append({'dependency':dependency,'seconds':time.time()-began,'job_states':recovered['jobs']})
            # Keep a real claimed job running in an embedding call, then kill/restart only the clone Gateway.
            (fixture/'dependency-mode').write_text('hold');update(nonce+'restart')
            running=wait(lambda:(lambda x:x if any(j['state']=='running' for j in x['jobs']) else None)(snapshot()),180)
            record('PRE_RESTART_CLAIM',running);lease=max(j['lease_until'] or 0 for j in running['jobs'])
            run('restart','--time','1',gateway);(fixture/'dependency-mode').write_text('online')
            # Independent n8n restart during the real five-minute Gateway lease expiry.
            before_n8n=json.loads(run('exec',n8n,'node','-e',N8N_STATE));run('restart','--time','10',n8n)
            time.sleep(5);after_n8n=wait(lambda:json.loads(run('exec',n8n,'node','-e',N8N_STATE)),90)
            assert before_n8n['workflows']==after_n8n['workflows'];assert len(after_n8n['executions'])>=len(before_n8n['executions'])
            record('N8N_RESTART_PRESERVED',{'before':before_n8n,'after':after_n8n});metrics('restarting')
            def query(_):
                began=time.monotonic();result=py("print(json.dumps(cmd('get_work_package',{'id':"+str(identifier)+"})))")
                return {'seconds':time.monotonic()-began,'native_id':result['id']}
            with ThreadPoolExecutor(max_workers=3) as pool:reads=list(pool.map(query,range(12)))
            record('BOUNDED_READS',{'concurrency':3,'runs':reads})
            remaining=max(0,lease-time.time());print('Waiting for actual persisted Gateway lease expiry',round(remaining),flush=True)
            recovered=synced(nonce+'restart',seconds=int(remaining)+150);record('GATEWAY_LEASE_RECOVERED',{'lease_until':lease,'snapshot':recovered})
            metrics('final')
            final_n8n=json.loads(run('exec',n8n,'node','-e',N8N_STATE));published=json.loads((fixture/'published.json').read_text())
            schedules=[]
            for name in ['WF07:','WF12:','WF16:']:
                wid=next(w['id'] for w in published if w['name'].startswith(name));runs=[x for x in final_n8n['executions'] if x['workflowId']==wid and x['mode']=='trigger']
                assert len(runs)>=3,(name,runs);assert all(x['status']=='success' and x['finished'] for x in runs),(name,runs)
                assert len({x['startedAt'][:16] for x in runs})==len(runs),('DUPLICATE_MINUTE',name)
                schedules.append({'workflow':name,'executions':runs})
            receipts=py("print(json.dumps({'automation':q('select id,request_key,receipt from automation_runs'),'monitor':q(\"select id,target,outcome,version from audit where action='health_monitor'\"),'proposals':q('select count(*) n from proposals')[0]['n'],'models':q('select count(*) n from gemini_usage')[0]['n']}))")
            assert len(receipts['automation'])==2 and receipts['proposals']==0 and receipts['models']==0
            assert all(json.loads(x['receipt'])['status']=='READY' for x in receipts['automation'])
            points=py("from gateway.vector_client import VectorClient;v=VectorClient();points=[x for x in v.scroll_points('5') if x['payload'].get('work_package_id')=="+str(identifier)+"];ids=[x['id'] for x in points];vectors=v._http.post(v.qdrant_url+'/collections/'+v.collection_name+'/points',json={'ids':ids,'with_vector':True}).json()['result'];assert all(len(x['vector'])==1024 for x in vectors);v.close();print(json.dumps({'ids':ids,'dimensions':1024,'count':len(points),'duplicates':len(ids)-len(set(ids))}))")
            assert points['duplicates']==0 and points['count']==2
            evidence.update(status='CLONE_AUTOMATION_STABILITY_PASS_PROVIDER_BLOCKED',duration_seconds=time.time()-start,gateway_image=image,core_image=clone['images']['web'],source_fixture=identifier,schedules=schedules,receipts=receipts,points=points,read_latencies=reads,main_native_writes=0,
                limitations=['No test Gemini credential supplied; no production provider key copied; continuous real-model gate remains EXTERNAL_DEPENDENCY_BLOCKED','Only this fixture has real vectors; imported baseline is text-only','Minute schedules in clone, actual production cron unchanged','Native writes only in disposable clone; no human QA decisions','Physical reboot and full DR not exercised'])
            (output/'result.json').write_text(json.dumps(evidence,indent=2));return evidence
        finally:
            if paused:run('unpause',vector)
            for name in reversed(created):
                own=json.loads(run('inspect',name))[0]
                if own['Config']['Labels'].get('org.qldapm.automation-clone')!=clone['id']:raise RuntimeError('CLONE_LABEL_MISMATCH')
                (output/(name.rsplit('-',1)[-1]+'-state.json')).write_text(json.dumps(own['State'],indent=2))
                (output/(name.rsplit('-',1)[-1]+'.log')).write_bytes(run('logs',name));run('rm','-f',name)
            own=json.loads(run('network','inspect',network))[0]
            if own['Labels'].get('org.qldapm.automation-clone')!=clone['id']:raise RuntimeError('CLONE_NETWORK_LABEL_MISMATCH')
            run('network','rm',network)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output');p.add_argument('--image',required=True);p.add_argument('--baseline',required=True)
    a=p.parse_args();result=qualify(a.output,a.image,a.baseline);print(json.dumps({'status':result['status'],'duration_seconds':result['duration_seconds']}))

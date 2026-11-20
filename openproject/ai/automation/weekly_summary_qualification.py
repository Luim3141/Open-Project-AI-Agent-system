"""Actual signed n8n schedule -> private Gateway -> real cloned Native reports; no Main writes."""
import argparse
import json
import secrets
import shutil
import hashlib
import sqlite3
import subprocess
import time
from pathlib import Path

from automation.comment_sync_qualification import run
from automation.main_native_clone import main_native_clone
from automation.main_operations import private_path
from automation.deploy_real_n8n_workflows import build_workflows,WEBHOOK_CRED_ID
from gateway.automation import signing_key


def qualify(output,image,business=False,baseline=None):
    output=private_path(output);output.mkdir(exist_ok=False)
    image=json.loads(run('image','inspect',image))[0]['Id']
    n8n_image=json.loads(run('inspect','qldapm-n8n-main'))[0]['Image']
    ui_key=None
    if business:
        (output/'native').mkdir();ui_key=output/'native/ui.key';ui_key.write_text(secrets.token_hex(32))
    with main_native_clone(output/'native',ui_key_path=ui_key) as clone:
        label='org.qldapm.weekly-clone='+clone['id'];prefix='qldapm-weekly-'+clone['id']
        gateway,n8n=prefix+'-gateway',prefix+'-n8n';created=[]
        state=output/'state';state.mkdir();fixture=output/'n8n';fixture.mkdir()
        if baseline is not None:
            baseline=private_path(baseline)
            with sqlite3.connect(baseline.as_uri()+'?mode=ro&immutable=1',uri=True) as source,sqlite3.connect(state/'knowledge.sqlite') as target:
                if source.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('CLONE_BASELINE_INVALID')
                maximum=int(run('exec',clone['database'],'psql','-U','postgres','-d','openproject','-At','-c','SELECT max(id) FROM work_packages'))
                if source.execute("SELECT count(*) FROM knowledge_documents WHERE json_extract(metadata,'$.native_id')>?",(maximum,)).fetchone()[0]:
                    raise ValueError('CLONE_BASELINE_HAS_FOREIGN_FIXTURE')
                source.backup(target)
        if ui_key:shutil.copy2(ui_key,state/'ui.key')
        if business:
            shutil.copy2(Path(__file__).parents[1]/'tests/workflow_business_native_client.js',fixture/'business.js')
            (fixture/'contract.md').write_text('Isolated workflow knowledge contract. Native changes require exact proposal approval.')
            import zipfile
            from pypdf import PdfWriter
            from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
            with zipfile.ZipFile(fixture/'contract.docx','w') as archive:
                archive.writestr('word/document.xml','<document><p><t>Isolated DOCX workflow citation.</t></p></document>')
            pdf=PdfWriter();page=pdf.add_blank_page(width=612,height=792)
            font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):pdf._add_object(font)})})
            stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 72 720 Td (Isolated PDF workflow citation.) Tj ET')
            page[NameObject('/Contents')]=pdf._add_object(stream);pdf.write(fixture/'contract.pdf')
        config=json.loads(run('exec','qldapm-ai-gateway-1','python','-c',
            "import json;from pathlib import Path;c=json.loads(Path('/state/config.json').read_text());assert c['project_id']==5;print(json.dumps({k:c[k] for k in ['project_id','gateway_mode','users','source_field','type_ids','status_ids','bug_task_mapping_sha256']}))"))
        config.update(openproject_url='http://web:8080',hosts=['qldapm-ai-gateway-1:8090'],native_incremental_sync={'enabled':False})
        if business:
            config['file_sources']={key:{'project_id':5,'root':'/qualification','path':'/qualification/'+filename,
                'sha256':hashlib.sha256((fixture/filename).read_bytes()).hexdigest(),'allowed_roles':['AI_SYSTEM_OWNER','PM','BA']}
                for key,filename in [('clone-contract','contract.md'),('clone-pdf','contract.pdf'),('clone-docx','contract.docx')]}
        (state/'config.json').write_text(json.dumps(config))
        ruby="require 'json'; puts JSON.generate("+json.dumps([int(a) for a in config['users']])+".to_h { |id| [id,Token::API.create_and_return_value(User.find(id))] })"
        keys=json.loads(run('exec','--user','app',clone['web'],'bundle','exec','rails','runner',ruby).decode().splitlines()[-1])
        (state/'credentials.json').write_text(json.dumps(keys))
        machine_key=secrets.token_hex(32);(state/'automation.key').write_text(machine_key)
        credentials=[{'id':'qldapmMachineStatus','name':'Clone machine status','type':'httpHeaderAuth',
                      'data':{'name':'X-QLDAPM-Machine-Key','value':machine_key}},
                     {'id':'qldapmCommandHmac','name':'Clone command HMAC','type':'crypto','data':{'hmacSecret':signing_key(machine_key)}},
                     {'id':WEBHOOK_CRED_ID,'name':'Clone webhook','type':'httpHeaderAuth',
                      'data':{'name':'X-QLDAPM-Webhook-Token','value':secrets.token_hex(32)}}]
        (fixture/'credentials.json').write_text(json.dumps(credentials))
        workflow=build_workflows()['WF12']
        workflow['settings'].update(saveDataErrorExecution='all',saveDataSuccessExecution='all',saveExecutionProgress=True)
        schedule=next(n for n in workflow['nodes'] if n['id']=='weekly_schedule')
        schedule['parameters']['rule']['interval'][0]['expression']='0 * * * * *'
        (fixture/'workflow.json').write_text(json.dumps(workflow))
        (fixture/'owner.json').write_text(json.dumps({'email':'weekly-clone@qldapm.local','firstName':'Clone','lastName':'Operator','password':'Aa9!'+secrets.token_urlsafe(24)}))
        (fixture/'n8n.env').write_text('N8N_ENCRYPTION_KEY='+secrets.token_hex(32)+'\nN8N_SECURE_COOKIE=false\nGENERIC_TIMEZONE=Asia/Bangkok\nN8N_DIAGNOSTICS_ENABLED=false\n')
        try:
            if business:
                vector=prefix+'-vector';embedding_network=prefix+'-embedding'
                vector_image=json.loads(run('inspect','qldapm-qdrant'))[0]['Image']
                run('network','create','--label',label,embedding_network)
                run('run','-d','--pull','never','--name',vector,'--label',label,'--network',clone['network'],
                    '--network-alias','qldapm-qdrant','--read-only','--tmpfs','/qdrant/storage:size=256m,mode=1777',
                    '--tmpfs','/qdrant/snapshots:size=64m,mode=1777','--tmpfs','/tmp:size=32m,mode=1777',
                    '--memory','384m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges:true',
                    '-e','QDRANT__TELEMETRY_DISABLED=true',vector_image)
                created.append(vector)
            run('run','-d','--pull','never','--name',gateway,'--label',label,'--network',clone['network'],
                '--network-alias','qldapm-ai-gateway-1','--read-only','--tmpfs','/tmp:size=128m,mode=1777',
                '--memory','768m','--cpus','1','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges:true',
                '-e','PYTHONPATH=/app','-e','QLDAPM_AI_RUNTIME=/state',
                '-e','QLDAPM_QDRANT_URL=http://qldapm-qdrant:6333','-e','QLDAPM_OLLAMA_URL=http://host.docker.internal:11434',
                '--mount',f'type=bind,source={fixture},target=/qualification,readonly',
                '--mount',f'type=bind,source={state},target=/state',
                image,'python','-m','uvicorn','gateway.app:app','--host','0.0.0.0','--port','8090')
            created.append(gateway)
            if business:run('network','connect',embedding_network,gateway)
            run('run','-d','--pull','never','--name',n8n,'--label',label,'--network',clone['network'],
                '--read-only','--tmpfs','/tmp:size=128m,mode=1777','--tmpfs','/home/node/.n8n:size=256m,mode=1777',
                '--tmpfs','/home/node/.cache:size=64m,mode=1777',
                '--memory','1536m','--cpus','1.5','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges:true',
                '--env-file',str(fixture/'n8n.env'),'--mount',f'type=bind,source={fixture},target=/qualification',n8n_image)
            created.append(n8n)
            setup=r"""const fs=require('fs'),{execFileSync}=require('child_process');
const base='http://localhost:5678';let cookie='';
async function call(path,body){let r=await fetch(base+path,{method:body?'POST':'GET',headers:{'content-type':'application/json',cookie},body:body?JSON.stringify(body):undefined});let b=await r.json();if(!r.ok)throw Error('CLONE_API_'+r.status+' '+JSON.stringify(b).slice(0,200));let cs=r.headers.getSetCookie();if(cs.length)cookie=cs.map(s=>s.split(';')[0]).join('; ');return b.data;}
(async()=>{let ready=false;for(let i=0;i<45;i++){try{await call('/rest/settings');ready=true;break;}catch(e){await new Promise(r=>setTimeout(r,1000));}}if(!ready)throw Error('N8N_CLONE_NOT_READY');
const o=JSON.parse(fs.readFileSync('/qualification/owner.json'));await call('/rest/owner/setup',o);await call('/rest/login',{emailOrLdapLoginId:o.email,password:o.password});
execFileSync('n8n',['import:credentials','--input=/qualification/credentials.json'],{stdio:'pipe'});
const w=JSON.parse(fs.readFileSync('/qualification/workflow.json'));let saved=await call('/rest/workflows',w);
await call('/rest/workflows/'+saved.id+'/activate',{versionId:saved.versionId,...(saved.checksum?{expectedChecksum:saved.checksum}:{})});
saved=await call('/rest/workflows/'+saved.id);if(!saved.active)throw Error('SCHEDULE_NOT_ACTIVE');
fs.writeFileSync('/qualification/published.json',JSON.stringify({id:saved.id,versionId:saved.versionId,active:saved.active}));console.log('CLONE_SCHEDULE_ACTIVE');})().catch(e=>{console.error(e.message);process.exit(1)});
"""
            setup_result=subprocess.run(['docker','exec',n8n,'node','-e',setup],capture_output=True,timeout=180)
            (output/'n8n-setup.log').write_bytes(setup_result.stdout+setup_result.stderr)
            if setup_result.returncode:raise RuntimeError('CLONE_N8N_SETUP_FAILED_SEE_PRIVATE_LOG')
            print('Isolated n8n schedule active; waiting for signed weekly receipt',flush=True)
            receipt=None
            for _ in range(180):
                code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);r=d.execute(\"select receipt from automation_runs where json_extract(receipt,'$.kind')='weekly_summary' order by created desc limit 1\").fetchone();print(r[0] if r else 'null')"
                receipt=json.loads(run('exec',gateway,'python','-c',code))
                if receipt and receipt['state']!='RUNNING':break
                time.sleep(1)
            if not receipt or receipt['state']!='COMPLETED' or receipt['status']!='READY':
                raise RuntimeError('CLONE_WEEKLY_BUSINESS_NOT_READY')
            verify="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'reports':d.execute(\"select count(*) from operational_reports where kind='weekly_summary'\").fetchone()[0],'proposals':d.execute('select count(*) from proposals').fetchone()[0],'models':d.execute('select count(*) from gemini_usage').fetchone()[0]}))"
            counts=json.loads(run('exec',gateway,'python','-c',verify))
            if counts!={'reports':receipt['targets'],'proposals':0,'models':0}:raise RuntimeError('CLONE_WEEKLY_COUNTS_MISMATCH')
            execution_code="const s=require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');let d=new s.Database('/home/node/.n8n/database.sqlite',s.OPEN_READONLY);d.all('SELECT id,mode,status,finished,workflowId FROM execution_entity ORDER BY id DESC LIMIT 3',(e,r)=>{if(e)throw e;console.log(JSON.stringify(r));d.close()})"
            executions=json.loads(run('exec',n8n,'node','-e',execution_code))
            if not any(e['status']=='success' and e['finished']==1 and e['mode']=='trigger' for e in executions):
                raise RuntimeError('CLONE_N8N_TERMINAL_SCHEDULE_NOT_VERIFIED')
            # Separate test actors/credentials and decisions are confined to the restored clone.
            token_code="import json;from gateway.store import Store;s=Store('/state');k=json.load(open('/state/credentials.json'));c=json.load(open('/state/config.json'));print(json.dumps({a:s.issue_token(int(a),r,k[a]) for a,r in c['users'].items()}))"
            bearer_tokens=json.loads(run('exec',gateway,'python','-c',token_code))
            for code in ('WF05','WF06'):
                spec=build_workflows()[code]
                spec['settings'].update(saveDataErrorExecution='all',saveDataSuccessExecution='all')
                (fixture/(code+'.json')).write_text(json.dumps(spec))
            (fixture/'bearers.json').write_text(json.dumps(bearer_tokens))
            approval=r"""const fs=require('fs'),crypto=require('crypto');let cookie='';
async function api(path,body){let r=await fetch('http://localhost:5678'+path,{method:body?'POST':'GET',headers:{'content-type':'application/json',cookie},body:body?JSON.stringify(body):undefined});let b=await r.json();if(!r.ok)throw Error('CLONE_N8N_'+r.status);let cs=r.headers.getSetCookie();if(cs.length)cookie=cs.map(s=>s.split(';')[0]).join('; ');return b.data;}
const tokens=JSON.parse(fs.readFileSync('/qualification/bearers.json'));const credentials=JSON.parse(fs.readFileSync('/qualification/credentials.json'));const wh=credentials.find(c=>c.name==='Clone webhook').data.value;
async function gateway(action,args){let r=await fetch('http://qldapm-ai-gateway-1:8090/api/v1/commands',{method:'POST',headers:{'content-type':'application/json',Authorization:'Bearer '+tokens['18']},body:JSON.stringify({action,arguments:args,idempotency_key:crypto.randomUUID()})});let b=await r.json();if(!r.ok)throw Error('CLONE_GATEWAY_'+r.status+':'+JSON.stringify(b).slice(0,200));return b.result;}
async function webhook(path,body,actor='18'){let r=await fetch('http://localhost:5678/webhook/'+path,{method:'POST',headers:{'content-type':'application/json','X-QLDAPM-Webhook-Token':wh,Authorization:'Bearer '+tokens[actor]},body:JSON.stringify(body)});return {status:r.status,body:await r.json()};}
(async()=>{const o=JSON.parse(fs.readFileSync('/qualification/owner.json'));await api('/rest/login',{emailOrLdapLoginId:o.email,password:o.password});let workflows=[];
for(const code of ['WF05','WF06']){let s=await api('/rest/workflows',JSON.parse(fs.readFileSync('/qualification/'+code+'.json')));await api('/rest/workflows/'+s.id+'/activate',{versionId:s.versionId,...(s.checksum?{expectedChecksum:s.checksum}:{})});workflows.push({code,id:s.id});}
const source='CLONE-APPROVAL-'+crypto.randomUUID();let p=await gateway('create_work_package',{source_id:source,subject:'Isolated approved workflow fixture',type_id:1});
let read=await webhook('qldapm-approval',{proposal_id:p.id});if(read.status!==200||read.body.proposal?.id!==p.id)throw Error('WF05_PROPOSAL_READ_FAILED');
let denied=await webhook('qldapm-execute-mutation',{proposal_id:p.id,hash:p.hash,decision:'approve'},'21');if(denied.status!==403)throw Error('NON_MANAGER_DECISION_NOT_DENIED');
let executed=await webhook('qldapm-execute-mutation',{proposal_id:p.id,hash:p.hash,decision:'approve'});if(executed.status!==200||!executed.body.result.id)throw Error('APPROVED_NATIVE_CREATE_FAILED:'+JSON.stringify(executed).slice(0,200));
let wp=await gateway('get_work_package',{id:executed.body.result.id});if(wp.subject!=='Isolated approved workflow fixture')throw Error('NATIVE_READBACK_MISMATCH');
let replay=await webhook('qldapm-execute-mutation',{proposal_id:p.id,hash:p.hash,decision:'approve'});if(replay.status!==409)throw Error('CONSUMED_PROPOSAL_REPLAY_NOT_DENIED');
let rejected=await gateway('create_work_package',{source_id:'CLONE-REJECT-'+crypto.randomUUID(),subject:'Rejected clone proposal',type_id:1});let rejection=await webhook('qldapm-execute-mutation',{proposal_id:rejected.id,hash:rejected.hash,decision:'reject'});if(rejection.status!==200)throw Error('PROPOSAL_REJECTION_FAILED');
fs.writeFileSync('/qualification/approval-result.json',JSON.stringify({workflows,source_id:source,native_id:wp.id,lock_version:wp.lockVersion,proposal_id:p.id,proposal_hash:p.hash,rejected_proposal_id:rejected.id,denied_http:denied.status,replay_http:replay.status,authorization_kind:'SIMULATED_ISOLATED_FIXTURE_NOT_MAIN_HUMAN_APPROVAL'}));console.log('CLONE_APPROVAL_NATIVE_READBACK_PASS');})().catch(e=>{console.error(e.message);process.exit(1)});
"""
            approval_result=subprocess.run(['docker','exec',n8n,'node','-e',approval],capture_output=True,timeout=180)
            (output/'approval.log').write_bytes(approval_result.stdout+approval_result.stderr)
            if approval_result.returncode:raise RuntimeError('CLONE_APPROVAL_WORKFLOW_FAILED_SEE_PRIVATE_LOG')
            approval_evidence=json.loads((fixture/'approval-result.json').read_text())
            count_sql="SELECT count(*) FROM work_packages w JOIN custom_values v ON v.customized_id=w.id AND v.customized_type='WorkPackage' WHERE w.project_id=5 AND v.value='"+approval_evidence['source_id']+"'"
            if int(run('exec',clone['database'],'psql','-U','postgres','-d','openproject','-At','-c',count_sql))!=1:
                raise RuntimeError('APPROVAL_DUPLICATED_NATIVE_WRITE')
            if business:
                for code,spec in build_workflows().items():
                    if code in {'WF05','WF06','WF12'}:continue
                    if code=='WF16':
                        for node in spec['nodes']:
                            if node['type']=='n8n-nodes-base.scheduleTrigger':node['disabled']=True
                    spec['settings'].update(saveDataErrorExecution='all',saveDataSuccessExecution='all')
                    (fixture/(code+'.json')).write_text(json.dumps(spec))
                with (output/'business.log').open('wb') as log:
                    process=subprocess.Popen(['docker','exec',n8n,'node','/qualification/business.js'],stdout=log,stderr=log)
                    deadline=time.monotonic()+900;paused=False
                    try:
                        while process.poll() is None and time.monotonic()<deadline:
                            if (fixture/'qa-fixture-request.json').exists() and not (fixture/'qa-fixture-ready.json').exists():
                                request=json.loads((fixture/'qa-fixture-request.json').read_text());assert request['id']==approval_evidence['native_id']
                                # Explicit disposable test setup, not a claimed Native transition or human approval.
                                ruby="require 'json';w=WorkPackage.find("+str(request['id'])+");raise 'FOREIGN_FIXTURE' unless w.subject=='Isolated approved workflow fixture';w.update_columns(status_id:9,qldapm_gate:w.qldapm_gate.merge('reviewer_id'=>19));puts JSON.generate({id:w.id,status_id:w.status_id,kind:'ISOLATED_QA_STARTING_STATE_ONLY'})"
                                prepared=json.loads(run('exec','--user','app',clone['web'],'bundle','exec','rails','runner',ruby).decode().splitlines()[-1])
                                (fixture/'qa-fixture-ready.json').write_text(json.dumps(prepared))
                            if (fixture/'dependency-fault-request.json').exists() and not (fixture/'dependency-fault-ready.json').exists():
                                own=json.loads(run('inspect',vector))[0];assert own['Config']['Labels']['org.qldapm.weekly-clone']==clone['id']
                                run('pause',vector);paused=True
                                code="import json,uuid;from gateway.store import Store;s=Store('/state');r={};k='isolated-dlq-'+str(uuid.uuid4());\nwith s.connect() as d:\n s._enqueue_knowledge_sync(d,18,k,"+str(approval_evidence['native_id'])+",r);d.execute(\"UPDATE knowledge_sync SET state='dlq',attempts=5,error='ISOLATED_DEPENDENCY_OUTAGE_FIXTURE' WHERE id=?\",(r['knowledge_sync']['id'],))\nprint(json.dumps(r))"
                                job=json.loads(run('exec',gateway,'python','-c',code));job['fixture_kind']='DELIBERATE_CLONE_DLQ_STATE_AND_REAL_PAUSED_QDRANT'
                                (fixture/'dependency-fault-ready.json').write_text(json.dumps(job))
                            if paused and (fixture/'dependency-recover-request.json').exists():
                                run('unpause',vector);paused=False
                                (fixture/'dependency-recovered.json').write_text(json.dumps({'state':'UNPAUSED_CLONE_ONLY'}))
                            if (fixture/'acl-revoke-request.json').exists() and not (fixture/'acl-revoked.json').exists():
                                ruby="require 'json';m=Member.where(project_id:5,user_id:20);raise 'CLONE_MEMBERSHIP_REQUIRED' unless m.count==1;m.first.destroy!;puts JSON.generate({actor:20,project_id:5,memberships:Member.where(project_id:5,user_id:20).count,kind:'ISOLATED_REVOCATION_FIXTURE'})"
                                revoked=json.loads(run('exec','--user','app',clone['web'],'bundle','exec','rails','runner',ruby).decode().splitlines()[-1])
                                (fixture/'acl-revoked.json').write_text(json.dumps(revoked))
                            if (fixture/'quiescent-request.json').exists() and not (fixture/'quiescent-ready.json').exists():
                                code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'unfinished_cache_jobs':d.execute(\"select count(*) from knowledge_sync where state!='verified'\").fetchone()[0]}))"
                                quiet=json.loads(run('exec',gateway,'python','-c',code))
                                if quiet['unfinished_cache_jobs']==0:(fixture/'quiescent-ready.json').write_text(json.dumps(quiet))
                            time.sleep(.5)
                        if process.poll() is None:
                            process.kill();process.wait();raise RuntimeError('CLONE_BUSINESS_TIMEOUT')
                    finally:
                        if process.poll() is None:process.kill();process.wait()
                        if paused:run('unpause',vector)
                if process.returncode:raise RuntimeError('CLONE_WORKFLOW_BUSINESS_FAILED_SEE_PRIVATE_LOG')
                business_rows=json.loads((fixture/'business-result.json').read_text())
                required={f'WF{i:02}' for i in range(1,17)}-{'WF05','WF06'}|{'ACL_REVOKE','DELETE_TOMBSTONE'}
                assert {r['code'] for r in business_rows}==required and all(r['state']=='PASS' for r in business_rows)
                assert len(next(r for r in business_rows if r['code']=='WF01')['evidence']['formats'])==2
                executions=json.loads(run('exec',n8n,'node','-e',execution_code.replace('LIMIT 3','LIMIT 300')))
            evidence={'status':'CLONE_N8N_WEEKLY_BUSINESS_PASS','receipt':receipt,'counts':counts,'executions':executions,
                'gateway_image':image,'core_image':clone['images']['web'],'main_business_writes':0,
                'approval_fixture':approval_evidence,
                'schedule_fixture':'Every minute in clone; production Friday17:00 Asia/Bangkok is statically checked separately'}
            if business:
                evidence.update(status='CLONE_N8N_NATIVE_RAG_QA_RECOVERY_BUSINESS_PASS',business=business_rows,
                    fixture_limits=['WF03 deterministic Native and WF04 local Supervisor; live Gemini is separately tested on MAIN',
                        'QA starting IN TESTING state and reviewer seeded only in disposable clone; all actual reviews and controlled transition use authenticated workflows',
                        'WF14 DLQ state deliberately injected; real Qdrant pause/unpause, status/retry/replay and worker recovery exercised',
                        'Text-only baseline imported; WF15 proves exact new fixture point repair, not completeness of every unrelated baseline vector',
                        'WF16 schedule disabled in clone to control first failure probe; real webhook and persisted 15-minute cache exercised'])
            (output/'result.json').write_text(json.dumps(evidence,indent=2));return evidence
        finally:
            for name in reversed(created):
                own=json.loads(run('inspect',name))[0]
                (output/(name.rsplit('-',1)[-1]+'-state.json')).write_text(json.dumps(own['State'],indent=2))
                (output/(name.rsplit('-',1)[-1]+'.log')).write_bytes(run('logs',name))
                if own['Config']['Labels'].get('org.qldapm.weekly-clone')!=clone['id']:raise RuntimeError('CLONE_LABEL_CHANGED')
                run('rm','-f',name)
            if business:
                own=json.loads(run('network','inspect',embedding_network))[0]
                if own['Labels'].get('org.qldapm.weekly-clone')!=clone['id']:raise RuntimeError('CLONE_NETWORK_LABEL_CHANGED')
                run('network','rm',embedding_network)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output');p.add_argument('--image',required=True)
    p.add_argument('--business',action='store_true')
    p.add_argument('--baseline')
    a=p.parse_args();result=qualify(a.output,a.image,a.business,a.baseline)
    print(json.dumps({'status':result['status'],'gateway_image':result['gateway_image'],'evidence_directory':str(a.output)}))

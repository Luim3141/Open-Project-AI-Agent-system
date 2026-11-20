from support import *
import os,sqlite3,urllib.request,urllib.error
assert CONTEXT['stage']=='LIVE_N8N_AUTH_DENIAL_AND_REDACTION_VERIFIED'
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai';backup=PRIVATE/'private-config'
preserved={}
for path in backup.rglob('*'):
    if not path.is_file():continue
    relative=path.relative_to(backup)
    if str(relative).replace('\\','/').startswith(('gateway/','operator/')) and relative.as_posix()!='gateway/config.json':
        current=runtime/relative
        assert current.is_file() and current.read_bytes()==path.read_bytes(),str(relative)
        preserved[str(relative)]=hashlib.sha256(current.read_bytes()).hexdigest()
old=json.loads((backup/'gateway/config.json').read_text());current=json.loads((runtime/'gateway/config.json').read_text())
assert {k:v for k,v in current.items() if k!='n8n_lifecycle'}==old
assert current['n8n_lifecycle']['enabled'] is True and len(current['n8n_lifecycle']['signing_key'])==64
core=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject'
assert (core/'.env').read_bytes()==(backup/'core-env').read_bytes()
def env(path):return dict(line.split('=',1) for line in path.read_text(encoding='utf-8-sig').splitlines() if line and not line.startswith('#') and '=' in line)
previous=env(backup/'.env');effective=env(runtime/'.env');assert {k:v for k,v in effective.items() if k!='AI_IMAGE'}=={k:v for k,v in previous.items() if k!='AI_IMAGE'}
assert effective['AI_IMAGE']==PROPOSAL['images']['gateway']
oldbridge=json.loads((backup/'core-ui-bridge.yml').read_text());newbridge=json.loads((core/'ui-bridge.yml').read_text())
oldbridge['services']['web']['image']=PROPOSAL['images']['core'];assert oldbridge==newbridge
q=queue();assert q=={'mode':'OFF','active':0,'provider_receipts':358}
pre=json.loads((RUN/'preflight.json').read_text())
native=sql("SELECT project_id,count(*),max(lock_version),max(updated_at) FROM work_packages WHERE project_id IN(5,6) GROUP BY project_id ORDER BY project_id; SELECT id,status_id,lock_version FROM work_packages WHERE id IN(379,386) ORDER BY id; SELECT count(*) FROM work_packages WHERE id=385")
assert native==pre['sql_baseline']
checks=json.loads((RUN/'serving-verification.json').read_text())
for kind,name in [('gateway','qldapm-ai-gateway-1'),('core','qldapm-openproject-web-1'),('n8n','qldapm-n8n-main')]:
    row=inspect(name);assert row['Image']==PROPOSAL['images'][kind] and row['State']['Status']=='running'
    if kind!='n8n':assert row['State']['Health']['Status']=='healthy'
    checks[kind].update(id=row['Id'],image=row['Image'])
starttime_changes=[]
for name in checks['unrelated_containers_unchanged']:
    baseline=next(r for r in json.loads((PRIVATE/'all-containers-before.json').read_text()) if r['Name']=='/'+name)
    row=inspect(name);assert (row['Id'],row['Image'])==(baseline['Id'],baseline['Image'])
    if row['State']['StartedAt']!=baseline['State']['StartedAt']:
        assert name=='qldapm-ai-stage-quick-tunnel-1','UNEXPECTED_UNRELATED_RESTART_'+name
        starttime_changes.append({'name':name,'before':baseline['State']['StartedAt'],'after':row['State']['StartedAt'],'restart_count':row['RestartCount'],'rollout_targeted_this_container':False})
# Read-only history fingerprints: the rollout must not rewrite prior runs, verdicts or receipts.
history={}
with sqlite3.connect((PRIVATE/'native-backup/gateway.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True) as db:
    for table in ['ai_runs','ai_queue','agent_runs','agent_tasks','engineering_checkpoints','engineering_plans','engineering_unit_definitions','gemini_call_receipts','requests']:
        rows=db.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
        expected=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
        code="import hashlib,json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);r=d.execute('SELECT * FROM "+table+" ORDER BY rowid').fetchall();print(hashlib.sha256(json.dumps(r,separators=(',',':')).encode()).hexdigest())"
        actual=docker('exec','qldapm-ai-gateway-1','python','-c',code).decode().strip()
        assert actual==expected,'GATEWAY_HISTORY_CHANGED_'+table
        history[table]={'rows':len(rows),'sha256':actual}
security={}
with sqlite3.connect((PRIVATE/'auxiliary-backup/n8n.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True) as db:
    db.row_factory=sqlite3.Row
    for table in ['user','credentials_entity','shared_workflow','shared_credentials']:
        before=[dict(r) for r in db.execute('SELECT * FROM "'+table+'" ORDER BY rowid')]
        after=n8n_read('SELECT * FROM "'+table+'" ORDER BY rowid')
        def canon(rows):return json.dumps([{k:v for k,v in r.items() if k not in {'updatedAt','lastActiveAt'}} for r in rows],sort_keys=True,separators=(',',':')).encode()
        assert canon(before)==canon(after),'N8N_AUTH_CHANGED_'+table
        security[table]={'rows':len(before),'sha256':hashlib.sha256(canon(after)).hexdigest()}
worker=json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',"import sqlite3,json,time;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);r=d.execute('SELECT worker_id,seen,run_id FROM engineering_worker_state WHERE project=6').fetchone();print(json.dumps({'worker_id':r[0],'age_seconds':time.time()-r[1],'run_id':r[2]}))"))
assert worker['age_seconds']<30 and worker['run_id'] is None
workflow=n8n_read("SELECT activeVersionId FROM workflow_entity WHERE id='"+PROPOSAL['workflow']['id']+"'")[0]
live_health=n8n_read("SELECT e.id,e.status,e.stoppedAt FROM execution_entity e JOIN workflow_entity w ON w.id=e.workflowId WHERE w.name LIKE 'WF16:%' AND e.deletedAt IS NULL ORDER BY CAST(e.id AS INTEGER) DESC LIMIT 1")
for url in ['http://127.0.0.1:18089/health','http://127.0.0.1:5679/healthz/readiness']:
    with urllib.request.urlopen(url,timeout=5) as response:assert response.status==200
result={'status':'DEPLOYED_TO_MAIN_READ_SMOKE_VERIFIED_WITH_LIMITS','approved_hash':CONTEXT['approved_hash'],
        'at':datetime.now(timezone.utc).isoformat(),'images':PROPOSAL['images'],'source_commit':PROPOSAL['qualification_source_commit'],
        'runtime_parity_files':15,'unrelated_container_ids_images_preserved':len(checks['unrelated_containers_unchanged']),
        'outside_scope_starttime_changes':starttime_changes,
        'queue':q,'sql':native,'worker':worker,'wf04_active_version':workflow['activeVersionId'],
        'active_workflows':sum(r['active'] for r in n8n_read('SELECT active FROM workflow_entity')),
        'preserved_private_files_sha256':preserved,'gateway_history':history,'n8n_auth':security,
        'n8n_latest_health_execution':live_health,'native_security':checks['native_business_security_preserved'],
        'main_business_e2e':'NOT_RUN_NOT_AUTHORIZED','owner_manual_uat':'PENDING OWNER MANUAL UAT',
        'positive_main_lifecycle_event_ack':'PENDING_NEXT_AUTHORIZED_REAL_EVENT; negative auth/redaction canary verified',
        'demo18791_changed':False,'wp385_replacement_created':False,'credentials_rotated':False,'historical_execution_purge_performed':False}
write('deployment-result.json',result)
path=ROOT/'docs/ai/engineering/deployment.json';metadata=json.loads(path.read_text())
metadata.setdefault('continuation_history',[]).append({'type':'APPROVED_CHATGPT_RECOVERY_PHASE2','approval_hash':CONTEXT['approved_hash'],
 'at':result['at'],'private_backup':str(PRIVATE),'observed_before':{k:json.loads((PRIVATE/(name+'-inspect.json')).read_text())['Image'] for k,name in [('gateway','qldapm-ai-gateway-1'),('core','qldapm-openproject-web-1'),('n8n','qldapm-n8n-main')]}})
metadata.update(gateway_deployed=PROPOSAL['images']['gateway'],core_deployed=PROPOSAL['images']['core'],n8n_deployed=PROPOSAL['images']['n8n'],
                gateway_health='healthy',core_health='healthy',gateway_revision='chatgpt-recovery-phase2-30218aff',core_revision='chatgpt-recovery-phase2-30218aff',phase='CHATGPT_RECOVERY_PHASE2_MAIN_DEPLOYED',approved_recovery_result=str(RUN/'deployment-result.json'))
path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
stage('DEPLOYMENT_VERIFIED_AND_METADATA_RECORDED')
print(json.dumps({'status':result['status'],'images':result['images'],'queue':q,'worker_alive':True,'wf04_nodes':8,
                  'unrelated_container_ids_images_preserved':result['unrelated_container_ids_images_preserved'],'gateway_history_tables_unchanged':len(history),'n8n_auth_tables_preserved':len(security)},indent=2))

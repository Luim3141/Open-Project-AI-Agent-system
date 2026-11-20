"""Before/after fingerprints; allow only exact declared image pins and new RAG receipts."""
import hashlib,json,os,sqlite3,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'docs/agent-studio-v2-stabilization'))
from preservation import capture
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def snapshot():
    data=capture();env=(private/'.env').read_text(encoding='utf-8-sig').splitlines()
    data['env_except_image_sha256']=digest([x for x in env if not x.startswith('AI_IMAGE=')])
    pins=json.loads((private/'image-lock.json').read_text());data['other_image_pins']=digest({k:v for k,v in pins.items() if k not in ['AI_IMAGE','CORE_IMAGE']})
    script='''import json,sqlite3,hashlib
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
tables=['agent_runs','agent_tasks','ai_queue','ai_runs','engineering_checkpoints','engineering_plans','engineering_unit_definitions','engineering_control','engineering_owner_commands','tokens']
def sha(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
rows=d.execute('SELECT * FROM gemini_call_receipts ORDER BY rowid').fetchall()
print(json.dumps({'critical':{t:sha(d.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall()) for t in tables},'provider_rows':len(rows),'provider_ids':[r[0] for r in rows],'provider_old_sha':sha(rows)}))'''
    p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=script,text=True,capture_output=True,check=True);data['runtime']=json.loads(p.stdout)
    sql='SELECT md5(row_to_json(w)::text) FROM work_packages w WHERE id=398;'
    data['native398']=subprocess.check_output(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',sql],text=True).strip()
    return data
phase=sys.argv[1]
if phase=='before':
    assert not (OUT/'integrity-before.json').exists();data=snapshot();(OUT/'integrity-before.json').write_text(json.dumps(data,indent=2)+'\n');print('Before captured; mode',data['gateway']['mode'],'provider rows',data['runtime']['provider_rows'])
else:
    before=json.loads((OUT/'integrity-before.json').read_text());after=snapshot();checks={}
    checks['Native_projects_roles_workflows_passwords']=before['native']==after['native']
    checks['Native398_entire_row']=before['native398']==after['native398']
    checks['runtime_tasks_runs_checkpoints_units_control_tokens']=before['runtime']['critical']==after['runtime']['critical']
    checks['config_secrets']=before['gateway']['files']==after['gateway']['files']
    # The existing release operator rewrites CRLF via text mode: compare the exact
    # pre-release backup plus all nonempty lines, rather than hiding a real key diff.
    env_check={'byte_normalized_equal':before['env_except_image_sha256']==after['env_except_image_sha256']}
    candidates=[]
    for mapping in (private/'operator').glob('integration-pair-*/backup-files.json'):
        files=json.loads(mapping.read_text())
        for index,path in files.items():
            if Path(path)==private/'.env':
                old=(mapping.parent/index).read_text(encoding='utf-8-sig').splitlines()
                if digest([x for x in old if not x.startswith('AI_IMAGE=')])==before['env_except_image_sha256']:
                    candidates.append((mapping.parent,old))
    assert candidates,'EXACT_BASELINE_ENV_BACKUP_REQUIRED'
    old=candidates[0][1];new=(private/'.env').read_text(encoding='utf-8-sig').splitlines()
    kept=lambda lines:[x for x in lines if x.strip() and not x.startswith('AI_IMAGE=')]
    env_check.update(exact_baseline_backup_verified=True,nonempty_lines_except_image_equal=kept(old)==kept(new),old_blank_lines=sum(not x.strip() for x in old),new_blank_lines=sum(not x.strip() for x in new))
    checks['environment_except_authorized_image']=env_check['nonempty_lines_except_image_equal']
    checks['other_image_pins']=before['other_image_pins']==after['other_image_pins']
    checks['OFF_idle']=after['gateway']['mode']=='OFF' and after['gateway']['active']==0
    checks['n8n_workflows_credentials']=before['ecosystem']['n8n']==after['ecosystem']['n8n']
    checks['bot_keys_notification_keys']=all(v==after['ecosystem']['files'][k] for k,v in before['ecosystem']['files'].items() if k!='.env')
    stable=['pairs','pair_codes','confirmations','notification_context','telegram_notification_outbox']
    checks['pairing_approval_outbox_context']=all(before['ecosystem']['telegram_tables'][t]==after['ecosystem']['telegram_tables'][t] for t in stable)
    code="import json,sqlite3,hashlib,sys;ids=json.load(sys.stdin);d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);rows=d.execute('SELECT * FROM gemini_call_receipts WHERE id IN (SELECT value FROM json_each(?)) ORDER BY rowid',(json.dumps(ids),)).fetchall();new=[json.loads(r[0]) for r in d.execute('SELECT document FROM gemini_call_receipts WHERE id NOT IN (SELECT value FROM json_each(?))',(json.dumps(ids),))];print(json.dumps({'old_sha':hashlib.sha256(json.dumps(rows,separators=(\",\",\":\")).encode()).hexdigest(),'new':[ {k:x.get(k) for k in ['id','actor','agent','run_id','phase','model','provider_model_version','state','http_status']} for x in new]}))"
    p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-c',code],input=json.dumps(before['runtime']['provider_ids']),text=True,capture_output=True,check=True);receipts=json.loads(p.stdout)
    checks['old_provider_receipts_immutable']=receipts['old_sha']==before['runtime']['provider_old_sha']
    checks['new_receipts_only_authorized_RAG']=all(r['agent']=='knowledge' and r['actor']==18 and r['run_id'] is None and r['model']=='gemini-3.5-flash-lite' for r in receipts['new'])
    (OUT/'integrity-after.json').write_text(json.dumps({'checks':checks,'environment_comparison':env_check,'after':after,'rag_receipts':receipts['new']},indent=2)+'\n');print(json.dumps(checks));assert all(checks.values())

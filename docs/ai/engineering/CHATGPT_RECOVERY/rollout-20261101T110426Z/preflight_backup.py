from support import *
import os,shutil
from automation.main_operations import capture,backup
from automation.main_auxiliary_backup import backup as auxiliary_backup,qualify_restore
stage('PREFLIGHT_STARTED')
assert CONTEXT['stage']=='PREFLIGHT_STARTED'
manifest=json.loads((PHASE/'source-versioning-manifest.json').read_text())
for row in manifest['included']:
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
for kind,image in PROPOSAL['images'].items():
    assert json.loads(docker('image','inspect',image))[0]['Id']==image
old={'qldapm-ai-gateway-1':'sha256:fcb44c49afb99efd85b4a00297a58e7c5a59d36ab2f2b78e15a6a6d135f5e93e',
     'qldapm-openproject-web-1':'sha256:a4fa8150728bc5fc50f8afed22fce898cc52065a55ff0fdb53b803a81d9e1c6b',
     'qldapm-n8n-main':'sha256:dd580fe1ab6e99e85bc66f2acf8bc8c5e9409fbe61b2e2803c5024403ef52833'}
rows={name:inspect(name) for name in json.loads(docker('ps','--format','json').decode().replace('\n',',').rstrip(','))} if False else {}
for name,image in old.items():
    row=inspect(name);assert row['Image']==image and row['State']['Status']=='running',name
    (PRIVATE/(name+'-inspect.json')).write_text(json.dumps(row,indent=2))
q=queue();assert q=={'mode':'OFF','active':0,'provider_receipts':358},q
baseline=sql("SELECT project_id,count(*),max(lock_version),max(updated_at) FROM work_packages WHERE project_id IN(5,6) GROUP BY project_id ORDER BY project_id; SELECT id,status_id,lock_version FROM work_packages WHERE id IN(379,386) ORDER BY id; SELECT count(*) FROM work_packages WHERE id=385")
assert '5|341|4|2026-10-29 10:08:56.897949' in baseline and '6|7|9|' in baseline and '379|7|4' in baseline
wf=n8n_read('SELECT w.id,w.name,w.activeVersionId,w.settings,h.nodes,h.connections FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId WHERE w.id='+"'"+PROPOSAL['workflow']['id']+"'")
assert len(wf)==1 and wf[0]['activeVersionId']==PROPOSAL['workflow']['expected_active_version']
preview=json.loads((PHASE/'n8n-rollout-preview.json').read_text());expected=json.loads((Path(preview['private_preview'])/'wf04-before.json').read_text())
current=wf[0]
for key in ['nodes','connections','settings']:
    if isinstance(current[key],str):current[key]=json.loads(current[key])
    assert current[key]==expected[key],key
(PRIVATE/'wf04-before.json').write_text(json.dumps(current,indent=2))
shutil.copy2(Path(preview['private_preview'])/'wf04-candidate.json',PRIVATE/'wf04-candidate.json')
workflow_state=n8n_read('SELECT id,name,active,activeVersionId,versionId,nodes,connections,settings FROM workflow_entity ORDER BY id')
(PRIVATE/'workflow-rows-before.json').write_text(json.dumps(workflow_state,indent=2))
all_rows=json.loads(docker('inspect',*docker('ps','-q').decode().split()))
(PRIVATE/'all-containers-before.json').write_text(json.dumps(all_rows,indent=2))
native=capture();assert native['active']==0
(PRIVATE/'main-manifest-before.json').write_text(json.dumps(native,indent=2))
assert shutil.disk_usage(PRIVATE).free>5*1024**3
stage('FRESH_BACKUP_STARTED')
a=backup(native,PRIVATE/'native-backup')
b=auxiliary_backup(native,PRIVATE/'auxiliary-backup',qualify=False)
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
config=PRIVATE/'private-config';config.mkdir()
for relative in ['.env','image-lock.json','gateway/config.json','gateway/credentials.json','gateway/ui.key','gateway/gemini.json','gateway/gemini.key','gateway/gemini-readiness.json','gateway/automation.key','operator/gemini-main/free-tier-proof.json','operator/n8n-main-owner/owner.json']:
    source=runtime/relative
    if source.is_file():
        target=config/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
core=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject'
for name in ['.env','ui-bridge.yml']:shutil.copy2(core/name,config/('core-'+name.lstrip('.')))
for name in ['engineering_worker.py','engineering_delivery.py','n8n_lifecycle_adapter.py']:
    shutil.copy2(ROOT/'openproject/ai/automation'/name,config/name)
for file in ['docs/ai/engineering/deployment.json','openproject/ai/CHECKPOINT.md','openproject/ai/README.md','architecture.md']:
    source=ROOT/file
    if source.is_file():shutil.copy2(source,config/file.replace('/','_'))
expected_ids={label:[r[0] for r in __import__('sqlite3').connect((PRIVATE/'auxiliary-backup/n8n.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True).execute('SELECT id FROM '+table+' ORDER BY id')] for label,table in [('workflow_ids','workflow_entity'),('credential_ids','credentials_entity')]}
qualify_restore(PRIVATE/'auxiliary-backup',PROPOSAL['images']['n8n'],expected_ids)
write('preflight.json',{'status':'PASS','queue':q,'sql_baseline':baseline,'workflow_version':current['activeVersionId'],'private_backup':str(PRIVATE),'postgres_sqlite_backup':a['status'],'n8n_assets_backup':b['status'],'fresh_n8n_candidate_credential_decryption':'PASS','workflows':len(workflow_state),'active_workflows':sum(r['active'] for r in workflow_state),'main_changed':False})
stage('PREFLIGHT_AND_FRESH_BACKUP_VERIFIED')

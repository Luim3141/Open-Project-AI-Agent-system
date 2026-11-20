"""Apply only Owner-approved 30218aff; preserve previous containers/config and data."""
from support import *
import os,re,secrets,urllib.request
assert CONTEXT['stage']=='TARGETED_WF04_IMPORT_QUALIFIED'
assert queue()=={'mode':'OFF','active':0,'provider_receipts':358}
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
core_runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject'
old=inspect('qldapm-n8n-main');saved=json.loads((PRIVATE/'qldapm-n8n-main-inspect.json').read_text())
assert old['Id']==saved['Id'] and old['Config']==saved['Config'] and old['HostConfig']==saved['HostConfig']
row=n8n_read("SELECT activeVersionId FROM workflow_entity WHERE id='"+PROPOSAL['workflow']['id']+"'")[0]
assert row['activeVersionId']==PROPOSAL['workflow']['expected_active_version']
envfile=PRIVATE/'n8n-preserved.env'
assert all('\n' not in v and '\r' not in v for v in old['Config']['Env'])
envfile.write_text('\n'.join(old['Config']['Env'])+'\n')
candidate_config=json.loads(docker('image','inspect',PROPOSAL['images']['n8n']))[0]['Config']
for key in ['Entrypoint','Cmd','User','WorkingDir']:
    assert candidate_config.get(key)==old['Config'].get(key),key
create=['create','--name','qldapm-n8n-main','--pull','never','--env-file',str(envfile),
        '--network',old['HostConfig']['NetworkMode'],'--restart',old['HostConfig']['RestartPolicy']['Name']]
for bind in old['HostConfig']['Binds']:create+=['--volume',bind]
for port,bindings in old['HostConfig']['PortBindings'].items():
    for binding in bindings:create+=['--publish',binding['HostIp']+':'+binding['HostPort']+':'+port]
for key,value in old['Config'].get('Labels',{}).items():create+=['--label',key+'='+value]
create+=[PROPOSAL['images']['n8n']]
stage('WORKER_STOP_REQUESTED')
execute(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Stop-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'; (Get-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery').State"],name='worker-stop')
for _ in range(15):
    count=execute(['powershell.exe','-NoProfile','-NonInteractive','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?(3)?\\.exe$' -and $_.CommandLine -like '*openproject*ai*automation*engineering_worker.py*--watch*' }).Count"]).decode().strip()
    if count=='0':break
    time.sleep(1)
else:raise RuntimeError('WORKER_PROCESS_STILL_RUNNING')
assert queue()['active']==0 and queue()['mode']=='OFF'
stage('WORKER_STOPPED_IDLE')
stage('N8N_STOP_REQUESTED')
docker('stop','--time','45','qldapm-n8n-main',name='n8n-stop')
cold=docker('run','--rm','--network','none','--mount','type=volume,source=qldapm-n8n-main-data,target=/data,readonly','--entrypoint','tar',PROPOSAL['images']['n8n'],'-C','/data','-cf','-','.',timeout=240,name='n8n-cold-backup')
(PRIVATE/'n8n-cold-volume.tar').write_bytes(cold)
write('n8n-cold-backup.json',{'bytes':len(cold),'sha256':hashlib.sha256(cold).hexdigest(),'private':True})
previous_name='qldapm-n8n-main-pre-30218aff-20261101T110426Z'
docker('rename','qldapm-n8n-main',previous_name)
CONTEXT['n8n_previous_name']=previous_name;stage('N8N_OLD_CONTAINER_PRESERVED')
docker(*create,name='n8n-create')
new=inspect('qldapm-n8n-main')
assert new['Image']==PROPOSAL['images']['n8n']
for key in ['Env','Entrypoint','Cmd','User','WorkingDir','Labels','ExposedPorts']:
    assert new['Config'].get(key)==old['Config'].get(key),'CONFIG_'+key
for key,value in old['HostConfig'].items():
    if key=='Dns' and not value and not new['HostConfig'].get(key):continue
    if key=='OomKillDisable' and not value and not new['HostConfig'].get(key):continue
    assert new['HostConfig'].get(key)==value,'HOSTCONFIG_'+key
for network,settings in old['NetworkSettings']['Networks'].items():
    if network==old['HostConfig']['NetworkMode']:continue
    args=['network','connect']
    aliases=[a for a in settings.get('Aliases') or [] if a not in {old['Id'],old['Id'][:12],'qldapm-n8n-main'}]
    for alias in aliases:args+=['--alias',alias]
    docker(*args,network,'qldapm-n8n-main')
stage('N8N_NEW_CONTAINER_CONFIG_VERIFIED')
code=r'''
const fs=require('fs'),cp=require('child_process'),{DatabaseSync}=require('node:sqlite');
const target=JSON.parse(fs.readFileSync('/backup/wf04-candidate.json'));
const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
if(d.prepare('SELECT activeVersionId FROM workflow_entity WHERE id=?').get(target.id).activeVersionId!==target.activeVersionId)throw Error('WORKFLOW_VERSION_CHANGED');d.close();
fs.writeFileSync('/tmp/wf04-single.json',JSON.stringify([target]));
for(const args of [['import:workflow','--input=/tmp/wf04-single.json'],['publish:workflow','--id='+target.id]])cp.execFileSync('n8n',args,{stdio:'pipe',timeout:120000});
console.log('TARGET_WF04_IMPORTED_PUBLISHED');
'''
docker('run','--rm','--pull','never','--network','none','--env-file',str(envfile),'--volume','qldapm-n8n-main-data:/home/node/.n8n:z','--mount',f'type=bind,source={PRIVATE},target=/backup,readonly','--entrypoint','node',PROPOSAL['images']['n8n'],'-e',code,timeout=300,name='n8n-target-update')
stage('WF04_TARGETED_UPDATE_APPLIED')
docker('start','qldapm-n8n-main')
for _ in range(90):
    try:
        with urllib.request.urlopen('http://127.0.0.1:5679/healthz/readiness',timeout=2) as response:
            if response.status==200:break
    except Exception:pass
    time.sleep(1)
else:raise RuntimeError('N8N_READINESS_TIMEOUT')
stage('N8N_CANDIDATE_READY')
config_path=runtime/'gateway/config.json';before=json.loads(config_path.read_text());after=dict(before)
assert not before.get('n8n_lifecycle',{}).get('enabled')
after['n8n_lifecycle']={'enabled':True,'webhook_url':'http://qldapm-n8n-main:5678/webhook/qldapm-lifecycle','signing_key':secrets.token_hex(32)}
temporary=config_path.with_suffix('.phase2.tmp');temporary.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');temporary.replace(config_path)
assert {k:v for k,v in json.loads(config_path.read_text()).items() if k!='n8n_lifecycle'}==before
# Persist the approved image pins so a later normal Compose invocation retains this rollout.
ai_env=runtime/'.env';text=ai_env.read_text(encoding='utf-8-sig')
assert len(re.findall('(?m)^AI_IMAGE=',text))==1
ai_env.write_text(re.sub('(?m)^AI_IMAGE=.*$', 'AI_IMAGE='+PROPOSAL['images']['gateway'],text),encoding='utf-8')
bridge=core_runtime/'ui-bridge.yml';data=json.loads(bridge.read_text());data['services']['web']['image']=PROPOSAL['images']['core'];bridge.write_text(json.dumps(data,indent=2)+'\n')
lock=runtime/'image-lock.json';data=json.loads(lock.read_text());data['AI_IMAGE']=PROPOSAL['images']['gateway'];data['CORE_IMAGE']=PROPOSAL['images']['core'];lock.write_text(json.dumps(data,indent=2)+'\n')
stage('APP_CONFIG_IMAGE_PINS_APPLIED')
previews=json.loads((PHASE/'compose-preview.json').read_text())
for record in previews:
    kind=record['kind'];name='qldapm-ai-gateway-1' if kind=='gateway' else 'qldapm-openproject-web-1';service='gateway' if kind=='gateway' else 'web'
    stage(kind.upper()+'_RECREATE_REQUESTED')
    execute(record['command_prefix']+['-f',record['candidate_override'],'up','-d','--no-deps',service],timeout=240,name=kind+'-apply')
    health(name,timeout=240);assert inspect(name)['Image']==PROPOSAL['images'][kind]
    stage(kind.upper()+'_CANDIDATE_HEALTHY')
assert queue()=={'mode':'OFF','active':0,'provider_receipts':358}
stage('MAIN_IMAGES_APPLIED_WORKER_HELD_FOR_VERIFICATION')

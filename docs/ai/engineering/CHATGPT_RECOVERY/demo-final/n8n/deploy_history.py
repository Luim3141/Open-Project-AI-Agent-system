"""Clone-qualified WF04/history rollout; key and existing business history are preserved."""
import datetime,hashlib,json,os,subprocess,sys,time,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.main_operations import capture
from automation.main_auxiliary_backup import backup
from automation.n8n_lifecycle_adapter import canonical_history_workflow
OUT=Path(__file__).parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('demo-n8n-rollout-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
private.mkdir(parents=True,exist_ok=False)
image=json.loads(subprocess.check_output(['docker','image','inspect','qldapm-n8n:demo-final']))[0]['Id']
assert json.loads((OUT/'history-clone-result.json').read_text())['image']==image
assert json.loads((OUT/'history-clone-result.json').read_text())['status']=='PASS'
oldname='qldapm-n8n-main-pre-demo-history-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
def docker(*args,data=None,timeout=240):
 p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
 if p.returncode:(private/'failure.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('N8N_ROLLOUT_COMMAND_FAILED_PRIVATE_LOG')
 return p.stdout
def inspect(name):return json.loads(docker('inspect',name))[0]
READ="""const s=require('node:sqlite'),d=new s.DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT w.id,w.name,w.active,w.activeVersionId,h.nodes,h.connections,w.settings FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId ORDER BY w.name').all()));d.close()"""
before=json.loads(docker('exec','qldapm-n8n-main','node','-e',READ));assert len(before)==16 and all(w['active'] for w in before)
STATE="""const s=require('node:sqlite'),crypto=require('crypto'),d=new s.DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const hash=t=>crypto.createHash('sha256').update(JSON.stringify(d.prepare('select * from "'+t+'" order by id').all())).digest('hex');console.log(JSON.stringify({credentials:hash('credentials_entity'),users:hash('user'),execution_count:d.prepare('select count(*) n from execution_entity').get().n,unfinished:d.prepare("select count(*) n from execution_entity where status in ('new','running','waiting')").get().n}));d.close()"""
state_before=json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE));assert state_before['unfinished']==0,'ACTIVE_N8N_EXECUTION; wait before restart'
(private/'published-before.json').write_text(json.dumps(before))
old=inspect('qldapm-n8n-main');assert old['Image']=='sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795'
candidate=json.loads(docker('image','inspect',image))[0]['Config']
for key in ['Entrypoint','Cmd','User','WorkingDir']:
 assert candidate.get(key)==old['Config'].get(key),'CANDIDATE_PROCESS_CONFIG_CHANGED_'+key
configcheck=docker('exec','qldapm-ai-gateway-1','python','-c',"import json;from pathlib import Path;c=json.load(open('/state/config.json'));assert c['n8n_lifecycle'].get('authenticated_webhook') is True;print('AUTHENTICATED_OUTBOX_CONFIGURED')")
aux=backup(capture(),private/'online-backup',qualify=True)
assert aux['credential_decryption'] is True and aux['credential_count']==4
target=next(w for w in before if w['name'].startswith('WF04:'))
oldspec={**target,'nodes':json.loads(target['nodes']),'connections':json.loads(target['connections']),'settings':json.loads(target['settings'])}
spec=canonical_history_workflow(oldspec,'http://qldapm-ai-gateway-1:8090')
(private/'workflow-new.json').write_text(json.dumps([spec]));(private/'workflow-old.json').write_text(json.dumps([oldspec]))
env={v.split('=',1)[0]:v.split('=',1)[1] for v in old['Config']['Env']}
env.update(EXECUTIONS_DATA_PRUNE='true',EXECUTIONS_DATA_MAX_AGE='720',EXECUTIONS_DATA_PRUNE_MAX_COUNT='10000')
envfile=private/'preserved.env';assert all('\n' not in k+v and '\r' not in k+v for k,v in env.items());envfile.write_text('\n'.join(k+'='+v for k,v in env.items())+'\n')
def cli(path,action):
 args=['run','--rm','--network','none','--env-file',str(envfile),'--volume','qldapm-n8n-main-data:/home/node/.n8n','--mount',f'type=bind,source={private},target=/fixture,readonly','--entrypoint','n8n',image,action]
 args+=['--input=/fixture/'+path] if action=='import:workflow' else ['--id='+target['id']]
 docker(*args)
renamed=False
try:
 docker('stop','--time','45','qldapm-n8n-main')
 cold=docker('run','--rm','--network','none','--mount','type=volume,source=qldapm-n8n-main-data,target=/data,readonly','--entrypoint','tar',image,'-C','/data','-cf','-','.')
 (private/'cold-volume.tar').write_bytes(cold)
 cli('workflow-new.json','import:workflow');cli(None,'publish:workflow')
 docker('rename','qldapm-n8n-main',oldname);renamed=True
 create=['create','--name','qldapm-n8n-main','--pull','never','--env-file',str(envfile),'--network',old['HostConfig']['NetworkMode'],'--restart',old['HostConfig']['RestartPolicy']['Name']]
 hc=old['HostConfig']
 for key,flag in [('Memory','--memory'),('MemorySwap','--memory-swap'),('CpuQuota','--cpu-quota'),('CpuPeriod','--cpu-period'),('PidsLimit','--pids-limit'),('CpusetCpus','--cpuset-cpus')]:
  if hc.get(key):create += [flag,str(hc[key])]
 if hc.get('NanoCpus'):create += ['--cpus',str(hc['NanoCpus']/1e9)]
 if hc.get('ReadonlyRootfs'):create += ['--read-only']
 for value in hc.get('CapDrop') or []:create += ['--cap-drop',value]
 for value in hc.get('CapAdd') or []:create += ['--cap-add',value]
 for value in hc.get('SecurityOpt') or []:create += ['--security-opt',value]
 for path,value in (hc.get('Tmpfs') or {}).items():create += ['--tmpfs',path+':'+value]
 if hc.get('Init'):create += ['--init']
 if hc.get('LogConfig',{}).get('Type'):create += ['--log-driver',hc['LogConfig']['Type']]
 for key,value in hc.get('LogConfig',{}).get('Config',{}).items():create += ['--log-opt',key+'='+value]
 for bind in old['HostConfig']['Binds']:create+=['--volume',bind]
 for port,bindings in old['HostConfig']['PortBindings'].items():
  for binding in bindings:create+=['--publish',binding['HostIp']+':'+binding['HostPort']+':'+port]
 for k,v in old['Config'].get('Labels',{}).items():create+=['--label',k+'='+v]
 docker(*create,image)
 new=inspect('qldapm-n8n-main')
 for key in ['Entrypoint','Cmd','User','WorkingDir','Labels','ExposedPorts']:
  assert new['Config'].get(key)==old['Config'].get(key),'RUNTIME_PROCESS_CONFIG_CHANGED_'+key
 for key,value in old['HostConfig'].items():
  if key in ['Dns','OomKillDisable'] and not value and not new['HostConfig'].get(key):continue
  assert new['HostConfig'].get(key)==value,'RUNTIME_HOST_CONFIG_CHANGED_'+key
 for network,settings in old['NetworkSettings']['Networks'].items():
  if network==old['HostConfig']['NetworkMode']:continue
  args=['network','connect']
  for alias in settings.get('Aliases') or []:
   if alias not in {old['Id'],old['Id'][:12],'qldapm-n8n-main'}:args+=['--alias',alias]
  docker(*args,network,'qldapm-n8n-main')
 docker('start','qldapm-n8n-main')
 for _ in range(120):
  try:
   if urllib.request.urlopen('http://127.0.0.1:5679/healthz/readiness',timeout=2).status==200:break
  except Exception:time.sleep(1)
 else:raise RuntimeError('N8N_READINESS_TIMEOUT')
 after=json.loads(docker('exec','qldapm-n8n-main','node','-e',READ));assert len(after)==16 and all(w['active'] for w in after)
 for oldrow,newrow in zip(before,after):
  if oldrow['id']!=target['id']:assert oldrow==newrow,'UNRELATED_WORKFLOW_CHANGED'
 current=next(w for w in after if w['id']==target['id']);assert json.loads(current['settings'])['saveDataSuccessExecution']=='all'
 assert len(json.loads(current['nodes']))==4
 state_after=json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE))
 assert state_after['credentials']==state_before['credentials'] and state_after['users']==state_before['users'],'N8N_CREDENTIAL_OR_USER_CHANGED'
 assert state_after['execution_count']>=state_before['execution_count'],'EXISTING_EXECUTION_HISTORY_LOST'
 (OUT/'published-after.json').write_text(json.dumps(after,indent=2)+'\n')
 result={'status':'DEPLOYED_READY_PENDING_MAIN_EXECUTION_READBACK','image':image,'previous_container':oldname,'backup':str(private),
  'cold_volume_sha256':hashlib.sha256(cold).hexdigest(),'credential_decryption':True,'credential_count':4,'workflow_count':16,'other_15_published_unchanged':True,
  'wf04_version':current['activeVersionId'],'preservation':{'credential_rows_unchanged':True,'users_unchanged':True,'existing_execution_count':state_before['execution_count'],'execution_count_after':state_after['execution_count']},'retention':{'success':'all','error':'all','progress':False,'age_hours':720,'max_count':10000},
  'master_key_rotation':'DEFERRED_BY_OWNER_FOR_LOCAL_DEMO','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 (OUT/'deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
except Exception:
 # Restore only the previous workflow definition, never reset history/credentials/DB.
 if renamed:
  docker('stop','--time','30','qldapm-n8n-main');docker('rename','qldapm-n8n-main',oldname+'-failed');docker('rename',oldname,'qldapm-n8n-main')
 cli('workflow-old.json','import:workflow');cli(None,'publish:workflow');docker('start','qldapm-n8n-main')
 raise

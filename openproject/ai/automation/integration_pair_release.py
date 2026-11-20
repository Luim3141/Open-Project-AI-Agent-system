"""Host-only, exact-source Gateway/Core patch. No action runs on import.

prepare/build never change serving containers. rollout is a separate explicit command.
Business databases are backed up through Linux SQLite and never restored automatically.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[3]
BASE_IMAGES={
    'gateway':'sha256:3c06559033eba39f423a0c6f9474d1f77e3ef2ebd3617e1b37e50147d2d51a31',
    'core':'sha256:5936d90e450e8af321557e94928807f646dd077e646c1ceb546f858890aef2e8'}
TARGETS={'gateway':('qldapm-ai-gateway-1','qldapm-ai','gateway'),
         'core':('qldapm-openproject-web-1','qldapm-openproject','web')}
SOURCES={**{'openproject/ai/gateway/'+name:('gateway','/app/gateway/'+name) for name in (
    'app.py','service.py','monitoring.py','integration_events.py','engineering_github_poll.py',
    'engineering_github_details.py','engineering_github_sync.py','engineering.py')},
    'openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb':
        ('core','/app/app/views/qldapm_ai/_engineering_command_center.html.erb')}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path,value):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');temporary.replace(path)


def run(args,*,data=None,timeout=300):
    process=subprocess.run(args,input=data,capture_output=True,timeout=timeout)
    if process.returncode:raise RuntimeError('INTEGRATION_RELEASE_COMMAND_FAILED:'+args[0]+':'+str(process.returncode))
    return process.stdout


def inspect(role):
    name,project,service=TARGETS[role];row=json.loads(run(['docker','inspect',name]))[0]
    labels=row['Config'].get('Labels') or {}
    if row['Name']!='/'+name or (labels.get('com.docker.compose.project'),labels.get('com.docker.compose.service'))!=(project,service):
        raise ValueError('INTEGRATION_RELEASE_TARGET_DENIED')
    return row


def runtime_hashes(role,image=None):
    paths={key:value[1] for key,value in SOURCES.items() if value[0]==role}
    if role=='gateway':
        code='import hashlib,json,pathlib; paths='+repr(paths)+'; print(json.dumps({k:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() if pathlib.Path(p).is_file() else None for k,p in paths.items()}))'
        prefix=['docker','exec',TARGETS[role][0]] if image is None else ['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--entrypoint','python',image]
        return json.loads(run(prefix+(['python'] if image is None else [])+['-c',code]))
    code="require 'json';require 'digest';puts JSON.generate(JSON.parse(ARGV.fetch(0)).transform_values{|p|File.file?(p) ? Digest::SHA256.file(p).hexdigest : nil})"
    prefix=['docker','exec',TARGETS[role][0],'ruby'] if image is None else ['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--entrypoint','ruby',image]
    return json.loads(run(prefix+['-e',code,json.dumps(paths)]))


def source_hashes(root=ROOT):return {key:sha(root/key) for key in SOURCES}


def guard_sources(root,expected):
    if any(sha(Path(root)/key)!=value for key,value in expected.items()):raise ValueError('INTEGRATION_RELEASE_SOURCE_CHANGED')


def qualified(proof,files):
    if (proof.get('status')!='PASS' or proof.get('source_hashes')!=files
            or proof.get('checks')!={'github':True,'events':True,'core':True}):
        raise ValueError('INTEGRATION_RELEASE_EXACT_QUALIFICATION_REQUIRED')


def next_config(before):
    after=copy.deepcopy(before)
    after.setdefault('engineering',{})['github_sync']={'enabled':False,'actor':18,'interval_seconds':300}
    after.setdefault('n8n_integration',{})['enabled']=False
    return after


def image_only(before,after):
    def other(row):return {key:value for key,value in row.items() if key not in {'image','pull_policy'}}
    if other(before)!=other(after):raise ValueError('INTEGRATION_RELEASE_COMPOSE_PARITY_FAILED')


def restore_pair(restore,images):
    failures=[]
    for role in ('gateway','core'):
        try:restore(role,images[role])
        except Exception:failures.append(role)
    if failures:raise RuntimeError('INTEGRATION_RELEASE_ROLLBACK_INCOMPLETE:'+','.join(failures))


def base_tag(image,nonce):return 'qldapm-local-base:integration-'+image.removeprefix('sha256:')[:12]+'-'+nonce


def dockerfile(role,image,nonce):
    text='FROM '+base_tag(image,nonce)+'\n'
    for key,(owner,destination) in SOURCES.items():
        if owner==role:text+='COPY --chown='+('10001:10001' if role=='gateway' else 'app:app')+' '+key.removeprefix('openproject/ai/')+' '+destination+'\n'
    return text


def compose_prefix(row):
    labels=row['Config']['Labels'];env=labels['com.docker.compose.project.environment_file']
    files=labels['com.docker.compose.project.config_files'].split(',')
    if not files or any(not Path(path).is_file() for path in [env,*files]):raise ValueError('INTEGRATION_RELEASE_COMPOSE_INPUT_MISSING')
    return ['docker','compose','-p',labels['com.docker.compose.project'],'--env-file',env]+[part for path in files for part in ['-f',path]]


def live_snapshot():
    rows={role:inspect(role) for role in TARGETS};result={}
    for role,row in rows.items():
        if row['Image']!=BASE_IMAGES[role] or row['State'].get('Health',{}).get('Status')!='healthy':raise ValueError('INTEGRATION_RELEASE_MAIN_BASELINE_CHANGED')
        result[role]={'id':row['Id'],'image':row['Image'],'started_at':row['State']['StartedAt'],
                      'compose':compose_prefix(row),'hashes':runtime_hashes(role)}
    return result


def protected_paths(snapshot):
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
    paths=[runtime/'openproject-ai/.env',runtime/'openproject/.env',runtime/'openproject-ai/image-lock.json',
           runtime/'openproject/ui-bridge.yml',runtime/'openproject-ai/gateway/config.json']
    for row in snapshot.values():
        prefix=row['compose'];paths.extend(Path(prefix[i+1]) for i,value in enumerate(prefix[:-1]) if value in {'-f','--env-file'})
    return list(dict.fromkeys(paths))


def prepare(bundle):
    bundle=Path(bundle).resolve()
    if bundle.exists():raise ValueError('INTEGRATION_RELEASE_NEW_BUNDLE_REQUIRED')
    initial=live_snapshot();files=source_hashes()
    pins=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/image-lock.json').read_text())
    if (pins.get('AI_IMAGE'),pins.get('CORE_IMAGE'))!=(BASE_IMAGES['gateway'],BASE_IMAGES['core']):raise ValueError('INTEGRATION_RELEASE_BASE_PINS_CHANGED')
    bundle.mkdir(parents=True)
    for key in SOURCES:
        target=bundle/'context'/key.removeprefix('openproject/ai/');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/key,target)
    guard_sources(ROOT,files)
    nonce=uuid.uuid4().hex
    for role,image in BASE_IMAGES.items():(bundle/'context'/('Dockerfile.'+role)).write_text(dockerfile(role,image,nonce),encoding='utf-8')
    manifest={'version':1,'state':'PREPARED_NOT_BUILT_OR_DEPLOYED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'base_tag_nonce':nonce,'initial_runtime':initial,'source_hashes':files,'protected_inputs':{str(path):sha(path) for path in protected_paths(initial)},
              'policy':{'github_sync':{'enabled':False,'actor':18,'interval_seconds':300},'n8n_integration_enabled':False,'lifecycle_unchanged':True}}
    write_json(bundle/'manifest.json',manifest)
    return manifest


def load_guarded(bundle):
    bundle=Path(bundle).resolve();manifest=json.loads((bundle/'manifest.json').read_text())
    if manifest.get('version')!=1 or set(manifest.get('source_hashes',{}))!=set(SOURCES):raise ValueError('INTEGRATION_RELEASE_MANIFEST_INVALID')
    if not re.fullmatch('[a-f0-9]{32}',manifest.get('base_tag_nonce','')):raise ValueError('INTEGRATION_RELEASE_NONCE_INVALID')
    guard_sources(ROOT,manifest['source_hashes'])
    for key,expected in manifest['source_hashes'].items():
        if sha(bundle/'context'/key.removeprefix('openproject/ai/'))!=expected:raise ValueError('INTEGRATION_RELEASE_CONTEXT_CHANGED')
    for role,image in BASE_IMAGES.items():
        if (bundle/'context'/('Dockerfile.'+role)).read_text()!=dockerfile(role,image,manifest['base_tag_nonce']):raise ValueError('INTEGRATION_RELEASE_DOCKERFILE_CHANGED')
    if live_snapshot()!=manifest['initial_runtime']:raise ValueError('INTEGRATION_RELEASE_MAIN_RUNTIME_CHANGED')
    if any(sha(path)!=expected for path,expected in manifest['protected_inputs'].items()):raise ValueError('INTEGRATION_RELEASE_PROTECTED_INPUT_CHANGED')
    return bundle,manifest


def reuse_core(previous,files):
    previous=Path(previous).resolve();saved=json.loads((previous/'manifest.json').read_text())
    proof=json.loads((previous.parent/'core-candidate-clone-result.json').read_text())
    image=saved.get('images',{}).get('core','')
    expected={key:value for key,value in files.items() if SOURCES[key][0]=='core'}
    if (saved.get('state')!='BUILT_NOT_DEPLOYED' or not re.fullmatch('sha256:[a-f0-9]{64}',image)
            or saved.get('initial_runtime',{}).get('core',{}).get('image')!=BASE_IMAGES['core']
            or any(saved.get('source_hashes',{}).get(k)!=v for k,v in expected.items())
            or proof.get('status')!='PASS' or proof.get('image')!=image
            or runtime_hashes('core',image)!=expected):
        raise ValueError('INTEGRATION_RELEASE_CORE_REUSE_DENIED')
    return image


def build(bundle,reuse_core_bundle=None):
    bundle,manifest=load_guarded(bundle);images={}
    suffix=uuid.uuid4().hex[:12]
    for role in TARGETS:
        if role=='core' and reuse_core_bundle is not None:
            images[role]=reuse_core(reuse_core_bundle,manifest['source_hashes'])
            continue
        base=BASE_IMAGES[role];local_tag=base_tag(base,manifest['base_tag_nonce'])
        existing=subprocess.run(['docker','image','inspect',local_tag],capture_output=True)
        if existing.returncode==0:
            if json.loads(existing.stdout)[0]['Id']!=base:raise ValueError('INTEGRATION_RELEASE_BASE_TAG_CONFLICT')
        else:run(['docker','image','tag',base,local_tag])
        if json.loads(run(['docker','image','inspect',local_tag]))[0]['Id']!=base:raise ValueError('INTEGRATION_RELEASE_BASE_TAG_MISMATCH')
        tag='qldapm-'+role+':integration-'+suffix
        run(['docker','build','--network','none','--pull=false','-f',str(bundle/'context'/('Dockerfile.'+role)),'-t',tag,str(bundle/'context')],timeout=600)
        image=json.loads(run(['docker','image','inspect',tag]))[0]['Id']
        expected={key:value for key,value in manifest['source_hashes'].items() if SOURCES[key][0]==role}
        if runtime_hashes(role,image)!=expected:raise ValueError('INTEGRATION_RELEASE_BUILT_SOURCE_MISMATCH')
        if json.loads(run(['docker','image','inspect',local_tag]))[0]['Id']!=base:raise ValueError('INTEGRATION_RELEASE_BASE_TAG_CHANGED')
        images[role]=image
    guard_sources(ROOT,manifest['source_hashes']);manifest.update(state='BUILT_NOT_DEPLOYED',images=images)
    if reuse_core_bundle is not None:manifest['core_reused_from']=str(Path(reuse_core_bundle).resolve())
    write_json(bundle/'manifest.json',manifest);return manifest


def queue():
    code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':d.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0],'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0]}))"
    state=json.loads(run(['docker','exec',TARGETS['gateway'][0],'python','-c',code]))
    if state!={'active':0,'mode':'OFF'}:raise ValueError('INTEGRATION_RELEASE_IDLE_OFF_REQUIRED')
    return state


def powershell(command):return run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"$ErrorActionPreference='Stop'; "+command]).decode().strip()


def stop_worker():
    powershell("Stop-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'")
    for _ in range(30):
        count=powershell("@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?(3)?\\.exe$' -and $_.CommandLine -match '(?i)(automation[\\/]+engineering_worker\\.py|automation\\.engineering_worker).*--watch' }).Count")
        if count=='0':return
        time.sleep(1)
    raise RuntimeError('INTEGRATION_RELEASE_WORKER_STILL_RUNNING')


def healthy(role,image):
    for _ in range(150):
        row=inspect(role)
        if row['Image']==image and row['State'].get('Health',{}).get('Status')=='healthy':return
        time.sleep(1)
    raise RuntimeError('INTEGRATION_RELEASE_HEALTH_TIMEOUT:'+role)


def snapshot_sqlite(private):
    for name in ('gateway','knowledge'):
        code="import sqlite3,sys,pathlib;p=pathlib.Path('/state/"+name+".sqlite');assert p.is_file();s=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True);d=sqlite3.connect(':memory:');s.backup(d);assert d.execute('pragma integrity_check').fetchone()[0]=='ok';sys.stdout.buffer.write(d.serialize())"
        # SQLite WAL readers may need writable shared-memory locks; database opens mode=ro.
        data=run(['docker','run','--rm','--network','none','--read-only','--volumes-from',TARGETS['gateway'][0],
                  '--entrypoint','python',BASE_IMAGES['gateway'],'-c',code],timeout=120)
        (private/(name+'.sqlite')).write_bytes(data)


def rollout(bundle,proof_path):
    bundle,manifest=load_guarded(bundle);proof=json.loads(Path(proof_path).read_text());qualified(proof,manifest['source_hashes'])
    images=manifest.get('images',{})
    if set(images)!=set(TARGETS):raise ValueError('INTEGRATION_RELEASE_BUILT_PAIR_REQUIRED')
    for role,image in images.items():
        if not re.fullmatch('sha256:[a-f0-9]{64}',image) or runtime_hashes(role,image)!={key:value for key,value in manifest['source_hashes'].items() if SOURCES[key][0]==role}:raise ValueError('INTEGRATION_RELEASE_IMAGE_PARITY_FAILED')
    queue();runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM';config_path=runtime/'openproject-ai/gateway/config.json'
    before=json.loads(config_path.read_text());after=next_config(before)
    if before.get('maintenance'):raise ValueError('INTEGRATION_RELEASE_EXISTING_MAINTENANCE_HOLD')
    private=runtime/'openproject-ai/operator'/('integration-pair-'+uuid.uuid4().hex);private.mkdir(parents=True)
    originals={Path(path):Path(path).read_bytes() for path in manifest['protected_inputs']}
    for number,(path,data) in enumerate(originals.items()):(private/str(number)).write_bytes(data)
    write_json(private/'backup-files.json',{str(index):str(path) for index,path in enumerate(originals)})
    write_json(private/'manifest-before.json',manifest);shutil.copyfile(proof_path,private/'qualification.json')
    prefixes={role:manifest['initial_runtime'][role]['compose'] for role in TARGETS}
    def apply(role,image):
        override=private/(role+'-'+image[7:19]+'.json');write_json(override,{'services':{TARGETS[role][2]:{'image':image,'pull_policy':'never'}}})
        prefix=prefixes[role]+['-f',str(override)]
        run(prefix+['up','-d','--no-deps',TARGETS[role][2]]);healthy(role,image)
    for role in TARGETS:
        prefix=prefixes[role];service=TARGETS[role][2];override=private/(role+'-parity.json')
        write_json(override,{'services':{service:{'image':images[role],'pull_policy':'never'}}})
        image_only(json.loads(run(prefix+['config','--format','json']))['services'][service],json.loads(run(prefix+['-f',str(override),'config','--format','json']))['services'][service])
    task_was_running=powershell("(Get-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery').State")=='Running'
    fenced=False;opened=False
    try:
        stop_worker();queue();load_guarded(bundle)
        write_json(config_path,{**before,'maintenance':True});fenced=True
        for role in TARGETS:run(['docker','stop',TARGETS[role][0]])
        snapshot_sqlite(private)
        write_json(config_path,{**after,'maintenance':True})
        for role in TARGETS:apply(role,images[role])
        for role in TARGETS:
            expected={key:value for key,value in manifest['source_hashes'].items() if SOURCES[key][0]==role}
            if runtime_hashes(role)!=expected:raise ValueError('INTEGRATION_RELEASE_SERVING_PARITY_FAILED')
        queue()
        probe="from types import SimpleNamespace as N;from pathlib import Path;from gateway.engineering_github_details import verified_release;import json;r=verified_release(N(store=N(root=Path('/state'))));assert r.get('state')=='DEPLOYED_TO_DEMO';print(json.dumps({'state':r['state'],'head_sha':r['head_sha'],'main_merged':r['main_merged']}))"
        observed=json.loads(run(['docker','exec',TARGETS['gateway'][0],'python','-c',probe]))
        env=runtime/'openproject-ai/.env';text=originals[env].decode('utf-8-sig')
        if len(re.findall(r'(?m)^AI_IMAGE=.*$',text))!=1:raise ValueError('INTEGRATION_RELEASE_ENV_IMAGE_MISSING')
        env.write_text(re.sub(r'(?m)^AI_IMAGE=.*$','AI_IMAGE='+images['gateway'],text),encoding='utf-8')
        lock=runtime/'openproject-ai/image-lock.json';pins=json.loads(originals[lock]);pins.update(AI_IMAGE=images['gateway'],CORE_IMAGE=images['core']);write_json(lock,pins)
        bridge=runtime/'openproject/ui-bridge.yml';bridged=json.loads(originals[bridge]);bridged['services']['web']['image']=images['core'];write_json(bridge,bridged)
        queue();guard_sources(ROOT,manifest['source_hashes'])
        # Opening is last: subsequent user writes must never be discarded by a DB rollback.
        write_json(config_path,after);opened=True
        result={'status':'DEPLOYED_SOURCE_AND_RELEASE_READBACK_VERIFIED','images':images,'source_hashes':manifest['source_hashes'],
                'demo_release':observed,'github_sync_enabled':False,'n8n_integration_enabled':False,'private_backup':str(private),'database_restore_performed':False}
        write_json(bundle/'deployment.json',result);return result
    except Exception:
        if fenced and not opened:
            for role in TARGETS:
                try:run(['docker','stop',TARGETS[role][0]])
                except Exception:pass
            rollback_errors=[]
            for path,data in originals.items():
                try:path.write_bytes(data)
                except Exception:rollback_errors.append('config')
            try:restore_pair(apply,BASE_IMAGES)
            except Exception:rollback_errors.append('images')
            if rollback_errors:
                (private/'ROLLBACK_INCOMPLETE').write_text('Keep worker stopped; inspect both images/config. Never restore business DB automatically.')
                raise RuntimeError('INTEGRATION_RELEASE_ROLLBACK_INCOMPLETE')
        raise
    finally:
        if task_was_running and not (private/'ROLLBACK_INCOMPLETE').exists():powershell("Start-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'")


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','build','rollout'])
    parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--qualification',type=Path)
    parser.add_argument('--reuse-core-bundle',type=Path)
    args=parser.parse_args()
    if args.action=='rollout' and not args.qualification:parser.error('rollout requires --qualification')
    result=prepare(args.bundle) if args.action=='prepare' else build(args.bundle,args.reuse_core_bundle) if args.action=='build' else rollout(args.bundle,args.qualification)
    print(json.dumps({key:result[key] for key in ('state','status','images') if key in result}))


if __name__=='__main__':main()

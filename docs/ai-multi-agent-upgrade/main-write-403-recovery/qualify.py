"""Build exact candidates; reuse only stopped owned Main clone data, no serving writes."""
import hashlib
import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path
from inspect_runtime import ROOT, OUT, run
sys.path.insert(0,str(ROOT/'openproject/ai'))
from free_tier_staging import private_directory
from tests import qualify_remaining as networks

def inspect(name): return json.loads(run('docker','inspect',name))[0]
def checked_build(args, log):
    with (OUT/log).open('wb') as f:
        p=subprocess.run(['docker',*args],stdout=f,stderr=subprocess.STDOUT,timeout=600)
    assert p.returncode==0, 'BUILD_FAILED:'+log

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-linux',action='store_true');args=parser.parse_args()
    output=OUT/'qualification.json'
    if args.resume_linux:
        previous=json.loads(output.read_text());assert previous['phase']=='BUILDING' and previous['checks']['linux_exit']!=0
        shutil.copy2(output,OUT/'qualification-initial-failed.json');shutil.copy2(OUT/'linux-tests.log',OUT/'linux-tests-initial-failed.log')
    else:assert not output.exists(),'EXISTING_QUALIFICATION_RECONCILE'
    private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/main-write-403-recovery'
    private_directory(private)
    record={'phase':'BUILDING','private':str(private),'checks':{},'google_calls':0}
    def save():output.write_text(json.dumps(record,indent=2))
    save()
    files={p.relative_to(ROOT/'openproject/ai').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for folder in ('gateway','core/overlay') for p in (ROOT/'openproject/ai'/folder).rglob('*')
           if p.is_file() and '__pycache__' not in str(p)}
    record['source']=files
    sha=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest();record['source_sha256']=sha;save()
    checked_build(['build','-f','openproject/ai/Dockerfile','-t','qldapm-ai:write403-20261021',
                   '--label','org.qldapm.source.sha256='+sha,'openproject/ai'],'gateway-build.log')
    base='sha256:95da6c8eed2e9cae1bc023b7f29451433bec3e1c68480421be1c4629542ef53f'
    run('docker','tag',base,'qldapm-core-dependency:write403-95da6c8e')
    checked_build(['build','-f','openproject/ai/automation/ExecutionMonitorCore.Dockerfile',
                   '--build-arg','CORE_IMAGE=qldapm-core-dependency:write403-95da6c8e',
                   '--build-arg','SOURCE_SHA256='+sha,'-t','qldapm-core:write403-20261021','openproject/ai'],'core-build.log')
    record['gateway_image']=run('docker','image','inspect','qldapm-ai:write403-20261021','--format','{{.Id}}').strip()
    record['core_image']=run('docker','image','inspect','qldapm-core:write403-20261021','--format','{{.Id}}').strip();save()
    with (OUT/'linux-tests.log').open('wb') as stream:
        p=subprocess.run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=256m',
            '--mount',f'type=bind,src={ROOT}/openproject/ai/tests,dst=/tests,readonly','--env','PYTHONPATH=/app:/','--env','QLDAPM_AI_RUNTIME=',
            '--entrypoint','python',record['gateway_image'],'-m','unittest',
            'tests.test_main_write_routing','tests.test_remaining_integration','tests.test_ai_worker',
            'tests.test_assistant_business','tests.test_live_agents','tests.test_main_business_mode'],
            stdout=stream,stderr=subprocess.STDOUT,timeout=180)
    record['checks']['linux_exit']=p.returncode;save();assert p.returncode==0,'LINUX_TESTS_FAILED'
    # Free resources held by the earlier owned qualification; retain all containers and data.
    for name in ('qldapm-rd-gateway-20261021','qldapm-rd-core-20261021','qldapm-rd-db-20261021'):
        c=inspect(name);assert c['Config']['Labels'].get('qldapm.qualification')=='remaining-20261021'
        if 'gateway' in name and c['State']['Running']:
            status=json.loads(run('docker','exec',name,'python','-c',"import sqlite3,json;s=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps(s.execute(\"select count(*) from ai_runs where state in ('running','queued')\").fetchone()[0]))"))
            assert status==0,'OWNED_CLONE_BUSY'
        if c['State']['Running']:run('docker','stop','--time','20',name)
    old=inspect('qldapm-codex-main-20261020-db');assert not old['State']['Running']
    assert old['Config']['Labels'].get('qldapm.qualification')=='codex-main-20261020'
    volume=next(m for m in old['Mounts'] if m['Destination']=='/var/lib/postgresql/data')
    assert volume['Type']=='volume'
    assert not any(m.get('Name')==volume['Name'] for n in run('docker','ps','--format','{{.Names}}').splitlines() for m in inspect(n)['Mounts'])
    clone=json.loads((OUT.parent/'codex-main-completion/clone.json').read_text());old_private=Path(clone['private'])
    fixtures=json.loads((old_private/'browser-accounts.json').read_text());record['fixture_users']=[{'id':u['id'],'role':u['role']} for u in fixtures['users']]
    (private/'browser-accounts.json').write_text(json.dumps(fixtures))
    state=private/'clone-state';private_directory(state)
    config=json.loads((old_private/'gateway/config.json').read_text());assert config['project_id']==5
    credentials=json.loads((old_private/'gateway/credentials.json').read_text())
    main_creds=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/credentials.json').read_text())
    config['users']['23']='QA';credentials['23']=main_creds['23']
    config.update(gateway_mode='native',openproject_url='http://web:8080',hosts=['gateway:8090','localhost:8090','127.0.0.1:8090','testserver'])
    (state/'config.json').write_text(json.dumps(config));(state/'credentials.json').write_text(json.dumps(credentials))
    (state/'gemini.json').write_text('{"enabled":false}');key=secrets.token_bytes(32);(state/'ui.key').write_bytes(key);(private/'ui.key').write_bytes(key)
    (state/'isolated-write-fixture.json').write_text(json.dumps({'parent_id':50,'type_id':6}))
    old_core=inspect(clone['names']['browser']);env=dict(s.split('=',1) for s in old_core['Config']['Env'])
    assert 'qa-db' in env['DATABASE_URL']
    env.update(QLDAPM_UI_KEY_FILE='/qa/ui.key',RAILS_MAX_THREADS='4',RAILS_MIN_THREADS='1',OPENPROJECT_HOST__NAME='localhost:18098',
               OPENPROJECT_ADDITIONAL__HOST__NAMES='["localhost:18098","127.0.0.1:18098","localhost:8088","web"]')
    (private/'core.env').write_text('\n'.join(k+'='+v for k,v in env.items())+'\n')
    (private/'db.env').write_text('\n'.join(old['Config']['Env'])+'\n')
    prefix='qldapm-write403-20261021';label='qldapm.qualification=main-write403-20261021'
    net=prefix+'-internal';front=prefix+'-front';networks.LABEL=label
    for name,internal in ((net,True),(front,False)):networks.create_network(name,internal=internal)
    record['names']={'db':prefix+'-db','core':prefix+'-core','gateway':prefix+'-gateway','network':net,'front':front};save()
    names=record['names']
    run('docker','run','-d','--name',names['db'],'--label',label,'--network',net,'--network-alias','qa-db',
        '--env-file',str(private/'db.env'),'--memory','768m','--mount',f'type=volume,src={volume["Name"]},dst=/var/lib/postgresql/data',old['Image'])
    for _ in range(30):
        p=subprocess.run(['docker','exec',names['db'],'pg_isready','-U','postgres'],capture_output=True)
        if p.returncode==0:break
        time.sleep(1)
    else:raise AssertionError('CLONE_DB_STARTUP_FAILED')
    run('docker','run','-d','--name',names['core'],'--label',label,'--network',net,'--network-alias','web',
        '--env-file',str(private/'core.env'),'--memory','3g','--mount',f'type=bind,src={private},dst=/qa,readonly',
        '--entrypoint','bundle',record['core_image'],'exec','rails','server','-b','0.0.0.0','-p','8080')
    run('docker','network','connect',front,names['core'])
    # Publish through a tiny existing Caddy image; Core stays on an internal network.
    (private/'Caddyfile').write_text(':8080 {\n reverse_proxy '+names['core']+':8080\n}\n')
    names['browser']=prefix+'-browser';save()
    run('docker','run','-d','--name',names['browser'],'--label',label,'--network',front,
        '-p','127.0.0.1:18098:8080','--mount',f'type=bind,src={private}/Caddyfile,dst=/etc/caddy/Caddyfile,readonly',
        '--memory','64m','sha256:d8542f48d34a9cf4e4c11a478865229840e87e4c96ea3f439101f31a5d35f75f')
    run('docker','run','-d','--name',names['gateway'],'--label',label,'--network',net,'--network-alias','gateway',
        '--read-only','--tmpfs','/tmp:rw,size=64m','--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','512m',
        '--mount',f'type=bind,src={state},dst=/state','--mount',f'type=bind,src={OUT},dst=/qualification,readonly',
        '--env','PYTHONPATH=/qualification:/app','--env','QLDAPM_OFFLINE_WRITE_UAT=1',record['gateway_image'])
    record.update(phase='CLONE_STARTING',base='http://localhost:18098',main_business_mutations=0,staging_untouched=True);save()
    print(json.dumps({k:record[k] for k in ('phase','core_image','gateway_image','base','fixture_users')}))

if __name__=='__main__':main()

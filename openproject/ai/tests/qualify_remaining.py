"""Prepare an isolated native backup clone and synthetic users, never a serving mutation.

All generated keys/passwords stay under the private operator directory. No provider key is copied.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import hashlib
import ipaddress

AI=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(AI))
from free_tier_staging import private_directory
from gateway.store import Store

OUT=AI.parents[1]/'docs/ai-multi-agent-upgrade/remaining-development'
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/remaining-qualification-20261018'
LABEL='qldapm.qualification=remaining-20261018'


def docker(*args,timeout=90):
    p=subprocess.run(['docker',*args],capture_output=True,timeout=timeout)
    if p.returncode:
        if PRIVATE.exists():(PRIVATE/('docker-error-'+str(time.time_ns())+'.log')).write_bytes(p.stdout+p.stderr)
        raise RuntimeError('ISOLATED_DOCKER_FAILED:'+args[0])
    return p.stdout.decode().strip()


def snapshot():
    rows=[]
    names=docker('ps','--format','{{.Names}}').splitlines()
    for name in names:
        if not name.startswith(('qldapm-ai-stage-','qldapm-openproject-')):continue
        i=json.loads(docker('inspect',name))[0]
        rows.append({'name':name,'id':i['Id'],'image':i['Image'],'started_at':i['State']['StartedAt'],'restarts':i['RestartCount']})
    return rows


def create_network(name, internal=False):
    ids=docker('network','ls','-q').splitlines()
    networks=json.loads(docker('network','inspect',*ids))
    used=[ipaddress.ip_network(c['Subnet']) for n in networks for c in (n.get('IPAM',{}).get('Config') or []) if c.get('Subnet') and ':' not in c['Subnet']]
    if os.name=='nt':
        routes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',
            'Get-NetRoute -AddressFamily IPv4 | Select-Object -ExpandProperty DestinationPrefix | ConvertTo-Json -Compress']))
        used.extend(ipaddress.ip_network(p) for p in routes if p!='0.0.0.0/0')
    for candidate in ipaddress.ip_network('10.254.236.0/22').subnets(new_prefix=28):
        if not any(candidate.overlaps(other) for other in used):
            docker('network','create',*(['--internal'] if internal else []),'--subnet',str(candidate),'--label',LABEL,name)
            return
    raise ValueError('NO_NONOVERLAPPING_QUALIFICATION_SUBNET; no existing network removed')


def prepare():
    if PRIVATE.exists():raise ValueError('EXISTING_QUALIFICATION_CHECKPOINT_DO_NOT_OVERWRITE')
    private_directory(PRIVATE)
    (OUT/'serving-before.json').write_text(json.dumps(snapshot(),indent=2))
    images=json.loads((OUT/'candidate-images.json').read_text())
    assert all(v['exit_code']==0 for v in images.values())
    backups=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/local-backups'
    backup=max((p for p in backups.iterdir() if p.is_dir() and (p/'backup.json').is_file()),key=lambda p:p.stat().st_mtime)
    info=json.loads((backup/'backup.json').read_text())
    assert info['target']=='staging' and info['project_id']==3
    state=PRIVATE/'state';state.mkdir()
    (state/'ui.key').write_bytes(secrets.token_bytes(32))
    accounts=[{'login':'rd-fixture-'+r.lower(),'role':r,'password':'Aa1!'+secrets.token_urlsafe(30)} for r in ('PM','BA','BE','FE','QA')]
    (PRIVATE/'fixture-input.json').write_text(json.dumps(accounts))
    # Environment is generated afresh; serving database URLs, keys and credentials are never copied.
    password=secrets.token_hex(24)
    (PRIVATE/'db.env').write_text('POSTGRES_DB=openproject\nPOSTGRES_PASSWORD=PUBLICATION_REDACTED\n')
    environment={'DATABASE_URL':'postgres://postgres:PUBLICATION_REDACTED@rd-db/openproject','SECRET_KEY_BASE':secrets.token_hex(64),
        'OPENPROJECT_HOST__NAME':'localhost:18095','OPENPROJECT_ADDITIONAL__HOST__NAMES':'["localhost:18095","127.0.0.1:18095","localhost:8088","staging-web"]',
        'OPENPROJECT_HTTPS':'false','OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL':'','OPENPROJECT_RAILS__CACHE__STORE':'file_store',
        'OPENPROJECT_WEB_WORKERS':'1','RAILS_MIN_THREADS':'1','RAILS_MAX_THREADS':'8','RAILS_ENV':'production',
        'QLDAPM_UI_KEY_FILE':'/qa/state/ui.key','QLDAPM_QUALIFICATION':'remaining-20261018','MIGRATE':'false'}
    (PRIVATE/'core.env').write_text('\n'.join(k+'='+v for k,v in environment.items())+'\n')
    names={'network':'qldapm-rd-20261018','front':'qldapm-rd-loopback-20261018','db':'qldapm-rd-db-20261018','core':'qldapm-rd-core-20261018','gateway':'qldapm-rd-gateway-20261018'}
    record={'names':names,'images':images,'backup':str(backup),'backup_dump_sha256':hashlib.sha256((backup/'database.dump').read_bytes()).hexdigest(),'status':'PREPARING'}
    (OUT/'qualification.json').write_text(json.dumps(record,indent=2))
    create_network(names['network'],internal=True)
    docker('run','-d','--name',names['db'],'--label',LABEL,'--network',names['network'],'--network-alias','rd-db',
        '--env-file',str(PRIVATE/'db.env'),'--memory','512m','--pids-limit','128',
        '--mount','type=bind,src='+str(backup/'database.dump')+',dst=/backup.dump,readonly',info['postgres_image'])
    for _ in range(45):
        p=subprocess.run(['docker','exec',names['db'],'pg_isready','-U','postgres','-d','openproject'],capture_output=True)
        if p.returncode==0:break
        time.sleep(1)
    else:raise RuntimeError('CLONE_DB_NOT_READY')
    docker('exec',names['db'],'pg_restore','--no-owner','--no-privileges','-U','postgres','-d','openproject','/backup.dump',timeout=120)
    print('Isolated PostgreSQL restored; serving database untouched.',flush=True)
    common=['--label',LABEL,'--network',names['network'],'--env-file',str(PRIVATE/'core.env'),'--memory','2g','--pids-limit','256',
        '--mount','type=bind,src='+str(PRIVATE)+',dst=/qa', '--mount','type=bind,src='+str(AI/'tests/remaining_fixture.rb')+',dst=/fixture.rb,readonly']
    docker('run','-d','--name',names['core'],'--network-alias','staging-web','--network-alias','web','-p','127.0.0.1:18095:8080',
        *common,'--entrypoint','sleep',images['core']['image'],'infinity')
    docker('cp',str(AI/'tests/remaining_fixture.rb'),names['core']+':/tmp/remaining_fixture.rb')
    docker('exec',names['core'],'bundle','exec','rails','runner','/tmp/remaining_fixture.rb',timeout=180)
    print('Five new synthetic fixture accounts and native work package created in clone.',flush=True)
    finish_prepare()


def finish_prepare():
    state=PRIVATE/'state'
    record=json.loads((OUT/'qualification.json').read_text())
    names=record['names']
    images=json.loads((OUT/'candidate-images.json').read_text())
    for kind in ('db','core'):
        info=json.loads(docker('inspect',names[kind]))[0]
        assert info['Config']['Labels'].get('qldapm.qualification')=='remaining-20261018'
        assert set(info['NetworkSettings']['Networks']) <= {names['network'],names['front']}
    record['images']=images
    data=json.loads((PRIVATE/'fixture-credentials.json').read_text())
    config={'gateway_mode':'native','users':{str(a['id']):a['role'] for a in data['users']},'project_id':data['project_id'],
        'openproject_url':'http://staging-web:8080','hosts':['gateway:8090','localhost:18096','127.0.0.1:18096']}
    native_config=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/stage-ai/config.json').read_text())
    config.update({key:native_config[key] for key in ('source_field','type_ids','status_ids')})
    (state/'config.json').write_text(json.dumps(config))
    store=Store(state)
    for account in data['users']:account['gateway_token']=store.issue_token(account['id'],account['role'],account['token'])
    (PRIVATE/'fixture-credentials.json').write_text(json.dumps(data))
    docker('run','-d','--name',names['gateway'],'--label',LABEL,'--network',names['network'],'--network-alias','gateway',
        '-p','127.0.0.1:18096:8090','--memory','384m','--pids-limit','96','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges:true','--tmpfs','/tmp:size=32m,mode=1777',
        '--mount','type=bind,src='+str(state)+',dst=/state',images['gateway']['image'])
    create_network(names['front'])
    for kind in ('core','gateway'):docker('network','connect',names['front'],names[kind])
    docker('exec','-d',names['core'],'sh','-c','bundle exec rails server -b 0.0.0.0 -p 8080 > /qa/core-server.log 2>&1')
    record['status']='STARTED_WAITING_HEALTH';record['fixture_user_ids']=[a['id'] for a in data['users']]
    record['work_package_id']=data['work_package_id']
    (OUT/'qualification.json').write_text(json.dumps(record,indent=2))
    print('Isolated Core/Gateway started on loopback18095/18096; no Gemini key, no public tunnel.',flush=True)


def build_gateway():
    images=json.loads((OUT/'candidate-images.json').read_text())
    hashes={p.relative_to(AI).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((AI/'gateway').rglob('*.py')) if '__pycache__' not in p.parts}
    source=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    tag='qldapm-rd-gateway:20261018-'+source[:10]
    log=OUT/('gateway-build-'+source[:10]+'.log')
    with log.open('wb') as stream:
        completed=subprocess.run(['docker','build','-f','automation/RemainingGateway.Dockerfile',
            '--build-arg','SOURCE_SHA256='+source,'-t',tag,'.'],cwd=AI,stdout=stream,stderr=subprocess.STDOUT)
    assert completed.returncode==0,'CANDIDATE_BUILD_FAILED'
    image=docker('image','inspect',tag,'--format','{{.Id}}')
    (OUT/('candidate-images-before-'+str(time.time_ns())+'.json')).write_text(json.dumps(images,indent=2))
    images['gateway'].update(tag=tag,image=image,source_sha256=source,exit_code=0)
    (OUT/'candidate-images.json').write_text(json.dumps(images,indent=2))
    (OUT/'candidate-gateway-source-hashes.json').write_text(json.dumps(hashes,indent=2))
    print(json.dumps({'image':image,'source_sha256':source,'build_exit':0}),flush=True)


def build_core():
    images=json.loads((OUT/'candidate-images.json').read_text())
    recipe=AI/'automation/DailyCore.Dockerfile'
    paths=[AI/line.split()[-2] for line in recipe.read_text().splitlines() if line.startswith('COPY ')]
    hashes={p.relative_to(AI).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [recipe,*paths]}
    source=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest();tag='qldapm-rd-core:20261018-'+source[:10]
    with (OUT/('core-build-'+source[:10]+'.log')).open('wb') as stream:
        r=subprocess.run(['docker','build','-f','automation/DailyCore.Dockerfile','--build-arg',
            'CORE_IMAGE=qldapm-rd-base:core-8a42c7ef','-t',tag,'.'],cwd=AI,stdout=stream,stderr=subprocess.STDOUT)
    assert r.returncode==0,'CANDIDATE_CORE_BUILD_FAILED'
    image=docker('image','inspect',tag,'--format','{{.Id}}')
    (OUT/('candidate-images-before-'+str(time.time_ns())+'.json')).write_text(json.dumps(images,indent=2))
    images['core'].update(tag=tag,image=image,source_sha256=source,exit_code=0)
    (OUT/'candidate-images.json').write_text(json.dumps(images,indent=2))
    print(json.dumps({'core_image':image,'source_sha256':source,'build_exit':0}),flush=True)


def refresh_gateway():
    record=json.loads((OUT/'qualification.json').read_text());names=record['names']
    images=json.loads((OUT/'candidate-images.json').read_text())
    assert names['gateway']=='qldapm-rd-gateway-20261018'
    current=json.loads(docker('inspect',names['gateway']))[0]
    assert current['Config']['Labels'].get('qldapm.qualification')=='remaining-20261018'
    assert set(current['NetworkSettings']['Networks'])=={names['network'],names['front']}
    assert any(m['Destination']=='/state' and Path(m['Source']).name=='state' for m in current['Mounts'])
    # Windows and Linux must not share SQLite WAL/SHM connections on the host bind.
    busy=docker('exec',names['gateway'],'python','-c',
        "import sqlite3;d=sqlite3.connect('/state/gateway.sqlite');print(d.execute(\"SELECT COUNT(*) FROM ai_queue WHERE state IN ('queued','executing')\").fetchone()[0]);d.close()")
    assert busy=='0','ACTIVE_CLONE_RUNS'
    before=snapshot()
    docker('stop',names['gateway']);docker('rm',names['gateway'])
    # The owned disposable container has no named/anonymous volume; private bind data stays in place.
    docker('run','-d','--name',names['gateway'],'--label',LABEL,'--network',names['network'],'--network-alias','gateway',
        '-p','127.0.0.1:18096:8090','--memory','384m','--pids-limit','96','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges:true','--tmpfs','/tmp:size=32m,mode=1777',
        '--mount','type=bind,src='+str(PRIVATE/'state')+',dst=/state',images['gateway']['image'])
    docker('network','connect',names['front'],names['gateway'])
    assert snapshot()==before,'SERVING_CONTAINER_DRIFT'
    record['images']=images;record['status']='CANDIDATE_GATEWAY_REFRESHED'
    (OUT/'qualification.json').write_text(json.dumps(record,indent=2))
    print('Only the owned isolated Gateway refreshed; persistent fixture state retained.',flush=True)


def refresh_core():
    record=json.loads((OUT/'qualification.json').read_text());names=record['names']
    images=json.loads((OUT/'candidate-images.json').read_text())
    assert names['core']=='qldapm-rd-core-20261018'
    info=json.loads(docker('inspect',names['core']))[0]
    assert info['Config']['Labels'].get('qldapm.qualification')=='remaining-20261018'
    assert set(info['NetworkSettings']['Networks'])=={names['network'],names['front']}
    env=PRIVATE/'core.env';lines=env.read_text().splitlines()
    assert any(line=='QLDAPM_QUALIFICATION=remaining-20261018' for line in lines)
    lines=[('RAILS_MAX_THREADS=8' if line.startswith('RAILS_MAX_THREADS=') else line) for line in lines]
    env.write_text('\n'.join(lines)+'\n')
    before=snapshot()
    docker('stop',names['core']);docker('rm',names['core'])
    docker('run','-d','--name',names['core'],'--label',LABEL,'--network',names['network'],
        '--network-alias','staging-web','--network-alias','web','-p','127.0.0.1:18095:8080',
        '--env-file',str(env),'--memory','2g','--pids-limit','256',
        '--mount','type=bind,src='+str(PRIVATE)+',dst=/qa',
        '--entrypoint','sleep',images['core']['image'],'infinity')
    docker('network','connect',names['front'],names['core'])
    docker('exec','-d',names['core'],'sh','-c','bundle exec rails server -b 0.0.0.0 -p 8080 > /qa/core-server.log 2>&1')
    assert snapshot()==before,'SERVING_CONTAINER_DRIFT'
    record['core_max_threads']=8;record['status']='CORE_REFRESHED_WAITING_HEALTH'
    (OUT/'qualification.json').write_text(json.dumps(record,indent=2))
    print('Owned clone Core refreshed with8 threads; database and fixture credentials retained.',flush=True)


if __name__=='__main__':
    if '--build-gateway' in sys.argv:build_gateway()
    elif '--build-core' in sys.argv:build_core()
    elif '--refresh-gateway' in sys.argv:refresh_gateway()
    elif '--refresh-core' in sys.argv:refresh_core()
    elif '--resume' in sys.argv:finish_prepare()
    else:prepare()

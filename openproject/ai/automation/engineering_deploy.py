"""Operator-only Phase2 patch deployment over exact qualified Main images.

Additive metadata/config only; never restores a business database or deletes volumes.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'
AI_ENV=PRIVATE.parent/'.env'
CORE_ENV=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject/.env'


def run(args,**kwargs):
    p=subprocess.run(args,capture_output=True,timeout=180,**kwargs)
    if p.returncode:raise RuntimeError('DEPLOY_COMMAND_FAILED:'+args[0]+':'+str(p.returncode))
    return p.stdout


def inspect(name):return json.loads(run(['docker','inspect',name]))[0]


def replace_env(path,key,value):
    text=path.read_text(encoding='utf-8-sig')
    if not re.search('(?m)^'+key+'=',text):raise ValueError('DEPLOY_ENV_KEY_MISSING')
    path.write_text(re.sub('(?m)^'+key+'=.*$',key+'='+value,text),encoding='utf-8')


def health(name):
    for _ in range(90):
        row=inspect(name)
        if row['State'].get('Health',{}).get('Status')=='healthy':return
        time.sleep(2)
    raise RuntimeError('DEPLOY_HEALTH_TIMEOUT')


def deploy():
    gateway=inspect('qldapm-ai-gateway-1');core=inspect('qldapm-openproject-web-1')
    if gateway['Image']!='sha256:eaaa1217ac79cfac4747e0fa71af40bf0d3c1a447f39e6cc24dc20e55a268fc4' or core['Image']!='sha256:08df5e2bda4042209217453a051671965b553e983001b76ebbb2e1a4d7ede9d3':
        raise ValueError('DEPLOY_BASELINE_CHANGED')
    active=json.loads(run(['docker','exec','qldapm-ai-gateway-1','python','-c',
        "import sqlite3,json;d=sqlite3.connect('/state/gateway.sqlite');print(json.dumps(d.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0]))"]))
    if active:raise ValueError('DEPLOY_ACTIVE_AI_RUN_HOLD')
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup=PRIVATE/('engineering-'+stamp);backup.mkdir(parents=True)
    state=Path(next(m['Source'] for m in gateway['Mounts'] if m['Destination']=='/state'))
    manifest={'backup':str(backup),'gateway_image':gateway['Image'],'core_image':core['Image'],
        'project5_business_writes':0,'database_reset':False,'volumes_deleted':False}
    for path in [AI_ENV,CORE_ENV,state/'config.json']:
        shutil.copy2(path,backup/('gateway-config.json' if path.name=='config.json' else 'ai.env' if path==AI_ENV else 'core.env'))
    # SQLite is owned by Linux. Windows sqlite3 opening its WAL files while Linux
    # holds them causes incompatible SHM locks / disk I/O errors. Backup in the
    # serving Linux process and explicitly close both handles before returning.
    for name in ['gateway','knowledge']:
        if not (state/(name+'.sqlite')).exists():continue
        snapshot='engineering-'+stamp+'-'+name+'.sqlite'
        code="from contextlib import closing; import sqlite3; "
        code+="\nwith closing(sqlite3.connect('/state/"+name+".sqlite')) as source,closing(sqlite3.connect('/state/"+snapshot+"')) as target:source.backup(target)"
        run(['docker','exec','qldapm-ai-gateway-1','python','-c',code])
        shutil.copy2(state/snapshot,backup/(name+'.sqlite'))
    (backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
    config=json.loads((state/'config.json').read_text())
    config['engineering']={'enabled':True,'actors':{'20':'PM'}}
    (state/'config.json').write_text(json.dumps(config,indent=2))
    replace_env(AI_ENV,'AI_IMAGE','qldapm-ai:engineering-phase2-20261029')
    bridge=CORE_ENV.parent/'ui-bridge.yml'
    shutil.copy2(bridge,backup/'ui-bridge.yml')
    bridge_config=json.loads(bridge.read_text())
    bridge_config['services']['web']['image']='qldapm-core:engineering-phase2-20261029'
    bridge.write_text(json.dumps(bridge_config,indent=2))
    try:
        run(['docker','compose','--env-file',str(AI_ENV),'-f',str(ROOT/'openproject/ai/compose.yml'),'-f',str(ROOT/'openproject/ai/gemini-free.main.yml'),'up','-d','--no-deps','gateway'])
        health('qldapm-ai-gateway-1')
        run(['docker','compose','--env-file',str(CORE_ENV),'-f',str(ROOT/'openproject/compose.yml'),'-f',str(bridge),'up','-d','--no-deps','web'])
        health('qldapm-openproject-web-1')
    except Exception:
        # Keep snapshots and exact prior images; no automatic DB restoration.
        (backup/'DEPLOY_FAILED').write_text('Inspect live containers before rollback; do not replay runs.')
        raise
    manifest.update(gateway_deployed=inspect('qldapm-ai-gateway-1')['Image'],core_deployed=inspect('qldapm-openproject-web-1')['Image'])
    for role,name in [('gateway','qldapm-ai-gateway-1'),('core','qldapm-openproject-web-1')]:
        manifest[role+'_health']=inspect(name)['State']['Health']['Status']
    target=ROOT/'docs/ai/engineering/deployment.json';target.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest))


if __name__=='__main__':deploy()

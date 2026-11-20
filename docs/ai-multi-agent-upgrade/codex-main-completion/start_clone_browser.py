"""Start only the labelled restored clone, with synthetic accounts and no Gemini key."""
import json
import os
import secrets
import subprocess
from pathlib import Path

OUT=Path(__file__).parent

def docker(*args):
    p=subprocess.run(['docker',*args],capture_output=True,timeout=45)
    assert p.returncode==0,'CLONE_START_FAILED_OUTPUT_WITHHELD'
    return p.stdout.decode().strip()

def main():
    record=json.loads((OUT/'clone.json').read_text());private=Path(record['private']);names=record['names']
    accounts=json.loads((private/'browser-accounts.json').read_text())
    state=private/'gateway';state.mkdir()
    key=secrets.token_hex(32).encode();(state/'ui.key').write_bytes(key);(private/'ui.key').write_bytes(key)
    main_config=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/config.json').read_text())
    config={'gateway_mode':'native','project_id':5,'users':{str(u['id']):u['role'] for u in accounts['users']},
            'openproject_url':'http://web:8080','source_field':main_config['source_field'],'hosts':['gateway:8090','localhost:18089','127.0.0.1:18089','127.0.0.1:8090'],
            'type_ids':[1,5,10],'status_ids':[1,7,9,33,34,35,36,37,38,39,40,41]}
    (state/'config.json').write_text(json.dumps(config))
    (state/'credentials.json').write_text(json.dumps({str(u['id']):u['token'] for u in accounts['users']}))
    (state/'gemini.json').write_text('{"enabled":false,"model":"gemini-3.5-flash-lite"}')
    env=(private/'core.env').read_text().splitlines()
    env=[line for line in env if not line.startswith('OPENPROJECT_ADDITIONAL__HOST__NAMES=')]
    env+=['OPENPROJECT_ADDITIONAL__HOST__NAMES=["localhost:18088","127.0.0.1:18088","localhost:8088","web"]',
          'QLDAPM_UI_KEY_FILE=/qa-private/ui.key','RAILS_MAX_THREADS=4','RAILS_MIN_THREADS=1']
    (private/'browser.env').write_text('\n'.join(env)+'\n')
    names['browser']='qldapm-codex-main-20261020-browser'
    names['gateway']='qldapm-codex-main-20261020-gateway'
    docker('run','-d','--name',names['browser'],'--label',record['label'],'--network',names['network'],'--network-alias','web',
           '-p','127.0.0.1:18088:8080','--env-file',str(private/'browser.env'),'--memory','1536m',
           '--mount',f'type=bind,src={private},dst=/qa-private','--entrypoint','bundle',record['image'],
           'exec','rails','server','-b','0.0.0.0','-p','8080')
    docker('network','connect',names['front'],names['browser'])
    docker('run','-d','--name',names['gateway'],'--label',record['label'],'--network',names['network'],'--network-alias','gateway',
           '--read-only','--tmpfs','/tmp:size=32m','--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','512m',
           '--mount',f'type=bind,src={state},dst=/state','--mount',f'type=bind,src={private}/workspaces,dst=/workspaces',
           'sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b')
    record['status']='BROWSER_STARTING';(OUT/'clone.json').write_text(json.dumps(record,indent=2))
    print(json.dumps({'browser_url':'http://localhost:18088','gateway_external_network':False,'real_provider_key':False,'names':names}))

if __name__=='__main__':main()

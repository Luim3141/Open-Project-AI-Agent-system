"""Start only owned isolated qualification services. No serving project is changed."""
import json,os,shutil,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
def run(*args):
    p=subprocess.run(args,capture_output=True,timeout=180);assert p.returncode==0,'CLONE_COMMAND_FAILED_WITHHELD';return p.stdout
def main():
    ai=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'
    private=ai/'main-live-write-production-closeout';state=private/'clone-state'
    refresh='--refresh' in sys.argv
    if not refresh:state.mkdir(exist_ok=False)
    prior=ai/'main-live-write-final-acceptance/clone-state';old=ai/'main-write-403-recovery'
    if not refresh:
        for name in ('config.json','credentials.json'):shutil.copy2(prior/name,state/name)
        shutil.copy2(old/'ui.key',state/'ui.key');(state/'gemini.key').write_text('synthetic-only-no-live-key')
    patch=private/'clone-patch'
    if not refresh:patch.mkdir(exist_ok=False)
    shutil.copy2(OUT/'clone_provider.py',patch/'sitecustomize.py')
    q=json.loads((OUT/'qualification.json').read_text());assert q['linux_exit']==q['windows_exit']==0
    db=json.loads(run('docker','inspect','qldapm-write403-20261021-db'))[0]
    assert db['Config']['Labels'].get('qldapm.qualification')=='main-write403-20261021'
    run('docker','start','qldapm-write403-20261021-db')
    if refresh:
        for name in ('qldapm-closeout-20261022-gateway','qldapm-closeout-20261022-core'):
            c=json.loads(run('docker','inspect',name))[0];assert c['Config']['Labels'].get('qldapm.qualification')=='main-closeout-20261022'
            run('docker','stop','--time','20',name);run('docker','rename',name,name+'-pre-'+c['Image'][7:19])
    run('docker','run','-d','--name','qldapm-closeout-20261022-core','--label','qldapm.qualification=main-closeout-20261022',
        '--network','qldapm-write403-20261021-internal','--network-alias','web','--memory','3g','--env-file',str(old/'core.env'),
        '--mount',f'type=bind,src={old},dst=/qa,readonly','--entrypoint','bundle',q['core_image'],'exec','rails','server','-b','0.0.0.0','-p','8080')
    run('docker','network','connect','qldapm-write403-20261021-front','qldapm-closeout-20261022-core')
    run('docker','run','-d','--name','qldapm-closeout-20261022-gateway','--label','qldapm.qualification=main-closeout-20261022',
        '--network','qldapm-write403-20261021-internal','--network-alias','gateway','--memory','768m','--read-only','--tmpfs','/tmp:size=128m',
        '--env','PYTHONPATH=/clone-patch:/app','--mount',f'type=bind,src={patch},dst=/clone-patch,readonly',
        '--mount',f'type=bind,src={state},dst=/state','--mount',f'type=bind,src={OUT}/clone_probe.py,dst=/probe.py,readonly',q['gateway_image'])
    (private/'Caddyfile').write_text(':8080 {\n reverse_proxy qldapm-closeout-20261022-core:8080\n}\n')
    oldbrowser=json.loads(run('docker','inspect','qldapm-write403-20261021-browser'))[0]
    if refresh:run('docker','restart','qldapm-closeout-20261022-browser')
    else:run('docker','run','-d','--name','qldapm-closeout-20261022-browser','--label','qldapm.qualification=main-closeout-20261022',
        '--network','qldapm-write403-20261021-front','--publish','127.0.0.1:18098:8080',
        '--mount',f'type=bind,src={private}/Caddyfile,dst=/etc/caddy/Caddyfile,readonly',oldbrowser['Image'])
    print(json.dumps({'phase':'CLONE_STARTED','url':'http://localhost:18098','google':'SDK_MOCK_ONLY','native_writes':0}))
if __name__=='__main__':main()

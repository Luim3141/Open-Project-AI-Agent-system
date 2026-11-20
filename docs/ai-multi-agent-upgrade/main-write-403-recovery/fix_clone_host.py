"""Correct only the owned clone hostname; preserve old container and never route browser to Main."""
import json
from pathlib import Path
from inspect_runtime import OUT,run
from qualify import inspect
q=json.loads((OUT/'qualification.json').read_text());p=Path(q['private']);n=q['names']
c=inspect(n['core']);assert c['Config']['Labels']['qldapm.qualification']=='main-write403-20261021'
assert c['Image']==q['core_image']
env=dict(s.split('=',1) for s in c['Config']['Env'])
assert env['OPENPROJECT_HOST__NAME']=='localhost:18088'
env.update(OPENPROJECT_HOST__NAME='localhost:18098',OPENPROJECT_ADDITIONAL__HOST__NAMES='["localhost:18098","127.0.0.1:18098","localhost:8088","web"]')
(p/'core.env').write_text('\n'.join(k+'='+v for k,v in env.items())+'\n')
run('docker','stop','--time','20',n['core']);run('docker','rename',n['core'],n['core']+'-old-host')
run('docker','run','-d','--name',n['core'],'--label','qldapm.qualification=main-write403-20261021',
    '--network',n['network'],'--network-alias','web','--env-file',str(p/'core.env'),'--memory','3g',
    '--mount',f'type=bind,src={p},dst=/qa,readonly','--entrypoint','bundle',q['core_image'],
    'exec','rails','server','-b','0.0.0.0','-p','8080')
run('docker','network','connect',n['front'],n['core'])
run('docker','restart',n['browser'])
print('OWNED_CLONE_HOST_FIXED_MAIN_AND_STAGE_UNTOUCHED')

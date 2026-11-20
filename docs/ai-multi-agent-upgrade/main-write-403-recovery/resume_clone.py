"""Resume after wrong clone entrypoint; retain the failed container and reuse the already started clone DB."""
import json
import time
import urllib.request
from pathlib import Path
from inspect_runtime import OUT, run
from qualify import inspect

q=json.loads((OUT/'qualification.json').read_text());private=Path(q['private']);n=q['names']
label='qldapm.qualification=main-write403-20261021'
failed=inspect(n['core']);assert failed['State']['Status']=='created' and failed['State']['ExitCode']==127
assert failed['Config']['Labels'].get('qldapm.qualification')=='main-write403-20261021'
(OUT/'clone-startup-initial-failed.json').write_text(json.dumps(failed['State'],indent=2))
run('docker','rename',n['core'],n['core']+'-initial-failed')
run('docker','run','-d','--name',n['core'],'--label',label,'--network',n['network'],'--network-alias','web',
    '--env-file',str(private/'core.env'),'--memory','3g','--mount',f'type=bind,src={private},dst=/qa,readonly',
    '--entrypoint','bundle',q['core_image'],'exec','rails','server','-b','0.0.0.0','-p','8080')
run('docker','network','connect',n['front'],n['core'])
(private/'Caddyfile').write_text(':8080 {\n reverse_proxy '+n['core']+':8080\n}\n')
n['browser']='qldapm-write403-20261021-browser'
run('docker','run','-d','--name',n['browser'],'--label',label,'--network',n['front'],
    '-p','127.0.0.1:18098:8080','--mount',f'type=bind,src={private}/Caddyfile,dst=/etc/caddy/Caddyfile,readonly',
    '--memory','64m','sha256:d8542f48d34a9cf4e4c11a478865229840e87e4c96ea3f439101f31a5d35f75f')
run('docker','run','-d','--name',n['gateway'],'--label',label,'--network',n['network'],'--network-alias','gateway',
    '--read-only','--tmpfs','/tmp:rw,size=64m','--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','512m',
    '--mount',f'type=bind,src={private}/clone-state,dst=/state','--mount',f'type=bind,src={OUT},dst=/qualification,readonly',
    '--env','PYTHONPATH=/qualification:/app','--env','QLDAPM_OFFLINE_WRITE_UAT=1',q['gateway_image'])
q.update(phase='CLONE_STARTING',base='http://localhost:18098',main_business_mutations=0,staging_untouched=True)
(OUT/'qualification.json').write_text(json.dumps(q,indent=2))
print('ISOLATED_CLONE_STARTED_NO_SERVING_CHANGE')

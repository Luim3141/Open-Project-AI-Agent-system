"""Fresh no-network Gateway startup and code rollback; no live state mounts."""
from pathlib import Path
import json,subprocess,time,uuid
RUN=Path(__file__).parent
images={'gateway':{'id':'sha256:ce047f82692e7c46db1ddcb675be85d43a99936f0859e055db5513219a9ab6d4'}}
code="""from gateway.app import create_app
from gateway.store import Store
from gateway.service import Service
from pathlib import Path
import uvicorn
s=Service(Store('/tmp/state'),{'project_id':6,'users':{},'hosts':['localhost:8090'],'engineering':{'enabled':False},'openproject_url':'http://127.0.0.1:9'},Path('/tmp/workspaces'))
uvicorn.run(create_app('/tmp/state',s),host='127.0.0.1',port=8090)
"""
results=[]
for role,image in [('candidate',images['gateway']['id']),('rollback','sha256:8359e250512b0a68a6e92892feb539d6f392b94aa39b91e670db42f49c411e8a')]:
    label=uuid.uuid4().hex;name='qldapm-p3-startup-'+label
    try:
        subprocess.run(['docker','run','-d','--pull','never','--name',name,'--label','org.qldapm.startup='+label,'--network','none','--read-only','--tmpfs','/tmp:rw,size=128m','-e','QLDAPM_AI_RUNTIME=','--entrypoint','python',image,'-c',code],capture_output=True,check=True)
        for _ in range(35):
            p=subprocess.run(['docker','exec',name,'python','-c',"import urllib.request;assert urllib.request.urlopen('http://localhost:8090/health',timeout=2).status==200"],capture_output=True)
            if p.returncode==0:break
            time.sleep(1)
        else:raise RuntimeError('GATEWAY_STARTUP_FAILED')
        results.append({'kind':role,'image':image,'health':200,'network':'none','private_or_live_mounts':0})
    finally:
        inspect=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
        assert inspect['Config']['Labels']['org.qldapm.startup']==label
        (RUN/('gateway-owner-'+role+'-startup.log')).write_bytes(subprocess.check_output(['docker','logs',name],stderr=subprocess.STDOUT))
        subprocess.run(['docker','rm','-f',name],capture_output=True,check=True)
(RUN/'gateway-owner-startup-rollback.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))

"""Fresh no-network Gateway startup and code rollback; no live state mounts."""
from pathlib import Path
import json,subprocess,time,uuid
RUN=Path(__file__).parent
images={'gateway':{'id':'sha256:21f1d62d46a95e91c1e1625fec5fe7d95b5f4b6db44792f11c161943daee9642'}}
code="""from gateway.app import create_app
from gateway.store import Store
from gateway.service import Service
from pathlib import Path
import uvicorn
s=Service(Store('/tmp/state'),{'project_id':6,'users':{},'hosts':['localhost:8090'],'engineering':{'enabled':False},'openproject_url':'http://127.0.0.1:9'},Path('/tmp/workspaces'))
uvicorn.run(create_app('/tmp/state',s),host='127.0.0.1',port=8090)
"""
results=[]
for role,image in [('candidate',images['gateway']['id']),('rollback','sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb')]:
    label=uuid.uuid4().hex;name='qldapm-p2-startup-'+label
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
        (RUN/('gateway-phase2-'+role+'-startup.log')).write_bytes(subprocess.check_output(['docker','logs',name],stderr=subprocess.STDOUT))
        subprocess.run(['docker','rm','-f',name],capture_output=True,check=True)
(RUN/'gateway-phase2-startup-rollback.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))

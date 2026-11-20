"""Fresh no-network Gateway startup and code rollback; no live state mounts."""
from pathlib import Path
import json,subprocess,time,uuid
RUN=Path(__file__).parent
images={'gateway':{'id':'sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb'}}
code="""from gateway.app import create_app
from gateway.store import Store
from gateway.service import Service
from pathlib import Path
import uvicorn
s=Service(Store('/tmp/state'),{'project_id':6,'users':{},'hosts':['localhost:8090'],'engineering':{'enabled':False},'openproject_url':'http://127.0.0.1:9'},Path('/tmp/workspaces'))
uvicorn.run(create_app('/tmp/state',s),host='127.0.0.1',port=8090)
"""
results=[]
for role,image in [('candidate',images['gateway']['id']),('rollback','sha256:9d02446cecd21fccbed2bcc43ae0a7d488f3b5ae2617f1d918926b4ba39aa0d6')]:
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
        (RUN/('gateway-admission-'+role+'-startup.log')).write_bytes(subprocess.check_output(['docker','logs',name],stderr=subprocess.STDOUT))
        subprocess.run(['docker','rm','-f',name],capture_output=True,check=True)
(RUN/'gateway-admission-startup-rollback.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))

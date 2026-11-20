import json,subprocess
from pathlib import Path
OUT=Path(__file__).parent
code=r'''import json,cProfile,pstats,time
from gateway.service import Service
from gateway.store import Store
from gateway.engineering import scoped_service,status
s=scoped_service(Service(Store('/state'),json.load(open('/state/config.json')),'/workspaces'),6)
rows=[]
for i in range(2):
 p=cProfile.Profile();p.enable();start=time.monotonic();result=status(s,20);elapsed=time.monotonic()-start;p.disable()
 stats=pstats.Stats(p)
 calls=sorted([{'file':k[0].split('/')[-1],'function':k[2],'calls':v[1],'seconds':round(v[3],4)} for k,v in stats.stats.items()],key=lambda r:-r['seconds'])[:28]
 rows.append({'index':i,'seconds':elapsed,'functions':calls})
print(json.dumps({'scope':'Serving image separate process, fresh actual Native reads; not HTTP transport','rows':rows}))'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-c',code],capture_output=True,timeout=120)
assert p.returncode==0,p.stderr.decode()[-500:]
result=json.loads(p.stdout);(OUT/'serving-read-profile.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

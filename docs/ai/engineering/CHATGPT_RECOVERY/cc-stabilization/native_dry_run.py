"""Own-principal Native previews; no Native mutation, no model calls."""
import json,subprocess
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.resolve().parents[4]
sources={name:(ROOT/'openproject/ai/gateway'/f'{name}.py').read_text() for name in ['engineering_github_sync','engineering_status_sync']}
policy=json.loads((OUT/'status-sync-policy-draft.json').read_text())
code='''import json,types,sys
data=json.load(sys.stdin)
for name,source in data['sources'].items():
 module=types.ModuleType('gateway.'+name);module.__package__='gateway';sys.modules[module.__name__]=module
 exec(compile(source,'candidate-'+name,'exec'),module.__dict__)
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service
config=json.load(open('/state/config.json'));config['engineering']['status_sync']=data['policy']
service=scoped_service(Service(Store('/state'),config,'/workspaces'),6)
sources=module.sources(service);targets=set(data['policy']['historical_native_ids'])
print(json.dumps({'route':'NATIVE_API_PREVIEW_ONLY','principal':25,'project':6,'generation_calls':0,'native_writes':0,
 'rows':[module.preview(service,s) for s in sources if s['native_id'] in targets]}))
'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-c',code],input=json.dumps({'sources':sources,'policy':policy}).encode(),capture_output=True,timeout=120)
assert p.returncode==0,p.stderr.decode()[-800:]
result=json.loads(p.stdout);assert len(result['rows'])==5
(OUT/'native-dry-run.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

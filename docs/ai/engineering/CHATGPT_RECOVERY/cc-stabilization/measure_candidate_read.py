"""Candidate Python read path in a separate process; runtime application code stays unchanged."""
import hashlib,json,subprocess,sys
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.resolve().parents[4]
names=['store','engineering_github_operations','engineering_github_sync','engineering_lifecycle','engineering_health','engineering_observability','engineering_owner_control','engineering_reporting','workflow_status','delegated_approval','engineering']
sources={name:(ROOT/'openproject/ai/gateway'/f'{name}.py').read_text(encoding='utf-8') for name in names}
code="""import json,sys,time,types,importlib,statistics,cProfile,pstats
sources=json.load(sys.stdin)
for name,source in sources.items():
 full='gateway.'+name
 try:module=importlib.import_module(full)
 except ModuleNotFoundError:
  module=types.ModuleType(full);module.__package__='gateway';sys.modules[full]=module
 exec(compile(source,'candidate/'+name+'.py','exec'),module.__dict__)
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service,status
base=Service(Store('/state'),json.load(open('/state/config.json')),'/workspaces')
rows=[];profile=cProfile.Profile();profile.enable()
for index in range(SAMPLE_COUNT):
 started=time.monotonic();result=status(scoped_service(base,6),20)
 rows.append({'index':index,'seconds':round(time.monotonic()-started,4),'mode':result['mode'],'active':result['queue']['active'],'github_state':result['github']['status']})
profile.disable();stats=pstats.Stats(profile)
functions=sorted([{'file':k[0].split('/')[-1],'function':k[2],'calls':v[1],'cumulative_seconds':round(v[3],4)} for k,v in stats.stats.items() if '/gateway/' in k[0] or k[0].startswith('candidate/')],key=lambda r:-r['cumulative_seconds'])[:30]
print(json.dumps({'scope':'SEPARATE_CANDIDATE_PROCESS_WITH_ACTUAL_MAIN_NATIVE_READS; not deployed HTTP/Core/browser proof','rows':rows,'p50_seconds':statistics.median(r['seconds'] for r in rows),'p95_seconds':max(r['seconds'] for r in rows),'generation_calls':0,'profile':functions}))
"""
profiling=sys.argv[1:]==['--profile'];combined=code.replace('sources=json.load(sys.stdin)','sources='+repr(sources)).replace('SAMPLE_COUNT','1' if profiling else '5')
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=combined.encode(),capture_output=True,timeout=120)
assert p.returncode==0,p.stderr.decode()[-600:]
result=json.loads(p.stdout);result['source_sha256']={k:hashlib.sha256(v.encode()).hexdigest() for k,v in sources.items()}
(OUT/('candidate-read-profile-v2.json' if profiling else 'candidate-read-performance-v2.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['profile','source_sha256']}))

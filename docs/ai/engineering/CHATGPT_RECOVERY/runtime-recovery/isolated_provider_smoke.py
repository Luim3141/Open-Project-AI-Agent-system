"""One isolated, fixed-public-prompt generation using the existing shared limiter."""
import ast,datetime,json,subprocess,uuid,os
from pathlib import Path
OUT=Path(__file__).parent
intent=OUT/'isolated-provider-smoke.intent';target=OUT/'isolated-provider-smoke.json'
assert not intent.exists() and not target.exists(),'ONE_ATTEMPT_ONLY: inspect existing evidence, never auto-retry'
source=(OUT.parent/'demo-final/provider_probe.py').read_text()
tree=ast.parse(source)
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
assert code.count("=='OFF'")==1 and code.count("Service(store,config,'/workspaces')")==1
code=code.replace("=='OFF'","=='PAUSED'").replace('from gateway.service import Service','from types import SimpleNamespace').replace("Service(store,config,'/workspaces')","SimpleNamespace(store=store,config=config,gemini=Gemini(root))")
assert 'SMOKE_PROMPT' in code and "'maxOutputTokens':128" in code and 'store.reserve_gemini' in code and 'task_resumed' in code
info=json.loads(subprocess.check_output(['docker','inspect','qldapm-ai-gateway-1']))[0]
assert info['Image']==json.loads((OUT/'baseline.json').read_text())['containers']['qldapm-ai-gateway-1']['image']
env=dict(e.split('=',1) for e in info['Config']['Env'] if '=' in e)
assert env['QLDAPM_AI_ENVIRONMENT']=='production'
proof_path=env['QLDAPM_GEMINI_FREE_PROOF']
state=next(m for m in info['Mounts'] if m['Destination']=='/state')
proof=next(m for m in info['Mounts'] if proof_path==m['Destination'] or proof_path.startswith(m['Destination'].rstrip('/')+'/'))
assert state['Type']=='bind' and proof['Type']=='bind'
name='qldapm-runtime-provider-smoke-'+uuid.uuid4().hex[:10]
args=['docker','run','--rm','-i','--name',name,'--label','qldapm.runtime-recovery=isolated-provider-smoke','--network','bridge','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','384m','--cpus','1','--pids-limit','128','--tmpfs','/tmp:rw,size=32m,mode=1777','--user',info['Config']['User']]
for key in ['QLDAPM_AI_ENVIRONMENT','QLDAPM_GEMINI_FREE_PROOF']:args+=['-e',key+'='+env[key]]
args+=['--mount','type=bind,source='+state['Source']+',target=/state']
if proof['Destination']!='/state':args+=['--mount','type=bind,source='+proof['Source']+',target='+proof['Destination']+',readonly']
args+=['--entrypoint','python',info['Image'],'-']
# Shared /state is only for the real policy/key, limiter and receipt, never a copied/reset budget.
with intent.open('x') as stream:stream.write('ONE_OWNER_AUTHORIZED_PUBLIC_GENERATION; NO_TOOLS_NO_REPO_NO_TASK_NO_AUTO_RETRY\n')
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/runtime-recovery'
try:
    p=subprocess.run(args,input=code.encode(),capture_output=True,timeout=75)
    (private/'isolated-provider-smoke-private.log').write_bytes(p.stderr)
    assert p.returncode==0,'PROBE_FAILED_NO_RETRY: inspect private log'
    result=json.loads(p.stdout.decode().splitlines()[-1])
    result.update(isolation='ONE_SHOT_CONTAINER; no app server, tools, repository, Docker socket or Native/GitHub clients; shared existing quota store only',container=name,image=info['Image'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempts=1)
    target.write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
    remaining=subprocess.run(['docker','inspect',name],capture_output=True)
    if remaining.returncode==0:
        container=json.loads(remaining.stdout)[0]
        assert container['Image']==info['Image'] and container['Config']['Labels'].get('qldapm.runtime-recovery')=='isolated-provider-smoke'
        subprocess.run(['docker','rm','-f',name],check=True,capture_output=True)

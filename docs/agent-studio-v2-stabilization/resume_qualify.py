"""Qualification of the small resume delta over previously verified images."""
import json,subprocess
from resume_release import release,OUT,bundle
repo=OUT.parents[1];manifest=json.loads((bundle/'manifest.json').read_text());evidence={}
def run(name,args):
 p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
 (OUT/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,name
 return (p.stdout+p.stderr)[-300:]
p=subprocess.run(['npm.cmd','test'],cwd=repo/'openproject/ai/core/agent-studio-v2',capture_output=True,text=True);assert p.returncode==0;evidence['node']=p.stdout[-250:]
gw=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=128m,mode=1777','-e','QLDAPM_AI_RUNTIME=','-e','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={repo / "openproject/ai/tests"},target=/app/tests,readonly','--entrypoint','python',manifest['images']['gateway']]
evidence['gateway']=run('resume-gateway',gw+['-m','unittest','tests.test_observer_read_path','tests.test_agent_observer','tests.test_telegram_notifications','tests.test_engineering_catalog_limit'])
core=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=16m,mode=1777','--mount',f'type=bind,source={repo / "openproject/ai/tests"},target=/qa,readonly','--entrypoint','bundle',manifest['images']['core'],'exec','ruby']
evidence['bridge']=run('resume-bridge',core+['/qa/test_ai_bridge_admission.rb','/app/app/services/qldapm/ai_bridge.rb'])
fixture=json.loads((OUT/'fixture-browser.json').read_text());assert fixture['status']=='PASS';evidence['fixture']=fixture['checks']
for role,image in manifest['images'].items():assert release.runtime_hashes(role,image)=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
release.guard_sources(repo,manifest['source_hashes'])
proof={'status':'PASS','source_hashes':manifest['source_hashes'],'checks':{'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True},'evidence':evidence,'scope':'Retry-After parsing/forwarding and stable record-order tie break; existing qualified admission/RBAC/runtime retained'}
release.write_json(OUT/'resume-qualification.json',proof);print(json.dumps({'status':'PASS','evidence':evidence}))

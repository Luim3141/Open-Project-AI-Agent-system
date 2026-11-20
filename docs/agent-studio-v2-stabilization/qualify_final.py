"""Exact final images, behavioral regressions and same-host UI candidate checks."""
import json,subprocess
from release_final import release,OUT,bundle
repo=OUT.parents[1];manifest=json.loads((bundle/'manifest.json').read_text());evidence={}
def run(name,args,data=None,cwd=None,expected=0):
 p=subprocess.run(args,input=data,cwd=cwd,text=True,capture_output=True,encoding='utf-8',errors='replace',timeout=150)
 (OUT/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==expected,name
 return (p.stdout+p.stderr)[-300:]
evidence['frontend']=run('final-frontend',['node','--test','model.test.mjs','request.test.mjs'],cwd=repo/'openproject/ai/core/agent-studio-v2')
base=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=128m,mode=1777','--cap-drop','ALL','--security-opt','no-new-privileges:true','-e','QLDAPM_AI_RUNTIME=','-e','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={repo / "openproject/ai/tests"},target=/app/tests,readonly','--entrypoint','python',manifest['images']['gateway']]
tests=['engineering_monitor_current','observer_read_path','agent_observer','gateway','telegram_notifications','engineering_catalog_limit','execution_monitor','engineering_integrity_projection','supervisor','supervisor_project_scope']
evidence['gateway']=run('final-gateway',base+['-m','unittest',*['tests.test_'+t for t in tests]])
core=['docker','run','--rm','-i','--network','none','--read-only','--tmpfs','/tmp:size=16m,mode=1777','--mount',f'type=bind,source={repo / "openproject/ai/tests"},target=/qa,readonly','--entrypoint','bundle',manifest['images']['core'],'exec','ruby']
controller=(repo/'openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb').read_text()
evidence['command']=run('final-command-status',core+['/qa/test_bridge_busy_controller.rb','/app/app/services/qldapm/ai_bridge.rb'],json.dumps({'controller':controller}))
evidence['admission']=run('final-admission',core+['/qa/test_ai_bridge_admission.rb','/app/app/services/qldapm/ai_bridge.rb'])
evidence['cc_ack']=run('final-cc-ack',core+['/qa/test_cc_core_ack.rb'],json.dumps({'controller':controller}))
fixture=json.loads((OUT/'fixture-browser.json').read_text());assert fixture['status']=='PASS';evidence['fixture']=fixture['checks']
host=json.loads((OUT/'candidate-browser.json').read_text());assert host['scope']=='CANDIDATE ASSET ON REAL MAIN HOST' and all(host['checks'].values()) and not host['errors'];evidence['host']=host['checks']
for role,image in manifest['images'].items():assert release.runtime_hashes(role,image)=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
proof={'status':'PASS','source_hashes':manifest['source_hashes'],'checks':{'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True},'evidence':evidence,'core_base':'Native/metadata/schema unchanged over isolated-clone-qualified Core; prior Puma HTTP callback red/green evidence admission-qualification.json'}
release.write_json(OUT/'final-qualification.json',proof);print(json.dumps({'status':'PASS','evidence':evidence}))

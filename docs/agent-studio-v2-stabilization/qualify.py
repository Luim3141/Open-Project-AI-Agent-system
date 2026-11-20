"""Record actual immutable candidate checks and exact source hashes."""
import json,re,subprocess,sys
from pathlib import Path
from release import OUT,REPO,release
bundle=OUT/'candidate-v2';manifest=json.loads((bundle/'manifest.json').read_text());evidence={}
def run(name,args,cwd=None):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    (OUT/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,name+'_FAILED'
    return (p.stdout+p.stderr)[-250:]
evidence['adapter']=run('frontend-tests',['node','--test','model.test.mjs','request.test.mjs'],REPO/'openproject/ai/core/agent-studio-v2')
evidence['fixture_browser']=json.loads((OUT/'fixture-browser.json').read_text());assert evidence['fixture_browser']['status']=='PASS'
image=manifest['images']['gateway'];tests=['engineering_monitor_current','observer_read_path','agent_observer','gateway','telegram_notifications','engineering_catalog_limit','execution_monitor','engineering_integrity_projection','supervisor','supervisor_project_scope']
args=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=128m,mode=1777','--cap-drop','ALL','--security-opt','no-new-privileges:true','-e','QLDAPM_AI_RUNTIME=','-e','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={REPO / "openproject/ai/tests"},target=/app/tests,readonly','--entrypoint','python',image,'-m','unittest',*['tests.test_'+t for t in tests]]
evidence['regressions']=run('image-regressions',args)
core=json.loads((OUT/'core-clone.json').read_text());assert core['status']=='PASS' and core['image']==manifest['images']['core'];evidence['immutable_core']=core
for role,image in manifest['images'].items():assert release.runtime_hashes(role,image)=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
proof={'status':'PASS','source_hashes':manifest['source_hashes'],'checks':{k:True for k in ['adapter','fixture_browser','regressions','immutable_core']},'evidence':evidence}
release.guard_sources(REPO,proof['source_hashes']);release.write_json(OUT/'qualification.json',proof);print(json.dumps({'status':'PASS','regressions':evidence['regressions']}))

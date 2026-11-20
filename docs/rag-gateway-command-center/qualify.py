"""Relevant offline suites on current host code or an immutable candidate; never MAIN mutations."""
import json,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
base=json.loads((OUT/'baseline.json').read_text())['containers']
candidate=json.loads(Path(sys.argv[sys.argv.index('--candidate')+1]).read_text()) if '--candidate' in sys.argv else None
modules=json.loads((ROOT/'docs/functional-audit/qualification.json').read_text())['gateway_modules']
modules=list(dict.fromkeys(modules+['test_rag_answers','test_rag_phase4','test_rag_recovery','test_knowledge_search','test_knowledge_storage','test_knowledge_integrity','test_knowledge_answer','test_allowlisted_file_knowledge','test_project6_file_knowledge','test_prompt_injection_and_secret_exfil']))
def run(name,args):
    p=subprocess.run(args,text=True,capture_output=True,encoding='utf-8',errors='replace',timeout=300)
    (OUT/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    return {'exit_code':p.returncode,'tail':(p.stdout+p.stderr)[-1000:]}
common=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=128m,mode=1777','-e','PYTHONDONTWRITEBYTECODE=1','-e','QLDAPM_AI_RUNTIME=']
gw=common+['-e','PYTHONPATH=/app:/app/tests:/repo:/repo/openproject/ai','--mount',f'type=bind,source={ROOT / "openproject/ai/tests"},target=/app/tests,readonly','--mount',f'type=bind,source={ROOT / "openproject/ai/core"},target=/app/core,readonly','--mount',f'type=bind,source={ROOT / "openproject"},target=/repo/openproject,readonly','--mount',f'type=bind,source={ROOT / "docs"},target=/repo/docs,readonly']
if not candidate:gw+=['--mount',f'type=bind,source={ROOT / "openproject/ai/gateway"},target=/app/gateway,readonly']
report={'scope':'ISOLATED CONTRACTS; no credentials or network; not MAIN E2E','candidate':bool(candidate),'modules':modules}
report['gateway']=run('gateway-regression',gw+['--entrypoint','python',candidate['images']['gateway'] if candidate else base['qldapm-ai-gateway-1']['image'],'-m','unittest',*['tests.'+m for m in modules]])
bot=common+['--mount',f'type=bind,source={ROOT / "openproject/ai/telegram-ai/tests"},target=/qa,readonly','--mount',f'type=bind,source={ROOT / "openproject/ai/telegram-ai/app"},target=/app/app,readonly','--entrypoint','python',base['qldapm-ai-telegram-ai-1']['image']]
report['telegram']=run('telegram-regression',bot+['-m','unittest','discover','-s','/qa'])
report['ui_transport']=run('ui-transport-regression',['node',str(ROOT/'openproject/ai/tests/test_owner_live_transport.js')])
(OUT/('candidate-regression.json' if candidate else 'regression.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));assert all(report[k]['exit_code']==0 for k in ['gateway','telegram','ui_transport'])

"""Guarded pair release; immutable bases and exact qualification, config unchanged."""
import copy,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[1]
sys.path.insert(0,str(REPO/'openproject/ai'))
from automation import integration_pair_release as release
baseline=json.loads((OUT/'baseline.json').read_text())
release.BASE_IMAGES={r:baseline['containers'][r]['image'] for r in ('gateway','core')}
core=['app/controllers/qldapm_ai_controller.rb','app/services/qldapm/ai_bridge.rb','app/services/qldapm/observer_packages.rb',
      'lib/api/v3/qldapm/gates_api.rb','app/views/qldapm_ai/observer.html.erb','app/views/qldapm_ai/execution.html.erb',
      *['public/qldapm-agent-studio-v2/'+n for n in ['studio.js','studio.css','studio.js.LEGAL.txt','manifest.json']]]
gateway=['agent_observer.py','observer_reads.py','engineering_monitor.py','engineering_planning.py','native.py','app.py']
release.SOURCES={**{'openproject/ai/core/overlay/'+p:('core','/app/'+p) for p in core},**{'openproject/ai/gateway/'+p:('gateway','/app/gateway/'+p) for p in gateway}}
release.next_config=copy.deepcopy
def qualified(proof,files):
    assert proof['status']=='PASS' and proof['source_hashes']==files
    assert proof['checks']=={'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True}
release.qualified=qualified
if __name__=='__main__':
    action=sys.argv[1];bundle=OUT/(sys.argv[2] if len(sys.argv)>2 else 'candidate')
    if action=='prepare':result=release.prepare(bundle)
    elif action=='build':result=release.build(bundle)
    elif action=='rollout':
        result=release.rollout(bundle,OUT/'qualification.json');result.pop('github_sync_enabled',None);result.pop('n8n_integration_enabled',None);result['configuration_policy']='UNCHANGED_EXACT_HASH';release.write_json(bundle/'deployment.json',result)
    else:raise ValueError(action)
    print(json.dumps({k:v for k,v in result.items() if k in {'status','state','images'}}))

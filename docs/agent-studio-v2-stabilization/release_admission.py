"""Puma callback-capacity fix; same runtime, data, config and UI assets."""
import json,sys
from release import release,OUT
current=json.loads((OUT/'candidate-final/deployment.json').read_text());release.BASE_IMAGES=current['images']
release.SOURCES={k:v for k,v in release.SOURCES.items() if k.endswith('/qldapm_ai_controller.rb') or k.endswith('/ai_bridge.rb')}
bundle=OUT/'candidate-admission';action=sys.argv[1]
if action=='prepare':result=release.prepare(bundle)
elif action=='build':
 result=release.build(bundle);result['images']['gateway']=release.BASE_IMAGES['gateway'];release.write_json(bundle/'manifest.json',result)
elif action=='rollout':
 result=release.rollout(bundle,OUT/'admission-qualification.json');result.pop('github_sync_enabled',None);result.pop('n8n_integration_enabled',None);result['configuration_policy']='UNCHANGED_EXACT_HASH';release.write_json(bundle/'deployment.json',result)
else:raise ValueError(action)
print(json.dumps({k:v for k,v in result.items() if k in {'status','state','images'}}))

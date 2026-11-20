"""Final scoped changes: busy RetryAfter, history order, command status, full-read compatibility."""
import json,sys
from release import release,OUT
release.BASE_IMAGES=json.loads((OUT/'candidate-admission/deployment.json').read_text())['images']
release.SOURCES={k:v for k,v in release.SOURCES.items() if (v[0]=='core' and ('/public/qldapm-agent-studio-v2/' in k or k.endswith('/qldapm_ai_controller.rb'))) or (v[0]=='gateway' and k.endswith(('/agent_observer.py','/observer_reads.py')))}
bundle=OUT/'candidate-release'
if __name__=='__main__':
 action=sys.argv[1]
 if action=='prepare':result=release.prepare(bundle)
 elif action=='build':result=release.build(bundle)
 elif action=='rollout':
  result=release.rollout(bundle,OUT/'final-qualification.json');result.pop('github_sync_enabled',None);result.pop('n8n_integration_enabled',None);result['configuration_policy']='UNCHANGED_EXACT_HASH';release.write_json(bundle/'deployment.json',result)
 else:raise ValueError(action)
 print(json.dumps({k:v for k,v in result.items() if k in {'status','state','images'}}))

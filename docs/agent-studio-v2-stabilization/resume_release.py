"""Resume-only release for proven Retry-After and timestamp-tie regressions."""
import json,sys
from release import release,OUT
release.BASE_IMAGES=json.loads((OUT/'candidate-release/deployment.json').read_text())['images']
release.SOURCES={k:v for k,v in release.SOURCES.items() if '/public/qldapm-agent-studio-v2/' in k or k.endswith(('/ai_bridge.rb','/agent_observer.py'))}
bundle=OUT/(sys.argv[2] if __name__=='__main__' and len(sys.argv)>2 else 'resume-candidate')
if __name__=='__main__':
 action=sys.argv[1]
 result=release.prepare(bundle) if action=='prepare' else release.build(bundle) if action=='build' else release.rollout(bundle,OUT/'resume-qualification.json') if action=='rollout' else None
 if result is None:raise ValueError(action)
 if action=='rollout':
  result.pop('github_sync_enabled',None);result.pop('n8n_integration_enabled',None);result['configuration_policy']='UNCHANGED_EXACT_HASH';release.write_json(bundle/'deployment.json',result)
 print(json.dumps({k:v for k,v in result.items() if k in {'status','state','images'}}))

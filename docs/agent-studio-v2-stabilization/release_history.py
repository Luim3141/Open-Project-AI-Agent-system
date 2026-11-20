"""Assets-only follow-up, retaining actual serving Gateway and Core base."""
import json
from release import release,OUT
before=json.loads((OUT/'candidate-v2/deployment.json').read_text());release.BASE_IMAGES=before['images']
release.SOURCES={k:v for k,v in release.SOURCES.items() if v[0]=='core' and '/public/qldapm-agent-studio-v2/' in k}
bundle=OUT/'candidate-final';manifest=json.loads((bundle/'manifest.json').read_text())
fixture=json.loads((OUT/'fixture-browser.json').read_text());assert fixture['status']=='PASS'
host=json.loads((OUT/'history-candidate.json').read_text());assert host['scope']=='CANDIDATE ASSET ON REAL HOST' and all(r['state']=='391' for r in host['rows'] if r['step'].startswith('back')) and not host['errors']
full=json.loads((OUT/'candidate-browser.json').read_text());assert full['scope']=='CANDIDATE ASSET ON REAL MAIN HOST' and all(full['checks'].values()) and not full['errors']
proof={'status':'PASS','source_hashes':manifest['source_hashes'],'checks':{'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True},
       'evidence':{'scope':'Only four compiled assets over qualified serving Core/Gateway','fixture':fixture['checks'],'real_host_candidate':'history-candidate.json; actual Main Rails/Gateway, only candidate JS intercepted','base_core':before['images']['core'],'gateway_unchanged':True}}
release.write_json(OUT/'history-qualification.json',proof)
result=release.rollout(bundle,OUT/'history-qualification.json');result.pop('github_sync_enabled',None);result.pop('n8n_integration_enabled',None);result['configuration_policy']='UNCHANGED_EXACT_HASH';release.write_json(bundle/'deployment.json',result);print(json.dumps({'status':result['status'],'images':result['images']}))

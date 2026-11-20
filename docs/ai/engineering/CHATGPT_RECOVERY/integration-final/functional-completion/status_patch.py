"""One-line status repair; reuse qualified Core and existing backed-up pair rollout."""
import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.functional_pair_release import release

OUT=Path(__file__).parent
BASE=json.loads((OUT/'candidate2/deployment.json').read_text())
release.BASE_IMAGES=BASE['images']
# Existing rollout fences both containers; preserve the already enabled integrations.
release.next_config=copy.deepcopy

def reuse_core(previous,files):
    expected={k:v for k,v in files.items() if release.SOURCES[k][0]=='core'}
    assert release.runtime_hashes('core',BASE['images']['core'])==expected
    proof=json.loads((OUT/'core-clone-result.json').read_text())
    assert proof['status']=='PASS' and proof['image']==BASE['images']['core']
    return BASE['images']['core']

release.reuse_core=reuse_core

if __name__=='__main__':
    bundle=OUT/'status-patch'
    action=sys.argv[1]
    if action=='prepare':result=release.prepare(bundle)
    elif action=='build':result=release.build(bundle,OUT/'candidate2')
    elif action=='rollout':
        result=release.rollout(bundle,bundle/'qualification.json')
        import os
        config=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/config.json').read_text())
        result.update(github_sync_enabled=config['engineering']['github_sync']['enabled'],
                      n8n_integration_enabled=config['n8n_integration']['enabled'])
        release.write_json(bundle/'deployment.json',result)
    else:raise ValueError('UNKNOWN_ACTION')
    print(json.dumps({k:result[k] for k in ('state','status','images') if k in result}))

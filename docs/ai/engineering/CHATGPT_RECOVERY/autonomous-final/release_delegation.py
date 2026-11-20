"""Reuse the existing backed-up image-pair rollout; RAG experiments are excluded."""
import copy,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.functional_pair_release import release

OUT=Path(__file__).parent;BUNDLE=OUT/'delegated-candidate-v3'
release.BASE_IMAGES={'gateway':'sha256:a6fe1d61982db84447f45eb35a56809ae4ab16d854012bec59db1f58d890b2be',
                     'core':'sha256:91afae9c6855417dcc14828d0bd16b3a5b780439d7d1fbbfede64c64241d83d4'}
release.SOURCES.update({'openproject/ai/gateway/'+name:('gateway','/app/gateway/'+name) for name in ('delegated_approval.py','permissions.py','engineering_reporting.py','catalog.py')})
release.SOURCES['openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_delegated.html.erb']=('core','/app/app/views/qldapm_ai/_engineering_delegated.html.erb')

def configured(before):
    path=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final/delegated-main-registry.json'
    registry=json.loads(path.read_text());after=copy.deepcopy(before)
    assert registry['project_id']==6 and registry['authority']=='Owner spec 2de7a2a7'
    after['delegated_demo']=registry['policy'];return after
release.next_config=configured

if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare':result=release.prepare(BUNDLE)
    elif action=='build':result=release.build(BUNDLE)
    elif action=='rollout':result=release.rollout(BUNDLE,OUT/'delegated-qualification.json')
    else:raise ValueError('UNKNOWN_ACTION')
    print(json.dumps({k:result[k] for k in ('state','status','images') if k in result}))

"""Exact-source local Studio patch using the established guarded image release."""
import copy,json,sys
from pathlib import Path

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[1]
sys.path.insert(0,str(REPO/'openproject/ai'))
from automation import integration_pair_release as release
from automation import telegram_rollout as observer

paths=[
 'app/controllers/qldapm_ai_controller.rb',
 'app/views/qldapm_ai/observer.html.erb',
 'app/views/qldapm_ai/_engineering_command_center.html.erb',
 *['public/qldapm-agent-studio-v2/'+name for name in ['studio.js','studio.css','studio.js.LEGAL.txt','manifest.json']],
]
baseline=json.loads((OUT/(sys.argv[3] if len(sys.argv)>3 else 'baseline.json')).read_text(encoding='utf-8'))
release.BASE_IMAGES={r:baseline['containers'][r]['image'] for r in ('gateway','core')}
release.SOURCES={'openproject/ai/core/overlay/'+p:('core','/app/'+p) for p in paths}
release.next_config=copy.deepcopy
def qualified(proof,files):
    assert proof['status']=='PASS' and proof['source_hashes']==files
    assert proof['checks']=={'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True}
release.qualified=qualified

if __name__=='__main__':
    action=sys.argv[1];bundle=OUT/(sys.argv[2] if len(sys.argv)>2 else 'candidate')
    if action=='prepare':
        result=release.prepare(bundle)
        result['policy']={'configuration':'UNCHANGED','telegram':'UNCHANGED','n8n':'UNCHANGED','completion_gates':'UNCHANGED'}
        release.write_json(bundle/'manifest.json',result)
    elif action=='build':
        result=release.build(bundle)
        # There is no Gateway source in this patch; retain its exact immutable image.
        result['images']['gateway']=release.BASE_IMAGES['gateway']
        release.write_json(bundle/'manifest.json',result)
    elif action=='rollout':
        result=release.rollout(bundle,OUT/'qualification.json')
        result.pop('github_sync_enabled',None);result.pop('n8n_integration_enabled',None)
        result['configuration_policy']='UNCHANGED_EXACT_HASH'
        release.write_json(bundle/'deployment.json',result)
    elif action=='verify':
        deployed=json.loads((bundle/'deployment.json').read_text())
        hashes=release.runtime_hashes('core');state=observer.protected_state()
        result={'status':'PASS','source_parity':hashes==deployed['source_hashes'],'protected_state_unchanged':state==baseline['protected_state'],
                'images':{r:release.inspect(r)['Image'] for r in release.TARGETS},'gateway_image_unchanged':release.inspect('gateway')['Image']==release.BASE_IMAGES['gateway']}
        assert all(result[k] for k in ('source_parity','protected_state_unchanged','gateway_image_unchanged'))
        observer.save(OUT/'verification.json',result)
    else:raise ValueError('unknown action')
    print(json.dumps({k:v for k,v in result.items() if k in {'state','status','images','source_parity','protected_state_unchanged','gateway_image_unchanged'}}))

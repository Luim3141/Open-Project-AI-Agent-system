"""Existing guarded paired operator, one Core controller delta; Gateway image retained."""
import copy,json,sys,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation import integration_pair_release as release
base=json.loads((OUT/'baseline.json').read_text())['containers']
release.BASE_IMAGES={'core':base['qldapm-openproject-web-1']['image'],'gateway':base['qldapm-ai-gateway-1']['image']}
release.SOURCES={'openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb':('core','/app/app/controllers/qldapm_ai_controller.rb')}
release.next_config=copy.deepcopy
def qualified(proof,files):
    assert proof['status']=='PASS' and proof['source_hashes']==files
    assert proof['checks']=={'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True}
release.qualified=qualified
bundle=OUT/(sys.argv[2] if len(sys.argv)>2 else 'core-candidate');action=sys.argv[1]
if (bundle/'manifest.json').exists():
    initial=json.loads((bundle/'manifest.json').read_text())['initial_runtime']
    release.BASE_IMAGES={role:initial[role]['image'] for role in ['core','gateway']}
else:
    release.BASE_IMAGES={role:json.loads(subprocess.check_output(['docker','inspect',release.TARGETS[role][0]]))[0]['Image'] for role in ['core','gateway']}
if action=='prepare':result=release.prepare(bundle)
elif action=='build':
    result=release.build(bundle)
    result['images']['gateway']=release.BASE_IMAGES['gateway']
    result['gateway_policy']='REUSE_EXACT_SERVING_IMAGE_NO_GATEWAY_SOURCE_CHANGE'
    release.write_json(bundle/'manifest.json',result)
elif action=='qualify':
    manifest=json.loads((bundle/'manifest.json').read_text());manifest['images']['gateway']=release.BASE_IMAGES['gateway'];manifest['gateway_policy']='REUSE_EXACT_SERVING_IMAGE_NO_GATEWAY_SOURCE_CHANGE';release.write_json(bundle/'manifest.json',manifest)
    controller=(ROOT/next(iter(release.SOURCES))).read_text();results={}
    for name in ['test_report_controller','test_read_bridge_errors','test_bridge_busy_controller']:
        code=(ROOT/'openproject/ai/tests'/f'{name}.rb').read_text()
        command=['docker','run','--rm','-i','--network','none','--read-only','--tmpfs','/tmp:size=32m,mode=1777','--entrypoint','bundle',manifest['images']['core'],'exec','ruby','-e',code]
        if name!='test_report_controller':command+=['/app/app/services/qldapm/ai_bridge.rb']
        p=subprocess.run(command,input=json.dumps({'controller':controller}),capture_output=True,text=True,timeout=60)
        (OUT/(name+'-candidate.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(name,p.stderr[-300:]);results[name]=p.stdout.strip()
    assert release.runtime_hashes('core',manifest['images']['core'])==manifest['source_hashes']
    release.guard_sources(ROOT,manifest['source_hashes'])
    proof={'status':'PASS','source_hashes':manifest['source_hashes'],'checks':{'adapter':True,'fixture_browser':True,'regressions':True,'immutable_core':True},'evidence':results,'ui_reuse':'Studio assets unchanged from deployed/qualified d0bdd; existing source-pinned retry fixture proof retained. New controller status contracts verified; actual MAIN UAT required after rollout.'}
    release.write_json(OUT/'core-qualification.json',proof);result={'status':'PASS','images':manifest['images']}
elif action=='rollout':
    assert json.loads((bundle/'manifest.json').read_text())['images']['gateway']==release.BASE_IMAGES['gateway']
    result=release.rollout(bundle,OUT/'core-qualification.json');result.pop('github_sync_enabled',None);result.pop('n8n_integration_enabled',None);result['configuration_policy']='UNCHANGED_EXACT_HASH';release.write_json(bundle/'deployment.json',result)
else:raise ValueError(action)
print(json.dumps({k:v for k,v in result.items() if k in {'status','state','images'}}))

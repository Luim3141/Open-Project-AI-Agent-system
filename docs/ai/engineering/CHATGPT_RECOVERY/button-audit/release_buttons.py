"""Existing pair release with schedule conflict and reader loading fixes."""
import copy,json,sys
from pathlib import Path
OUT=Path(__file__).parent
sys.path.insert(0,str(OUT.parent/'cc-stabilization'))
import release_caption as previous
release=previous.release
BUNDLE=OUT/'candidate-v10'
release.BASE_IMAGES={'gateway':'sha256:9e1d53e6d1d1894e50db3bb22d8ff7fbb6a45d1bde3473437a831e9fe3b5257b','core':'sha256:5ee7a24482be81dd7312e8c4560773aede32ec9f8bc2f6da9593c9f223e1b822'}
release.SOURCES['openproject/ai/gateway/catalog.py']=('gateway','/app/gateway/catalog.py')
release.SOURCES['openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_workforce.html.erb']=('core','/app/app/views/qldapm_ai/_engineering_workforce.html.erb')
release.next_config=lambda before:copy.deepcopy(before)
def dockerfile(role,image,nonce):
    text='FROM '+release.base_tag(image,nonce)+'\n'
    names=['gateway/engineering_reporting.py','gateway/catalog.py','gateway/service.py','gateway/engineering.py','gateway/engineering_lifecycle.py'] if role=='gateway' else ['core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb','core/overlay/app/views/qldapm_ai/_engineering_report_reader.html.erb','core/overlay/app/services/qldapm/ai_bridge.rb','core/overlay/app/controllers/qldapm_ai_controller.rb','core/overlay/app/views/qldapm_ai/_engineering_workforce.html.erb','core/overlay/app/views/qldapm_ai/_engineering_work_list.html.erb']
    for name in names:
        text+='COPY --chown='+('10001:10001' if role=='gateway' else 'app:app')+' '+name+' '+release.SOURCES['openproject/ai/'+name][1]+'\n'
    return text
release.dockerfile=dockerfile
def serving_core(previous,files):
    proof=json.loads((OUT/'core-reuse-proof.json').read_text())
    image=release.BASE_IMAGES['core']
    expected={k:v for k,v in files.items() if release.SOURCES[k][0]=='core'}
    assert proof['status']=='PASS' and proof['core']['status']=='PASS' and proof['images']['core']==image
    assert {k:v for k,v in proof['source_hashes'].items() if release.SOURCES[k][0]=='core'}==expected
    assert release.runtime_hashes('core',image)==expected
    return image
release.reuse_core=serving_core
if __name__=='__main__':
    action=sys.argv[1]
    result=release.prepare(BUNDLE) if action=='prepare' else release.build(BUNDLE,OUT/'candidate-v9') if action=='build' else release.rollout(BUNDLE,OUT/'qualification.json') if action=='rollout' else None
    assert result is not None
    print(json.dumps({k:result[k] for k in ('state','status','images') if k in result}))

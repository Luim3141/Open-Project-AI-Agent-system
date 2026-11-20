"""Native/AI full-navigation boundary over the qualified report/caption release."""
import json,sys
from pathlib import Path
import release_reports as setup
release=setup.release;OUT=Path(__file__).parent;BUNDLE=OUT/'candidate-v12'
release.BASE_IMAGES={'gateway':'sha256:698224aa0ddc88808ebab30b4705dfe7050b09db67b8ae3fc4a569d6a8447e1c','core':'sha256:5e5cb9fb31d7b3d9beb46dda80b3c53361e2cd3adb495ee100ac14d78c542eb4'}
release.SOURCES['openproject/ai/core/overlay/config/initializers/qldapm_gates.rb']=('core','/app/config/initializers/qldapm_gates.rb')
def dockerfile(role,image,nonce):
    text='FROM '+release.base_tag(image,nonce)+'\n'
    if role=='core':
        for path in ['core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb','core/overlay/config/initializers/qldapm_gates.rb']:
            text+='COPY --chown=app:app '+path+' '+release.SOURCES['openproject/ai/'+path][1]+'\n'
    return text
release.dockerfile=dockerfile
def build():
    manifest=release.build(BUNDLE)
    expected={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]=='gateway'}
    assert release.runtime_hashes('gateway',release.BASE_IMAGES['gateway'])==expected
    manifest['images']['gateway']=release.BASE_IMAGES['gateway'];manifest['gateway_reused_unchanged']=True
    release.write_json(BUNDLE/'manifest.json',manifest);return manifest
if __name__=='__main__':
    action=sys.argv[1]
    result=release.prepare(BUNDLE) if action=='prepare' else build() if action=='build' else release.rollout(BUNDLE,OUT/'qualification-caption.json') if action=='rollout' else None
    assert result is not None
    print(json.dumps({k:result[k] for k in ('state','status','images') if k in result}))

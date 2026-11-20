"""Final Report Reader and request-scoped sync-ACK follow-up."""
import json,sys
from pathlib import Path
import release_polish as setup
release=setup.release;OUT=Path(__file__).parent;BUNDLE=OUT/'candidate-v10'
release.BASE_IMAGES={'gateway':'sha256:8a86413762dcf09615f673dae2ad9a37d0c631f67fb2b09d7aa05f31c6c08199','core':'sha256:3fd0c48a54585d63bbe49a89ab712f4162dbae5388f17159143cf7449a63680a'}
helper='openproject/ai/core/overlay/app/helpers/qldapm_report_reader_helper.rb'
release.SOURCES[helper]=('core','/app/app/helpers/qldapm_report_reader_helper.rb')
def dockerfile(role,image,nonce):
    text='FROM '+release.base_tag(image,nonce)+'\n'
    if role=='core':
        for path in [helper,'openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_report_reader.html.erb']:
            text+='COPY --chown=app:app '+path.removeprefix('openproject/ai/')+' '+release.SOURCES[path][1]+'\n'
    else:
        for name in ['engineering.py','service.py','engineering_github_operations.py','engineering_github_poll.py','engineering_status_sync.py']:
            text+='COPY --chown=10001:10001 gateway/'+name+' /app/gateway/'+name+'\n'
    return text
release.dockerfile=dockerfile
if __name__=='__main__':
    action=sys.argv[1]
    result=release.prepare(BUNDLE) if action=='prepare' else release.build(BUNDLE,reuse_core_bundle=OUT/'candidate-v9') if action=='build' else release.rollout(BUNDLE,OUT/'qualification-reports.json') if action=='rollout' else None
    assert result is not None
    print(json.dumps({k:result[k] for k in ('state','status','images') if k in result}))

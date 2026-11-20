"""Follow-up for Report Reader, Turbo restoration and bounded summary reads."""
import copy,json,sys
from pathlib import Path
import release_cc as setup
release=setup.release;OUT=Path(__file__).parent;BUNDLE=OUT/'candidate-v6'
release.BASE_IMAGES={'gateway':'sha256:016115071c25fc3f1aa0c595e8add80228df5d47c92807dc35537fef8780ec28','core':'sha256:06aeb74a42763aa0026b5ee55538ee36da62fc51db5db64948ff638356dfc880'}
release.SOURCES.update({'openproject/ai/core/overlay/'+path:('core','/app/'+path) for path in ('app/views/qldapm_ai/_engineering_report_reader.html.erb','app/services/qldapm/ai_bridge.rb')})
release.next_config=lambda before:copy.deepcopy(before)
if __name__=='__main__':
    action=sys.argv[1]
    result=release.prepare(BUNDLE) if action=='prepare' else release.build(BUNDLE) if action=='build' else release.rollout(BUNDLE,OUT/'qualification-polish.json') if action=='rollout' else None
    assert result is not None
    print(json.dumps({k:result[k] for k in ('state','status','images') if k in result}))

"""Existing exact-source release guard, unchanged Core and no configuration changes."""
import copy
import json
import sys
from pathlib import Path

OUT=Path(__file__).parent
sys.path.insert(0,str(OUT.parent/'button-audit'))
import release_buttons as previous
release=previous.release
release.BASE_IMAGES={'gateway':'sha256:77213702ef933943a1fbee6feffc0d410062b8f16928dd3d1621f9489e581a12',
                     'core':'sha256:5ee7a24482be81dd7312e8c4560773aede32ec9f8bc2f6da9593c9f223e1b822'}
for name in ['engineering_planning.py','engineering_auto.py']:
    release.SOURCES['openproject/ai/gateway/'+name]=('gateway','/app/gateway/'+name)
release.next_config=lambda before:copy.deepcopy(before)
BUNDLE=OUT/'candidate-v1'

def dockerfile(role,image,nonce):
    lines=['FROM '+release.base_tag(image,nonce)]
    if role=='gateway':
        for name in ['engineering.py','engineering_operator.py','engineering_planning.py','engineering_auto.py']:
            lines.append('COPY --chown=10001:10001 gateway/'+name+' /app/gateway/'+name)
    return '\n'.join(lines)+'\n'

release.dockerfile=dockerfile
if __name__=='__main__':
    action=sys.argv[1]
    result=(release.prepare(BUNDLE) if action=='prepare' else
            release.build(BUNDLE,OUT.parent/'button-audit/candidate-v10') if action=='build' else
            release.rollout(BUNDLE,OUT/'qualification.json') if action=='rollout' else None)
    assert result is not None
    print(json.dumps({k:result[k] for k in ['state','status','images'] if k in result}))

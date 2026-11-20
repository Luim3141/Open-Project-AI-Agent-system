"""Exact affected-source image pair; preserve PAUSED, integrations and delegation OFF."""
import copy,json,sys
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.resolve().parents[4];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation import integration_pair_release as release
BUNDLE=OUT/'candidate-v5'
release.BASE_IMAGES={'gateway':'sha256:f91c98823b42cb2d9499de1a8d3e3935fd59a594b6b92b3f9a4bd4cf2dc0087c','core':'sha256:1f1b366abc88c20794992ee2df9a7227417fc3a770ca4b8abdb1e34becd82db8'}
release.SOURCES={'openproject/ai/gateway/'+name:('gateway','/app/gateway/'+name) for name in (
    'store.py','service.py','engineering.py','engineering_operator.py','engineering_lifecycle.py','engineering_health.py',
    'engineering_observability.py','engineering_owner_control.py','engineering_reporting.py','workflow_status.py','delegated_approval.py',
    'engineering_github_sync.py','engineering_github_operations.py','engineering_github_poll.py','engineering_status_sync.py')}
release.SOURCES.update({'openproject/ai/core/overlay/'+path:('core','/app/'+path) for path in (
    'app/controllers/qldapm_ai_controller.rb','app/views/qldapm_ai/_engineering_command_center.html.erb',
    'app/views/qldapm_ai/_engineering_notifications.html.erb','app/views/qldapm_ai/_engineering_work_list.html.erb')})

def queue():
    code="import json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':d.execute(\"SELECT count(*) FROM ai_queue WHERE state!='finished'\").fetchone()[0],'mode':d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],'delegation':d.execute('SELECT enabled FROM delegated_control WHERE project=6').fetchone()[0]}))"
    state=json.loads(release.run(['docker','exec',release.TARGETS['gateway'][0],'python','-c',code]))
    assert state=={'active':0,'mode':'PAUSED','delegation':0},'CC_RELEASE_REQUIRES_OWNER_PAUSED_IDLE_DELEGATION_OFF'
    return state

def configured(before):
    after=copy.deepcopy(before);policy=json.loads((OUT/'status-sync-policy-draft.json').read_text())
    # Activation follows post-rollout readback; background writes remain disabled during rollout.
    after.setdefault('engineering',{})['status_sync']={**policy,'enabled':False}
    return after
release.queue=queue;release.next_config=configured
if __name__=='__main__':
    action=sys.argv[1]
    result=release.prepare(BUNDLE) if action=='prepare' else release.build(BUNDLE) if action=='build' else release.rollout(BUNDLE,OUT/'qualification.json') if action=='rollout' else None
    assert result is not None
    print(json.dumps({k:result[k] for k in ('state','status','images') if k in result}))

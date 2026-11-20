"""Read-only Native form preflight on Main; grant missing permission only in the owned clone."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from inspect_runtime import ROOT, OUT, run
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.native import Native
from jira_sync_backup import database_state

def main():
    q=json.loads((OUT/'qualification.json').read_text());private=Path(q['private'])
    state=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway'
    creds=json.loads((state/'credentials.json').read_text());config=json.loads((state/'config.json').read_text())
    before=database_state('qldapm-openproject-db-1');native=Native('http://localhost:8088',creds['19'],5)
    payload={'subject':'test',config['source_field']:'write403-preflight-not-created','description':{'format':'markdown','raw':''},
             '_links':{k:{'href':v} for k,v in {'project':'/api/v3/projects/5','type':'/api/v3/types/10',
                                               'parent':'/api/v3/work_packages/50','assignee':'/api/v3/users/23'}.items()}}
    form=native.call('/api/v3/projects/5/work_packages/form','POST',payload)
    memberships=run('docker','exec','qldapm-openproject-db-1','psql','-X','-U','postgres','-d','openproject','-qAtc',
        "BEGIN READ ONLY; SELECT json_build_object('user',m.user_id,'project',m.project_id,'role',mr.role_id) FROM members m JOIN member_roles mr ON m.id=mr.member_id WHERE mr.role_id=22; COMMIT;")
    after=database_state('qldapm-openproject-db-1')
    protected=('work_packages','relations','sprints','versions','members','member_roles','role_permissions')
    assert all(before[t]==after[t] for t in protected)
    result={'main_native_form_errors':form.get('_embedded',{}).get('validationErrors',{}),
            'role22_memberships':[json.loads(s) for s in memberships.splitlines() if s.startswith('{')],
            'main_protected_unchanged':True,'native_business_mutations':0}
    assert result['main_native_form_errors'].get('parent',{}).get('errorIdentifier','').endswith('PropertyIsReadOnly')
    (OUT/'native-permission-before.json').write_text(json.dumps(result,indent=2))
    code='''require 'json'
raise 'WRONG_TARGET' unless ENV['OPENPROJECT_HOST__NAME']=='localhost:18098'
r=Role.find(22);raise 'WRONG_ROLE' unless r.name=='QLDAPM PM'
before=r.permissions.map(&:to_s);raise 'ALREADY_PRESENT' if before.include?('manage_subtasks')
r.permissions=(before+['manage_subtasks']).map(&:to_sym);r.save!
raise 'WRONG_DIFF' unless (r.reload.permissions.map(&:to_s)-before)==['manage_subtasks']
puts JSON.generate({role:22,permission_added:'manage_subtasks',target:'ISOLATED_CLONE_ONLY',passed:true})
'''
    p=subprocess.run(['docker','exec','-i',q['names']['core'],'bundle','exec','rails','runner','-'],input=code.encode(),capture_output=True,timeout=120)
    assert p.returncode==0,'CLONE_ROLE_CHANGE_FAILED_OUTPUT_WITHHELD'
    lines=[s for s in p.stdout.decode().splitlines() if s.startswith('{')]
    result['clone_permission_change']=json.loads(lines[-1]);(OUT/'native-permission-before.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

if __name__=='__main__':main()

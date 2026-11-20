"""Actual Native clone, existing fixture #369; only GET, no Google, no new work package."""
import json,time
from pathlib import Path
from unittest.mock import patch
from gateway.store import Store
from gateway.service import Service
from gateway.native import Native
from gateway.business_runs import register,link_command,resume
root=Path('/state');store=Store(root);service=Service(store,json.loads((root/'config.json').read_text()),'/tmp/workspaces')
native,who=service.native_actor(25);before=native.packages();item=native.package(369)
assert who['role']=='PM' and item['_links']['author']['href']=='/api/v3/users/25'
args={'source_id':item[service.config['source_field']],'subject':item['subject'],'type_id':10,
      'parent_id':50,'assignee_id':23,'description':item['description']['raw']}
identifier=store.create_run(25);key='ai-'+identifier+'-1'
register(store,25,5,identifier,{'prompt':'Existing isolated clone fixture #369, lost response simulation; no CREATE.'})
link_command(service,25,identifier,key);store.begin(25,key,{'action':'create_work_package','arguments':args})
store.finish_run(25,identifier,{'tools':[{'action':'create_work_package','arguments':args,'result':{'error':'NativeError','outcome_unknown':True}}],
    'error':'SIMULATED_LOST_HTTP_RESPONSE_AFTER_COMMIT'},'failed_or_unknown')
methods=[];original=Native.call
def read_only(self,path,method='GET',payload=None):
    assert method=='GET','RECOVERY_NATIVE_WRITE_FORBIDDEN';methods.append([method,path.split('?')[0]])
    return original(self,path,method,payload)
with patch.object(Native,'call',read_only):
    resume(service)
    view=service.execute_actor(25,{'action':'get_ai_run','arguments':{'id':identifier}})['result']
    monitor=service.execute_actor(25,{'action':'get_execution_monitor','arguments':{'id':identifier}})['result']
assert view['state']=='reconciled_success' and view['result']['completion']['native']=='RECONCILED_SUCCESS'
assert view['worker_state']=='failed_or_unknown' and view['result']['synthesis_origin']=='SYSTEM'
assert monitor['state']=='RECONCILED_SUCCESS' and monitor['terminal']
native.deadline=time.monotonic()+90;after=native.packages();assert len(after)==len(before)
out={'passed':True,'provider':'OFFLINE_NO_GOOGLE','native':'REAL_ISOLATED_CLONE','fixture':369,'run_id':identifier,
 'native_mutations':0,'count_before':len(before),'count_after':len(after),'read_calls':methods,'state':view['state'],
 'worker_state':view['worker_state'],'completion':view['result']['completion'],'monitor_state':monitor['state']}
(root/'clone-proof.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

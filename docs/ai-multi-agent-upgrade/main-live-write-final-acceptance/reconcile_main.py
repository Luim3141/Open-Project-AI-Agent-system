"""Explicit operator recovery via Core signed bridge; Native GET only, no new AI/business write."""
import json,subprocess,time
from pathlib import Path
OUT=Path(__file__).parent
def main():
    assert not (OUT/'reconciliation.json').exists(),'RECONCILIATION_EXISTS_READ_RECEIPT_FIRST'
    assert json.loads((OUT/'deployment-recovery.json').read_text())['phase']=='RECOVERY_DEPLOYED_HEALTH_PARITY_PASS'
    code="""require 'json'
raise 'WRONG_MAIN_HOST' unless ENV['OPENPROJECT_HOST__NAME']=='localhost:8088'
project=Project.find(5);actor=User.find(19)
raise 'WRONG_PROJECT_ACTOR' unless project.identifier=='qldapm-local' && actor.login=='ba-pm' && !actor.admin?
key='owner-create-e3626ae0-ce29-4e52-bcb8-98793eeefce5'
receipt=Qldapm::AiBridge.call(project,actor,'command',{action:'reconcile_request',arguments:{key:key},idempotency_key:SecureRandom.uuid})
view=Qldapm::AiBridge.call(project,actor,'command',{action:'get_ai_run',arguments:{id:'6276720c-d6f8-4c3a-bf64-1e4fca623eb0'}})
raise 'RECOVERY_NOT_PROVED' unless receipt.dig('result','reconciled') && receipt.dig('result','result','id')==367
raise 'UI_RECEIPT_NOT_READY' unless view.dig('result','result','native_reconciled') && view.dig('result','result','status')=='partial'
puts JSON.generate({receipt:receipt,view:view})
"""
    p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner','-'],input=code.encode(),capture_output=True,timeout=150)
    assert p.returncode==0,'RECOVERY_BRIDGE_FAILED_RECONCILE_SQLITE_BEFORE_ANY_REPEAT'
    lines=[s for s in p.stdout.decode().splitlines() if s.startswith('{')];data=json.loads(lines[-1])
    summary={'route':'OPERATOR_CORE_SIGNED_BRIDGE_NATIVE_GET_ONLY','at':time.time(),'run_id':'6276720c-d6f8-4c3a-bf64-1e4fca623eb0',
        'id':367,'reconciled':True,'actor':19,'native_mutations':0,'google_calls':0,
        'request_key':'owner-create-e3626ae0-ce29-4e52-bcb8-98793eeefce5',
        'correlation_id':data['receipt']['result']['correlation_id'],'bridge_command_correlation':data['receipt']['correlation_id'],
        'worker_state_preserved':data['view']['result']['state'],'display':data['view']['result']['result']}
    (OUT/'reconciliation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='display'},ensure_ascii=False))
if __name__=='__main__':main()

"""One Owner-authorized two-request fixed-text Main probe. Never automatically rerun."""
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).parent
RESULT = OUT / 'main-minimal-smoke-result.json'

def main():
    assert not RESULT.exists(), 'PROBE_ALREADY_ATTEMPTED_RECONCILE_DO_NOT_RETRY'
    RESULT.write_text(json.dumps({'state': 'APPROVED_ATTEMPT_STARTING', 'approval': 'Owner replied with the fixed prompt to the bounded smoke approval question'}))
    program = r'''
import json,time
from pathlib import Path
from gateway.gemini import Gemini,ProviderError,SMOKE_PROMPT
from gateway.store import Store,canonical,digest
g=Gemini(Path('/state')); phases=[]
result={'scope':'MAIN_FIXED_PUBLIC_TEXT_ONLY','at':time.time(),'provider_phases':phases,'business_writes':0,'retries':0,'passed':False}
try:
 p=g.settings()
 assert p['model']=='gemini-3.5-flash-lite' and p['project']=='gen-lang-client-0020540057' and p['billing_enabled'] is False
 assert not Store(g.root).provider_wait(p),'PROVIDER_GUARD_BLOCKED_NO_NETWORK'
 result['guard']='PASS'
 original=g.sdk_post
 def bounded(client,policy,phase,payload):
  assert phase==('countTokens','generateContent')[len(phases)] and len(phases)<2,'REQUEST_BUDGET_EXCEEDED'
  phases.append(phase)
  return original(client,policy,phase,payload)
 g.sdk_post=bounded
 reply=g.smoke(SMOKE_PROMPT,p)
 assert reply['text']=='QLDAPM_OK' and reply['tools']==[]
 result.update(passed=True,text=reply['text'],model=reply['model'],usage=reply['usage'])
 # This is a fresh real probe receipt, not a receipt copied from another environment.
 receipt={'passed':True,'checked_at':time.time(),'policy_sha256':digest(canonical(p)),'key_sha256':p['key_sha256'],'model':p['model']}
 path=g.root/'gemini-readiness.json'
 assert not path.exists(),'EXISTING_READINESS_REQUIRES_RECONCILIATION'
 path.write_text(canonical(receipt))
 result['readiness']=g.readiness(p)
except ProviderError as error:
 result['error']=str(error)
except Exception as error:
 result['error_type']=type(error).__name__
print(json.dumps(result))
'''
    try:
        command = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'], input=program.encode(), capture_output=True, timeout=90)
        assert command.returncode == 0, 'PROBE_EXECUTION_ERROR_OUTPUT_WITHHELD_NO_RETRY'
        result = json.loads(command.stdout)
    except Exception as error:
        result = {'passed': False, 'state': 'INDETERMINATE_DO_NOT_RETRY', 'error_type': type(error).__name__}
    RESULT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()

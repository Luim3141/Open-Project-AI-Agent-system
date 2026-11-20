"""Prepare approved production-target Free-only enrollment; no provider/DB/network calls."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'openproject/ai'))
from free_tier_staging import private_directory
from gateway.gemini import Gemini

def main():
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
    stage=runtime/'stage-ai'
    proof=runtime/'operator/gemini-free/free-tier-proof.json'
    os.environ['QLDAPM_AI_ENVIRONMENT']='staging'
    os.environ['QLDAPM_GEMINI_FREE_PROOF']=str(proof)
    current=Gemini(stage).settings(require_enabled=False)
    assert current['quota']=={'rpm':15,'tpm':250000,'rpd':500},'QUOTA_DIFFERS_RECONCILE'
    assert current['data_scope']=='project-business-content'
    assert Gemini.continuous_authorized(current),'CONTINUOUS_FREE_CONSENT_REQUIRED'
    target=runtime/'operator/codex-main-completion/provider-candidate'
    assert not target.exists(),'PREPARED_ALREADY_RECONCILE'
    private_directory(target)
    approval='Owner 20261020: Duyệt cả hai, chưa gọi Google. AI_CREDENTIAL_READINESS_PREVIEW.md; Main uses existing key/model/Free Tier with separate config and usage.'
    fingerprint=hashlib.sha256(approval.encode()).hexdigest()
    policy=json.loads(proof.read_text())
    policy['target_environment']='production'
    policy['authorization']={**policy['authorization'],'authorized_at':time.time(),'user_request_sha256':fingerprint}
    policy['business_content_authorization']={'authorized_at':time.time(),'user_request_sha256':fingerprint}
    policy['evidence_reference']=str(policy['evidence_reference'])+'; Owner-approved Main enrollment 20261020, no fresh billing-console verification'
    state=json.loads((stage/'gemini.json').read_text())
    assert state['model']==policy['model']
    (target/'gemini.key').write_bytes((stage/'gemini.key').read_bytes())
    (target/'gemini.json').write_text(json.dumps(state,indent=2))
    (target/'free-tier-proof.json').write_text(json.dumps(policy,indent=2))
    os.environ['QLDAPM_AI_ENVIRONMENT']='production'
    os.environ['QLDAPM_GEMINI_FREE_PROOF']=str(target/'free-tier-proof.json')
    validated=Gemini(target).settings(require_enabled=False)
    assert validated['model']==current['model'] and validated['limits']==current['limits']
    assert (target/'gemini.key').read_bytes()==(stage/'gemini.key').read_bytes()
    receipt={'prepared':True,'installed':False,'private_directory':str(target),'model':validated['model'],
             'provider_policy':'FREE_ONLY','quotas':validated['quota'],'limits':validated['limits'],
             'same_key_bytes':True,'billing_changed':False,'fresh_console_verification':False,'provider_calls':0,
             'readiness_receipt_copied':False,'usage_copied':False,'owner_approval_sha256':fingerprint}
    (Path(__file__).parent/'provider-candidate.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()

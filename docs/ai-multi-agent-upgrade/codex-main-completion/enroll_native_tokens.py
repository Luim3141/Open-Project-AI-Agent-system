"""Execute the explicitly approved three Main token creations and verify native identities."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'openproject/ai'))
from free_tier_staging import private_directory,save
from gateway.native import Native

def docker(*args,data=None):
    p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=180)
    assert p.returncode==0,'TOKEN_ENROLLMENT_FAILED_OUTPUT_WITHHELD_RECONCILE_BEFORE_RETRY'
    return p.stdout

def main():
    out=Path(__file__).parent
    assert json.loads((out/'token-clone-qualification.json').read_text())['passed']
    runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
    state=runtime/'gateway';path=state/'credentials.json'
    previous=json.loads(path.read_text());config=json.loads((state/'config.json').read_text())
    assert config['project_id']==5 and all(config['users'][str(a)]==r for a,r in [(21,'BE'),(22,'FE'),(23,'QA')])
    assert all(str(a) not in previous for a in (21,22,23)),'ALREADY_REGISTERED_DO_NOT_REISSUE'
    private=runtime/'operator/codex-main-completion/native-enrollment'
    assert not private.exists(),'ENROLLMENT_EXISTS_RESUME_REQUIRED'
    private_directory(private)
    (private/'previous-credentials.json').write_bytes(path.read_bytes())
    info=json.loads(docker('inspect','qldapm-openproject-web-1'))[0]
    assert info['Config']['Labels']['com.docker.compose.project']=='qldapm-openproject'
    source=(REPO/'openproject/ai/core/enroll_main_agent_tokens.rb').read_bytes()
    output=docker('exec','-i','-e','QLDAPM_TOKEN_ENROLLMENT_TARGET=main-owner-approved-20261020','qldapm-openproject-web-1',
                  'bundle','exec','rails','runner','-',data=source)
    receipt=json.loads(output.decode().strip().splitlines()[-1])
    assert [r['user_id'] for r in receipt['created']]==[21,22,23]
    (private/'native-service-receipt.json').write_text(json.dumps(receipt,indent=2))
    tokens={};identities=[]
    for actor,role in [(21,'BE'),(22,'FE'),(23,'QA')]:
        source_file=f'/tmp/qldapm-approved-token-enrollment-20261020/user-{actor}.api-token'
        token=docker('exec','qldapm-openproject-web-1','ruby','-e','STDOUT.write(File.binread(ARGV.fetch(0)))',source_file).decode().strip()
        assert re.fullmatch(r'opapi-[a-f0-9]{64}',token),'INVALID_TOKEN_SHAPE'
        (private/f'user-{actor}.api-token').write_text(token)
        native=Native('http://127.0.0.1:8088',token,5)
        who=native.identity(actor)
        assert who['role']==role
        tokens[str(actor)]=token;identities.append({k:who[k] for k in ('user_id','role','project_id')})
    assert json.loads(path.read_text())==previous,'CREDENTIALS_CHANGED_CONCURRENTLY'
    save(path,json.dumps({**previous,**tokens},sort_keys=True))
    assert all(json.loads(path.read_text())[k]==v for k,v in previous.items())
    result={**receipt,'native_identities':identities,'previous_credential_actors_preserved':sorted(previous),
            'registered_actors':[21,22,23],'provider_calls':0,'passwords_or_totp_changed':False}
    (out/'native-enrollment-result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

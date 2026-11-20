"""Run the existing fixed signed status workflow with new synthetic credentials on an owned CLI clone."""
import json
import secrets
import subprocess
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.qualify_remaining import PRIVATE,OUT,LABEL,docker,snapshot,AI
from gateway.automation import signing_key


def main():
    name='qldapm-rd-n8n-20261018';root=PRIVATE/'n8n-qualification'
    assert not root.exists(),'EXISTING_N8N_QUALIFICATION_DO_NOT_OVERWRITE'
    root.mkdir();(root/'data').mkdir();key=secrets.token_hex(32)
    path=PRIVATE/'state/automation.key'
    with path.open('x') as stream:stream.write(key)
    creds=[{'id':'qldapmMachineStatus','name':'QLDAPM Gateway status read only','type':'httpHeaderAuth',
        'data':{'name':'X-QLDAPM-Machine-Key','value':key}},
        {'id':'qldapmCommandHmac','name':'QLDAPM status command HMAC','type':'crypto','data':{'hmacSecret':signing_key(key)}}]
    (root/'credentials.json').write_text(json.dumps(creds))
    image=docker('inspect','qldapm-ai-stage-n8n-1','--format','{{.Image}}')
    before=snapshot()
    docker('run','-d','--name',name,'--label',LABEL,'--network','qldapm-rd-20261018',
        '--memory','512m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '--mount','type=bind,src='+str(root/'data')+',dst=/home/node/.n8n',
        '--mount','type=bind,src='+str(root)+',dst=/qa,readonly',
        '--mount','type=bind,src='+str(AI/'automation/workflows/manual-status.v2.json')+',dst=/workflow.json,readonly',
        '-e','N8N_DIAGNOSTICS_ENABLED=false','-e','N8N_VERSION_NOTIFICATIONS_ENABLED=false',
        '-e','N8N_COMMUNITY_PACKAGES_ENABLED=false','-e','N8N_RUNNERS_ENABLED=false',
        '--entrypoint','sleep',image,'infinity')
    results=[]
    for args in [('import:credentials','--input=/qa/credentials.json'),('import:workflow','--input=/workflow.json'),
                 ('execute','--id=qldapmManualStatus')]:
        proc=subprocess.run(['docker','exec',name,'n8n',*args],capture_output=True,timeout=150)
        (root/(args[0].replace(':','-')+'.log')).write_bytes(proc.stdout+proc.stderr)
        results.append({'command':args[0],'exit_code':proc.returncode})
        if proc.returncode:break
    assert snapshot()==before,'SERVING_CONTAINER_DRIFT'
    report={'scope':'ISOLATED_N8N_SYNTHETIC_CREDENTIALS','image':image,'steps':results,
        'serving_changes':0,'provider_calls':0,'passed':len(results)==3 and all(r['exit_code']==0 for r in results)}
    if report['passed']:
        text=(root/'execute.log').read_text();execution=None
        for pos,char in enumerate(text):
            if char!='{':continue
            try:value,_=json.JSONDecoder().raw_decode(text[pos:])
            except ValueError:continue
            if isinstance(value,dict) and value.get('finished') is True and value.get('status')=='success':
                execution=value;break
        assert execution is not None,'N8N_WORKFLOW_NOT_FINISHED'
        receipt=execution['data']['resultData']['runData']['Gateway status'][-1]['data']['main'][0][0]['json']['result']
        assert receipt['state']=='COMPLETED' and receipt['actor_id'] is None
        assert receipt['model_calls']==0 and receipt['native_write_allowed'] is False
        report['receipt']={k:receipt[k] for k in ('state','actor_id','model_calls','native_write_allowed','run_id')}
    (OUT/'n8n-qualification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())

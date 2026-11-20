"""One authorized MAIN principal/fixture setup. Never blind-replay a consumed intent."""
import datetime,hashlib,json,os,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
private.mkdir(parents=True,exist_ok=True);registry=private/'delegated-main-registry.json';intent=private/'main-setup-intent.json'
assert not registry.exists() and not intent.exists(),'MAIN_SETUP_EXISTS_RECONCILE_NO_BLIND_REPLAY'
proof=json.loads((OUT/'delegated-qualification.json').read_text());assert proof['status']=='PASS'
def run(*args,data=None,timeout=240):
    result=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
    if result.returncode:
        (private/'main-setup-failure.log').write_bytes(result.stdout+result.stderr);raise RuntimeError('MAIN_SETUP_FAILED_PRIVATE_DIAGNOSTIC_RECONCILE_INTENT')
    return result.stdout
state=json.loads(run('exec','qldapm-ai-gateway-1','python','-c',"import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':d.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0],'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0],'provider_receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0]}))"))
assert state['active']==0 and state['mode']=='OFF'
source=ROOT/'openproject/ai/core/enroll_delegated_demo.rb';marker='OWNER-DELEGATED-'+uuid.uuid4().hex[:12]
record={'authority':'Owner spec 2de7a2a7','owner_grant':'dd43ae4b5fb4646fa614e7d5d4ae166b127cf8e5fbd653b3382a4a1366c151c4','project_id':6,
        'marker':marker,'state':'PREPARED','before':state,'enrollment_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with intent.open('x') as stream:json.dump(record,stream,indent=2)
receipt=json.loads(run('exec','-i','-e','QLDAPM_DELEGATED_TARGET=main-demo-20261104','qldapm-openproject-web-1','bundle','exec','rails','runner','-',data=source.read_bytes()).decode().splitlines()[-1])
assert receipt['admin'] is False and receipt['project_ids']==[6] and receipt['protected_before']==receipt['protected_after']
secret=run('exec','qldapm-openproject-web-1','ruby','-e',"STDOUT.write(File.binread('/tmp/qldapm-owner-delegated-20261104/principal-secret.json'))")
with (private/'main-principal-secret.json').open('xb') as stream:stream.write(secret)
credentials=json.loads(secret);assert credentials['principal_id']==receipt['principal_id']
credential_path=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/credentials.json'
before=credential_path.read_bytes();(private/'credentials.before.json').write_bytes(before);keys=json.loads(before)
assert str(receipt['principal_id']) not in keys
keys[str(receipt['principal_id'])]=credentials['api_token'];temp=credential_path.with_name('credentials.delegated.tmp.json');temp.write_text(json.dumps(keys));temp.replace(credential_path)
record.update(state='PRINCIPAL_CREATED',principal_id=receipt['principal_id'],receipt=receipt);intent.write_text(json.dumps(record,indent=2)+'\n')
code=(ROOT/'openproject/ai/automation/delegated_demo_fixture.py').read_text()+"\nimport json\nfrom gateway.native import Native\nfrom gateway.store import Store\ns=Store('/state');c=json.load(open('/state/config.json'));actor="+str(receipt['principal_id'])+"\nn=Native(c['openproject_url'],s.credential(actor),6);created=create_fixture(n,actor,c['source_field'],"+repr(marker)+");print(json.dumps(created))\n"
fixture=json.loads(run('exec','-i','qldapm-ai-gateway-1','python','-',data=code.encode(),timeout=120))
body={'authority':'Owner spec 2de7a2a7','project_id':6,'policy':fixture['policy'],'fixture':fixture['fixture'],'principal':receipt}
with registry.open('x') as stream:json.dump(body,stream,indent=2)
record.update(state='VERIFIED_PRINCIPAL_AND_FIXTURE_CREATED',fixture=fixture['fixture']);intent.write_text(json.dumps(record,indent=2)+'\n')
public={**record,'credentials_output':'PRIVATE_ONLY','gateway_config_activated':False,'delegation_enabled':False}
(OUT/'main-principal-setup.json').write_text(json.dumps(public,indent=2)+'\n');print(json.dumps({k:public[k] for k in ('state','principal_id','fixture','delegation_enabled')}))

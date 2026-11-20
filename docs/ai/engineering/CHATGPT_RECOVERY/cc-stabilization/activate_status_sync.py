"""Explicit scoped activation after immutable rollout and actual Native preview."""
import copy,json,os,subprocess,time
from pathlib import Path
import release_cc as setup
OUT=Path(__file__).parent;release=setup.release
deployment=json.loads((setup.BUNDLE/'deployment.json').read_text())
assert deployment['status']=='DEPLOYED_SOURCE_AND_RELEASE_READBACK_VERIFIED'
for role in deployment['images']:
    assert release.inspect(role)['Image']==deployment['images'][role]
    assert release.runtime_hashes(role)=={k:v for k,v in deployment['source_hashes'].items() if release.SOURCES[k][0]==role}
setup.queue()
p=subprocess.run(['python',str(OUT/'native_dry_run.py')],capture_output=True,timeout=120);assert p.returncode==0,p.stderr.decode()[-500:]
preview=json.loads((OUT/'native-dry-run.json').read_text());assert len(preview['rows'])==5 and all(r['state']=='DRY_RUN' for r in preview['rows'])
path=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/config.json';before=json.loads(path.read_text())
assert before['engineering']['status_sync']['enabled'] is False and not before.get('maintenance')
after=copy.deepcopy(before);after['engineering']['status_sync']['enabled']=True
backup=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/cc-stabilization/status-sync-before-activation.json'
assert not backup.exists();backup.write_text(json.dumps(before))
temporary=path.with_suffix('.cc-activation.tmp');temporary.write_text(json.dumps(after,indent=2)+'\n');temporary.replace(path)
assert json.loads(path.read_text())['engineering']['status_sync']['enabled'] is True
result={'at':time.time(),'owner_grant':after['engineering']['status_sync']['owner_grant'],'principal_id':25,'project_id':6,'historical_native_ids':preview['rows'] and [r['native_id'] for r in preview['rows']],
    'enabled':True,'execution':'existing GitHub reconciliation worker; fresh form/version/Native readback; no coding scheduler','owner_mode':'PAUSED','delegation':'OFF','business_db_direct_writes':0}
(OUT/'status-sync-activation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

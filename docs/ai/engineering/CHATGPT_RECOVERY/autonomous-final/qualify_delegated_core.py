"""Reuse passed Native/n8n business evidence; verify unchanged Core routes independently."""
import ast,datetime,hashlib,json,os,sqlite3,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.main_native_clone import main_native_clone
OUT=Path(__file__).parent.parent/'integration-final/n8n';result_out=Path(__file__).parent
manifest=json.loads((result_out/'delegated-candidate-v3/manifest.json').read_text());core=manifest['images']['core']
business=json.loads((OUT/'autonomous-delegated-clone-result.json').read_text())
passed=next(r for r in business['checks'] if r['workflow']=='OWNER_DELEGATED_PROJECT6');assert passed['status']=='BUSINESS_PASS_IN_CLONE'
evidence=passed['evidence'];assert evidence['delegation_final_enabled'] is False
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('delegated-core-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'));private.mkdir()
saved=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-n8n-business-c335a25490/state'
config=json.loads((saved/'config.json').read_text());db=sqlite3.connect((saved/'gateway.sqlite').as_uri()+'?mode=ro',uri=True)
proposals=[json.loads(r[0]) for r in db.execute('SELECT document FROM delegated_proposals ORDER BY rowid DESC')]
fixture=business['delegated_fixture'];after=evidence['after']
core_status_override={'policy':'OWNER_DELEGATED_DEMO_APPROVAL','enabled':False,'revision':2,'principal_id':evidence['service_principal'],
    'current_fixtures':[{'native_id':after['native_id'],'lock_version':after['lock_version'],'status_id':after['status_id'],
                         'marker':fixture['marker'],'transitions':config['delegated_demo']['fixtures'][str(after['native_id'])]['transitions']}],
    'proposals':proposals,'commands':[]}
core_before_web=True
def run(*args,data=None,timeout=240):
    process=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
    if process.returncode:
        (private/'failure.log').write_bytes(process.stdout+process.stderr);raise RuntimeError('CORE_ONLY_FAILED_PRIVATE_DIAGNOSTIC')
    return process.stdout
tree=ast.parse((result_out/'delegated_clone_cases.py').read_text(encoding='utf-8'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='delegated_core_case')
exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(result_out/'delegated_clone_cases.py'),'exec'))
proof={}
def qualify_before_web(web):
    global clone
    clone={'web':web};proof.update(delegated_core_case())
with main_native_clone(private/'native',candidate_web_image=core,before_web=qualify_before_web) as clone:
    assert proof['status']=='PASS'
proof.update(status='PASS',image=core,source='Actual Rails session/routes/CSRF/render with passed-business snapshot at synthetic Gateway boundary',
             business_source_sha256=hashlib.sha256((OUT/'autonomous-delegated-clone-result.json').read_bytes()).hexdigest(),
             human_browser_uat=False,main_writes=0,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(result_out/'delegated-core-clone.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

"""Validate observed clone/API/test evidence before writing candidate qualification."""
import argparse,datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6];OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation import integration_pair_release as release

BUNDLE=OUT/'candidate-20261103g';N8N=OUT.parent/'n8n';TESTS=OUT/'qualification-tests.json';PROOF=OUT/'qualification.json'
MODULES=('test_integration_pair_release','test_project6_file_workflow','test_project6_file_knowledge',
 'test_integration_route','test_integration_events','test_github_integration_projection','test_github_integration',
 'test_engineering_github_sync','test_engineering_github_owner_contract','test_engineering_github_journal','test_engineering_github_recovery')
REQUIRED={'LOCAL_DOCUMENT','LOCAL_DOCUMENT_P6','DURABLE_PRODUCERS','GITHUB_PRODUCER'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def hashes():return {name:sha(ROOT/'openproject/ai/tests'/(name+'.py')) for name in MODULES}

def run_tests():
 _,manifest=release.load_guarded(BUNDLE);expected=manifest['source_hashes'];before=hashes()
 env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'openproject/ai')+os.pathsep+str(ROOT/'openproject/ai/tests')
 try:
  completed=subprocess.run([sys.executable,'-m','unittest',*MODULES,'-q'],cwd=ROOT,env=env,capture_output=True,timeout=300)
  output=(completed.stdout+completed.stderr).decode(errors='replace');match=re.search(r'Ran (\d+) tests? in [0-9.]+s',output)
  count=int(match.group(1)) if match else 0
  status='PASS' if completed.returncode==0 and count>=60 and re.search(r'(?m)^OK\s*$',output) else 'FAILED'
 except subprocess.TimeoutExpired:
  output='TEST_TIMEOUT';count=0;status='FAILED'
 assert before==hashes() and expected==release.source_hashes(),'SOURCE_CHANGED_DURING_TESTS'
 data={'status':status,'count':count,'test_modules':list(MODULES),'test_hashes':before,'source_hashes':expected,
       'adapter_sha256':sha(ROOT/'openproject/ai/automation/n8n_integration_adapter.py'),
       'log_sha256':hashlib.sha256(output.encode()).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 TESTS.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'status':status,'count':count}))
 if status!='PASS':raise RuntimeError('QUALIFICATION_TESTS_FAILED')

def seal():
 if PROOF.exists():raise ValueError('QUALIFICATION_ALREADY_EXISTS_PRESERVE_EVIDENCE')
 _,manifest=release.load_guarded(BUNDLE);assert manifest['state']=='BUILT_NOT_DEPLOYED'
 files=manifest['source_hashes'];adapter=sha(ROOT/'openproject/ai/automation/n8n_integration_adapter.py')
 for role,image in manifest['images'].items():
  expected={k:v for k,v in files.items() if release.SOURCES[k][0]==role}
  assert release.runtime_hashes(role,image)==expected,'CANDIDATE_IMAGE_SOURCE_MISMATCH'
 tests=read(TESTS);assert tests['status']=='PASS' and tests['count']>=60 and tests['source_hashes']==files and tests['test_hashes']==hashes() and tests['adapter_sha256']==adapter
 core=read(OUT/'core-candidate-clone-result.json');assert core['status']=='PASS' and core['image']==manifest['images']['core'] and core['native_http']=='PASS' and core['full_template']=='PASS'
 gh=read(OUT/'github-readonly-projection-final.json');assert gh['status']=='PASS' and {p['number'] for p in gh['prs']}==set(range(1,12)) and all(not p.get('details_error') for p in gh['prs'])
 assert set(gh['source_hashes'])=={'openproject/ai/gateway/engineering_github_sync.py','openproject/ai/gateway/engineering_github_details.py'}
 for name,expected in gh['source_hashes'].items():assert files[name]==expected
 current=read(N8N/'business-clone-result.json');assert current['status']=='PASS' and current['passed']==current['total'] and current['main_native_writes']==0 and current['provider_calls']==0
 assert REQUIRED<={r['workflow'] for r in current['checks'] if r['status']=='BUSINESS_PASS_IN_CLONE'}
 local=next(r['evidence'] for r in current['checks'] if r['workflow']=='LOCAL_DOCUMENT_P6')
 assert local['project']==6 and local['replay_same_result'] is True and local['actor21_denied_http'] in {403,404} and local['cross_project_source_denied_http']==403 and local['stale_pin_denied_http']==409
 assert local['actual_sqlite_vector_readback']['point_ids'] and local['actual_sqlite_vector_readback']['document_id']==local['document_id'] and local['source_sha256'] in local['citation']
 chain=next(r['evidence'] for r in current['checks'] if r['workflow']=='GITHUB_PRODUCER')
 assert chain['pr_number']==6 and chain['native_wp']==386 and chain['first_sync'] in {'UPDATED','RECONCILED','UNCHANGED'} and chain['repeat_sync']=='UNCHANGED'
 assert chain['outbox_state']=='ACKED' and chain['business_state']=='DELIVERY_OBSERVED' and str(chain['n8n_execution_id']).isdigit() and chain['automatic_poll']=='SUCCESS' and chain['repeat_poll']=='NOT_DUE' and chain['poll_lease_cleared'] is True
 producers=next(r['evidence'] for r in current['checks'] if r['workflow']=='DURABLE_PRODUCERS')
 assert len(producers['actual_delivery'])==4 and all(str(item['execution_id']).isdigit() for item in producers['actual_delivery'])
 assert current['adapter_sha256']==adapter
 for path,expected in files.items():
  if path.startswith('openproject/ai/gateway/'):
   assert current['gateway_sources'][Path(path).name]==expected,'CLONE_GATEWAY_SOURCE_MISMATCH'
 previous=read(N8N/'business-clone-attempt4.json')
 assert {f'WF{i:02d}' for i in range(1,17)}<={r['workflow'] for r in previous['checks'] if r['status']=='BUSINESS_PASS_IN_CLONE'}
 assert previous['main_native_writes']==0 and previous['provider_calls']==0
 assert current['published_source_sha256']==previous['published_source_sha256'],'PUBLISHED_WORKFLOW_SOURCE_CHANGED'
 evidence=[TESTS,OUT/'core-candidate-clone-result.json',OUT/'github-readonly-projection-final.json',N8N/'business-clone-result.json',N8N/'business-clone-attempt4.json']
 result={'status':'PASS','source_hashes':files,'checks':{'github':True,'events':True,'core':True},
         'images':manifest['images'],'evidence_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in evidence},
         'limits':['n8n clone proof does not imply MAIN deployment','RAG semantic gate separately failed','GitHub polling and n8n integration start disabled'],
         'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 PROOF.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','proof':str(PROOF)}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['test','seal']);args=parser.parse_args()
 run_tests() if args.action=='test' else seal()

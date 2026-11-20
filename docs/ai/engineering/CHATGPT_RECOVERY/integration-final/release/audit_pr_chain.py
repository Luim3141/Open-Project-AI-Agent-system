"""Read actual GitHub PRs and local Git ancestry; no PR merge or state mutation."""
import datetime,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];OUT=Path(__file__).parent
SOURCE=ROOT/'.codex-local/demo-release-candidate';GH=r'C:\Program Files\GitHub CLI\gh.exe'
def api(path):return json.loads(subprocess.check_output([GH,'api','repos/Luim3141/mini-task-manager/'+path],timeout=30))
def ancestor(a,b):return subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=SOURCE,capture_output=True).returncode==0
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE).decode().strip();prs=[]
for number in range(1,11):
 p=api('pulls/'+str(number));reviews=api('pulls/'+str(number)+'/reviews');checks=api('commits/'+p['head']['sha']+'/check-runs')
 rows=[]
 for path in (ROOT/'docs/ai/engineering/runs').glob('*/result.json'):
  try:r=json.loads(path.read_text(encoding='utf-8'))
  except (ValueError,OSError):continue
  if r.get('pr_url')==p['html_url'] and r.get('head_sha')==p['head']['sha']:
   rows.append({'run_id':path.parent.name,'status':r.get('status'),'test_exit_code':(r.get('test_evidence') or {}).get('exit_code'),
    'review_verdict':(r.get('review_evidence') or {}).get('verdict'),'qa_status':((r.get('review_evidence') or {}).get('qa') or {}).get('status'),'native_id':(r.get('native_readback') or {}).get('child_id')})
 prs.append({'number':number,'url':p['html_url'],'state':p['state'],'merged_at':p['merged_at'],'base':p['base']['ref'],'base_sha':p['base']['sha'],'head':p['head']['ref'],'head_sha':p['head']['sha'],
  'mergeable':p['mergeable'],'mergeable_state':p['mergeable_state'],'merge_target':'MAIN' if p['merged_at'] and p['base']['ref']=='main' else 'FEATURE_BRANCH' if p['merged_at'] else 'UNMERGED',
  'integrated_in_candidate':ancestor(p['head']['sha'],head),'review_submissions':[{'state':r['state'],'commit_id':r['commit_id']} for r in reviews],
  'github_checks':[{'name':r['name'],'status':r['status'],'conclusion':r['conclusion']} for r in checks['check_runs']],'local_engineering_evidence':rows})
assert all(p['state']=='open' and not p['merged_at'] and p['integrated_in_candidate'] for p in prs if 6<=p['number']<=10)
main=api('branches/main')['commit']['sha'];assert ancestor(main,head)
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':'Luim3141/mini-task-manager','candidate_head':head,'candidate_branch':'codex/demo-integration-20261103','remote_main_sha':main,'main_integrated_in_candidate':True,'prs':prs,'provider_calls':0,'pr_merges_performed':0}
(OUT/'pr-chain.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'candidate_head':head,'main':main,'prs':[{k:p[k] for k in ['number','state','merge_target','integrated_in_candidate','mergeable_state']} for p in prs]}))

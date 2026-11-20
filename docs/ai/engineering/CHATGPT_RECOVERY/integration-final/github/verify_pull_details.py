"""Read-only GitHub projection check with existing credential, never print credentials."""
import datetime,hashlib,json,subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[6];out=Path(__file__).parent
manifest=json.loads((out/'candidate-20261103f/manifest.json').read_text())
for key,expected in manifest['source_hashes'].items():
 assert hashlib.sha256((root/key).read_bytes()).hexdigest()==expected,'SOURCE_CHANGED'
code='''import json,time
from gateway.engineering_github_sync import fetch_pull_requests
t=time.monotonic();rows=fetch_pull_requests('Luim3141/mini-task-manager',force=True,include_details=True)
print(json.dumps({'seconds':round(time.monotonic()-t,3),'prs':[{'number':p['number'],'state':p['state'],'head_sha':p['head_sha'],'merge_target':p['merge_target'],'reviews_state':p.get('reviews_state'),'checks_state':p.get('checks_state'),'details_error':p.get('details_error')} for p in rows]}))
'''
command=['docker','run','--rm','--network','qldapm-ai_ai','--read-only','--volumes-from','qldapm-ai-gateway-1:ro',
         '--mount',f'type=bind,source={root / "openproject/ai"},target=/candidate,readonly','--workdir','/candidate',
         '-e','PYTHONPATH=/candidate','-e','PYTHONDONTWRITEBYTECODE=1','--entrypoint','python',
         'sha256:3c06559033eba39f423a0c6f9474d1f77e3ef2ebd3617e1b37e50147d2d51a31','-c',code]
try:
 result=subprocess.run(command,capture_output=True,timeout=45)
 if result.returncode:raise ValueError('CHILD_FAILED')
 data=json.loads(result.stdout)
 data['status']='PARTIAL' if any(p.get('details_error') for p in data['prs']) else 'PASS'
except (subprocess.TimeoutExpired,ValueError,KeyError,TypeError):
 data={'status':'UNKNOWN','prs':[],'seconds':None}
data.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  scope='GitHub API read-only; candidate source; credential not exported; no Native or n8n writes',
  source_hashes={k:v for k,v in manifest['source_hashes'].items() if k.endswith(('engineering_github_sync.py','engineering_github_details.py'))})
for key,expected in manifest['source_hashes'].items():
 assert hashlib.sha256((root/key).read_bytes()).hexdigest()==expected,'SOURCE_CHANGED_DURING_GITHUB_CHECK'
(out/'github-readonly-projection-final.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':data['status'],'prs':len(data['prs']),'detail_errors':sum(bool(p.get('details_error')) for p in data['prs']),'seconds':data['seconds']}))

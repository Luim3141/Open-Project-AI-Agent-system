"""Read-only metadata + Native GET diagnosis; never print credentials/payloads."""
from pathlib import Path
import hashlib
import json
import subprocess
import time

OUT=Path(__file__).parent
CODE=r'''import hashlib,json,sqlite3
from pathlib import Path
from gateway.native import Native
c=json.loads(Path('/state/config.json').read_text());credentials=json.loads(Path('/state/credentials.json').read_text())
out={'project_id':c['project_id'],'actors':[],'collectors':[]}
for actor,role in sorted(c['users'].items(),key=lambda x:int(x[0])):
 actor=int(actor);n=Native(c['openproject_url'],credentials[str(actor)],c['project_id']);row={'actor':actor,'registry_role':role}
 try:
  u=n.call('/api/v3/users/me');row['native_user']={k:u.get(k) for k in ['id','login','admin','status']}
  i=n.identity(actor);row['identity_role']=i['role'];row['registry_matches']=i['role']==role
  if role!='AI_SYSTEM_OWNER':
   summary=n.summary(actor);row['summary']={'count':summary['count'],'by_status':summary['by_status']}
 except Exception as e:row.update(error_class=type(e).__name__,error=str(e)[:200])
 out['actors'].append(row)
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
for kind in ['daily_brief','weekly_summary']:
 row=d.execute("SELECT receipt FROM automation_runs WHERE json_extract(receipt,'$.kind')=? ORDER BY created DESC LIMIT 1",(kind,)).fetchone()
 if row:
  r=json.loads(row[0]);out['collectors'].append({k:r.get(k) for k in ['kind','run_id','state','status','targets','ready','unavailable','project_id','reports']})
out['source_sha256']={f:hashlib.sha256(Path('/app/gateway/'+f).read_bytes()).hexdigest() for f in ['native.py','daily_brief.py','weekly_report.py'] if Path('/app/gateway/'+f).exists()}
print(json.dumps(out))'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=CODE,text=True,capture_output=True,timeout=100)
assert p.returncode==0,p.stderr
result=json.loads(p.stdout)
result.update(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              command='openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/workflows/read_main.py',
              route='Native HTTP GET + SQLite mode=ro; credential values never exported',
              environment='MAIN read-only business diagnostic',business_writes=0)
result['images']={c:subprocess.check_output(['docker','inspect',c,'--format','{{.Image}}'],text=True).strip() for c in ['qldapm-ai-gateway-1','qldapm-n8n-main','qldapm-openproject-web-1']}
(OUT/'main-read-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'actors':len(result['actors']),'denied':[r['actor'] for r in result['actors'] if 'error' in r],'collectors':[{k:r.get(k) for k in ['kind','status','ready','targets']} for r in result['collectors']]}))

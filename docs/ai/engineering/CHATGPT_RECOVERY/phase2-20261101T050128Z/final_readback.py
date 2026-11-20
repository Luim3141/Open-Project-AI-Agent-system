"""Read-only serving check; export metadata only."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,sqlite3,subprocess,urllib.request,urllib.error
RUN=Path(__file__).parent
result={'at':datetime.now(timezone.utc).isoformat(),'route':'read-only SQL/SQLite/HTTP/Docker inspect','probes':[]}
for name,url in [('gateway','http://127.0.0.1:18089/health'),('n8n','http://127.0.0.1:5679/healthz'),
 ('qdrant','http://127.0.0.1:6333/collections'),('ollama','http://127.0.0.1:11434/api/tags'),
 ('demo-health','http://127.0.0.1:18791/healthz'),('demo-summary','http://127.0.0.1:18791/tasks/summary')]:
    try:
        with urllib.request.urlopen(url,timeout=5) as response:status=response.status
    except urllib.error.HTTPError as e:status=e.code
    except Exception:status='UNAVAILABLE'
    result['probes'].append({'service':name,'status':status})
query="BEGIN READ ONLY; SELECT project_id,count(*),max(lock_version),max(updated_at) FROM work_packages WHERE project_id IN(5,6) GROUP BY project_id ORDER BY project_id; SELECT id,status_id,lock_version FROM work_packages WHERE id IN(379,386) ORDER BY id; SELECT count(*) FROM work_packages WHERE id=385; COMMIT;"
result['sql']=subprocess.check_output(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-XAtc',query]).decode().strip()
path=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/gateway.sqlite'
with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
    db.execute('PRAGMA query_only=ON')
    result['queue']={'mode':db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],
      'active':db.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0],
      'provider_receipts':db.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0]}
names=subprocess.check_output(['docker','ps','--format','{{.Names}}']).decode().splitlines()
result['containers']=[]
for name in names:
    if name.startswith('qldapm') and 'qualification' not in name and 'recovery-p2' not in name:
        row=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
        result['containers'].append({'name':name,'id':row['Id'],'image':row['Image'],
          'started':row['State']['StartedAt'],'status':row['State']['Status'],'health':row['State'].get('Health',{}).get('Status')})
baseline=json.loads((RUN.parent/'run-20261101T035551Z/final-readback.json').read_text())
by_name={row['name'].lstrip('/'):row for row in result['containers']}
result['baseline_container_identity_image_unchanged']=all(by_name[row['name'].lstrip('/')]['id']==row['id'] and by_name[row['name'].lstrip('/')]['image']==row['image'] for row in baseline['containers'])
assert '5|341|4|2026-10-29 10:08:56.897949' in result['sql']
assert '6|7|9|' in result['sql'] and '379|7|4' in result['sql']
assert result['queue']=={'mode':'OFF','active':0,'provider_receipts':358}
assert result['baseline_container_identity_image_unchanged']
(RUN/'final-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='containers'},indent=2))

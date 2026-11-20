"""Read-only, redacted takeover evidence. Never open live Docker SQLite on Windows."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent

def command(args, data=None):
    result = subprocess.run(args, input=data, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); output withheld")
    return result.stdout.decode('utf-8', errors='replace')

def main():
    names = command(['docker', 'ps', '--format', '{{.Names}}']).splitlines()
    containers = json.loads(command(['docker', 'inspect', *names]))
    report = {'at': datetime.now(timezone.utc).isoformat(), 'containers': [], 'gateways': {}}
    for c in containers:
        report['containers'].append({
            'name': c['Name'], 'id': c['Id'], 'image': c['Image'],
            'started': c['State']['StartedAt'], 'health': c['State'].get('Health', {}).get('Status'),
            'restart_count': c['RestartCount'], 'policy': c['HostConfig']['RestartPolicy']['Name'],
            'mounts': [{k: m[k] for k in ('Source', 'Destination', 'RW')} for m in c['Mounts']],
            'networks': list(c['NetworkSettings']['Networks']),
        })
    probe = r'''
import json, sqlite3, pathlib
r=pathlib.Path('/state'); c=json.loads((r/'config.json').read_text())
out={'config':{k:c.get(k) for k in ('project_id','users','openproject_url','gateway_mode','hosts','type_ids','status_ids')},'files':{p.name:{'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else None} for p in [r/n for n in ('ui.key','credentials.json','gemini.key','gemini.json','gateway.sqlite','knowledge.sqlite')]}}
for filename in ('gemini.json',):
 p=r/filename
 if p.exists():
  d=json.loads(p.read_text());out[filename]={k:d.get(k) for k in ('enabled','model','project_id','free_only','provider','multi_agent','policy_file')}
db=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
tables=[row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
out['tables']={t:db.execute('SELECT COUNT(*) FROM "'+t+'"').fetchone()[0] for t in tables if not t.startswith('sqlite_')}
out['audit_schema']=[row[1] for row in db.execute('PRAGMA table_info(audit)')]
if 'audit' in tables:
 out['audit_recent']=[dict(zip([x[0] for x in q.description],row)) for q in [db.execute('SELECT * FROM audit ORDER BY rowid DESC LIMIT 20')] for row in q]
print(json.dumps(out))
'''
    # Do not print audit values until explicitly allowlisted below.
    for env, name in [('main','qldapm-ai-gateway-1'),('staging','qldapm-ai-stage-staging-gateway-1')]:
        data=json.loads(command(['docker','exec','-i',name,'python','-'], probe.encode()))
        data['audit_recent']=[{k:v for k,v in row.items() if k in ('actor','action','outcome','result','at','created_at','correlation_id')} for row in data.get('audit_recent',[])]
        report['gateways'][env]=data
    dest=OUT/'runtime-baseline.json'
    if dest.exists():
        dest=OUT/('runtime-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'evidence':str(dest),'containers':len(names),'gateways':{
        env:{'project_id':d['config']['project_id'],'gateway_mode':d['config']['gateway_mode'],
             'tables':d['tables'],'provider_files_present':d['files']['gemini.key']['exists'] and d['files']['gemini.json']['exists']}
        for env,d in report['gateways'].items()}},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()

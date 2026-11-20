"""Bounded read-only identity/collector diagnosis; no credential values or work-package contents leave MAIN."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
CODE = r'''import hashlib,json,sqlite3
from pathlib import Path
from gateway.native import Native
config=json.loads(Path('/state/config.json').read_text())
credentials=json.loads(Path('/state/credentials.json').read_text())
out={'project_id':config['project_id'],'actors':[],'collectors':[]}
for raw_actor,role in sorted(config['users'].items(),key=lambda x:int(x[0])):
 actor=int(raw_actor)
 native=Native(config['openproject_url'],credentials[str(actor)],config['project_id'])
 row={'actor':actor,'registry_role':role,'scheduled_target':role!='AI_SYSTEM_OWNER'}
 try:
  user=native.call('/api/v3/users/me')
  row['native_identity']={key:user.get(key) for key in ('id','login','admin','status')}
  identity=native.identity(actor)
  row['resolved_role']=identity['role']
  row['registry_matches']=identity['role']==role
 except Exception as error:
  row['identity_error_class']=type(error).__name__
  row['identity_denied']=isinstance(error,PermissionError)
 out['actors'].append(row)
db=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
for kind in ('daily_brief','weekly_summary'):
 row=db.execute("SELECT receipt FROM automation_runs WHERE json_extract(receipt,'$.kind')=? ORDER BY created DESC LIMIT 1",(kind,)).fetchone()
 if row:
  receipt=json.loads(row[0]);summary={key:receipt.get(key) for key in ('kind','run_id','project_id','state','status','targets','ready','unavailable')}
  summary['actor_states']=[{key:report.get(key) for key in ('actor','state')} for report in receipt.get('reports',[]) or []]
  out['collectors'].append(summary)
out['source_sha256']={name:hashlib.sha256(Path('/app/gateway/'+name).read_bytes()).hexdigest() for name in ('native.py','daily_brief.py','weekly_report.py')}
print(json.dumps(out))'''


def main():
    started = datetime.now(timezone.utc).isoformat()
    command = ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-']
    result = subprocess.run(command, input=CODE, text=True, capture_output=True, timeout=150)
    if result.returncode:
        raise RuntimeError('READ_ONLY_PRINCIPAL_PROBE_FAILED')
    report = json.loads(result.stdout)
    report.update(started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
                  command=command, route='Native HTTP GET and SQLite mode=ro; no business writes',
                  probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    report['images'] = {name: subprocess.check_output(['docker', 'inspect', name, '--format', '{{.Image}}'], text=True).strip()
                        for name in ('qldapm-ai-gateway-1', 'qldapm-n8n-main', 'qldapm-openproject-web-1')}
    (HERE / 'principal-readback.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'status': 'READ_ONLY_DIAGNOSIS_RECORDED', 'actors': len(report['actors']),
                      'denied': [row['actor'] for row in report['actors'] if row.get('identity_denied')]}))


if __name__ == '__main__':
    main()

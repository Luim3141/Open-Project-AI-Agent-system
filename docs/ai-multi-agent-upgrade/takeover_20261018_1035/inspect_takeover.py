"""Read-only takeover evidence. No restart, provisioning, provider call or business mutation."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import urllib.error
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PREV = ROOT / 'docs/ai-multi-agent-upgrade/verification_runs/run_20261018_0515'

def run(*args, data=None, timeout=35):
    p = subprocess.run(args, input=data, capture_output=True, encoding='utf-8', timeout=timeout, cwd=ROOT)
    if p.returncode:
        raise RuntimeError(f'{args[0]} failed: exit {p.returncode}')
    return p.stdout

def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def pg(sql):
    return json.loads(run('docker', 'exec', '-i', 'qldapm-ai-stage-db-1', 'psql', '-U', 'postgres', '-d', 'openproject', '-At', '-v', 'ON_ERROR_STOP=1', '-c', sql))

def probe(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            b = r.read(262144)
            return {'status': r.status, 'url': r.url, 'bytes_read': len(b), 'login_form': b'id="username"' in b,
                    'csp_present': bool(r.headers.get('Content-Security-Policy'))}
    except urllib.error.HTTPError as e:
        return {'status': e.code, 'url': url}
    except Exception as e:
        return {'error_type': type(e).__name__, 'url': url}

def main():
    status = run('git', 'status', '--porcelain=v1', '--untracked-files=all')
    (OUT / 'git-status-full.txt').write_text(status, encoding='utf-8')
    (OUT / 'tracked.diff').write_text(run('git', 'diff'), encoding='utf-8')
    ignored = run('git', 'ls-files', '--others', '--ignored', '--exclude-standard')
    (OUT / 'git-ignored-paths.txt').write_text(ignored, encoding='utf-8')
    save('git-summary.json', {'branch': run('git', 'branch', '--show-current').strip(), 'head': run('git', 'rev-parse', 'HEAD').strip(),
          'tracked': run('git', 'ls-files').splitlines(), 'status_counts': {k: sum(x.startswith(k) for x in status.splitlines()) for k in ['??', ' M', 'M ', ' D', 'A ']},
          'ignored_count': len(ignored.splitlines()), 'nested_head': run('git', '-C', 'openproject/development/core', 'rev-parse', 'HEAD').strip(),
          'nested_status': run('git', '-C', 'openproject/development/core', 'status', '--porcelain=v1', '--untracked-files=all').splitlines()})
    names = run('docker', 'ps', '-a', '--format', '{{.Names}}').splitlines()
    selected = [n for n in names if n.startswith(('qldapm-ai-stage-', 'qldapm-openproject-', 'qldapm-ai-gateway-'))]
    info = json.loads(run('docker', 'inspect', *selected))
    safe = []
    for c in info:
        safe.append({'name': c['Name'].lstrip('/'), 'image': c['Image'], 'image_ref': c['Config']['Image'],
            'state': c['State']['Status'], 'health': c['State'].get('Health', {}).get('Status'), 'started': c['State']['StartedAt'],
            'restart_count': c['RestartCount'], 'restart_policy': c['HostConfig']['RestartPolicy'],
            'entrypoint': c['Config'].get('Entrypoint'), 'command': c['Config'].get('Cmd'),
            'ports': c['HostConfig']['PortBindings'], 'networks': list(c['NetworkSettings']['Networks']),
            'mounts': [{k: m.get(k) for k in ['Type','Source','Destination','RW']} for m in c['Mounts']],
            'env_names': sorted(v.split('=',1)[0] for v in c['Config'].get('Env', [])),
            'compose_files': c['Config'].get('Labels', {}).get('com.docker.compose.project.config_files'),
            'socket_mount': any('docker.sock' in m['Destination'] for m in c['Mounts'])})
    save('runtime.json', {'at': datetime.now(timezone.utc).isoformat(), 'containers': safe})
    devices = pg('''SELECT coalesce(json_agg(t), '[]'::json) FROM
        (SELECT d.id,d.user_id,u.login,d.channel,d.active,d."default",d.created_at,d.updated_at
         FROM two_factor_authentication_devices d JOIN users u ON u.id=d.user_id
         WHERE d.user_id IN (6,7,8,9,10,13) ORDER BY d.user_id,d.id) t''')
    save('totp-devices.json', devices)
    save('native-identity.json', pg('''SELECT coalesce(json_agg(t), '[]'::json) FROM
        (SELECT u.id,u.login,u.status,m.project_id,r.name AS role
        FROM users u JOIN members m ON m.user_id=u.id JOIN member_roles mr ON mr.member_id=m.id
        JOIN roles r ON r.id=mr.role_id WHERE u.id IN (6,7,8,9,10,13) ORDER BY u.id,m.project_id,r.name) t'''))
    save('native-counts.json', pg('''SELECT json_build_object('projects',(SELECT count(*) FROM projects),
        'work_packages',(SELECT count(*) FROM work_packages),'public_tables',(SELECT count(*) FROM information_schema.tables WHERE table_schema='public'),
        'knowledge_tables',(SELECT coalesce(json_agg(table_name),'[]'::json) FROM information_schema.tables WHERE table_schema='qldapm_knowledge'))'''))
    # Execute only stdlib reads inside Gateway; do not import Store (constructor may migrate/recover).
    code = '''import hashlib,json,sqlite3,pathlib
r=pathlib.Path('/state')
c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row
run=c.execute("SELECT id,request_key,created,receipt FROM automation_runs WHERE request_key='daily:2026-10-18'").fetchall()
brief=c.execute("SELECT actor,project,day,document FROM daily_briefs WHERE day='2026-10-18' ORDER BY actor").fetchall()
tables=[x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
out={'automation_runs':[], 'daily_briefs':[], 'tables':tables}
for x in run:
 d=dict(x);d['receipt']=json.loads(d['receipt']);out['automation_runs'].append(d)
for x in brief:
 d=dict(x);b=json.loads(d.pop('document'));d.update({k:b.get(k) for k in ['run_id','role','model_used','state','collected_at']});d['count']=b.get('snapshot',{}).get('count');out['daily_briefs'].append(d)
out['table_counts']={t:c.execute('SELECT count(*) FROM "'+t+'"').fetchone()[0] for t in ['gemini_usage','agent_tasks','agent_runs','automation_runs','daily_briefs'] if t in tables}
out['gateway_hashes']={str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app/gateway').glob('*.py')}
k=r/'knowledge.sqlite';out['knowledge_exists']=k.is_file()
if k.is_file():
 q=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True)
 out['knowledge_tables']=[x[0] for x in q.execute("SELECT name FROM sqlite_master WHERE type='table'")]
 out['knowledge_documents']=q.execute('SELECT count(*) FROM knowledge_documents').fetchone()[0]
 q.close()
print(json.dumps(out));c.close()
'''
    gw = json.loads(run('docker', 'exec', '-i', 'qldapm-ai-stage-staging-gateway-1', 'python', '-', data=code))
    local = {'gateway/'+p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'openproject/ai/gateway').glob('*.py')}
    gw['parity'] = {'same': sorted(k for k,v in local.items() if gw['gateway_hashes'].get(k)==v),
                    'different': sorted(k for k,v in local.items() if k in gw['gateway_hashes'] and gw['gateway_hashes'][k]!=v),
                    'missing_runtime': sorted(set(local)-set(gw['gateway_hashes']))}
    save('gateway-storage-and-parity.json', gw)
    rows = list(csv.DictReader((PREV/'TEST_RESULTS.csv').open(encoding='utf-8-sig', newline='')))
    checks=[]
    with zipfile.ZipFile(PREV/'logs.zip') as z:
        znames = z.namelist()
        for row in rows:
            evidence = row.get('raw_log_path') or row.get('evidence_path') or row.get('evidence') or row.get('log_file')
            if not evidence:
                checks.append({'case':row, 'error':'NO_EVIDENCE_COLUMN'});continue
            p = Path(evidence)
            if not p.is_absolute(): p=ROOT/p
            if not p.is_file(): p=PREV/'logs'/Path(evidence).name
            h=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
            expected=row.get('raw_log_hash') or row.get('evidence_sha256') or row.get('sha256') or row.get('log_sha256')
            members=[n for n in znames if Path(n).name==p.name]
            zh=hashlib.sha256(z.read(members[0])).hexdigest() if len(members)==1 else None
            checks.append({'id':row.get('test_id') or row.get('case_id'), 'status':row.get('status'), 'file':p.name,
                           'hash':h,'csv_hash':expected,'csv_match':h==expected,'zip_match':h==zh})
    save('handoff-integrity.json', {'csv_fields':list(rows[0]), 'rows':len(rows), 'zip_members':len(znames), 'checks':checks})
    runtime = Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
    url = json.loads((runtime/'access/current-url.json').read_text(encoding='utf-8-sig'))['url']
    paths=['/login','/api/v3/users/me','/internal/automation/commands','/rest/workflows','/staging_totp_secrets.json','/secrets/staging_totp_secrets.json']
    save('http-probes.json', {'at':datetime.now(timezone.utc).isoformat(),'current_url':url,
          'public':{p:probe(url+p) for p in paths}, 'local':{str(port):probe(f'http://127.0.0.1:{port}'+path) for port,path in [(8088,'/login'),(8090,'/health'),(18091,'/login'),(18092,'/health'),(5678,'/healthz')]},
          'credentials_in_access': (runtime/'access/staging_totp_secrets.json').exists(),
          'credentials_in_secrets': (runtime/'secrets/staging_totp_secrets.json').is_file()})
    print(json.dumps({'output':str(OUT), 'containers':len(safe), 'devices':len(devices), 'gateway_parity':gw['parity'], 'integrity_rows':len(rows)},ensure_ascii=False))

if __name__ == '__main__':
    main()

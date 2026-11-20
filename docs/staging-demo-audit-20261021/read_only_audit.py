"""Bounded read-only evidence collection; no deployment, login, AI execution or writes to runtime."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

OUT = Path(__file__).resolve().parent
RUNTIME = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'


def command(args, body=None):
    p = subprocess.run(args, input=body, text=True, capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError(f'{args[:4]}: exit {p.returncode}; raw output withheld')
    return p.stdout


def snapshot():
    names = command(['docker', 'ps', '--format', '{{.Names}}']).splitlines()
    info = json.loads(command(['docker', 'inspect', *names]))
    result = []
    for item in info:
        if not item['Name'].startswith('/qldapm-'):
            continue
        result.append(dict(name=item['Name'][1:], id=item['Id'], image=item['Image'],
                           started=item['State']['StartedAt'], running=item['State']['Running'],
                           health=item['State'].get('Health', {}).get('Status'),
                           restart_count=item['RestartCount'], oom=item['State'].get('OOMKilled'),
                           restart_policy=item['HostConfig']['RestartPolicy']['Name'],
                           ports=item['NetworkSettings']['Ports'],
                           networks=list(item['NetworkSettings']['Networks']),
                           mounts=[dict(source=m['Source'], destination=m['Destination'], rw=m['RW']) for m in item['Mounts']]))
    return result


def postgres(container):
    queries = {
        'projects': 'SELECT id,identifier,name,active FROM projects ORDER BY id',
        'work_packages': 'SELECT project_id,count(*) AS total,count(start_date) AS with_start,count(due_date) AS with_due,count(version_id) AS with_version FROM work_packages GROUP BY project_id ORDER BY project_id',
        'types': 'SELECT w.project_id,t.name,count(*) FROM work_packages w JOIN types t ON t.id=w.type_id GROUP BY w.project_id,t.name ORDER BY w.project_id,t.name',
        'users': "SELECT id,login,status,admin FROM users WHERE type='User' ORDER BY id",
        'memberships': 'SELECT m.project_id,m.user_id,r.name AS role FROM members m JOIN member_roles mr ON mr.member_id=m.id JOIN roles r ON r.id=mr.role_id ORDER BY m.project_id,m.user_id,r.id',
        'versions': 'SELECT id,project_id,name,status,start_date,effective_date FROM versions ORDER BY project_id,id',
        'modules': 'SELECT project_id,name FROM enabled_modules ORDER BY project_id,name',
        'tables': "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name",
        'business_fingerprints': "SELECT 'work_packages' AS name,count(*) AS count,md5(string_agg(row_to_json(t)::text,'' ORDER BY t.id)) AS digest FROM work_packages t UNION ALL SELECT 'relations',count(*),md5(string_agg(row_to_json(t)::text,'' ORDER BY t.id)) FROM relations t UNION ALL SELECT 'versions',count(*),md5(string_agg(row_to_json(t)::text,'' ORDER BY t.id)) FROM versions t",
    }
    result = {}
    for key, query in queries.items():
        sql = 'BEGIN READ ONLY; SELECT coalesce(json_agg(x),\'[]\'::json) FROM (' + query + ') x; ROLLBACK;'
        raw = command(['docker', 'exec', '-i', container, 'psql', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'openproject', '-Atq'], sql)
        result[key] = json.loads(raw.strip())
    return result


def gateway(container):
    program = '''import json,sqlite3,pathlib,hashlib
root=pathlib.Path('/state'); out={}
for name in ['config.json','gemini.json']:
 p=root/name
 if p.exists():
  d=json.loads(p.read_text()); allowed=['gateway_mode','gemini_multi_agent_enabled','maintenance','enabled','model','billing_allowed','data_scope','mode','expires_at','max_generation_calls','max_http_attempts']
  out[name]={k:d[k] for k in allowed if k in d}
out['key_present']=(root/'gemini.key').is_file()
for p in root.glob('*.sqlite'):
 db=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True); db.execute('PRAGMA query_only=ON'); tables=[r[0] for r in db.execute("select name from sqlite_master where type='table'")]
 out[p.name]={'integrity':db.execute('PRAGMA quick_check').fetchone()[0],'tables':{}}
 for name in tables:
  if not name.startswith('sqlite_'):
   out[p.name]['tables'][name]={'count':db.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0],'columns':[r[1] for r in db.execute('PRAGMA table_info("'+name+'")')]}
 for name in ['agent_runs','ai_runs','jobs','gemini_call_receipts','ai_queue','knowledge_documents']:
  if name not in tables: continue
  cols=[r[1] for r in db.execute('PRAGMA table_info("'+name+'")')]
  safe=[c for c in ['id','actor','project','state','engine','status','model_used','agent','created','updated','input_tokens','output_tokens','http_attempts','generation_calls'] if c in cols]
  if safe: out[p.name][name+'_recent']=[dict(zip(safe,row)) for row in db.execute('SELECT '+','.join('"'+c+'"' for c in safe)+' FROM "'+name+'" ORDER BY rowid DESC LIMIT 12')]
 db.close()
print(json.dumps(out))'''
    return json.loads(command(['docker', 'exec', '-i', container, 'python', '-'], program))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http(url, headers=None):
    start = time.monotonic()
    try:
        response = urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url, headers=headers or {}), timeout=15)
        body = response.read(250000).decode(errors='replace')
        return dict(url=url, status=response.status, seconds=round(time.monotonic()-start, 2),
                    title=re.findall(r'<title>(.*?)</title>', body, re.S)[:1],
                    login_form='login' in body.lower(), cloudflare='cloudflare' in str(response.headers).lower(),
                    bytes_read=len(body), body_sha256=hashlib.sha256(body.encode()).hexdigest())
    except urllib.error.HTTPError as e:
        return dict(url=url, status=e.code, location=e.headers.get('Location'), seconds=round(time.monotonic()-start, 2))
    except Exception as e:
        return dict(url=url, error=type(e).__name__, seconds=round(time.monotonic()-start, 2))


def main():
    phase = sys.argv[1]
    assert phase in ('before', 'after')
    target = OUT / (phase + '.json')
    assert not target.exists(), 'Refuse evidence overwrite'
    url = json.loads((RUNTIME/'access/current-url.json').read_text())['url']
    assert re.fullmatch(r'https://[a-z0-9-]+\.trycloudflare\.com', url)
    data = dict(timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(), url=url,
                containers=snapshot())
    for name, container in [('stage','qldapm-ai-stage-db-1'), ('main','qldapm-openproject-db-1')]:
        try: data[name+'_postgres'] = postgres(container)
        except Exception as e: data[name+'_postgres_error'] = str(e)
    for name, container in [('stage','qldapm-ai-stage-staging-gateway-1'), ('main','qldapm-ai-gateway-1')]:
        try: data[name+'_gateway'] = gateway(container)
        except Exception as e: data[name+'_gateway_error'] = str(e)
    urls = [('http://127.0.0.1:18091/health_checks/default',None),
            ('http://127.0.0.1:18092/health',{'Host':'gateway:8090'}),
            ('http://localhost:5678/healthz/readiness',None),
            (url+'/health_checks/default',None),(url+'/login',None)]
    data['http'] = [http(u,h) for u,h in urls]
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(evidence=str(target),timestamp=data['timestamp'],url=url,http=data['http'],errors={k:v for k,v in data.items() if k.endswith('_error')}),ensure_ascii=False))


if __name__ == '__main__':
    main()

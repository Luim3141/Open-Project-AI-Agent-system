"""Read-only P00 inventory. No raw Docker env, credentials, prompts or DB rows are exported."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = {'qldapm-openproject', 'qldapm-ai', 'qldapm-ai-stage'}


def command(argv, data=None):
    result = subprocess.run(argv, input=data, capture_output=True, timeout=90)
    if result.returncode:
        # Docker/psql errors may embed secrets. Only the failed executable is reported.
        raise RuntimeError('AUDIT_COMMAND_FAILED:' + argv[0])
    return result.stdout.decode('utf-8').strip()


def container_summary(info):
    return {'name': info['Name'].lstrip('/'), 'image': info['Image'],
            'project': info['Config']['Labels'].get('com.docker.compose.project'),
            'status': info['State']['Status'], 'health': info['State'].get('Health', {}).get('Status'),
            'restart': info['HostConfig']['RestartPolicy']['Name'],
            'ports': info['HostConfig'].get('PortBindings'),
            'mounts': [{'type': m['Type'], 'source': m['Source'], 'target': m['Destination'], 'rw': m['RW']}
                       for m in info['Mounts']],
            'networks': sorted(info['NetworkSettings']['Networks']),
            'environment_names': sorted(s.split('=', 1)[0] for s in info['Config'].get('Env', []))}


def database(container):
    sql = """BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT jsonb_build_object('kind','tables','value',array_agg(tablename ORDER BY tablename))
 FROM pg_tables WHERE schemaname='public';
SELECT jsonb_build_object('kind','migrations','value',array_agg(version ORDER BY version)) FROM schema_migrations;
SELECT jsonb_build_object('kind','projects','value',jsonb_agg(t)) FROM
 (SELECT id, identifier, (SELECT count(*) FROM work_packages w WHERE w.project_id=p.id) AS work_packages
 FROM projects p ORDER BY id) t;
SELECT jsonb_build_object('kind','membership_roles','value',jsonb_agg(t)) FROM
 (SELECT m.project_id, m.user_id, r.id AS role_id, r.name AS role
 FROM members m JOIN member_roles mr ON mr.member_id=m.id JOIN roles r ON r.id=mr.role_id
 WHERE m.entity_id IS NULL ORDER BY m.project_id,m.user_id,r.id) t;
SELECT jsonb_build_object('kind','columns','value',jsonb_agg(t)) FROM
 (SELECT table_name,column_name,data_type,is_nullable FROM information_schema.columns
 WHERE table_schema='public' ORDER BY table_name,ordinal_position) t;
COMMIT;"""
    output = command(['docker', 'exec', '-i', container, 'psql', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres',
                      '-d', 'openproject', '-qAt'], sql.encode())
    return {row['kind']: row['value'] for row in map(json.loads, output.splitlines())}


def gateway_state(container):
    program = """import json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
tables=[r[0] for r in d.execute("select name from sqlite_master where type='table' order by name")]
result={'tables':tables,'quick_check':d.execute('PRAGMA quick_check').fetchone()[0]}
for table in ('jobs','ai_runs','proposals'):
 if table in tables:
  result[table]=dict(d.execute('select state,count(*) from '+table+' group by state'))
if 'gemini_usage' in tables:
 result['usage_history_rows']=d.execute('select count(*) from gemini_usage').fetchone()[0]
print(json.dumps(result))
"""
    return json.loads(command(['docker', 'exec', container, 'python', '-c', program]))


def private_metadata(root):
    result = {}
    for state in ('gateway', 'stage-ai'):
        folder = root / state
        config = json.loads((folder / 'config.json').read_text(encoding='utf-8'))
        provider = json.loads((folder / 'gemini.json').read_text()) if (folder / 'gemini.json').is_file() else {}
        result[state] = {'project_id': config.get('project_id'), 'users': config.get('users'),
                         'gateway_mode': config.get('gateway_mode'),
                         'provider_enabled': provider.get('enabled', False), 'model': provider.get('model'),
                         'files': {name: 'PRESENT' if (folder / name).is_file() else 'MISSING'
                                   for name in ('credentials.json', 'ui.key', 'gemini.key', 'gemini.json', 'gateway.sqlite')}}
    path = root / 'operator/gemini-free/free-tier-proof.json'
    proof = json.loads(path.read_text()) if path.is_file() else {}
    result['historical_provider_proof'] = {k: proof.get(k) for k in
        ('project', 'model', 'tier', 'billing_enabled', 'checked_at', 'quota', 'data_scope')}
    result['historical_provider_proof']['continuous_billing_allowed'] = proof.get('authorization', {}).get('billing_allowed')
    result['fresh_account_verification'] = 'NOT_VERIFIED_BY_THIS_SCRIPT'
    return result


def collect():
    containers = []
    for identifier in command(['docker', 'ps', '-aq']).splitlines():
        info = json.loads(command(['docker', 'inspect', identifier]))[0]
        if info['Config']['Labels'].get('com.docker.compose.project') in PROJECTS:
            containers.append(container_summary(info))
    result = {'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'workspace': str(ROOT),
              'containers': containers, 'databases': {}, 'gateways': {}, 'http': {}}
    for env, db, gateway in [('main', 'qldapm-openproject-db-1', 'qldapm-ai-gateway-1'),
                             ('staging', 'qldapm-ai-stage-db-1', 'qldapm-ai-stage-staging-gateway-1')]:
        result['databases'][env] = database(db)
        result['gateways'][env] = gateway_state(gateway)
    for port, path in [(8088, '/'), (8090, '/health'), (18091, '/health_checks/default'), (18092, '/health')]:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=5) as response:
                result['http'][str(port)] = response.status
        except urllib.error.HTTPError as error:
            result['http'][str(port)] = error.code
        except OSError:
            result['http'][str(port)] = 'UNREACHABLE'
    result['private_metadata'] = private_metadata(Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai')
    images = sorted({c['image'] for c in containers})
    result['images'] = {i: json.loads(command(['docker', 'image', 'inspect', i]))[0].get('RepoDigests') for i in images}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    record = collect()
    data = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    # Preserve previous observations; the caller must choose a fresh evidence path.
    with args.output.open('xb') as stream:
        stream.write(data)
    print(json.dumps({'output': str(args.output), 'sha256': hashlib.sha256(data).hexdigest(),
                      'containers': len(record['containers']), 'http': record['http']}))

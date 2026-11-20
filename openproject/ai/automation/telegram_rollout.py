"""Local operator for an additive Telegram/Observer release; no action on import."""
import argparse
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

AI = Path(__file__).resolve().parents[1]
REPO = AI.parents[1]
EVIDENCE = REPO / 'docs/telegram-observer'
PRIVATE = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'QLDAPM/openproject-ai'
CONTAINERS = {'gateway': 'qldapm-ai-gateway-1', 'core': 'qldapm-openproject-web-1',
              'n8n': 'qldapm-n8n-main'}
EXTENSIONS = {'.py', '.rb', '.erb', '.css', '.js', '.json', '.yml'}
RELEASE_FILES = {
    'gateway/agent_observer.py', 'gateway/telegram_notifications.py', 'gateway/service.py', 'gateway/catalog.py',
    'core/overlay/app/controllers/qldapm_ai_controller.rb',
    'core/overlay/app/views/qldapm_ai/observer.html.erb',
    'core/overlay/app/views/qldapm_ai/_observer_client.html.erb',
    'core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb',
    'core/overlay/app/services/qldapm/observer_acceptance.rb',
    'core/overlay/config/routes.rb',
    'core/overlay/config/initializers/qldapm_gates.rb',
    'core/overlay/lib/api/v3/qldapm/gates_api.rb',
}


def call(args, timeout=180):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'LOCAL_OPERATOR_COMMAND_FAILED:{args[0]}:{result.returncode}')
    return result.stdout


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def source_diff(root, baseline):
    root = Path(root)
    result = {}
    for directory in ('gateway', 'core/overlay'):
        for path in (root / directory).rglob('*'):
            if not path.is_file() or path.suffix not in EXTENSIONS or '__pycache__' in path.parts:
                continue
            relative = path.relative_to(root).as_posix()
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            if baseline.get(relative) != checksum:
                result[relative] = checksum
    return result


def replacement_env(text, key, value):
    pattern = r'(?m)^' + re.escape(key) + r'=.*$'
    if len(re.findall(pattern, text)) != 1:
        raise ValueError('EXACTLY_ONE_ENV_SETTING_REQUIRED')
    return re.sub(pattern, lambda _: key + '=' + value, text)


def approved_sources(changes):
    return {path: checksum for path, checksum in changes.items() if path in RELEASE_FILES}


def initialize_files(root):
    root = Path(root)
    for directory in (root, root / 'state', root / 'secrets'):
        directory.mkdir(parents=True, exist_ok=True)
        if directory.is_symlink():
            raise PermissionError('SECRET_DIRECTORY_LINK_DENIED')
    defaults = {
        root / '.env': ('TELEGRAM_BOT_TOKEN=\nGEMINI_API_KEY=\nGEMINI_MODEL=gemini-3.5-flash-lite\n'
                        'GEMINI_PROJECT_DATA_CONSENT=false\nTELEGRAM_POLLING_ENABLED=true\n'
                        'TELEGRAM_NOTIFICATIONS_ENABLED=true\nTELEGRAM_ALLOW_WEBHOOK_REMOVAL=false\n'),
        root / 'secrets/notification.key': secrets.token_urlsafe(48),
    }
    for path, value in defaults.items():
        if path.exists():
            continue
        with path.open('x', encoding='utf-8') as stream:
            stream.write(value)


def initialize():
    target = PRIVATE / 'telegram-ai'
    from free_tier_staging import private_directory
    private_directory(target)
    initialize_files(target)
    return {'status': 'LOCAL_CONFIGURATION_READY', 'config_file': str(target / '.env')}


def enroll_service():
    target = PRIVATE / 'telegram-ai/secrets/gateway.token'
    if target.exists():
        raise ValueError('EXISTING_SERVICE_TOKEN_PRESERVED')
    # The dedicated bearer shares an existing real principal; Native ACL is rechecked per command.
    program = """import json,secrets,time
from pathlib import Path
from gateway.native import Native
from gateway.store import Store,digest
r=Path('/state');c=json.loads((r/'config.json').read_text());s=Store(r)
assert c['users'].get('18')=='AI_SYSTEM_OWNER' and c['project_id']==5
n=Native(c['openproject_url'],s.credential(18),5);identity=n.identity(18)
assert identity['user_id']==18 and identity['role']=='AI_SYSTEM_OWNER'
token=secrets.token_urlsafe(48)
with s.connect() as db:db.execute('INSERT INTO tokens(hash,user_id,role,expires) VALUES(?,?,?,?)',(digest(token),18,'AI_SYSTEM_OWNER',time.time()+30*86400))
assert s.authenticate(token)['user_id']==18
s.record(18,'telegram_service_enroll','dedicated_bearer','30_DAY_TOKEN_NO_NATIVE_CREDENTIAL_CHANGE')
print(token,end='')"""
    token = call(['docker', 'exec', CONTAINERS['gateway'], 'python', '-c', program])
    if not re.fullmatch(rb'[A-Za-z0-9_-]{64}', token):
        raise ValueError('SERVICE_TOKEN_RESPONSE_INVALID')
    with target.open('xb') as stream:
        stream.write(token)
    result = {'status': 'DEDICATED_SERVICE_TOKEN_ENROLLED', 'actor': 18, 'projects': [5, 6],
              'expires_in_days': 30, 'existing_credentials_replaced': False}
    save(EVIDENCE / 'service-enrollment.json', result)
    return result


def ecosystem_snapshot(phase):
    target = EVIDENCE / ('ecosystem-' + phase + '.json')
    if target.exists():
        raise ValueError('EXISTING_EVIDENCE_PRESERVED')
    legacy = REPO / 'docs/ai/engineering/CHATGPT_RECOVERY/integration-final/native_integrity.py'
    tree = ast.parse(legacy.read_text(encoding='utf-8'))
    queries = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(name, ast.Name) and name.id == 'queries' for name in node.targets))
    native = {}
    for name, query in queries.items():
        query = query.replace('project_id=5', 'project_id IN (5,6)').replace('WHERE id=5', 'WHERE id IN (5,6)')
        sql = "SELECT coalesce(json_agg(row ORDER BY row::text),'[]'::json) FROM (SELECT row_to_json(t) AS row FROM (" + query + ') t) s;'
        data = call(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',sql])
        rows = json.loads(data)
        native[name] = {'rows': len(rows), 'sha256': hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    program = """const {DatabaseSync}=require('node:sqlite');const {createHash}=require('node:crypto');
const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const pin=t=>d.prepare('SELECT * FROM '+t+' ORDER BY id').all().map(r=>({id:r.id,sha256:createHash('sha256').update(JSON.stringify(r)).digest('hex')}));
console.log(JSON.stringify({workflows:pin('workflow_entity'),credentials:pin('credentials_entity')}));d.close();"""
    n8n = json.loads(call(['docker','exec',CONTAINERS['n8n'],'node','-e',program]))
    result = {'native':native,'n8n':n8n,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if phase == 'after':
        before = json.loads((EVIDENCE / 'ecosystem-before.json').read_text(encoding='utf-8'))
        result['native_unchanged'] = all(value == before['native'][key] for key,value in native.items() if key != 'users')
        if native['users'] != before['native']['users']:
            expected_users=json.loads((EVIDENCE/'auth-security-before.json').read_text(encoding='utf-8'))
            result['native_unchanged'] = result['native_unchanged'] and auth_security_pin() == expected_users
            result['allowed_auth_delta']='Only last_login_on/updated_at excluded from verified user security hash'
        result['existing_n8n_unchanged'] = all(row in n8n[key] for key in ('workflows','credentials') for row in before['n8n'][key])
        save(target,result)
        assert result['native_unchanged'] and result['existing_n8n_unchanged'], 'EXISTING_ECOSYSTEM_CHANGED'
    save(target,result)
    return {'status':'ECOSYSTEM_SNAPSHOT_'+phase.upper(),'native_tables':len(native),
            'n8n_workflows':len(n8n['workflows']),'n8n_credentials':len(n8n['credentials'])}


def auth_security_pin():
    query="SELECT coalesce(json_agg(row ORDER BY row::text),'[]'::json) FROM (SELECT to_jsonb(u)-'last_login_on'-'updated_at' AS row FROM users u) s;"
    raw=call(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',query])
    rows=json.loads(raw)
    return {'rows':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()}


def source_hashes():
    code = """import hashlib,json,pathlib
p=pathlib.Path('/app/gateway');print(json.dumps({'gateway/'+str(f.relative_to(p)).replace('\\\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*.py')}))"""
    gateway = json.loads(call(['docker', 'exec', CONTAINERS['gateway'], 'python', '-c', code]))
    files = [p for p in (AI / 'core/overlay').rglob('*') if p.is_file() and p.suffix in EXTENSIONS]
    paths = {p.relative_to(AI).as_posix(): '/app/' + p.relative_to(AI / 'core/overlay').as_posix() for p in files}
    ruby = "require 'json';require 'digest';puts JSON.generate(JSON.parse(ARGV[0]).transform_values{|p|File.file?(p) ? Digest::SHA256.file(p).hexdigest : nil})"
    core = json.loads(call(['docker', 'exec', CONTAINERS['core'], 'ruby', '-e', ruby, json.dumps(paths)]))
    return {**gateway, **core}


def protected_state():
    code = """import sqlite3,json,hashlib,pathlib
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
tables=['engineering_control','engineering_owner_revision','ai_queue','ai_runs','requests','gemini_call_receipts','engineering_checkpoints','tokens']
present={r[0] for r in d.execute('select name from sqlite_master where type=?',('table',))}
pins={}
for t in tables:
 if t in present:
  rows=d.execute('select * from '+t+' order by rowid').fetchall();pins[t]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()}
print(json.dumps({'tables':pins,'control':d.execute('select project,mode from engineering_control').fetchall(),'active':d.execute('select count(*) from ai_queue where state!=?',('finished',)).fetchone()[0],'files':{n:hashlib.sha256((pathlib.Path('/state')/n).read_bytes()).hexdigest() for n in ['config.json','credentials.json','gemini.key','gemini.json','ui.key','automation.key'] if (pathlib.Path('/state')/n).is_file()}}))"""
    return json.loads(call(['docker', 'exec', CONTAINERS['gateway'], 'python', '-c', code]))


def audit(destination=None):
    destination=Path(destination or EVIDENCE/'baseline.json')
    if destination.exists():
        raise ValueError('BASELINE_EXISTS_PRESERVED')
    rows = {}
    for role, name in CONTAINERS.items():
        item = json.loads(call(['docker', 'inspect', name]))[0]
        rows[role] = {'name': name, 'id': item['Id'], 'image': item['Image'],
                      'health': item['State'].get('Health', {}).get('Status'),
                      'restart': item['HostConfig']['RestartPolicy']['Name'],
                      'networks': list(item['NetworkSettings']['Networks']),
                      'mounts': [{'type': m['Type'], 'destination': m['Destination']} for m in item['Mounts']]}
    result = {'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'containers': rows, 'source_hashes': source_hashes(), 'protected_state': protected_state(),
              'branch': call(['git', 'branch', '--show-current']).decode().strip(),
              'head': call(['git', 'rev-parse', 'HEAD']).decode().strip()}
    save(destination, result)
    return {'status': 'BASELINE_CAPTURED', 'control': result['protected_state']['control'],
            'active': result['protected_state']['active'], 'images': {k: v['image'] for k, v in rows.items()}}


def release_module(baseline_path=None):
    from automation import integration_pair_release as release
    baseline = json.loads(Path(baseline_path or EVIDENCE/'baseline.json').read_text(encoding='utf-8'))
    release.BASE_IMAGES = {r: baseline['containers'][r]['image'] for r in ('gateway', 'core')}
    changed = approved_sources(source_diff(AI, baseline['source_hashes']))
    if not changed:
        raise ValueError('OBSERVER_CHANGES_REQUIRED')
    release.SOURCES = {'openproject/ai/' + path:
        ('gateway', '/app/' + path) if path.startswith('gateway/') else
        ('core', '/app/' + path.removeprefix('core/overlay/')) for path in changed}
    # This release changes source only; retain current Main policies verbatim.
    release.next_config = copy.deepcopy
    def qualified(proof, files):
        if (proof.get('status') != 'PASS' or proof.get('source_hashes') != files
                or proof.get('checks') != {'observer':True,'notifications':True,'core':True,'security':True}):
            raise ValueError('EXACT_TELEGRAM_OBSERVER_QUALIFICATION_REQUIRED')
    release.qualified = qualified
    return release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['audit', 'init', 'enroll-service', 'auth-before', 'ecosystem-before', 'ecosystem-after', 'prepare', 'build', 'rollout', 'verify'])
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--qualification', type=Path)
    parser.add_argument('--baseline',type=Path,default=EVIDENCE/'baseline.json')
    args = parser.parse_args()
    if args.action == 'audit':
        result = audit(args.baseline)
    elif args.action == 'init':
        result = initialize()
    elif args.action == 'enroll-service':
        result = enroll_service()
    elif args.action == 'auth-before':
        target=EVIDENCE/'auth-security-before.json'
        if target.exists():raise ValueError('AUTH_BASELINE_PRESERVED')
        save(target,auth_security_pin());result={'status':'AUTH_SECURITY_BASELINE_SAVED'}
    elif args.action.startswith('ecosystem-'):
        result = ecosystem_snapshot(args.action.removeprefix('ecosystem-'))
    elif args.action == 'verify':
        baseline = json.loads((EVIDENCE / 'baseline.json').read_text(encoding='utf-8'))
        state = protected_state()
        expected = copy.deepcopy(baseline['protected_state'])
        original_tokens = expected['tables'].pop('tokens')
        actual = copy.deepcopy(state)
        new_tokens = actual['tables'].pop('tokens')
        program = ('import sqlite3,json,hashlib;d=sqlite3.connect("file:/state/gateway.sqlite?mode=ro",uri=True);'
                   'rows=d.execute("SELECT * FROM tokens ORDER BY rowid LIMIT ?",(' + str(original_tokens['rows']) + ',)).fetchall();'
                   'print(hashlib.sha256(json.dumps(rows,separators=(",",":")).encode()).hexdigest())')
        old_token_hash = call(['docker','exec',CONTAINERS['gateway'],'python','-c',program]).decode().strip()
        result = {'protected_state_unchanged': actual == expected and old_token_hash == original_tokens['sha256'],
                  'dedicated_service_tokens_added': new_tokens['rows'] - original_tokens['rows'], 'state': state}
        save(EVIDENCE / 'state-verification.json', result)
    else:
        if args.bundle is None:
            parser.error('--bundle required')
        release = release_module(args.baseline)
        if args.action == 'prepare':
            result = release.prepare(args.bundle)
        elif args.action == 'build':
            result = release.build(args.bundle)
        else:
            if args.qualification is None:
                parser.error('--qualification required')
            result = release.rollout(args.bundle, args.qualification)
    print(json.dumps({k: v for k, v in result.items() if k in
                     {'status', 'state', 'images', 'control', 'active', 'protected_state_unchanged', 'config_file'}}))


if __name__ == '__main__':
    main()

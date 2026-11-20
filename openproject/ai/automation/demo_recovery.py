"""Private portable demo backup and isolated restore. Never restores or replays MAIN."""
import argparse
from contextlib import closing
import datetime as dt
import hashlib
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
import urllib.request
import uuid

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'openproject/ai'))
from automation import main_operations as ops
from automation.main_auxiliary_backup import backup as auxiliary_backup, qualify_restore, qualify_restored_server
from automation.main_native_clone import main_native_clone
from free_tier_staging import private_directory

MAGIC = b'QLDAPM-DEMO-RECOVERY-V1\n'
REPORTS = ROOT / 'docs/ai/engineering/CHATGPT_RECOVERY/demo-final/dr'
SKIP = {'.venv', 'node_modules', '__pycache__', '.pytest_cache', '.ruff_cache', '.cache'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(args, *, data=None, timeout=600, output=None):
    if output is not None:
        with Path(output).open('xb') as stream:
            p = subprocess.run(args, input=data, stdout=stream, stderr=subprocess.PIPE, timeout=timeout)
    else:
        p = subprocess.run(args, input=data, capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError('RECOVERY_COMMAND_FAILED: ' + args[0])
    return None if output is not None else p.stdout


def safe_new(path):
    path = ops.private_path(path)
    if path.exists():
        raise ValueError('NEW_PRIVATE_DESTINATION_REQUIRED')
    private_directory(path)
    return path


def encrypt(source, destination, key):
    nonce = os.urandom(12)
    writer = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    writer.authenticate_additional_data(MAGIC)
    with Path(source).open('rb') as incoming, Path(destination).open('xb') as outgoing:
        outgoing.write(MAGIC + nonce)
        while block := incoming.read(1024 * 1024):
            outgoing.write(writer.update(block))
        outgoing.write(writer.finalize())
        outgoing.write(writer.tag)


def decrypt(source, destination, key):
    # Unauthenticated output is private temporary data and is never parsed before tag verification.
    with Path(source).open('rb') as incoming:
        if incoming.read(len(MAGIC)) != MAGIC:
            raise ValueError('RECOVERY_FORMAT_INVALID')
        nonce = incoming.read(12)
        incoming.seek(-16, 2)
        tag = incoming.read(16)
        remaining = incoming.tell() - len(MAGIC) - 12 - 16
        incoming.seek(len(MAGIC) + 12)
        reader = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
        reader.authenticate_additional_data(MAGIC)
        try:
            with Path(destination).open('xb') as outgoing:
                while remaining:
                    block = incoming.read(min(1024 * 1024, remaining))
                    if not block: raise ValueError('RECOVERY_TRUNCATED')
                    outgoing.write(reader.update(block)); remaining -= len(block)
                outgoing.write(reader.finalize())
        except Exception:
            Path(destination).unlink(missing_ok=True)
            raise


def validate_archive(path):
    with tarfile.open(path, 'r:*') as archive:
        names = set()
        for item in archive:
            name = PurePosixPath(item.name)
            if name.is_absolute() or '..' in name.parts or '\\' in item.name or ':' in item.name or item.name in names or not (item.isfile() or item.isdir()):
                raise ValueError('UNSAFE_RECOVERY_ARCHIVE')
            names.add(item.name)
        if 'manifest.json' not in names:
            raise ValueError('RECOVERY_MANIFEST_REQUIRED')


def json_http(path, payload=None):
    request = urllib.request.Request('http://127.0.0.1:6333' + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)['result']


def qdrant_export():
    rows = []
    for collection in json_http('/collections')['collections']:
        name = collection['name']
        info = json_http('/collections/' + name)
        points, offset = [], None
        while True:
            page = json_http('/collections/' + name + '/points/scroll',
                {'limit': 128, 'with_payload': True, 'with_vector': True, **({'offset': offset} if offset else {})})
            points.extend(page['points']); offset = page.get('next_page_offset')
            if offset is None: break
        points.sort(key=lambda p: str(p['id']))
        rows.append({'name': name, 'vectors': info['config']['params']['vectors'],
            'sparse_vectors': info['config']['params'].get('sparse_vectors'), 'points': points})
    return rows


def package_tree(archive, source, prefix):
    source = Path(source)
    for path in sorted(source.rglob('*')):
        rel = path.relative_to(source)
        if any(part in SKIP for part in rel.parts) or path.is_dir(): continue
        if path.is_symlink(): raise ValueError('WINDOWS_SOURCE_SYMLINK_DENIED')
        archive.add(path, arcname=str(PurePosixPath(prefix) / rel.as_posix()), recursive=False)


def create(label):
    if not label or not all(c.isalnum() or c in '-_' for c in label): raise ValueError('SAFE_LABEL_REQUIRED')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    kit = safe_new(ops.PRIVATE_ROOT / ('demo-recovery-' + stamp + '-' + label))
    payload = safe_new(kit / 'snapshot'); public = safe_new(kit / 'ciphertext'); custody = safe_new(kit / 'recovery-custody')
    runtime = ops.capture()
    queue_code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0],'active':d.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0]}))"
    queue = json.loads(ops.command('exec', 'qldapm-ai-gateway-1', 'python', '-c',queue_code))
    if queue != {'mode': 'OFF', 'active': 0}: raise ValueError('QUIESCENT_ENGINEERING_REQUIRED')
    native = ops.backup(runtime, payload / 'native')
    auxiliary = auxiliary_backup(runtime, payload / 'auxiliary', qualify=False)
    (payload / 'runtime.json').write_text(json.dumps(runtime, indent=2))
    config = payload / 'configuration'; config.mkdir()
    runtime_root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM'
    for group, names in {'openproject': ['.env', 'accounts.json', 'ui-bridge.yml', 'manifest.json', 'source-mapping.json'],
        'openproject-ai': ['.env', 'image-lock.json', 'gateway/config.json', 'gateway/credentials.json', 'gateway/ui.key',
        'gateway/gemini.json', 'gateway/gemini.key', 'gateway/gemini-readiness.json', 'gateway/automation.key',
        'gateway/n8n_encryption.key', 'gateway/webhook_secret.json', 'operator/gemini-main/free-tier-proof.json', 'operator/n8n-main-owner/owner.json']}.items():
        for name in names:
            path = runtime_root / group / name
            if not path.is_file() or path.is_symlink(): raise ValueError('REQUIRED_PRIVATE_CONFIG_MISSING')
            target = config / group / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(path.read_bytes())
    for name in runtime['containers']:
        (config / (name + '.inspect.json')).write_bytes(ops.command('inspect', name))
    # Optional on pre-demo baselines; final provider admission also needs its private host token.
    for name in ['engineering-provider-token', 'openclaw-health.json', 'demo-dr-status.json']:
        path=runtime_root/'openproject-ai/gateway'/name
        if path.is_file() and not path.is_symlink():
            (config/'openproject-ai/gateway'/name).write_bytes(path.read_bytes())
    source = payload / 'source.tar.gz'
    with tarfile.open(source, 'w:gz', compresslevel=3) as archive:
        for part in ['gateway', 'automation', 'core/overlay', 'tests', 'engineering_skills']:
            package_tree(archive, ROOT / 'openproject/ai' / part, 'openproject/ai/' + part)
        for path in (ROOT / 'openproject/ai').iterdir():
            if path.is_file() and path.suffix in {'.py', '.ps1', '.yml', '.json', '.toml', '.txt', '.sh', '.md'}:
                archive.add(path, arcname='openproject/ai/' + path.name)
        for part in ['openproject/compose.yml', 'openproject/Caddyfile', 'architecture.md', 'AGENTS.md', 'CONTEXT.md']:
            archive.add(ROOT / part, arcname=part)
        package_tree(archive, ROOT / 'docs/agents', 'docs/agents')
        package_tree(archive, ROOT / 'docs/ai/engineering', 'docs/ai/engineering')
    run(['git', '-C', str(ROOT), 'bundle', 'create', str(payload / 'workspace.bundle'), '--all'])
    demo = Path(r'D:\AI project\QLDAPM-demo\mini-task-manager')
    with tarfile.open(payload / 'demo-source.tar.gz', 'w:gz', compresslevel=3) as archive:
        package_tree(archive, demo, 'mini-task-manager')
    run(['git', '-C', str(demo), 'bundle', 'create', str(payload / 'demo.bundle'), '--all'])
    wsl = ['wsl', '-d', 'OpenClawGateway', '-u', 'root', '--exec']
    run(wsl + ['/bin/tar', '-C', '/', '--exclude=*/.venv', '--exclude=*/__pycache__', '--exclude=*/.pytest_cache',
        '--exclude=home/openclaw/.openclaw/cache', '--exclude=home/openclaw/.openclaw/downloads', '--exclude=home/openclaw/.openclaw/tmp',
        '--exclude=home/openclaw/engineering/demo-data', '-czf', '-', 'usr/local/bin/openclaw', 'home/openclaw/.openclaw',
        'home/openclaw/.config/systemd/user', 'home/openclaw/workspaces/mini-task-manager', 'home/openclaw/engineering', 'root/.qldapm-openclaw'],
        output=payload / 'openclaw-wsl.tar.gz', timeout=900)
    sql = "import sqlite3,sys;s=sqlite3.connect('file:/home/openclaw/engineering/demo-data/tasks.sqlite?mode=ro',uri=True);d=sqlite3.connect(':memory:');s.backup(d);sys.stdout.buffer.write(d.serialize())"
    (payload / 'demo.sqlite').write_bytes(run(wsl + ['/usr/bin/python3', '-c', sql]))
    vectors = qdrant_export()
    if vectors != qdrant_export(): raise ValueError('QDRANT_CHANGED_DURING_EXPORT')
    (payload / 'qdrant.json').write_text(json.dumps(vectors, separators=(',', ':')), encoding='utf8')
    ollama={}
    for endpoint in ['version','tags']:
        with urllib.request.urlopen('http://127.0.0.1:11434/api/'+endpoint,timeout=10) as response:
            ollama[endpoint]=json.load(response)
    model_root=Path(os.environ.get('OLLAMA_MODELS',str(Path.home()/'.ollama/models')))
    if not model_root.is_dir():raise ValueError('OLLAMA_MODEL_FILES_REQUIRED')
    ollama['model_sources']=[]
    for model in ollama['tags']['models']:
        request=urllib.request.Request('http://127.0.0.1:11434/api/show',data=json.dumps({'model':model['name']}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=10) as response:detail=json.load(response)
        paths=re.findall(r'^FROM (.+)$',detail.get('modelfile',''),re.M)
        if len(paths)!=1:raise ValueError('OLLAMA_MODEL_SOURCE_REQUIRED')
        path=Path(paths[0].strip().strip('"')).resolve()
        if not path.is_relative_to(model_root.resolve()) or not path.is_file():raise ValueError('OLLAMA_MODEL_SOURCE_SCOPE_INVALID')
        ollama['model_sources'].append({'model':model['name'],'blob':path.name})
    with tarfile.open(payload/'ollama-models.tar','w') as archive:
        package_tree(archive,model_root,'ollama-models')
    (payload/'ollama-runtime.json').write_text(json.dumps(ollama,indent=2))
    images = sorted(set(row['image'] for row in runtime['containers'].values()))
    run(['docker', 'save', '--output', str(payload / 'images.tar'), *images], timeout=900)
    ops.verify(runtime)
    if json.loads(ops.command('exec','qldapm-ai-gateway-1','python','-c',queue_code))!=queue:
        raise ValueError('ENGINEERING_CHANGED_DURING_BACKUP')
    manifest = {'schema': 'qldapm.demo.recovery.v1', 'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'label': label,
        'images': runtime['containers'], 'native': native['files'], 'n8n_workflows': auxiliary['workflow_count'],
        'n8n_credentials': auxiliary['credential_count'], 'qdrant_collections': {v['name']: len(v['points']) for v in vectors},
        'source_includes_uncommitted': True, 'windows_delivery_journals_included': True,
        'files': {str(p.relative_to(payload)).replace('\\', '/'): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in payload.rglob('*') if p.is_file()},
        'limits': ['Consistent individual snapshots, not an atomic cross-service transaction', 'No MAIN restore/replay',
        'OpenClaw Node runtime/config/source retained; Python virtualenv/cache rebuildable from pinned requirements',
        'Physical-machine recovery not tested; off-host copy and separate recovery-key custody require Owner']}
    (payload / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    archive = kit / 'payload.tar'
    with tarfile.open(archive, 'w') as output:
        for p in payload.rglob('*'):
            if p.is_file(): output.add(p, arcname=p.relative_to(payload).as_posix(), recursive=False)
    key = os.urandom(32); (custody / 'recovery.key').write_bytes(key)
    encrypted = public / 'qldapm-demo-recovery.aesgcm'; encrypt(archive, encrypted, key)
    bootstrap = Path(__file__).with_name('decrypt_demo_recovery.py')
    (public / bootstrap.name).write_bytes(bootstrap.read_bytes())
    (public / 'FORMAT.json').write_text(json.dumps({'schema':'qldapm.demo.recovery.v1','magic_ascii':MAGIC.decode(),
        'cipher':'AES-256-GCM','key_bytes':32,'nonce_bytes':12,'tag_bytes':16,'aad':'magic',
        'bootstrap_sha256':sha(bootstrap),'ciphertext_sha256':sha(encrypted),'image_ids':images},indent=2))
    check = kit / 'roundtrip.tar'; decrypt(encrypted, check, key)
    if sha(check) != sha(archive): raise ValueError('ENCRYPTED_ROUNDTRIP_MISMATCH')
    # Retain private raw snapshots for immediate rollback; ciphertext/key are independently portable.
    result = {'status': 'PORTABLE_BACKUP_CREATED', 'kit': str(kit), 'label': label, 'ciphertext_bytes': encrypted.stat().st_size,
        'ciphertext_sha256': sha(encrypted), 'payload_sha256': sha(archive), 'manifest_sha256': sha(payload / 'manifest.json'),
        'images': images, 'component_snapshots': len(manifest['files']), 'off_host_copy': 'OFF_HOST_COPY_PENDING_OWNER', 'physical_machine_dr': 'NOT_TESTED'}
    (kit / 'creation.json').write_text(json.dumps(result, indent=2))
    REPORTS.mkdir(parents=True, exist_ok=True); (REPORTS / ('creation-' + label + '.json')).write_text(json.dumps(result, indent=2))
    return result


def verify(kit):
    kit = ops.private_path(kit)
    if not kit.name.startswith('demo-recovery-'): raise ValueError('RECOVERY_KIT_SCOPE_DENIED')
    output = safe_new(kit / ('restore-' + uuid.uuid4().hex[:8]))
    archive = output / 'payload.tar'
    key = (kit / 'recovery-custody/recovery.key').read_bytes()
    decrypt(kit / 'ciphertext/qldapm-demo-recovery.aesgcm', archive, key)
    validate_archive(archive)
    restored = output / 'files'; restored.mkdir()
    with tarfile.open(archive) as incoming: incoming.extractall(restored, filter='data')
    manifest = json.loads((restored / 'manifest.json').read_text())
    for rel, expected in manifest['files'].items():
        path = restored / rel
        if not path.resolve().is_relative_to(restored.resolve()) or not path.is_file() or path.stat().st_size != expected['bytes'] or sha(path) != expected['sha256']:
            raise ValueError('RESTORE_CHECKSUM_FAILED')
    images = manifest['images']; components = {}
    n8n = images['qldapm-n8n-main']['image']
    with closing(sqlite3.connect((restored / 'auxiliary/n8n.sqlite').as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        expected = {key: [r[0] for r in db.execute('select id from ' + table + ' order by id')] for key, table in [('workflow_ids', 'workflow_entity'), ('credential_ids', 'credentials_entity')]}
    components['n8n_credentials'] = qualify_restore(restored / 'auxiliary', n8n, expected)
    components['n8n_server'] = qualify_restored_server(restored / 'auxiliary', n8n, expected)
    with main_native_clone(output / 'native-clone', source_dump_path=restored / 'native/postgres.dump', candidate_web_image=images['qldapm-openproject-web-1']['image']) as clone:
        sql = "SELECT json_build_object('project5_wp',(SELECT count(*) FROM work_packages WHERE project_id=5),'project6_wp',(SELECT count(*) FROM work_packages WHERE project_id=6),'project5_relations',(SELECT count(*) FROM relations WHERE from_id IN (SELECT id FROM work_packages WHERE project_id=5) OR to_id IN (SELECT id FROM work_packages WHERE project_id=5)));"
        counts = json.loads(run(['docker', 'exec', clone['database'], 'psql', '-U', 'postgres', '-d', 'openproject', '-At', '-c', sql]))
        if counts['project5_wp'] != 341 or counts['project5_relations'] != 344 or counts['project6_wp'] < 1: raise ValueError('NATIVE_RESTORE_DATA_MISMATCH')
        ruby = r'''require 'net/http';require 'json'
raise 'RESTORE_CLONE_ONLY' unless ENV['QLDAPM_TEST_ONLY']=='true' && ENV.fetch('DATABASE_URL').include?('@qa-db/')
owner=User.find(18);token=Token::API.create_and_return_value(owner)
reads=[5,6].map do |id|
 uri=URI("http://localhost:8080/api/v3/projects/#{id}");request=Net::HTTP::Get.new(uri);request.basic_auth('apikey',token);request['Host']='localhost:8088'
 response=Net::HTTP.start(uri.host,uri.port,read_timeout:30){|http|http.request(request)}
 raise 'RESTORED_NATIVE_PROJECT_API_FAILED' unless response.code=='200' && JSON.parse(response.body)['id']==id
 {project_id:id,http_status:200}
end
puts({authenticated_native_project_reads:reads,clone_only_api_token:true}.to_json)'''
        api=json.loads(run(['docker','exec','-i',clone['web'],'bundle','exec','rails','runner','-'],data=ruby.encode(),timeout=180).splitlines()[-1])
        components['native_core'] = {'data': counts, 'http_readiness': 200, 'image': clone['images']['web'], 'isolated': True, **api}
    components['gateway_knowledge'] = verify_gateway(restored, images['qldapm-ai-gateway-1']['image'])
    components['qdrant'] = verify_qdrant(restored, images['qldapm-qdrant']['image'], images['qldapm-ai-gateway-1']['image'])
    components['openclaw_runtime'] = verify_openclaw(restored, images['qldapm-ai-gateway-1']['image'])
    components['source_configuration_demo'] = verify_source(restored)
    components['ollama_model_files'] = verify_ollama_files(restored)
    result = {'status': 'LOCAL_RESTORE_VERIFIED', 'kit': str(kit), 'completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'verified_components': components, 'off_host_copy': 'OFF_HOST_COPY_PENDING_OWNER', 'physical_machine_dr': 'NOT_TESTED',
        'main_restore': False, 'main_native_writes': 0, 'provider_calls': 0, 'manifest_sha256': sha(restored / 'manifest.json')}
    (kit / 'restore-result.json').write_text(json.dumps(result, indent=2))
    REPORTS.mkdir(parents=True, exist_ok=True); (REPORTS / ('restore-' + manifest['label'] + '.json')).write_text(json.dumps(result, indent=2))
    return result


def verify_gateway(restored, image):
    code = r'''import json,sqlite3,shutil,threading,time,urllib.request,os
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
import uvicorn
state=Path('/tmp/state');state.mkdir()
for name in ['gateway','knowledge']:
 shutil.copyfile('/backup/native/'+name+'.sqlite',state/(name+'.sqlite'))
 d=sqlite3.connect(state/(name+'.sqlite'));assert d.execute('pragma quick_check').fetchone()[0]=='ok';d.close()
config={'project_id':6,'users':{},'hosts':['localhost:8090'],'engineering':{'enabled':False},'openproject_url':'http://127.0.0.1:9'}
(state/'config.json').write_text(json.dumps(config));os.environ['QLDAPM_AI_RUNTIME']=str(state)
from gateway.app import create_app
store=Store(state);service=Service(store,config,Path('/tmp/workspaces'))
t=threading.Thread(target=lambda:uvicorn.run(create_app(state,service),host='127.0.0.1',port=8090,log_level='error'),daemon=True);t.start()
for i in range(50):
 try:
  assert urllib.request.urlopen('http://localhost:8090/health',timeout=1).status==200;break
 except Exception:time.sleep(.1)
else:raise RuntimeError('RESTORED_GATEWAY_NOT_READY')
out={'gateway_health':200,'gateway_integrity':'ok','knowledge_integrity':'ok'}
for name in ['gateway','knowledge']:
 d=sqlite3.connect(state/(name+'.sqlite'));out[name+'_tables']=len(d.execute("select name from sqlite_master where type='table'").fetchall());d.close()
print(json.dumps(out))'''
    raw = run(['docker', 'run', '--rm', '--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,size=256m', '--memory', '512m', '--cpus', '1',
        '--mount', f'type=bind,source={restored},target=/backup,readonly', '--entrypoint', 'python', image, '-c', code])
    return json.loads(raw.splitlines()[-1])


def verify_qdrant(restored, image, runner):
    label = str(uuid.uuid4()); name = 'qldapm-demo-dr-' + label; network = name + '-net'
    run(['docker', 'network', 'create', '--internal', '--label', 'org.qldapm.demo-dr=' + label, network])
    created=False
    try:
        run(['docker', 'run', '-d', '--name', name, '--label', 'org.qldapm.demo-dr=' + label, '--network', network, '--network-alias', 'qdrant',
            '--read-only', '--tmpfs', '/qdrant/storage:size=512m', '--tmpfs', '/qdrant/snapshots:size=64m', '--memory', '768m', '--cpus', '1', image])
        created=True
        code = r'''import json,time,urllib.request,hashlib
rows=json.load(open('/backup/qdrant.json'))
def call(path,data=None,method=None):
 req=urllib.request.Request('http://qdrant:6333'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'},method=method)
 with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)['result']
for i in range(60):
 try:call('/collections');break
 except Exception:time.sleep(.5)
else:raise RuntimeError('QDRANT_CLONE_NOT_READY')
out={}
for collection in rows:
 name=collection['name'];config={'vectors':collection['vectors']}
 if collection.get('sparse_vectors'):config['sparse_vectors']=collection['sparse_vectors']
 call('/collections/'+name,config,'PUT')
 for index in range(0,len(collection['points']),128):call('/collections/'+name+'/points?wait=true',{'points':collection['points'][index:index+128]},'PUT')
 actual=[];offset=None
 while True:
  page=call('/collections/'+name+'/points/scroll',{'limit':128,'with_vector':True,'with_payload':True,**({'offset':offset} if offset else {})});actual.extend(page['points']);offset=page.get('next_page_offset')
  if offset is None:break
 actual.sort(key=lambda p:str(p['id']))
 assert len(actual)==len(collection['points']),'POINT_COUNT_MISMATCH'
 maximum_error=0.0
 for current,expected in zip(actual,collection['points']):
  assert current['id']==expected['id'] and current['payload']==expected['payload'],'IDENTITY_OR_PAYLOAD_MISMATCH'
  if isinstance(current['vector'],list):
   assert len(current['vector'])==len(expected['vector'])
   maximum_error=max(maximum_error,max((abs(a-b) for a,b in zip(current['vector'],expected['vector'])),default=0))
  else:assert current['vector']==expected['vector'],'NAMED_VECTOR_MISMATCH'
 assert maximum_error<1e-6,'VECTOR_NUMERIC_DRIFT'
 query_check='NO_PROJECT_VECTOR_IN_COLLECTION'
 sample=next((p for p in actual if isinstance(p['vector'],list) and 'project_id' in p['payload']),None)
 if sample:
  project=sample['payload']['project_id']
  body={'query':sample['vector'],'limit':len(actual),'with_payload':True,'filter':{'must':[{'key':'project_id','match':{'value':project}}]}}
  matches=call('/collections/'+name+'/points/query',body)['points']
  assert any(p['id']==sample['id'] for p in matches),'RESTORED_VECTOR_QUERY_MISSING'
  assert all(p['payload'].get('project_id')==project for p in matches),'RESTORED_PROJECT_FILTER_LEAK'
  body['filter']['must'][0]['match']['value']='__qldapm_restore_no_such_project__'
  assert call('/collections/'+name+'/points/query',body)['points']==[],'RESTORED_ABSENT_PROJECT_FILTER_LEAK'
  query_check='KNOWN_VECTOR_QUERY_AND_PROJECT_FILTER_PASS'
 out[name]={'points':len(actual),'all_id_payload_equal':True,'max_vector_absolute_error':maximum_error,'vector_tolerance':1e-6,'query_filter':query_check}
print(json.dumps(out))'''
        raw = run(['docker', 'run', '--rm', '--network', network, '--read-only', '--tmpfs', '/tmp:size=64m', '--memory', '512m', '--cpus', '1',
            '--mount', f'type=bind,source={restored},target=/backup,readonly', '--entrypoint', 'python', runner, '-c', code])
        return json.loads(raw)
    finally:
        if created:
            current = json.loads(run(['docker', 'inspect', name]))[0]
            if current['Config']['Labels'].get('org.qldapm.demo-dr') != label: raise ValueError('RESTORE_CONTAINER_OWNERSHIP_MISMATCH')
            run(['docker', 'rm', '-f', name])
        current=json.loads(run(['docker','network','inspect',network]))[0]
        if current['Labels'].get('org.qldapm.demo-dr')!=label:raise ValueError('RESTORE_NETWORK_OWNERSHIP_MISMATCH')
        run(['docker', 'network', 'rm', network])


def verify_source(restored):
    checks = {}
    for name in ['workspace.bundle', 'demo.bundle']:
        run(['git', '-C', str(ROOT), 'bundle', 'verify', str(restored / name)])
        checks[name] = 'GIT_HISTORY_VERIFIED'
    with closing(sqlite3.connect((restored / 'demo.sqlite').as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        assert db.execute('pragma quick_check').fetchone()[0] == 'ok'
        checks['demo_sqlite'] = 'INTEGRITY_OK'
    with tarfile.open(restored/'source.tar.gz','r:gz') as archive:
        source_names=set(archive.getnames())
        journal='docs/ai/engineering/IMPLEMENTATION_STATE.json'
        checks['windows_delivery_journals']='INCLUDED' if journal in source_names and any(n.startswith('docs/ai/engineering/runs/') and n.endswith('/delivery-steps.json') for n in source_names) else 'NOT_INCLUDED_IN_BASELINE; final capture required'
    with tarfile.open(restored / 'openclaw-wsl.tar.gz', 'r:gz') as archive:
        members = archive.getmembers(); names = {m.name for m in members}
        required = {'home/openclaw/.openclaw/openclaw.json', 'usr/local/bin/openclaw', 'home/openclaw/.config/systemd/user/openclaw-gateway.service',
            'home/openclaw/engineering/mini-task-manager-server.py', 'root/.qldapm-openclaw/active.json'}
        assert required <= names
        config = json.load(archive.extractfile('home/openclaw/.openclaw/openclaw.json')); assert isinstance(config, dict)
        gate = json.load(archive.extractfile('root/.qldapm-openclaw/active.json')); assert gate.get('active') is False
        checks['openclaw_configuration'] = {'required_files': len(required), 'config_parse': True, 'provider_gate_off': True, 'archive_entries': len(members), 'runtime_tools_included': any(n.startswith('home/openclaw/.openclaw/tools/') for n in names)}
    checks['docker_images_archive'] = 'CHECKSUM_VERIFIED; exact image IDs in manifest, docker load not run on MAIN'
    checks['limits'] = 'OpenClaw config/runtime files verified, not a second OpenClaw service or physical laptop boot'
    return checks


def verify_openclaw(restored, image):
    code = r'''import json,tarfile,subprocess,os,re
from pathlib import Path
root=Path('/tmp/restored');root.mkdir()
with tarfile.open('/backup/openclaw-wsl.tar.gz','r:gz') as archive:
 for member in archive:
  if member.name.startswith('home/openclaw/.openclaw/tools/') or member.name=='home/openclaw/.openclaw/openclaw.json':
   archive.extract(member,root,filter='data')
home=root/'home/openclaw';tools=home/'.openclaw/tools/node-v24.22.2'
config=json.loads((home/'.openclaw/openclaw.json').read_text());assert isinstance(config,dict)
result=subprocess.run([str(tools/'bin/node'),str(tools/'lib/node_modules/openclaw/openclaw.mjs'),'--version'],capture_output=True,timeout=60,env={**os.environ,'HOME':str(home),'PATH':str(tools/'bin')+':/usr/bin:/bin'})
assert result.returncode==0,'RESTORED_OPENCLAW_CLI_FAILED'
version=result.stdout.decode().strip();assert re.fullmatch(r'[a-zA-Z0-9 .+()_-]{1,100}',version),'VERSION_FORMAT_INVALID'
print(json.dumps({'cli_version':version,'restored_node_binary':True,'config_json_valid':True,'network':'none','model_inference':False}))'''
    raw = run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=1536m,mode=1777',
        '--memory','2048m','--cpus','1','--pids-limit','128','--mount',f'type=bind,source={restored},target=/backup,readonly',
        '--entrypoint','python',image,'-c',code],timeout=240)
    return json.loads(raw.splitlines()[-1])


def verify_ollama_files(restored):
    runtime=json.loads((restored/'ollama-runtime.json').read_text())
    models=runtime['tags']['models'];required=set();manifest_digests=set()
    with tarfile.open(restored/'ollama-models.tar','r:') as archive:
        members={m.name:m for m in archive if m.isfile()}
        for name,member in members.items():
            if '/manifests/' in name:
                raw=archive.extractfile(member).read();manifest_digests.add(hashlib.sha256(raw).hexdigest());document=json.loads(raw)
                for layer in [document['config'],*document['layers']]:
                    required.add('ollama-models/blobs/'+layer['digest'].replace(':','-'))
        if not required:raise ValueError('OLLAMA_MANIFESTS_REQUIRED')
        for source in runtime['model_sources']:
            if not re.fullmatch('sha256-[a-f0-9]{64}',source['blob']) or 'ollama-models/blobs/'+source['blob'] not in required:
                raise ValueError('OLLAMA_RUNTIME_SOURCE_MISMATCH')
        if {s['model'] for s in runtime['model_sources']}!={m['name'] for m in models}:raise ValueError('OLLAMA_RUNTIME_SOURCE_MISMATCH')
        for name in required:
            member=members.get(name)
            if member is None:raise ValueError('OLLAMA_MODEL_BLOB_MISSING')
            with archive.extractfile(member) as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
            if actual!=name.rsplit('sha256-',1)[-1]:raise ValueError('OLLAMA_MODEL_BLOB_CORRUPT')
    return {'version':runtime['version']['version'],'models':[{'name':m['name'],'digest':m['digest']} for m in models],
        'content_addressed_blobs_verified':len(required),'manifest_file_sha256':sorted(manifest_digests),
        'runtime_model_sources_verified':True,'scope':'Model files verified; host Ollama installer/service not restored on a second machine'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    backup = sub.add_parser('backup'); backup.add_argument('--label', required=True)
    restore = sub.add_parser('restore'); restore.add_argument('--kit', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(create(args.label) if args.action == 'backup' else verify(args.kit), indent=2))

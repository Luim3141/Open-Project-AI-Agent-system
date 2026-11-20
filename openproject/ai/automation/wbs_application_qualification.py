"""Host operator: fixed WBS regression and disposable Native proof, never Main writes."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from automation.main_native_clone import main_native_clone
from automation.main_operations import PRIVATE_ROOT, capture, private_path, verify, work_state
from gateway.application_qa_proof import (
    CODE_SHA256, CORE_SOURCES, DOMAIN, GATEWAY_SOURCES, PRODUCER, QUALIFICATION, MANIFEST_PATH, criteria, validate, qualification_manifest, producer_code_sha256,
)
from gateway.native_qa_runs import snapshot
from gateway.store import canonical, digest

REPO = Path(__file__).resolve().parents[3]
RUNTIME = PRIVATE_ROOT.parent
UNIT_RUNNER = '''import json,pathlib,unittest
from unittest.mock import patch
import httpx,requests
records=[]
class Result(unittest.TextTestResult):
 def addSuccess(self,test):super().addSuccess(test);records.append({'id':test.id(),'outcome':'PASSED'})
 def addFailure(self,test,error):super().addFailure(test,error);records.append({'id':test.id(),'outcome':'FAILED'})
 def addError(self,test,error):super().addError(test,error);records.append({'id':test.id(),'outcome':'FAILED'})
 def addSkip(self,test,reason):super().addSkip(test,reason);records.append({'id':test.id(),'outcome':'BLOCKED'})
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
 ['test_native_wbs_analysis','test_wbs_scheduled_parent_effects'])
with patch('httpx.HTTPTransport.handle_request',side_effect=httpx.ConnectError('OFFLINE_NETWORK_DISABLED')),patch('requests.adapters.HTTPAdapter.send',side_effect=requests.ConnectionError('OFFLINE_NETWORK_DISABLED')):
 result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
pathlib.Path('/out/unit-results.json').write_text(json.dumps({'run':result.testsRun,'records':records,'network':'NONE'},indent=2))
'''


def command(output, *args, data=None, timeout=600):
    result = subprocess.run(['docker', *args], input=data, capture_output=True, timeout=timeout)
    if result.returncode:
        (output / 'docker-error-private.log').write_bytes(result.stdout + result.stderr)
        raise RuntimeError('APPLICATION_QUALIFICATION_DOCKER_FAILED_PRIVATE_LOG')
    return result.stdout


def sources(output):
    code = "import hashlib,json,sys;from pathlib import Path;print(json.dumps({p:hashlib.sha256((Path('/app/gateway')/p).read_bytes()).hexdigest() for p in sys.argv[1:]}))"
    gateway = json.loads(command(output, 'exec', 'qldapm-ai-gateway-1', 'python', '-c', code, *GATEWAY_SOURCES))
    code = "puts JSON.generate(ARGV.to_h { |p| [p,Digest::SHA256.file('/app/'+p).hexdigest] })"
    core = json.loads(command(output, 'exec', 'qldapm-openproject-web-1', 'ruby', '-rjson', '-rdigest', '-e', code, *CORE_SOURCES))
    return {'gateway': gateway, 'core': core}


def owner_source(output):
    code = """import json
from pathlib import Path
from gateway.native import Native
cfg=json.loads(Path('/state/config.json').read_text());keys=json.loads(Path('/state/credentials.json').read_text())
assert cfg['project_id']==5 and cfg['gateway_mode']=='native'
native=Native(cfg['openproject_url'],keys['18'],5);who=native.identity(18)
assert who['user_id']==18 and who['role']=='AI_SYSTEM_OWNER'
print(json.dumps({'identity':who,'item':native.package(371)}))
"""
    return json.loads(command(output, 'exec', 'qldapm-ai-gateway-1', 'python', '-c', code))


def sqlite_snapshot(output, name, target):
    assert name in {'gateway', 'knowledge'}
    code = f"import sqlite3,sys;s=sqlite3.connect('file:/state/{name}.sqlite?mode=ro',uri=True);d=sqlite3.connect(':memory:');s.backup(d);sys.stdout.buffer.write(d.serialize())"
    target.write_bytes(command(output, 'exec', 'qldapm-ai-gateway-1', 'python', '-c', code))


def units(output, image):
    frozen = output / 'unit-input'
    frozen.mkdir()
    shutil.copytree(REPO / 'openproject/ai/tests', frozen / 'tests', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (frozen / 'runner.py').write_text(UNIT_RUNNER)
    result = output / 'unit-output'
    result.mkdir()
    args = ['run', '--rm', '--pull', 'never', '--network', 'none', '--read-only', '--tmpfs', '/tmp:size=128m,mode=1777',
        '--memory', '768m', '--cpus', '1', '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
        '-e', 'QLDAPM_AI_RUNTIME=', '-e', 'PYTHONPATH=/qualification:/qualification/tests:/app',
        '--mount', f'type=bind,source={frozen},target=/qualification,readonly', '--mount', f'type=bind,source={result},target=/out',
        image, 'python', '/qualification/runner.py']
    process = subprocess.run(['docker', *args], capture_output=True, timeout=600)
    (output / 'unit-private.log').write_bytes(process.stdout + process.stderr)
    if process.returncode:
        raise RuntimeError('APPLICATION_UNIT_PROCESS_FAILED_PRIVATE_LOG')
    return json.loads((result / 'unit-results.json').read_text())


def native_wbs(output, images, credentials, config):
    target = output / 'native'
    target.mkdir()
    (target / 'ui.key').write_bytes(uuid.uuid4().bytes + uuid.uuid4().bytes)
    with main_native_clone(target, candidate_web_image=images['core'], ui_key_path=target / 'ui.key') as clone:
        clone['gateway_image'] = images['gateway']
        name = 'qldapm-appqa-' + clone['id'] + '-vector'
        main_vector = json.loads(command(output, 'inspect', 'qldapm-qdrant'))[0]
        identity = (main_vector['Id'], main_vector['Image'], main_vector['State']['StartedAt'])
        command(output, 'run', '-d', '--pull', 'never', '--name', name, '--label', 'org.qldapm.appqa=' + clone['id'],
            '--network', clone['network'], '--network-alias', 'fixture-vector', '--read-only',
            '--tmpfs', '/qdrant/storage:size=256m,mode=1777', '--tmpfs', '/qdrant/snapshots:size=64m,mode=1777',
            '--tmpfs', '/tmp:size=32m,mode=1777', '--memory', '384m', '--cpus', '1', '--pids-limit', '128',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '-e', 'QDRANT__TELEMETRY_DISABLED=true', main_vector['Image'])
        try:
            client = target / 'client'
            client.mkdir()
            (client / 'state').mkdir()
            for table, field in [('work_packages', 'original_max_wp_id'), ('relations', 'original_max_relation_id')]:
                query = 'select coalesce(max(id),0) from ' + table
                clone[field] = int(command(output, 'exec', clone['database'], 'psql', '-U', 'postgres', '-d', 'openproject', '-At', '-c', query))
            (client / 'clone.json').write_text(json.dumps(clone))
            (client / 'config.json').write_text(json.dumps({k: config[k] for k in
                ['project_id', 'gateway_mode', 'type_ids', 'status_ids', 'source_field', 'users', 'openproject_url']}))
            (client / 'credentials.json').write_text(json.dumps(credentials))
            shutil.copy2(target / 'ui.key', client / 'ui.key')
            shutil.copy2(REPO / 'openproject/ai/tests/wbs_application_native_client.py', client / 'qualify.py')
            for name_db in ['gateway', 'knowledge']:
                sqlite_snapshot(output, name_db, client / 'state' / (name_db + '.sqlite'))
            tables = ['work_packages', 'relations', 'users', 'user_passwords', 'two_factor_authentication_devices',
                'tokens', 'members', 'member_roles', 'qldapm_native_deletion_events']
            def fingerprints():
                result = {}
                for table in tables:
                    where = ' where id<=' + str(clone['original_max_wp_id']) if table == 'work_packages' else ' where id<=' + str(clone['original_max_relation_id']) if table == 'relations' else ''
                    query = "select count(*),md5(string_agg(row_to_json(t)::text,E'\\n' order by id)) from " + table + ' t' + where
                    result[table] = command(output, 'exec', clone['database'], 'psql', '-U', 'postgres', '-d', 'openproject', '-At', '-c', query).decode().strip()
                return result
            before = fingerprints()
            args = ['run', '--rm', '--pull', 'never', '--network', clone['network'], '--read-only', '--tmpfs', '/tmp:size=64m,mode=1777',
                '--memory', '512m', '--cpus', '1', '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                '-e', 'QLDAPM_AI_RUNTIME=', '-e', 'PYTHONPATH=/app', '-e', 'QLDAPM_APPLICATION_QUALIFICATION=' + clone['id'],
                '--mount', f'type=bind,source={client},target=/qualification', images['gateway'], 'python', '/qualification/qualify.py']
            (target / 'client-private.log').write_bytes(command(output, *args, timeout=1200))
            if fingerprints() != before:
                raise RuntimeError('APPLICATION_NATIVE_ORIGINAL_DATA_CHANGED')
            result = json.loads((client / 'result.json').read_text())
            if (result['status'] != 'PASS_RETAINED_BA_TO_ISOLATED_NATIVE_WBS_RELATION_SCHEDULE_RAG_RECOVERY' or
                    result['new_model_calls_in_clone'] != 0 or not result['raw_ba_output_unchanged']):
                raise RuntimeError('APPLICATION_NATIVE_QUALIFICATION_INCOMPLETE')
            result.update(original_data_hashes_preserved=before, source_dump_sha256=clone['source_dump_sha256'])
            (target / 'result.json').write_text(json.dumps(result, indent=2))
            return result
        finally:
            own = json.loads(command(output, 'inspect', name))[0]
            if own['Config']['Labels'].get('org.qldapm.appqa') != clone['id']:
                raise RuntimeError('APPLICATION_VECTOR_RESOURCE_OWNERSHIP_CHANGED')
            command(output, 'rm', '-f', name)
            current = json.loads(command(output, 'inspect', 'qldapm-qdrant'))[0]
            if identity != (current['Id'], current['Image'], current['State']['StartedAt']):
                raise RuntimeError('MAIN_VECTOR_CHANGED_DURING_APPLICATION_QUALIFICATION')


def qualify(output):
    output = private_path(output)
    output.mkdir(parents=False, exist_ok=False)
    pinned = json.loads(MANIFEST_PATH.read_text())
    if qualification_manifest() != pinned:
        raise RuntimeError('APPLICATION_QUALIFIER_SOURCE_CHANGED_REBUILD_MANIFEST')
    manifest = capture()
    if work_state()['active']:
        raise RuntimeError('MAIN_ACTIVE_WORK_HOLD')
    config = json.loads((RUNTIME / 'gateway/config.json').read_text())
    credentials = json.loads((RUNTIME / 'gateway/credentials.json').read_text())
    key_file = RUNTIME / 'gateway/ui.key'
    key = key_file.read_bytes()
    if config['project_id'] != 5 or config['gateway_mode'] != 'native':
        raise RuntimeError('MAIN_NATIVE_SCOPE_REQUIRED')
    observed = owner_source(output)
    who = observed['identity']
    if who['user_id'] != 18 or who['role'] != 'AI_SYSTEM_OWNER':
        raise PermissionError('APPLICATION_OWNER_PRODUCER_REQUIRED')
    item = observed['item']
    source = snapshot(item)
    actual_criteria = criteria(item)
    images = {'gateway': manifest['containers']['qldapm-ai-gateway-1']['image'],
        'core': manifest['containers']['qldapm-openproject-web-1']['image']}
    hashes = sources(output)
    started = time.time()
    unit = units(output, images['gateway'])
    records = unit['records']
    groups = {'AC1': [r for r in records if r['id'].startswith('test_native_wbs_analysis.NativeWbsAnalysisTests.')],
        'AC2': [r for r in records if r['id'].endswith('.test_exact_native_two_save_first_child_and_later_child_chain')],
        'AC3': [r for r in records if r['id'].endswith(('.test_business_edit_unknown_child_extra_version_and_bad_calendar_are_not_parent_effects',
            '.test_expanded_parent_changes_do_not_change_the_verified_work_package'))]}
    tests = []
    for criterion, count in [('AC1', 13), ('AC2', 1), ('AC3', 2)]:
        rows = groups[criterion]
        verdict = 'BLOCKED' if len(rows) != count or any(r['outcome'] == 'BLOCKED' for r in rows) else 'FAILED' if any(r['outcome'] == 'FAILED' for r in rows) else 'PASSED'
        tests.append({'criterion_id': criterion, 'reference': 'wbs-application:' + criterion,
            'expected': str(count) + ' pinned application regression tests pass',
            'actual': canonical({'tests': len(rows), 'passed': sum(r['outcome'] == 'PASSED' for r in rows), 'records': rows}),
            'outcome': verdict, 'proof_sha256': digest(canonical(rows))})
    if unit['run'] != 16 or len(records) != 16:
        raise RuntimeError('APPLICATION_UNIT_MANIFEST_CHANGED')
    # A failing application suite is retained; it never becomes a passing Native proof.
    if any(test['outcome'] != 'PASSED' for test in tests):
        (output / 'blocked.json').write_text(json.dumps({'status': 'FAILED_APPLICATION_REGRESSION', 'tests': tests}, indent=2))
        raise RuntimeError('APPLICATION_REGRESSION_FAILED_NO_PASS_ARTIFACT')
    result = native_wbs(output, images, credentials, config)
    tests.append({'criterion_id': 'AC4', 'reference': 'wbs-application:AC4',
        'expected': 'Four actual Native WBS nodes with supplied dates/follows, target RAG and one create after lost ACK',
        'actual': canonical({'status': result['status'], 'nodes': list(result['native_readback']),
            'raw_ba_output_unchanged': result['raw_ba_output_unchanged'], 'lost_ack': result['lost_node_response_reconciled_one_create']}),
        'outcome': 'PASSED', 'proof_sha256': digest(canonical(result))})
    verify(manifest)
    if qualification_manifest() != pinned or producer_code_sha256() != CODE_SHA256:
        raise RuntimeError('APPLICATION_QUALIFIER_CHANGED_DURING_RUN')
    if sources(output) != hashes or snapshot(owner_source(output)['item']) != source or key_file.read_bytes() != key:
        raise RuntimeError('APPLICATION_SOURCE_BUILD_OR_KEY_CHANGED_NO_PASS_ARTIFACT')
    body = {'version': 1, 'id': str(uuid.uuid4()), 'actor': 18, 'project_id': 5, 'producer': PRODUCER,
        'producer_sha256': CODE_SHA256, 'source': source, 'criteria': actual_criteria, 'sources': hashes, 'build': images,
        'started_at': started, 'finished_at': time.time(), 'tests': tests, 'verdict': 'PASSED', 'qualification': QUALIFICATION}
    text = canonical(body)
    bundle = {'document': text, 'signature': hmac.new(key, DOMAIN + text.encode(), hashlib.sha256).hexdigest()}
    validate(bundle, key, owner_source(output)['item'], hashes)
    (output / 'proof.json').write_text(json.dumps(bundle, indent=2))
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return {'status': 'QUALIFIED_PRIVATE_ARTIFACT_NOT_IMPORTED_OR_HUMAN_REVIEWED', 'id': body['id'],
        'artifact_sha256': digest(text), 'verdict': body['verdict'], 'main_native_writes': 0, 'new_model_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', help='New dedicated directory below the existing private operator directory')
    print(json.dumps(qualify(parser.parse_args().output)))

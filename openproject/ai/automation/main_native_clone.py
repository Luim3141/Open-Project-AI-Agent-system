"""Host-only Main snapshot qualification; disposable resources never share Main networks or volumes."""
import hashlib
import json
import re
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def owned_resource(name, identifier, kind='container'):
    if not re.fullmatch(r'[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}', identifier):
        raise ValueError('QUALIFICATION_UUID_REQUIRED')
    suffix = '(?:db|web)' if kind == 'container' else 'net' if kind == 'network' else None
    if suffix is None or not re.fullmatch('qldapm-main-qualification-' + re.escape(identifier) + '-' + suffix, name):
        raise ValueError('QUALIFICATION_RESOURCE_DENIED')
    field = '.Config.Labels' if kind == 'container' else '.Labels'
    args = ['docker', 'inspect'] if kind == 'container' else ['docker', 'network', 'inspect']
    label = subprocess.check_output(args + ['--format', '{{index ' + field + ' "org.qldapm.qualification"}}', name], stderr=subprocess.PIPE)
    return label.decode().strip() == identifier


@contextmanager
def main_native_clone(output, *, candidate_web_image=None, ui_key_path=None, migration_versions=(), source_dump_path=None, before_web=None, web_start_timeout=120):
    if type(web_start_timeout) is not int or not 1<=web_start_timeout<=480:raise ValueError('CLONE_WEB_START_TIMEOUT_INVALID')
    if before_web is not None and not callable(before_web):raise ValueError('ISOLATED_BOOTSTRAP_CALLBACK_REQUIRED')
    supplied_dump = None
    if source_dump_path is not None:
        backup = Path(source_dump_path)
        if not backup.is_file():
            raise ValueError('POSTGRES_BACKUP_REQUIRED')
        supplied_dump = backup.read_bytes()
        if not supplied_dump.startswith(b'PGDMP'):
            raise ValueError('POSTGRES_BACKUP_REQUIRED')
    if (not isinstance(migration_versions,tuple) or len(migration_versions)>5 or
            any(not isinstance(version,str) or not re.fullmatch(r'[0-9]{14}',version) for version in migration_versions) or
            migration_versions and candidate_web_image is None):
        raise ValueError('ISOLATED_EXACT_CANDIDATE_MIGRATIONS_REQUIRED')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    shared_key=None
    if ui_key_path is not None:
        shared_key=Path(ui_key_path).resolve()
        if not shared_key.is_relative_to(root.resolve()) or not shared_key.is_file() or not 16<=shared_key.stat().st_size<=4096:
            raise ValueError('ISOLATED_CLONE_OWN_KEY_REQUIRED')
    identifier = str(uuid.uuid4())
    prefix = 'qldapm-main-qualification-' + identifier
    database, web, network = prefix + '-db', prefix + '-web', prefix + '-net'
    created = []
    def docker(*args, **kwargs):
        result = subprocess.run(['docker', *args], capture_output=True, timeout=600, **kwargs)
        if result.returncode:
            (root/'clone-command-error.log').write_bytes(result.stdout + result.stderr)
            raise RuntimeError('CLONE_COMMAND_FAILED_PRIVATE_LOG')
        return result.stdout
    main = [json.loads(docker('inspect', name))[0] for name in ['qldapm-openproject-db-1', 'qldapm-openproject-web-1']]
    for item in main:
        if item['Config'].get('Labels', {}).get('com.docker.compose.project') != 'qldapm-openproject' or item['State']['Status'] != 'running':
            raise ValueError('MAIN_SOURCE_IDENTITY_REQUIRED')
    images = {role: item['Image'] for role, item in zip(['database', 'web'], main)}
    if any(not re.fullmatch('sha256:[a-f0-9]{64}', value) for value in images.values()):
        raise ValueError('EXACT_MAIN_IMAGES_REQUIRED')
    source_images = dict(images)
    if candidate_web_image is not None:
        if not re.fullmatch('sha256:[a-f0-9]{64}', candidate_web_image):
            raise ValueError('EXACT_CANDIDATE_IMAGE_REQUIRED')
        actual = json.loads(docker('image', 'inspect', candidate_web_image))[0]['Id']
        if actual != candidate_web_image:raise ValueError('CANDIDATE_IMAGE_MISMATCH')
        images['web'] = actual
    dump = supplied_dump if supplied_dump is not None else docker('exec', 'qldapm-openproject-db-1', 'pg_dump', '-U', 'postgres', '-Fc', 'openproject')
    (root/'clone-source.dump').write_bytes(dump)
    info = {'id': identifier, 'database': database, 'web': web, 'network': network,
            'base_url': 'http://web:8080', 'images': images, 'source_images': source_images, 'source_dump_sha256': hashlib.sha256(dump).hexdigest(),
            'source': 'Supplied backup; isolated restore' if supplied_dump is not None else 'Main read-only pg_dump; no Staging source', 'main_mutations': 0,
            'isolated_ui_key_shared':shared_key is not None}
    (root/'clone.json').write_text(json.dumps(info, indent=2))
    try:
        docker('network', 'create', '--internal', '--label', 'org.qldapm.qualification=' + identifier, network)
        created.append(('network', network))
        docker('run', '-d', '--pull', 'never', '--name', database, '--label', 'org.qldapm.qualification=' + identifier,
               '--network', network, '--network-alias', 'qa-db', '--user', 'postgres', '--read-only',
               '--tmpfs', '/tmp:size=512m,mode=1777', '--tmpfs', '/var/run/postgresql:mode=1777',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '--memory', '512m', '--cpus', '1', '--pids-limit', '128',
               '-e', 'PGDATA=/tmp/postgres', '-e', 'POSTGRES_DB=openproject', '-e', 'POSTGRES_HOST_AUTH_METHOD=trust', images['database'])
        created.append(('container', database))
        for _ in range(60):
            ready = subprocess.run(['docker', 'exec', database, 'pg_isready', '-U', 'postgres', '-d', 'openproject'], capture_output=True)
            if ready.returncode == 0:break
            time.sleep(1)
        else:raise RuntimeError('CLONE_DATABASE_TIMEOUT')
        docker('exec', '-i', database, 'pg_restore', '-U', 'postgres', '--no-owner', '--exit-on-error', '-d', 'openproject', input=dump)
        print('Isolated Main database restored; starting fixed Core image', flush=True)
        environment = {'DATABASE_URL': 'postgres://postgres@qa-db/openproject?pool=5&encoding=unicode',
                       'SECRET_KEY_BASE': 'isolated-qualification-only-' + '0'*96, 'RAILS_ENV': 'production',
                       'OPENPROJECT_HOST__NAME': 'localhost:8088', 'OPENPROJECT_ADDITIONAL__HOST__NAMES': json.dumps(['localhost', 'localhost:8088', 'web']),
                       'OPENPROJECT_HTTPS': 'false', 'OPENPROJECT_HSTS': 'false', 'OPENPROJECT_RAILS__CACHE__STORE': 'file_store',
                       'OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL': '', 'OPENPROJECT_WEB_WORKERS': '1',
                       'RAILS_MIN_THREADS': '1', 'RAILS_MAX_THREADS': '2', 'IMAP_ENABLED': 'false', 'QLDAPM_TEST_ONLY': 'true'}
        args = ['run', '-d', '--pull', 'never', '--name', web, '--label', 'org.qldapm.qualification=' + identifier,
                '--network', network, '--network-alias', 'web', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                '--memory', '1536m', '--cpus', '1.5', '--pids-limit', '256', '--tmpfs', '/tmp:size=128m,mode=1777',
                '--tmpfs', '/app/tmp:size=128m,mode=1777', '--tmpfs', '/app/log:size=32m,mode=1777',
                '--tmpfs', '/var/openproject/assets:size=128m,mode=1777']
        for key, value in environment.items():args += ['-e', key + '=' + value]
        if shared_key is not None:
            args += ['--mount',f'type=bind,source={shared_key},target=/tmp/qa-ui.key,readonly','-e','QLDAPM_UI_KEY_FILE=/tmp/qa-ui.key']
        if migration_versions:
            # Apply only requested versions on the restored private DB, before the Web readiness check.
            docker(*args, images['web'], 'sleep', '600');created.append(('container',web))
            for version in migration_versions:
                docker('exec','--user','app',web,'bundle','exec','rails','db:migrate:up','VERSION='+version)
            docker('rm','-f',web);created.remove(('container',web))
            info['isolated_migrations']=list(migration_versions)
            (root/'clone.json').write_text(json.dumps(info,indent=2))
        if before_web is None:
            docker(*args, images['web'], './docker/prod/web');created.append(('container', web))
        else:
            # One Rails boot at a time fits the existing clone memory/CPU limits.
            docker(*args, images['web'], 'sleep','3600');created.append(('container',web))
            before_web(web)
            docker('exec','-d',web,'/bin/sh','-c','echo $$ >/tmp/clone-web-server.pid; exec ./docker/prod/web >/tmp/clone-web-server.log 2>&1')
            info['isolated_bootstrap_before_web']=True
        for _ in range(web_start_timeout):
            healthy = subprocess.run(['docker', 'exec', web, 'curl', '-fsS', 'http://localhost:8080/health_checks/default'], capture_output=True)
            if healthy.returncode == 0:break
            status = json.loads(docker('inspect', web))[0]['State']
            if status['Status'] != 'running':raise RuntimeError('CLONE_WEB_EXITED')
            time.sleep(1)
        else:raise RuntimeError('CLONE_WEB_TIMEOUT')
        print('Isolated Native API healthy; no shared Main volume/network', flush=True)
        yield info
    finally:
        if ('container', web) in created:
            (root/'clone-web.log').write_bytes(docker('logs', web))
            if before_web is not None:
                log=subprocess.run(['docker','exec',web,'cat','/tmp/clone-web-server.log'],capture_output=True,timeout=15)
                (root/'clone-web-server.log').write_bytes(log.stdout+log.stderr)
        for kind, name in reversed(created):
            if not owned_resource(name, identifier, kind):
                raise RuntimeError('CLONE_CLEANUP_LABEL_MISMATCH')
            docker('rm', '-f', name) if kind == 'container' else docker('network', 'rm', name)
        for old in main:
            current = json.loads(docker('inspect', old['Name']))[0]
            if (current['Id'], current['Image'], current['State']['StartedAt']) != (old['Id'], old['Image'], old['State']['StartedAt']):
                raise RuntimeError('UNEXPECTED_MAIN_RUNTIME_CHANGE')

"""Read-only candidate Core against the existing staging database. No seeder/migrations."""
import json
from contextlib import contextmanager
from pathlib import Path
import subprocess
import time

from provision_local_stage import daily_report_core


@contextmanager
def core_clone(docker, image, name, label, root):
    primary = json.loads(docker('inspect', 'qldapm-ai-stage-staging-web-1'))[0]
    candidate = json.loads(docker('image', 'inspect', image))[0]
    previous = json.loads(docker('image', 'inspect', primary['Image']))[0]
    daily_report_core(candidate, previous)
    # libpq applies read-only mode to every connection, including Rack authentication.
    env = [value for value in primary['Config']['Env'] if not value.startswith('PGOPTIONS=')]
    env.append('PGOPTIONS=-c default_transaction_read_only=on')
    envfile = root / 'core-readonly.env'
    envfile.write_text('\n'.join(env) + '\n')
    args = ['run', '-d', '--name', name, '--label', label, '--network', 'qldapm-ai-stage_stage',
            '--env-file', str(envfile), '--memory', '2g', '--pids-limit', '256', '--entrypoint', 'bundle',
            image, 'exec', 'rails', 'server', '-b', '0.0.0.0', '-p', '8080']
    try:
        docker(*args)
        check = "require 'pg'; c=PG.connect(ENV.fetch('DATABASE_URL')); raise 'NOT_READ_ONLY' unless c.exec('SHOW default_transaction_read_only').getvalue(0,0) == 'on'; puts 'READ_ONLY'"
        docker('exec', name, 'bundle', 'exec', 'ruby', '-e', check)
        for _ in range(90):
            probe = subprocess.run(['docker', 'exec', name, 'curl', '-fsS', 'http://127.0.0.1:8080/health_checks/default'],
                                   capture_output=True, timeout=10)
            if probe.returncode == 0:
                break
            time.sleep(2)
        else:
            raise RuntimeError('READ_ONLY_CORE_NOT_READY')
        ip = json.loads(docker('inspect', name))[0]['NetworkSettings']['Networks']['qldapm-ai-stage_stage']['IPAddress']
        yield ip
    finally:
        found = docker('ps', '-aq', '--filter', 'name=^/' + name + '$', '--filter', 'label=' + label)
        if found:
            logs = subprocess.run(['docker', 'logs', name], capture_output=True, timeout=20)
            (root / 'core-private.log').write_bytes(logs.stdout + logs.stderr)
            info = json.loads(docker('inspect', name))[0]
            assert info['Image'] == image and info['Config']['Labels'].get('qldapm.acceptance.p04-owner') == label.split('=', 1)[1]
            docker('stop', '--time', '30', name)
            docker('rm', name)

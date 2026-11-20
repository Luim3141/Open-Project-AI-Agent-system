"""Build and qualify a new Gateway, replacing only the idle owned clone; retain every prior container."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from start_qualification import OUT, PRIVATE, ROOT, docker, inspect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=int, choices=(2, 3), required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args(); version = args.version
    proof_path = OUT / f'gateway-v{version}-qualification.json'
    if args.resume:
        previous = json.loads(proof_path.read_text())
        assert previous['phase'] == 'BUILDING' and previous['linux_exit_code'] != 0
        (OUT / f'gateway-v{version}-initial-failed.json').write_bytes(proof_path.read_bytes())
        (OUT / f'gateway-v{version}-linux-initial-failed.log').write_bytes((OUT / f'gateway-v{version}-linux.log').read_bytes())
    else:
        assert not proof_path.exists(), 'EXISTING_CANDIDATE_RECONCILE_BEFORE_RETRY'
    ai = ROOT / 'openproject/ai'
    excluded = {line.strip() for line in (ai / '.dockerignore').read_text().splitlines() if line.startswith('gateway/')}
    files = {p.relative_to(ai).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (ai / 'gateway').glob('*') if p.is_file() and p.relative_to(ai).as_posix() not in excluded}
    for name in ('Dockerfile', 'requirements.lock.txt'):
        files[name] = hashlib.sha256((ai / name).read_bytes()).hexdigest()
    source_hash = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    tag = f'qldapm-ai:rd-qual-20261021-v{version}'
    command = ['docker', 'build', '--file', str(ai / 'Dockerfile'), '--tag', tag,
               '--label', 'org.qldapm.source.sha256=' + source_hash,
               '--label', 'org.qldapm.deployment=isolated-qualification', str(ai)]
    result = {'version': version, 'source_sha256': source_hash, 'files': files, 'build_command': command,
              'scope': 'QUALIFIED_NOT_DEPLOYED', 'provider_calls': 0, 'serving_changes': 0, 'phase': 'BUILDING'}
    proof_path.write_text(json.dumps(result, indent=2))
    with (OUT / f'gateway-v{version}-build.log').open('wb') as log:
        built = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    assert built.returncode == 0, 'CANDIDATE_BUILD_FAILED'
    image = json.loads(docker('image', 'inspect', tag))[0]['Id']
    result['image'] = image
    tests = ['tests.test_remaining_integration', 'tests.test_planner', 'tests.test_supervisor',
             'tests.test_reviewer_agent',
             'tests.test_execution_monitor', 'tests.test_live_agents']
    args = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,size=256m',
            '--env', 'QLDAPM_AI_RUNTIME=', '--env', 'PYTHONPATH=/app', '--mount',
            f'type=bind,src={ai / "tests"},dst=/app/tests,readonly', '--entrypoint', 'python', image, '-m', 'unittest', *tests]
    with (OUT / f'gateway-v{version}-linux.log').open('wb') as log:
        tested = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    result['linux_exit_code'] = tested.returncode
    proof_path.write_text(json.dumps(result, indent=2))
    assert tested.returncode == 0, 'CANDIDATE_CONTRACTS_FAILED_NO_CLONE_REFRESH'
    state = PRIVATE / 'state'
    assert not (state / 'gemini.key').exists() and json.loads((state / 'gemini.json').read_text())['enabled'] is False
    q = json.loads((OUT / 'qualification.json').read_text())
    name = q['names']['gateway']; current = inspect(name)
    assert current['Config']['Labels']['qldapm.qualification'] == 'remaining-20261021'
    program = "import json,sqlite3; d=sqlite3.connect('/state/gateway.sqlite'); assert not d.execute(\"SELECT 1 FROM ai_runs WHERE state='running'\").fetchone(); b=sqlite3.connect('/state/before-v" + str(version) + ".sqlite');d.backup(b);b.close();d.close();print('IDLE_BACKUP_OK')"
    docker('exec', name, 'python', '-c', program)
    old_name = name + f'-v{version - 1}'
    assert old_name not in docker('ps', '-a', '--format', '{{.Names}}').splitlines()
    docker('stop', '--time', '20', name)
    docker('rename', name, old_name)
    docker('run', '-d', '--name', name, '--label', 'qldapm.qualification=remaining-20261021',
           '--network', q['names']['network'], '--network-alias', 'gateway', '--read-only',
           '--tmpfs', '/tmp:rw,size=64m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
           '--memory', '512m', '--mount', f'type=bind,src={state},dst=/state', image)
    q['gateway_image'] = image; q['previous_gateway'] = old_name
    (OUT / 'qualification.json').write_text(json.dumps(q, indent=2))
    program = "import httpx;assert httpx.get('http://127.0.0.1:8090/health',trust_env=False).status_code==200;print('HEALTH_OK')"
    for _ in range(10):
        health = subprocess.run(['docker', 'exec', name, 'python', '-c', program], capture_output=True, timeout=10)
        if health.returncode == 0:
            break
        time.sleep(1)
    assert health.returncode == 0, 'CLONE_HEALTH_FAILED_PREVIOUS_CONTAINER_RETAINED'
    program = "import hashlib,json,pathlib;print(json.dumps({p.relative_to('/app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app/gateway').glob('*') if p.is_file()}))"
    actual = json.loads(docker('exec', name, 'python', '-c', program))
    assert all(actual[k] == v for k, v in files.items() if k.startswith('gateway/'))
    result.update(phase='CLONE_HEALTH_PARITY_AND_LINUX_PASS', passed=True, runtime_files_matched=len(actual),
                  previous_clone_container=old_name)
    proof_path.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ('files', 'build_command')}))


if __name__ == '__main__':
    main()

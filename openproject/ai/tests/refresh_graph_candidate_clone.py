from pathlib import Path
import json, sys, time, os

sys.path.insert(0, str(Path('openproject/ai').resolve()))
from jira_sync_backup import command, inspect

def main():
    core_name = 'qldapm-em-core-20261019-1635'
    candidate_image = 'qldapm-graph-candidate:final'
    label = 'execution-monitor-20261019-1635'

    old = inspect(core_name)
    assert old['Config']['Labels'].get('qldapm.qualification') == label, "Label mismatch on core clone"

    print(f"Stopping old clone {core_name}...")
    try:
        command(['docker', 'stop', core_name])
    except Exception:
        pass

    backup_name = core_name + '-old-' + str(time.time_ns())
    print(f"Renaming old clone to {backup_name}...")
    command(['docker', 'rename', core_name, backup_name])

    args = [
        'docker', 'run', '-d',
        '--name', core_name,
        '--label', f'qldapm.qualification={label}',
        '--network', 'qldapm-rd-20261018',
        '--network-alias', 'staging-web',
        '--memory', '1536m',
        '--pids-limit', '256',
        '--entrypoint', 'sleep'
    ]

    for k, v in old['HostConfig']['PortBindings'].items():
        for port in v:
            args += ['-p', f"{port['HostIp']}:{port['HostPort']}:{k.split('/')[0]}"]

    for e in old['Config']['Env']:
        args += ['--env', e]

    for m in old['Mounts']:
        if m['Type'] not in ['bind', 'volume']:
            continue
        source = m.get('Name') if m['Type'] == 'volume' else m['Source']
        args += ['--mount', f"type={m['Type']},source={source},target={m['Destination']}" + ('' if m.get('RW') else ',readonly')]

    args += [candidate_image, 'infinity']

    print(f"Starting candidate container with {candidate_image}...")
    command(args)
    command(['docker', 'network', 'connect', 'qldapm-rd-loopback-20261018', core_name])

    print("Launching Rails server inside candidate clone...")
    command(['docker', 'exec', '-d', core_name, 'bundle', 'exec', 'rails', 'server', '-b', '0.0.0.0', '-p', '8080', '--pid', '/tmp/execution-monitor.pid'])

    print("Candidate clone launched successfully! Waiting for port 18097 to respond...")
    import httpx
    for i in range(60):
        try:
            resp = httpx.get('http://127.0.0.1:18097/login', timeout=3.0)
            if resp.status_code == 200:
                print(f"Ready! Status {resp.status_code} after {i+1} attempts.")
                return
        except Exception:
            pass
        time.sleep(2)
    print("Warning: Timed out waiting for 18097/login, but Rails may still be booting.")

if __name__ == '__main__':
    main()

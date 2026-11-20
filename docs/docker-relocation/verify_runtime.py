"""Read-only engine inventory comparison after physical Docker data relocation."""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/docker-relocation-20261016'


def command(arguments):
    try:
        result = subprocess.run(arguments, capture_output=True, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('MIGRATION_READ_TIMEOUT:' + arguments[0]) from error
    if result.returncode:
        raise RuntimeError('MIGRATION_READ_FAILED:' + arguments[0])
    return result.stdout.decode('utf-8').strip()


def collect():
    rows = []
    identifiers = command(['docker', 'ps', '-aq']).splitlines()
    for row in json.loads(command(['docker', 'inspect', *identifiers])) if identifiers else []:
        rows.append({'id': row['Id'], 'name': row['Name'].lstrip('/'), 'image': row['Image'],
                     'running': row['State']['Running'], 'status': row['State']['Status'],
                     'health': row['State'].get('Health', {}).get('Status'),
                     'restart': row['HostConfig']['RestartPolicy']['Name'],
                     'mounts': sorted([{'type': m['Type'], 'source': m['Source'], 'target': m['Destination'], 'rw': m['RW']}
                                       for m in row['Mounts']], key=lambda m: m['target']),
                     'ports': row['HostConfig'].get('PortBindings'), 'networks': sorted(row['NetworkSettings']['Networks'])})
    images = [json.loads(line) for line in command(['docker', 'image', 'ls', '--format', 'json']).splitlines()]
    info = json.loads(command(['docker', 'info', '--format', '{{json .}}']))
    return {'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'containers': rows,
            'images': sorted({i['ID'] for i in images}),
            'image_tags': sorted([i['Repository'], i['Tag'], i['ID']] for i in images),
            'volumes': sorted(command(['docker', 'volume', 'ls', '-q']).splitlines()),
            'networks': sorted(command(['docker', 'network', 'ls', '--format', '{{.ID}} {{.Name}}']).splitlines()),
            'engine': {k: info.get(k) for k in ('ID', 'Name', 'ServerVersion', 'Driver', 'DockerRootDir', 'OSType', 'OperatingSystem', 'NCPU', 'MemTotal')}}


def verify(before, after):
    for field in ('images', 'image_tags', 'volumes', 'engine'):
        assert before[field] == after[field], 'CHANGED:' + field
    old_networks = {name: identifier for identifier, name in (row.split(' ', 1) for row in before['networks'])}
    new_networks = {name: identifier for identifier, name in (row.split(' ', 1) for row in after['networks'])}
    assert old_networks.keys() == new_networks.keys(), 'NETWORK_NAMES_CHANGED'
    # The engine recreates its built-in bridge; every user-created network ID must survive.
    for name, identifier in old_networks.items():
        if name != 'bridge':
            assert identifier == new_networks[name], 'CUSTOM_NETWORK_ID_CHANGED:' + name
    old = {row['id']: row for row in before['containers']}
    new = {row['id']: row for row in after['containers']}
    assert old.keys() == new.keys(), 'CONTAINER_IDS_CHANGED'
    for identifier, row in old.items():
        current = new[identifier]
        for field in ('name', 'image', 'restart', 'mounts', 'ports', 'networks', 'running'):
            assert row[field] == current[field], 'CONTAINER_CHANGED:' + row['name'] + ':' + field
        if row['running'] and row['health'] == 'healthy':
            assert current['health'] == 'healthy', 'NOT_HEALTHY:' + row['name']
        if not row['running']:
            assert current['status'] == row['status'], 'STOPPED_STATE_CHANGED:' + row['name']


def self_check():
    fixture = {'images': ['pinned'], 'image_tags': [], 'volumes': ['keep'], 'networks': ['old bridge', 'fixed custom'], 'engine': {'ID': 'same'},
               'containers': [{'id': 'fixed', 'name': 'fixture', 'image': 'pinned', 'restart': 'unless-stopped',
                               'mounts': [], 'ports': {}, 'networks': [], 'running': True, 'health': 'healthy', 'status': 'running'}]}
    verify(fixture, copy.deepcopy(fixture))
    regenerated = copy.deepcopy(fixture)
    regenerated['networks'][0] = 'new bridge'
    verify(fixture, regenerated)
    changed_network = copy.deepcopy(fixture)
    changed_network['networks'][1] = 'wrong custom'
    try:
        verify(fixture, changed_network)
    except AssertionError:
        pass
    else:
        raise AssertionError('SELF_CHECK_DID_NOT_DENY:custom_network')
    for field in ('volumes', 'images'):
        changed = copy.deepcopy(fixture)
        changed[field] = []
        try:
            verify(fixture, changed)
        except AssertionError:
            continue
        raise AssertionError('SELF_CHECK_DID_NOT_DENY:' + field)
    changed = copy.deepcopy(fixture)
    changed['containers'][0]['running'] = False
    try:
        verify(fixture, changed)
    except AssertionError:
        print('Migration verifier self-check PASS: volume/image loss and stopped container denied')
        return
    raise AssertionError('SELF_CHECK_DID_NOT_DENY:stopped')


def main():
    before = json.loads((PRIVATE / 'before.json').read_text())
    deadline = time.monotonic() + 480
    previous_wait = None
    while time.monotonic() < deadline:
        try:
            after = collect()
        except RuntimeError:
            time.sleep(5)
            continue
        expected = {row['id'] for row in before['containers'] if row['running']}
        waiting = sorted(row['name'] for row in after['containers'] if row['id'] in expected and
                         (not row['running'] or row['health'] not in (None, 'healthy')))
        if waiting:
            if waiting != previous_wait:
                print(json.dumps({'waiting_for': waiting}), flush=True)
                previous_wait = waiting
            time.sleep(5)
            continue
        verify(before, after)
        # MSIX redirects AppData and HKCU in Codex children; inspect from a real host task.
        host_path = Path('D:/Docker/relocation-host-state.json')
        assert time.time() - host_path.stat().st_mtime < 600, 'REAL_HOST_PATH_EVIDENCE_STALE'
        host = json.loads(host_path.read_text(encoding='utf-8-sig'))
        control = Path(host['control_root']['FullName'])
        resolved = Path('D:/Docker/wsl')
        entries = {row['Name']: row for row in host['entries']}
        for part in ('wsl', 'log', 'tasks'):
            assert [Path(p) for p in entries[part]['Target']] == [Path('D:/Docker') / part], 'REAL_HOST_JUNCTION_MISMATCH:' + part
        assert Path(host['custom_wsl']) == resolved, 'CUSTOM_WSL_SETTING_MISMATCH'
        assert host['containerd_store'] is True, 'ORIGINAL_IMAGE_STORE_NOT_RESTORED'
        bases = [row['BasePath'] for row in host['registry'] if row['DistributionName'] == 'docker-desktop']
        assert bases == [r'\\?\D:\Docker\wsl\main'], 'WSL_REGISTRATION_NOT_DIRECT_D'
        switch = json.loads((ROOT / 'docs/docker-relocation/switch-state.json').read_text(encoding='utf-8-sig'))
        assert Path(switch['retained_original_root']).is_dir()
        assert Path(switch['retained_original_wsl']).is_dir()
        (PRIVATE / 'after.json').write_text(json.dumps(after, indent=2))
        receipt = {'passed': True, 'physical_data_root': 'D:\\Docker', 'physical_wsl': str(resolved),
                   'control_ipc_stub': str(control), 'direct_wsl_registration': True, 'same_engine_id': True,
                   'containers_retained': len(after['containers']), 'running_recovered': len(expected),
                   'images_retained': len(after['images']), 'volumes_retained': len(after['volumes']),
                   'networks_retained': len(after['networks']), 'all_previous_healthy_recovered': True,
                   'custom_network_ids_unchanged': True,
                   'default_bridge_before': next(row for row in before['networks'] if row.endswith(' bridge')),
                   'default_bridge_after': next(row for row in after['networks'] if row.endswith(' bridge')),
                   'same_images_mounts_ports_restart_policies': True, 'stopped_containers_stay_stopped': True,
                   'both_original_locations_retained': True, 'deleted_items': 0, 'formatted_disks': 0}
        (ROOT / 'docs/docker-relocation/runtime-verification.json').write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt), flush=True)
        return
    raise RuntimeError('MIGRATION_RECOVERY_TIMEOUT_KEEP_BOTH_DATASETS')


if __name__ == '__main__':
    self_check() if sys.argv[1:] == ['--self-test'] else main()

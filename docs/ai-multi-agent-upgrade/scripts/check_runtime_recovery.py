"""Compare two redacted runtime inventories; mounting order is not semantic."""
import argparse
import json
from pathlib import Path


def verify(before, after):
    old = {c['name']: c for c in before['containers']}
    new = {c['name']: c for c in after['containers']}
    assert old.keys() == new.keys(), 'CONTAINER_SET_CHANGED'
    for name, row in old.items():
        current = new[name]
        assert row['image'] == current['image'], 'IMAGE_CHANGED:' + name
        assert sorted(row['mounts'], key=lambda m: m['target']) == sorted(current['mounts'], key=lambda m: m['target']), 'MOUNT_CHANGED:' + name
        assert row['ports'] == current['ports'], 'PORT_CHANGED:' + name
        if name.startswith('qldapm-ai-stage-'):
            assert current['restart'] == 'unless-stopped', 'RESTART_POLICY:' + name
            if row['status'] == 'running':
                assert current['status'] == 'running' and current['health'] == 'healthy', 'NOT_HEALTHY:' + name
            else:
                # Retired Radmin proxy must stay stopped when Quick Tunnel replaces it.
                assert current['status'] == row['status'], 'STOPPED_SERVICE_RESTARTED:' + name
    for key in ('databases', 'gateways', 'private_metadata'):
        assert before[key] == after[key], 'STATE_CHANGED:' + key
    assert after['http']['18091'] == after['http']['18092'] == 200, 'STAGE_HTTP_FAILED'
    return {'pass': True, 'before': before['observed_at'], 'after': after['observed_at'],
            'same_container_images_mounts_ports': True, 'active_stage_all_healthy': True,
            'intentionally_stopped_services_preserved': True,
            'schema_roles_counts_gateway_ledger_states_unchanged': True,
            'private_file_presence_provider_state_unchanged': True,
            'no_key_validity_or_client_acceptance_claim': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(json.loads(args.before.read_text(encoding='utf-8')),
                            json.loads(args.after.read_text(encoding='utf-8'))), indent=2))

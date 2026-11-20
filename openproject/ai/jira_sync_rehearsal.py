"""Exercise the same native sync adapter on an owned private restore, never the primary targets."""
import json
import time
from pathlib import Path

from jira_sync_target import Target
from jira_sync_backup import command, inspect


class CloneTarget(Target):
    rehearsal = True

    def __init__(self, source, network, container, identifier, core_image):
        self.name, self.project, self.actor, self.token, self.bootstrap, self.base = (
            source.name, source.project, source.actor, source.token, source.bootstrap, source.base)
        self.network, self.container, self.identifier, self.core_image = network, container, identifier, core_image
        self.check_scope()
        self.reader = container + '-client'
        command(['docker', 'run', '-d', '--rm', '--pull', 'never', '--name', self.reader,
            '--label', 'org.qldapm.sync-restore=' + identifier, '--network', self.network, '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '--memory', '128m', '--pids-limit', '32',
            '--entrypoint', 'python', 'sha256:1cd1687b61ea4ca56ae5d41a6b624909e8a70b78263d9ce977d3e264ad9da9ec',
            '-c', 'import time; time.sleep(7200)'])

    def close(self):
        info = inspect(self.reader)
        if info['Config']['Labels'].get('org.qldapm.sync-restore') != self.identifier:
            raise ValueError('RESTORE_CLIENT_CLEANUP_SCOPE_MISMATCH')
        command(['docker', 'rm', '-f', self.reader])

    def check_scope(self):
        info = inspect(self.container)
        if (self.container != 'qldapm-sync-restore-' + self.identifier or info['Image'] != self.core_image or
                info['Config']['Labels'].get('org.qldapm.sync-restore') != self.identifier or
                set(info['NetworkSettings']['Networks']) != {self.network} or info['HostConfig'].get('PortBindings')):
            raise ValueError('PRIVATE_RESTORE_TARGET_REQUIRED')

    def _execute(self, program, data):
        self.check_scope()
        output = command(['docker', 'exec', '-i', self.reader, 'python', '-c', program],
            json.dumps(data).encode(), timeout=110)
        return json.loads(output)

    def fixed_runner(self, packet):
        self.check_scope()
        return command(['docker', 'exec', '-i', self.container, 'bundle', 'exec', 'rails', 'runner', '-'], packet)

    def wait_ready(self):
        for _ in range(60):
            try:
                if self.call('/api/v3/users/me')['id'] == self.actor:
                    return
            except Exception:
                time.sleep(2)
        raise RuntimeError('CLONE_NATIVE_API_NOT_READY')


def exercise_snapshot(snapshot_path, backup_path, core_image=None, sample=False):
    from jira_sync import load_snapshot, make_preview, private_save
    from jira_sync_backup import rehearse_backup
    from jira_sync_operator import configuration, script_hashes
    from jira_sync_apply import apply_preview, verify_preview
    from gateway.native import NativeError
    snapshot = load_snapshot(snapshot_path)
    scripts = script_hashes()
    team = json.loads((Path(__file__).resolve().parents[2] / 'JIRA_TEAM_QAG3.json').read_text())

    def exercise(name, network, container, identifier, directory, image):
        target = CloneTarget(Target(name), network, container, identifier, image)
        try:
            target.wait_ready()
            before = configuration(target)
            changed = configuration(target, before['hash']) # Disposable clone ONLY; never operator approval on primary.
            activities = [row for row in changed['before']['activities'] if row['name'] == 'Simulation']
            if len(activities) != 1 or activities[0]['active']:
                raise ValueError('SIMULATION_ACTIVITY_REHEARSAL_INVALID')
            activity_id = activities[0]['id']
            from jira_sync import source_id
            selected = {source_id(next(issue for issue in snapshot['issues'] if issue['fields']['issuetype']['name'] == 'Sub-task' and snapshot['children'][issue['key']]['worklogs']))} if sample else None
            preview = make_preview(snapshot, target, team, only_sources=selected)
            private_save(directory / 'import-preview.json', {'preview': preview})
            result = apply_preview(preview, target, directory / 'receipts', activity_id,
                progress=lambda n, total: print(json.dumps({'clone': name, 'applied_rows': n, 'total': total}), flush=True) if n % 10 == 0 or n == total else None)
            verified = verify_preview(preview, target, activity_id)
            private_save(directory / 'import-verify.json', verified)
            if verified['summary']['content_conflicts']:
                raise ValueError('NATIVE_IMPORT_CONTENT_REHEARSAL_FAILED')
            if verified['summary']['worklogs_synced'] != sum(len(row['children']['worklogs']) for row in preview['rows']):
                raise ValueError('NATIVE_WORKLOG_IMPORT_REHEARSAL_FAILED')
            if name == 'staging':
                row = next(row for row in preview['rows'] if row['kind'] == 'Subtask')
                actual = target.call(f"/api/v3/work_packages/{row['id']}")
                try:
                    target.call(f"/api/v3/work_packages/{row['id']}?notify=false", 'PATCH',
                        {'lockVersion': actual['lockVersion'], '_links': {'status': {'href': '/api/v3/statuses/' + str(target.bootstrap['statuses']['DONE'])}}})
                    raise ValueError('NATIVE_GATE_BYPASS_ACCEPTED')
                except NativeError as error:
                    if error.status not in {403, 422}:
                        raise
                insights = target.call('/api/v3/qldapm/insights?days=90&user_id=' + str(target.actor))
                if any(event['work_package_id'] == row['id'] for event in insights['events']):
                    raise ValueError('IMPORTED_SIMULATION_COUNTED_IN_INSIGHTS')
            replay = apply_preview(preview, target, directory / 'receipts', activity_id)
            final = verify_preview(preview, target, activity_id)
            if final['summary'] != verified['summary']:
                raise ValueError('NATIVE_IMPORT_REPLAY_CHANGED_DATA')
            if scripts != script_hashes():
                raise ValueError('OPERATOR_CODE_CHANGED_DURING_REHEARSAL')
            return {'passed': True, 'sample_only': sample, 'rows': len(result), 'summary': final['summary'],
                    'replay_rows': len(replay), 'scripts': scripts, 'snapshot_hash': preview['snapshot_hash'],
                    'scope': 'isolated_native_import_not_live_approval'}
        finally:
            target.close()

    return rehearse_backup(backup_path, exercise=exercise, core_image=core_image)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--core-image')
    parser.add_argument('--sample', action='store_true')
    options = parser.parse_args()
    try:
        print(json.dumps(exercise_snapshot(options.snapshot, options.backup, options.core_image, options.sample)))
    except Exception as error:
        code = str(error) if isinstance(error, (ValueError, RuntimeError)) and __import__('re').fullmatch('[A-Z_]{1,100}', str(error)) else 'NATIVE_REHEARSAL_FAILED'
        print(json.dumps({'failed': True, 'code': code, 'primary_sync_applied': False}))
        raise SystemExit(1)

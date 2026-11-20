import os
import unittest

from jira_sync import source_id, read_issue_pages, plan_item, read_children, status_map


class JiraSyncTests(unittest.TestCase):
    def test_data_restore_cannot_include_import_exercise_or_candidate_image(self):
        from unittest.mock import patch
        from jira_sync_backup import rehearse_backup
        for options in ({'exercise': lambda: None}, {'core_image': 'sha256:' + 'a' * 64}):
            with self.subTest(options=list(options)), patch('jira_sync_backup.command') as docker:
                with self.assertRaisesRegex(ValueError, 'DATA_RESTORE_CANNOT_QUALIFY_IMPORT_OR_IMAGE'):
                    rehearse_backup('not-opened', data_only=True, **options)
                docker.assert_not_called()

    def test_data_only_restore_receipt_never_authorizes_jira_import(self):
        import json
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch
        from jira_sync_operator import backup_proof
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'backup.json').write_text(json.dumps({'target': 'staging', 'project_id': 3, 'manifest': {}}))
            receipt = root / 'restore-fixture'
            receipt.mkdir()
            (receipt / 'result.json').write_text(json.dumps({'passed': True, 'database_assets_config': True,
                'configuration_transaction': False, 'purpose': 'data-restore-only'}))
            with patch('jira_sync_operator.verify_archive'), patch('jira_sync_operator.inspect', return_value={'Image': 'fixture'}), \
                    patch('jira_sync_operator.script_hashes', return_value={}):
                with self.assertRaisesRegex(ValueError, 'RESTORE_REHEARSAL_PROOF_REQUIRED'):
                    backup_proof(root, SimpleNamespace(name='staging', project=3))

    def test_preview_does_not_reschedule_dependencies_when_syncing_a_manual_leaf(self):
        issue = {'key': 'QAG3-3', 'fields': {'labels': ['source-AUTH-01-BA', 'qag3-simulation'],
            'summary': 'Analysis', 'description': 'Source', 'status': {'name': 'Done'}, 'issuetype': {'name': 'Sub-task'},
            'duedate': '2026-04-08', 'customFields': {'Start date': {'value': '2026-04-06'}}}}
        item = {'id': 102, 'lockVersion': 1, 'subject': 'Analysis', 'description': {'raw': 'Local source'},
            'scheduleManually': True, 'startDate': None, 'dueDate': None, '_links': {'type': {'title': 'Subtask'}}}
        preview = plan_item(issue, item, {'AUTH-01-BA': item}, {}, dependent_ids={102,103})
        self.assertNotIn('startDate', preview['payload'])
        self.assertNotIn('dueDate', preview['payload'])
        self.assertIn('NATIVE_DEPENDENCY_SCHEDULE_DATES_RETAINED', preview['skipped'])

    def test_preview_preserves_automatic_parent_schedule_and_documents_source_dates(self):
        issue = {'key': 'QAG3-1', 'fields': {'labels': ['source-E01', 'qag3-simulation'],
            'summary': 'Epic', 'description': 'Source', 'status': {'name': 'Done'}, 'issuetype': {'name': 'Epic'},
            'duedate': '2026-04-30', 'customFields': {'Start date': {'value': '2026-04-03'}}}}
        item = {'id': 38, 'lockVersion': 1, 'subject': 'Epic', 'description': {'raw': 'Local source'},
            'scheduleManually': False, 'startDate': None, 'dueDate': None,
            '_links': {'type': {'title': 'Epic'}, 'children': [{'href': '/api/v3/work_packages/49'}]}}
        preview = plan_item(issue, item, {'E01': item}, {})
        self.assertNotIn('startDate', preview['payload'])
        self.assertNotIn('dueDate', preview['payload'])
        self.assertNotIn('scheduleManually', preview['payload'])
        self.assertIn('NATIVE_AUTOMATIC_PARENT_DATES_NOT_DIRECTLY_WRITABLE', preview['skipped'])
        self.assertIn('2026-04-03', preview['payload']['description']['raw'])
        self.assertIn('2026-04-30', preview['payload']['description']['raw'])

    @unittest.skipUnless(os.name == 'nt', 'The local sync operator lease uses Windows msvcrt')
    def test_operator_lease_prevents_a_second_writer_and_releases_after_exit(self):
        from jira_sync_backup import operator_lease
        with operator_lease('staging'):
            with self.assertRaisesRegex(ValueError, 'ANOTHER_SYNC_OPERATOR_IS_RUNNING'):
                with operator_lease('staging'):
                    self.fail('Two operators acquired the same target')
        with operator_lease('staging'):
            pass

    def test_apply_cli_requires_a_human_console_before_opening_target(self):
        import subprocess, sys
        from pathlib import Path
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'jira_sync.py'),
            'apply', '--preview', 'not-opened.json'], input='', capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('LOCAL_INTERACTIVE_OPERATOR_REQUIRED', result.stdout)

    def test_status_timeout_is_durable_and_stops_replay_without_second_write(self):
        import tempfile
        from pathlib import Path
        from jira_sync_apply import apply_preview
        class NativeFixture:
            name, project, actor = 'staging', 3, 7
            bootstrap = {'fields': {'Source ID': 'customField1'}}
            writes = 0
            def collection(self, path):
                return []
            def call(self, path, method='GET', payload=None):
                if method == 'PATCH':
                    self.writes += 1
                    raise TimeoutError('fixture response lost')
                if path.endswith('/capabilities'):
                    return {'gate_schema': 2, 'enforced': True, 'project_id': 3}
                if '/gates/' in path:
                    return {'transitions': [{'to': 'IN PROGRESS', 'errors': []}]}
                return {'id': 123, 'lockVersion': 2, 'customField1': 'AUTH-01', '_links': {
                    'project': {'href': '/api/v3/projects/3'}, 'status': {'title': 'NEW', 'href': '/api/v3/statuses/1'}}}
        row = {'id': 123, 'source_id': 'AUTH-01', 'jira_key': 'QAG3-4', 'version': 2, 'payload': {}, 'skipped': [],
            'source_status': 'IN PROGRESS', 'native_status': 'NEW', 'status_id': 2, 'gate_errors': [],
            'children': {'comments': [], 'worklogs': []}}
        target = NativeFixture()
        with tempfile.TemporaryDirectory() as directory:
            for _ in range(2):
                result = apply_preview({'target': target.name, 'project_id': 3, 'actor': 7, 'rows': [row]}, target, Path(directory), 9)
                self.assertEqual(result[0]['status']['state'], 'unknown')
            self.assertEqual(target.writes, 1)

    def test_primary_configuration_cannot_be_committed_by_noninteractive_agent(self):
        from jira_sync_operator import configuration
        class Primary:
            name, project, actor = 'staging', 3, 7
        with self.assertRaisesRegex(PermissionError, 'LOCAL_INTERACTIVE_OPERATOR_REQUIRED'):
            configuration(Primary(), '0' * 64)

    def test_long_worklog_keeps_full_source_in_ticket_and_respects_native_comment_limit(self):
        from jira_sync_records import child_preview, source_history
        original = 'x' * 2000
        children = {'comments': [], 'changelogs': [], 'worklogs': [{'id': 'w1', 'started': '2026-09-07T09:00:00+07:00',
            'timeSpentSeconds': 3600, 'author': {'accountId': 'source-author'}, 'comment': original}]}
        result = child_preview('QAG3-4', 123, 7, children)
        self.assertLessEqual(len(result['worklogs'][0]['payload']['comment']['raw']), 1000)
        self.assertIn(original, source_history(children))
        self.assertIn('w1', source_history(children))

    def test_run_stops_all_later_writes_after_comment_timeout(self):
        import tempfile
        from pathlib import Path
        from jira_sync_apply import apply_preview
        class NativeFixture:
            name, project, actor = 'staging', 3, 7
            bootstrap = {'fields': {'Source ID': 'customField1'}}
            writes = []
            def collection(self, path):
                return []
            def call(self, path, method='GET', payload=None):
                if method == 'POST':
                    self.writes.append(path)
                    if '/activities' not in path:
                        raise AssertionError('Run continued writing after timeout')
                    raise TimeoutError('fixture')
                return {'id': 123, 'lockVersion': 2, 'customField1': 'AUTH-01', '_links': {'project': {'href': '/api/v3/projects/3'}}}
        row = {'id': 123, 'source_id': 'AUTH-01', 'jira_key': 'QAG3-4', 'version': 2, 'payload': {}, 'skipped': [],
            'source_status': 'NEW', 'native_status': 'NEW', 'gate_errors': [], 'children': {
                'comments': [{'source_id': 'c1', 'marker': 'comment-marker', 'payload': {'comment': {'raw': 'comment-marker'}}}],
                'worklogs': [{'source_id': 'w1', 'marker': 'worklog-marker', 'payload': {'comment': {'raw': 'worklog-marker'},
                    'spentOn': '2026-10-01', 'hours': 'PT1H', '_links': {'entity': {'href': '/api/v3/work_packages/123'}, 'user': {'href': '/api/v3/users/7'}}}}]}}
        target = NativeFixture()
        with tempfile.TemporaryDirectory() as directory:
            result = apply_preview({'target': 'staging', 'project_id': 3, 'actor': 7, 'rows': [row]}, target, Path(directory), 9)
            self.assertEqual(result[0]['comments'][0]['state'], 'unknown')
            self.assertEqual(len(target.writes), 1)

    def test_worklog_create_uses_simulation_activity_and_actual_publisher(self):
        import tempfile
        from pathlib import Path
        from jira_sync_apply import apply_record
        record = {'marker': 'QLDAPM-JIRA:QAG3-4:worklog:w1:abc', 'payload': {
            'comment': {'format': 'plain', 'raw': 'SIMULATION QLDAPM-JIRA:QAG3-4:worklog:w1:abc'},
            'spentOn': '2026-10-01', 'hours': 'PT1H30M', '_links': {
                'entity': {'href': '/api/v3/work_packages/123'}, 'user': {'href': '/api/v3/users/7'}}}}
        class NativeFixture:
            actor = 7
            def collection(self, path):
                return []
            def call(self, path, method='GET', payload=None):
                if method == 'POST':
                    assert payload['_links']['activity']['href'] == '/api/v3/time_entries/activities/9'
                    self.resource = {'id': 456, **payload}
                return self.resource
        with tempfile.TemporaryDirectory() as directory:
            result = apply_record('worklog', 123, record, NativeFixture(), Path(directory), activity_id=9)
            self.assertEqual(result['state'], 'applied')
            self.assertEqual(result['native_id'], 456)

    def test_import_comment_already_present_is_reconciled_not_duplicated(self):
        import tempfile
        from pathlib import Path
        from jira_sync_apply import apply_record
        record = {'marker': 'QLDAPM-JIRA:QAG3-4:comment:c1:abc',
                  'payload': {'comment': {'format': 'markdown', 'raw': 'source text with QLDAPM-JIRA:QAG3-4:comment:c1:abc'}}}
        class NativeFixture:
            actor = 7
            def collection(self, path):
                return [{'id': 456, 'comment': record['payload']['comment'], '_links': {'user': {'href': '/api/v3/users/7'}}}]
            def call(self, *args):
                raise AssertionError('Existing source comment reached POST')
        with tempfile.TemporaryDirectory() as directory:
            result = apply_record('comment', 123, record, NativeFixture(), Path(directory))
            self.assertEqual(result['state'], 'reconciled')
            self.assertEqual(result['native_id'], 456)

    def test_timeout_keeps_unknown_and_does_not_retry_a_committed_write(self):
        import tempfile
        from pathlib import Path
        from jira_sync_apply import apply_content
        class NativeFixture:
            def __init__(self):
                self.current = {'id': 123, 'lockVersion': 2, 'subject': 'Old'}
                self.writes = 0
            def call(self, path, method='GET', payload=None):
                if method == 'PATCH':
                    self.writes += 1
                    self.current = {'id': 123, 'lockVersion': 3, 'subject': 'New'}
                    raise TimeoutError('fixture response lost after commit')
                return dict(self.current)
        native = NativeFixture()
        row = {'id': 123, 'version': 2, 'payload': {'subject': 'New'}}
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(apply_content(row, native, Path(directory))['state'], 'unknown')
            self.assertEqual(apply_content(row, native, Path(directory))['state'], 'unknown')
            self.assertEqual(native.writes, 1)

    def test_sprint_membership_requires_complete_count_not_a_partial_issue_list(self):
        from jira_sync import read_sprint_membership
        response = {'resolvedSprint': {'id': 1}, 'sprintMetrics': {'totalIssues': 0}, 'issues': []}
        self.assertEqual(read_sprint_membership(lambda *args: response, [{'id': 1, 'originBoardId': 3}]), {'1': []})
        response['sprintMetrics']['totalIssues'] = 2
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE_SPRINT_MEMBERSHIP'):
            read_sprint_membership(lambda *args: response, [{'id': 1, 'originBoardId': 3}])

    def test_apply_content_replay_reads_back_without_a_second_write(self):
        import tempfile
        from pathlib import Path
        from jira_sync_apply import apply_content
        class NativeFixture:
            def __init__(self):
                self.current = {'id': 123, 'lockVersion': 2, 'subject': 'Old'}
                self.writes = 0
            def call(self, path, method='GET', payload=None):
                if method == 'PATCH':
                    self.writes += 1
                    self.current = {'id': 123, 'lockVersion': 3, 'subject': payload['subject']}
                return dict(self.current)
        native = NativeFixture()
        row = {'id': 123, 'version': 2, 'payload': {'subject': 'New'}}
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(apply_content(row, native, Path(directory))['state'], 'applied')
            self.assertEqual(apply_content(row, native, Path(directory))['state'], 'applied')
            self.assertEqual(native.writes, 1)

    def test_apply_never_writes_when_native_version_changed(self):
        import tempfile
        from pathlib import Path
        from jira_sync_apply import apply_content
        class NativeFixture:
            def call(self, path, method='GET', payload=None):
                if method != 'GET':
                    raise AssertionError('A stale preview reached native write')
                return {'id': 123, 'lockVersion': 9}
        with tempfile.TemporaryDirectory() as directory:
            result = apply_content({'id': 123, 'version': 2, 'payload': {'subject': 'New'}}, NativeFixture(), Path(directory))
            self.assertEqual(result['state'], 'conflict')
            self.assertEqual(result['reason'], 'NATIVE_VERSION_CHANGED')

    def test_child_preview_preserves_authorship_without_importing_restricted_comments(self):
        from jira_sync_records import child_preview
        children = {'comments': [
            {'id': 'c1', 'body': 'public text', 'created': '2026-10-01T09:00:00+07:00', 'author': {'accountId': 'original'}},
            {'id': 'c2', 'body': 'private text', 'visibility': {'type': 'role', 'value': 'QA'}}],
            'worklogs': [{'id': 'w1', 'started': '2026-10-01T09:00:00+07:00', 'timeSpentSeconds': 5400, 'author': {'accountId': 'original'}, 'comment': 'hypothetical contributor'}],
            'changelogs': []}
        result = child_preview('QAG3-4', 123, 7, children)
        self.assertEqual(len(result['comments']), 1)
        self.assertNotIn('private text', str(result))
        self.assertEqual(result['skipped'][0]['reason'], 'COMMENT_VISIBILITY_NOT_PRESERVABLE')
        self.assertEqual(result['worklogs'][0]['payload']['hours'], 'PT1H30M')
        self.assertEqual(result['worklogs'][0]['payload']['_links']['user']['href'], '/api/v3/users/7')
        self.assertIn('original', result['worklogs'][0]['payload']['comment']['raw'])
        self.assertIn('SIMULATION', result['worklogs'][0]['payload']['comment']['raw'])

    def test_backup_manifest_rejects_tampering_and_path_escape(self):
        import tempfile
        from pathlib import Path
        from jira_sync_backup import verify_archive
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'database.dump').write_bytes(b'fixture')
            with self.assertRaisesRegex(ValueError, 'BACKUP_HASH_MISMATCH'):
                verify_archive(root, {'database.dump': '0' * 64})
            with self.assertRaisesRegex(ValueError, 'BACKUP_PATH_DENIED'):
                verify_archive(root, {'../outside': '0' * 64})

    def test_isolated_configuration_runner_rejects_arbitrary_suite_before_docker(self):
        from runner import isolated_core
        with self.assertRaisesRegex(ValueError, "FIXED_TEST_SUITE_REQUIRED"):
            isolated_core("unused", "0" * 36, "unused", suite="arbitrary-script")

    def test_identity_is_source_label_not_issue_number_or_title(self):
        self.assertEqual(source_id({"key": "QAG3-4", "fields": {
            "summary": "Do not match by this title", "labels": ["qag3-wbs", "source-AUTH-01-BE"]}}), "AUTH-01-BE")
        with self.assertRaises(ValueError):
            source_id({"fields": {"labels": ["source-E01", "source-E02"]}})

    def test_snapshot_rejects_repeated_source_and_unfinished_pagination(self):
        issue = {"key": "QAG3-1", "fields": {"labels": ["source-E01"]}}
        pages = iter([{"issues": [issue], "isLast": False, "nextPageToken": "p2"},
                      {"issues": [{**issue, "key": "QAG3-2"}], "isLast": True}])
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            read_issue_pages(lambda *args: next(pages))
        with self.assertRaises(ValueError):
            read_issue_pages(lambda *args: {"issues": [issue], "isLast": False})

    def test_preview_preserves_missing_fields_and_keeps_status_separate(self):
        issue = {"key": "QAG3-4", "fields": {"labels": ["source-AUTH-01-BE", "qag3-simulation"],
            "summary": "New title", "description": "Source AC", "status": {"name": "Done"},
            "issuetype": {"name": "Sub-task"}, "assignee": {"accountId": "be"}}}
        item = {"id": 123, "lockVersion": 2, "subject": "Old title", "description": {"raw": "Local note"},
            "startDate": "2026-04-01", "dueDate": "2026-04-02", "_links": {
                "assignee": {"href": "/api/v3/users/8"}, "type": {"title": "Subtask", "href": "/api/v3/types/8"},
                "status": {"title": "NEW", "href": "/api/v3/statuses/1"}}}
        planned = plan_item(issue, item, {"AUTH-01-BE": item}, {"be": 8})
        self.assertEqual(planned['payload']['subject'], 'New title')
        self.assertNotIn('dueDate', planned['payload'])
        self.assertNotIn('startDate', planned['payload'])
        self.assertNotIn('status', planned['payload'].get('_links', {}))
        self.assertEqual(planned['source_status'], 'DONE')
        self.assertIn('Local note', planned['payload']['description']['raw'])

    def test_source_html_and_script_links_remain_inert_data(self):
        from jira_sync import inert_text
        rendered = inert_text('<script>steal()</script> [link](javascript:alert(1))')
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('javascript:', rendered)
        self.assertIn('steal()', rendered)

    def test_child_pagination_does_not_assume_missing_counts_are_empty(self):
        with self.assertRaises(ValueError):
            read_children(lambda *args: {'comments': []}, 'listJiraIssueComments', 'QAG3-1', 'comments')
        pages = iter([{'comments': [{'id': 'a'}], 'total': 2}, {'comments': [{'id': 'b'}], 'total': 2}])
        self.assertEqual(read_children(lambda *args: next(pages), 'listJiraIssueComments', 'QAG3-1', 'comments'),
                         [{'id': 'a'}, {'id': 'b'}])

    def test_status_resolution_is_scoped_to_existing_project_workflow_ids(self):
        self.assertEqual(status_map([{'id': 1, 'name': 'New'}, {'id': 13, 'name': 'NEW'}], {13}), {'NEW': 13})
        with self.assertRaises(ValueError):
            status_map([{'id': 1, 'name': 'New'}, {'id': 13, 'name': 'NEW'}], {1, 13})


if __name__ == "__main__":
    unittest.main()

import copy
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest

from gateway import integration_events, workflow_status
from gateway.store import Store, canonical


class Native:
    def call(self, path):
        assert path == '/api/v3/projects/6'
        return {'identifier': 'ai-dev-demo', 'active': True}

    def package(self, identifier):
        if identifier != 391:
            raise PermissionError('OTHER_PROJECT_OR_INVISIBLE')
        return {'id': 391, 'lockVersion': 4}


class WorkflowStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name))
        self.role = 'PM'
        self.service = SimpleNamespace(store=self.store, config={'project_id': 6, 'engineering': {'enabled': True}},
            native_actor=lambda actor: (Native(), {'user_id': actor, 'role': self.role}))

    def metadata(self, *, age=0):
        execution = {'id': '123', 'status': 'success', 'mode': 'webhook', 'started_at': time.time()-20, 'stopped_at': time.time()-10}
        value = {'schema_version': 1, 'checked_at': time.time()-age, 'workflows': [
            {'code': code, 'id': identifier, 'name': name, 'active': True, 'published_version_id': 'abc-123',
             'definition_sha256': 'a'*64, 'trigger_types': ['webhook'], 'last_execution': dict(execution), 'last_success': dict(execution)}
            for code, identifier, name, *_ in workflow_status.CATALOG]}
        self.save(value)
        return value

    def save(self, value):
        (self.store.root / workflow_status.SNAPSHOT_FILE).write_text(json.dumps(value))

    def receipt(self, *, code='INDEX_VERIFIED', native_id=391, execution_id='123', state='ACKED', business_state='INDEX_VERIFIED', source_version=4):
        identifier = integration_events.enqueue(self.store, code, 'source:fixture', 1,
            payload={'native_id': native_id, 'job_id': 'job-fixture'})
        with self.store.connect() as db:
            event = json.loads(db.execute('SELECT document FROM integration_event_outbox WHERE id=?', (identifier,)).fetchone()[0])
            ack = {'event_id': identifier, 'project_id': 6, 'workflow': event['workflow'], 'correlation_id': event['correlation_id'],
                   'business_result': {'state': business_state, 'source_version': source_version, 'api_key': 'DO_NOT_EXPOSE'}}
            db.execute('INSERT INTO integration_event_receipts VALUES(?,?,?,?)', (identifier, canonical(ack), execution_id, time.time()))
            db.execute('UPDATE integration_event_outbox SET state=? WHERE id=?', (state, identifier))
        return identifier

    def row(self, code='WF13', actor=20):
        return next(row for row in workflow_status.snapshot(self.service, actor) if row['code'] == code)

    def test_missing_metadata_still_lists_16_without_execution_or_business_claim(self):
        rows = workflow_status.snapshot(self.service, 20)
        self.assertEqual(len(rows), 16)
        self.assertEqual({r['metadata_state'] for r in rows}, {'NOT_OBSERVED'})
        self.assertEqual({r['current_state'] for r in rows}, {'NOT_OBSERVED'})
        self.assertTrue(all(r['retry_eligibility'] == 'NOT_APPLICABLE' for r in rows))

    def test_project_identity_role_and_enabled_are_verified_before_projection(self):
        for project, enabled, role in [(5, True, 'PM'), (6, False, 'PM'), (6, True, 'BA')]:
            self.service.config.update(project_id=project, engineering={'enabled': enabled})
            self.role = role
            with self.assertRaises(PermissionError):
                workflow_status.snapshot(self.service, 20)

    def test_exact_success_and_durable_receipt_are_required_for_business_verified(self):
        self.metadata()
        self.assertEqual(self.row()['current_state'], 'WORKFLOW_SUCCEEDED')
        self.assertEqual(self.row()['business_side_effect'], 'NOT_VERIFIED')
        self.receipt(execution_id='122')
        self.assertEqual(self.row()['current_state'], 'WORKFLOW_SUCCEEDED')
        self.assertIn('not matched', self.row()['business_side_effect'])
        with self.store.connect() as db:
            db.execute("UPDATE integration_event_receipts SET execution_id='123'")
        result = self.row()
        self.assertEqual(result['current_state'], 'BUSINESS_SIDE_EFFECT_VERIFIED')
        self.assertNotIn('DO_NOT_EXPOSE', json.dumps(result))
        self.assertEqual(result['project_event']['native_id'], 391)
        self.assertEqual(result['execution_url'], 'http://localhost:5679/workflow/2tr0jpqaaAiq9IOU/executions/123')

    def test_ack_without_fresh_n8n_metadata_only_proves_triggered(self):
        self.receipt()
        self.assertEqual(self.row()['current_state'], 'WORKFLOW_TRIGGERED')
        self.metadata(age=301)
        self.assertEqual(self.row()['metadata_state'], 'STALE')
        self.assertEqual(self.row()['current_state'], 'NOT_OBSERVED')
        self.assertNotEqual(self.row()['business_side_effect'], 'INDEX_VERIFIED')

    def test_stale_source_and_invisible_source_do_not_claim_business_pass(self):
        self.metadata()
        self.receipt(source_version=3)
        self.assertEqual(self.row()['business_side_effect'], 'STALE_SOURCE_VERSION')
        self.assertEqual(self.row()['current_state'], 'WORKFLOW_SUCCEEDED')
        with self.store.connect() as db:
            db.execute('DELETE FROM integration_event_outbox')
            db.execute('DELETE FROM integration_event_receipts')
        self.receipt(native_id=385)
        self.assertIsNone(self.row()['project_event'])
        self.assertEqual(self.row()['retry_eligibility'], 'NOT_APPLICABLE')
        self.assertNotIn('385', json.dumps(self.row()))

    def test_pm_does_not_read_other_actor_receipts_owner_can_oversee(self):
        self.metadata()
        self.receipt()
        self.assertIsNone(self.row(actor=21)['project_event'])
        self.role = 'AI_SYSTEM_OWNER'
        self.assertIsNotNone(self.row(actor=18)['project_event'])

    def test_owner_command_receipt_is_not_exposed_to_pm(self):
        from gateway.workflow_commands import setup
        self.metadata()
        identifier = integration_events.enqueue(self.store, 'UI_FILE_INDEXED', 'ui-command:owner-only', 'a'*64,
            payload={'command_id': 'owner-only', 'action': 'knowledge_file_ingest'})
        with self.store.connect() as db:
            setup(db)
            db.execute('INSERT INTO workflow_command_sources VALUES(?,?,?,?,?,?)', ('owner-only', 18, 'knowledge_file_ingest', 'a'*64, '{}', time.time()))
        self.assertIsNone(self.row('WF01')['project_event'])
        self.role = 'AI_SYSTEM_OWNER'
        self.assertEqual(self.row('WF01', actor=18)['project_event']['event_id'], identifier)

    def test_callback_observation_does_not_complete_running_execution(self):
        document = self.metadata()
        document['workflows'][12]['last_execution']['status'] = 'running'
        document['workflows'][12]['last_execution']['stopped_at'] = None
        self.save(document)
        self.receipt()
        self.assertEqual(self.row()['current_state'], 'WORKFLOW_EXECUTING')

    def test_last_success_survives_latest_failure_and_error_text_is_fixed(self):
        document = self.metadata()
        document['workflows'][12]['last_execution']['status'] = 'error'
        document['workflows'][12]['last_execution']['id'] = '124'
        document['workflows'][12]['last_failure'] = dict(document['workflows'][12]['last_execution'])
        self.save(document)
        result = self.row()
        self.assertEqual(result['current_state'], 'FAILED')
        self.assertEqual(result['last_successful_execution']['id'], '123')
        self.assertEqual(result['last_failed_execution']['id'], '124')
        self.assertEqual(result['last_error'], 'N8N_EXECUTION_ERROR')

    def test_metadata_rejects_arbitrary_url_execution_scope_secret_and_bad_size(self):
        document = self.metadata()
        variants = []
        for field, value in [('id', '../../evil'), ('execution_url', 'http://secret/'), ('token', 'DO_NOT_EXPOSE')]:
            changed = copy.deepcopy(document)
            changed['workflows'][0][field] = value
            variants.append(changed)
        changed = copy.deepcopy(document)
        changed['workflows'][0]['last_execution']['id'] = '123?token=private'
        variants.append(changed)
        changed = copy.deepcopy(document)
        changed['workflows'][0] = copy.deepcopy(changed['workflows'][1])
        variants.append(changed)
        for value in variants:
            self.save(value)
            result = self.row()
            self.assertEqual(result['metadata_state'], 'INVALID')
            self.assertIsNone(result['last_execution'])
            self.assertNotIn('private', json.dumps(result))
        (self.store.root / workflow_status.SNAPSHOT_FILE).write_bytes(b' ' * 65537)
        self.assertEqual(self.row()['metadata_state'], 'INVALID')

    def test_not_applicable_without_trigger_not_failed(self):
        document = self.metadata()
        document['workflows'][12]['trigger_types'] = []
        self.save(document)
        self.assertEqual(self.row()['current_state'], 'NOT_APPLICABLE')

    def test_retry_visibility_is_automatic_or_blocked_never_arbitrary_replay(self):
        self.receipt(state='RETRY')
        self.assertEqual(self.row()['retry_eligibility'], 'AUTOMATIC_BOUNDED_OUTBOX')
        with self.store.connect() as db:
            db.execute("UPDATE integration_event_outbox SET state='DEAD',error='http://user:password@private'")
        result = self.row()
        self.assertEqual(result['retry_eligibility'], 'BLOCKED_REQUIRES_SOURCE_REVIEW')
        self.assertNotIn('password', json.dumps(result))


if __name__ == '__main__':
    unittest.main()

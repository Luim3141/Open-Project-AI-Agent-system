import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gateway import engineering, engineering_planning as planning
from gateway.engineering_operator import native_once
from gateway.native import NativeError
from gateway.store import Store, canonical, digest


class PlanningTimeoutRecovery(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Store(Path(tmp.name))
        self.item = {'id': 379, 'lockVersion': 0, 'subject': 'Existing task',
                     'description': {'raw': 'Existing spec'}}
        self.native = SimpleNamespace(call=lambda path: {'identifier': 'ai-dev-demo', 'active': True},
                                      package=lambda identifier: {**self.item, 'id': identifier})
        self.service = SimpleNamespace(store=self.store, config={'project_id': 6, 'engineering': {'enabled': True}},
            native_actor=lambda actor: (self.native, {'user_id': actor, 'role': 'PM'}))
        engineering.setup(self.store)

    def test_failed_auto_admission_does_not_leave_auto_enabled(self):
        with patch('gateway.engineering_auto.schedule_next_auto_unit', side_effect=ValueError('ENGINEERING_PLAN_HANDOFF_REQUIRED')):
            with self.assertRaisesRegex(ValueError, 'PLAN_HANDOFF_REQUIRED'):
                engineering.control(self.service, 20, 'AUTO')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0], 'OFF')

    def test_global_run_once_selects_existing_eligible_unit_instead_of_403(self):
        result=engineering.admit(self.service,20,{},'global-run-once')
        with self.store.connect() as db:
            payload=json.loads(db.execute('SELECT payload FROM ai_queue WHERE id=?',(result['id'],)).fetchone()[0])
        self.assertEqual(payload['unit'],engineering.UNIT)
        self.assertEqual(payload['native_id'],379)

    def test_global_run_once_preserves_owner_pause_guard(self):
        engineering.control(self.service,20,'PAUSED')
        with self.assertRaisesRegex(ValueError,'^ENGINEERING_PAUSED$'):
            engineering.admit(self.service,20,{},'paused-global-run-once')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM ai_queue').fetchone()[0],0)

    def test_unpublished_feedback_is_not_advertised_as_eligible(self):
        definition = {'kind': 'development', 'native_id': 396, 'plan_id': 'partial-plan',
                      'title': 'Status route', 'base_unit': None}
        with self.store.connect() as db:
            db.execute('INSERT INTO engineering_unit_definitions VALUES(?,?,?,?)',
                       ('feedback-partial', 20, 396, canonical(definition)))
        rows, _ = engineering.backlog_snapshot(self.service, 20)
        unit = next(r for r in rows if r['unit'] == 'feedback-partial')
        self.assertFalse(unit['eligible'])
        self.assertEqual(unit['blocked_reason'], 'ENGINEERING_PLAN_HANDOFF_REQUIRED')

    def test_pre_transport_deadline_is_rejected_no_write(self):
        client = SimpleNamespace(call=Mock(side_effect=NativeError(503, 'REQUEST_DEADLINE_EXCEEDED')))
        with self.assertRaisesRegex(NativeError, '^REQUEST_DEADLINE_EXCEEDED$'):
            native_once(self.service, client, 'fixture', 'plan-parent', '/api/v3/work_packages/379/activities', 'POST', {})
        with self.store.connect() as db:
            row = db.execute('SELECT state,result FROM requests WHERE key=?', ('engineering-fixture-plan-parent',)).fetchone()
        self.assertEqual(row['state'], 'rejected')
        self.assertEqual(json.loads(row['result'])['outcome'], 'REJECTED_NO_WRITE')
        retried=SimpleNamespace(call=Mock(return_value={'id': 123}))
        args=(self.service,retried,'fixture','plan-parent','/api/v3/work_packages/379/activities','POST',{})
        self.assertEqual(native_once(*args),{'id':123})
        self.assertEqual(native_once(*args),{'id':123})
        retried.call.assert_called_once()

    def test_internal_planning_transport_allows_two_turns_and_publication(self):
        from automation import engineering_worker as worker
        with patch.object(worker,'command',return_value=SimpleNamespace(stdout=b'{"ok":true,"result":{}}')) as command:
            worker.operator('generate_plan',run_id='fixture')
        self.assertGreaterEqual(command.call_args.kwargs['timeout'],270)
        self.assertLessEqual(command.call_args.kwargs['timeout'],360)

    def test_transport_unknown_remains_pending(self):
        client = SimpleNamespace(call=Mock(side_effect=NativeError(503, 'REQUEST_DEADLINE_EXCEEDED_OUTCOME_MAY_BE_UNKNOWN')))
        with self.assertRaises(NativeError):
            native_once(self.service, client, 'fixture', 'child', '/api/v3/work_packages', 'POST', {})
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM requests').fetchone()[0], 'pending')

    def test_publication_gets_fresh_authority_after_analysis_and_reuses_models(self):
        clock = [0]
        authorities = []
        class PhaseNative:
            def __init__(this):
                this.deadline = clock[0] + 90
                authorities.append(this)
            def package(this, identifier):
                if clock[0] >= this.deadline:
                    raise NativeError(503, 'REQUEST_DEADLINE_EXCEEDED')
                return {**self.item, 'id': identifier}
            def relations(this, packages):
                return []
        def knowledge(*args):
            clock[0] += 91
            return {'items': []}
        self.service.knowledge = knowledge
        self.service.gemini = SimpleNamespace(structured=Mock(side_effect=AssertionError('Must reuse saved BA/PM')))
        document = {'id': 'saved-plan', 'project_id': 6, 'native_id': 379, 'source_version': 0,
                    'state': 'PLANNING', 'feedback': '', 'ba': {}, 'pm': {'assignments': []},
                    'native_units': {'existing': {'id': 380, 'dependencies': [], 'state': 'DELIVERED'}}, 'relations': []}
        with self.store.connect() as db:
            db.execute('INSERT INTO engineering_plans VALUES(?,?,?)', ('saved-plan', 20, canonical(document)))
        contract = {'source_version': 0, 'spec_sha256': digest('Existing spec'),
                    'definition': {'feedback': ''}, 'deadline': time.time() + 1800}
        with patch('gateway.engineering.authorized', side_effect=lambda *a: (PhaseNative(), {'user_id': 20, 'role': 'PM'})), \
             patch.object(planning, 'definitions', return_value={}), \
             patch('gateway.engineering_lifecycle.signal', return_value={'mode': 'RUN_ONCE'}), \
             patch('gateway.engineering_operator.native_once', return_value={'id': 123}) as mutation:
            result = planning.generate(self.service, 20, 'saved-plan', contract)
        self.assertEqual(result['state'], 'PUBLISHED')
        self.assertEqual(len(authorities), 2)
        self.service.gemini.structured.assert_not_called()
        mutation.assert_called_once()


if __name__ == '__main__':
    unittest.main()

import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from gateway import engineering
from gateway.engineering_auto import schedule_next_auto_unit
from gateway.store import Store, canonical


class NativeMock:
    def __init__(self, packages=None):
        self._packages = packages or {
            379: {'id': 379, 'lockVersion': 5, 'subject': 'Develop Mini Task Manager Application', 'description': {'raw': 'Spec 379'}},
            380: {'id': 380, 'lockVersion': 2, 'subject': 'Unit 1: Create/list', 'description': {'raw': 'Spec 380'}},
            381: {'id': 381, 'lockVersion': 2, 'subject': 'Unit 2: CRUD Web', 'description': {'raw': 'Spec 381'}}
        }

    def call(self, path):
        if path == '/api/v3/projects/6':
            return {'id': 6, 'identifier': 'ai-dev-demo', 'active': True}
        raise AssertionError(f"Unexpected path {path}")

    def package(self, identifier):
        if identifier in self._packages:
            return self._packages[identifier]
        raise ValueError(f"Unknown package {identifier}")

    def packages(self):
        return list(self._packages.values())


class GeminiMock:
    def __init__(self, available=True):
        self.available = available

    def settings(self):
        if not self.available:
            return {'state': 'UNAVAILABLE'}
        return {
            'model': 'gemini-3.5-flash-lite',
            'limits': {'rpm': 15, 'tpm': 1000000},
            'project': 'qldapm-gemini'
        }


def make_service(temp_dir, gemini_available=True):
    store = Store(Path(temp_dir))
    config = {
        'project_id': 6,
        'default_project': 6,
        'projects': [6],
        'supervisors': [20],
        'engineering': {'enabled': True},
        'native': {'url': 'http://mock-openproject', 'key': 'secret'}
    }
    def mock_native_actor(actor):
        if actor in {18, 20}:
            role = 'AI_SYSTEM_OWNER' if actor == 18 else 'PM'
            return (NativeMock(), {'user_id':actor,'project_id':6,'role': role, 'login': f'user{actor}', 'name': f'User {actor}'})
        return (NativeMock(), {'user_id':actor,'project_id':6,'role': 'DEV', 'login': f'user{actor}', 'name': f'User {actor}'})

    service = SimpleNamespace(
        store=store,
        config=config,
        gemini=GeminiMock(available=gemini_available),
        native_actor=mock_native_actor
    )
    return service


class TestEngineeringAutoMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = make_service(self.tmp.name)
        engineering.setup(self.service.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_control_auto_mode_accepted_for_pm_and_owner(self):
        # PM 20
        res20 = engineering.control(self.service, 20, 'AUTO')
        self.assertIn(res20['mode'], {'AUTO', 'OFF'})

        # Reset to OFF
        engineering.control(self.service, 20, 'OFF')

        # Owner 18
        res18 = engineering.control(self.service, 18, 'AUTO')
        self.assertIn(res18['mode'], {'AUTO', 'OFF'})

    def test_control_invalid_mode_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            engineering.control(self.service, 20, 'INVALID_MODE')
        self.assertEqual(str(ctx.exception), 'ENGINEERING_MODE_INVALID')

    def test_control_unauthorized_rejected(self):
        with self.assertRaises(PermissionError):
            engineering.control(self.service, 19, 'AUTO')

    def test_auto_mode_concurrency_lock(self):
        with self.service.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='AUTO',updated=? WHERE project=6", (time.time(),))
            db.execute(
                "INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,'{\"engine\":\"openclaw\"}','executing',?,'agent')",
                ('run-active-1', 20, time.time())
            )

        sched = schedule_next_auto_unit(self.service, 20)
        self.assertFalse(sched['scheduled'])
        self.assertEqual(sched['reason'], 'CONCURRENCY_LOCKED')
        self.assertEqual(sched['active_run'], 'run-active-1')

    def test_auto_mode_schedules_ready_unit(self):
        # With no runs yet, 'create-list-persistence-v1' is PLANNED and dependency_ready is True
        with self.service.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='AUTO',updated=? WHERE project=6", (time.time(),))

        sched = schedule_next_auto_unit(self.service, 20)
        self.assertTrue(sched['scheduled'])
        self.assertEqual(sched['unit'], 'create-list-persistence-v1')
        self.assertEqual(sched['mode'], 'AUTO')

        # Verify it was placed in queue and mode is AUTO
        with self.service.store.connect() as db:
            row = db.execute("SELECT id, state FROM ai_queue WHERE id=?", (sched['run_id'],)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['state'], 'queued')
            mode = db.execute("SELECT mode FROM engineering_control WHERE project=6").fetchone()[0]
            self.assertEqual(mode, 'AUTO')

    def test_auto_mode_stays_idle_when_all_delivered(self):
        with self.service.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='AUTO',updated=? WHERE project=6", (time.time(),))
            for unit in ['create-list-persistence-v1', 'crud-search-web-v1']:
                run_id = f"run-{unit}"
                payload = canonical({'engine': 'openclaw', 'project_id': 6, 'unit': unit, 'native_id': 379})
                result = canonical({'status': 'succeeded', 'head_sha': 'abc1234', 'pr_url': 'http://pr', 'test_evidence': {}, 'review_evidence': {}})
                db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,'finished',?,'agent')", (run_id, 20, payload, time.time()))
                db.execute("INSERT INTO ai_runs(id,actor,state,result,created) VALUES(?,?,'done',?,?)", (run_id, 20, result, time.time()))

        sched = schedule_next_auto_unit(self.service, 20)
        self.assertFalse(sched['scheduled'])
        self.assertEqual(sched['reason'], 'ALL_DELIVERED')
        self.assertEqual(sched['mode'], 'AUTO')

        with self.service.store.connect() as db:
            mode = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
            self.assertEqual(mode, 'AUTO')

    def test_auto_mode_shutoff_on_failure(self):
        # First admit a unit to establish valid agent task and run
        admitted = engineering.admit(self.service, 20, {
            'native_id': 379,
            'lock_version': 5,
            'unit': 'create-list-persistence-v1'
        }, 'test-req-fail-1')
        run_id = admitted['id']

        with self.service.store.connect() as db:
            # Set mode to AUTO and mark run executing
            db.execute("UPDATE engineering_control SET mode='AUTO',updated=? WHERE project=6", (time.time(),))
            db.execute("UPDATE ai_queue SET state='executing' WHERE id=?", (run_id,))

        # Finish with failure
        fin = engineering.finish(self.service, 20, run_id, {'status': 'failed', 'error': 'TEST_FAILURE'})
        self.assertEqual(fin['mode'], 'OFF')

        with self.service.store.connect() as db:
            mode = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
            self.assertEqual(mode, 'OFF')

    def test_auto_mode_shutoff_on_quota_unavailable(self):
        svc_no_quota = make_service(self.tmp.name, gemini_available=False)
        with svc_no_quota.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='AUTO',updated=? WHERE project=6", (time.time(),))

        sched = schedule_next_auto_unit(svc_no_quota, 20)
        self.assertFalse(sched['scheduled'])
        self.assertEqual(sched['reason'], 'QUOTA_UNAVAILABLE')
        self.assertEqual(sched['mode'], 'OFF')


    def test_auto_mode_schedules_subsequent_unit_when_dependency_delivered(self):
        # 1. Mark first unit (create-list-persistence-v1) as delivered/succeeded with 40-char head_sha
        with self.service.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='AUTO',updated=? WHERE project=6", (time.time(),))
            run_id = "run-unit1"
            payload = canonical({'engine': 'openclaw', 'project_id': 6, 'unit': 'create-list-persistence-v1', 'native_id': 379})
            result = canonical({'status': 'succeeded', 'head_sha': 'a' * 40, 'pr_url': 'http://pr/1'})
            db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,'finished',?,'agent')", (run_id, 20, payload, time.time()))
            db.execute("INSERT INTO ai_runs(id,actor,state,result,created) VALUES(?,?,'done',?,?)", (run_id, 20, result, time.time()))

        # 2. schedule_next_auto_unit should now pick up the second unit (crud-search-web-v1)
        sched = schedule_next_auto_unit(self.service, 20)
        self.assertTrue(sched['scheduled'])
        self.assertEqual(sched['unit'], 'crud-search-web-v1')
        self.assertEqual(sched['mode'], 'AUTO')

        with self.service.store.connect() as db:
            row = db.execute("SELECT id, state FROM ai_queue WHERE id=?", (sched['run_id'],)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['state'], 'queued')

    def test_auto_mode_schedules_dynamic_registered_backlog_unit(self):
        # 1. Mark both default units as succeeded
        with self.service.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='AUTO',updated=? WHERE project=6", (time.time(),))
            for unit in ['create-list-persistence-v1', 'crud-search-web-v1']:
                run_id = f"run-{unit}"
                payload = canonical({'engine': 'openclaw', 'project_id': 6, 'unit': unit, 'native_id': 379})
                result = canonical({'status': 'succeeded', 'head_sha': 'b' * 40, 'pr_url': f'http://pr/{unit}'})
                db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,'finished',?,'agent')", (run_id, 20, payload, time.time()))
                db.execute("INSERT INTO ai_runs(id,actor,state,result,created) VALUES(?,?,'done',?,?)", (run_id, 20, result, time.time()))

            # 2. Register a new dynamic backlog unit dependent on crud-search-web-v1
            dynamic_unit = {
                'title': 'Unit 3: Tagging and Advanced Filters',
                'native_id': 379,
                'base_unit': 'crud-search-web-v1',
                'base_branch': 'codex/openclaw-crud-search-web-v1',
                'acceptance_file': 'test_tags.py',
                'acceptance': {'AC10': 'GET /tasks?tag=... filters by tag'}
            }
            db.execute(
                "INSERT INTO engineering_unit_definitions(id,actor,native_id,document) VALUES(?,?,?,?)",
                ('unit3-tagging-v1', 20, 379, canonical(dynamic_unit))
            )

        # 3. schedule_next_auto_unit should detect unit3-tagging-v1 is PLANNED and dependency is DELIVERED
        sched = schedule_next_auto_unit(self.service, 20)
        self.assertTrue(sched['scheduled'])
        self.assertEqual(sched['unit'], 'unit3-tagging-v1')
        self.assertEqual(sched['mode'], 'AUTO')

        # 4. Verify it is queued in ai_queue
        with self.service.store.connect() as db:
            row = db.execute("SELECT id, state, payload FROM ai_queue WHERE id=?", (sched['run_id'],)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['state'], 'queued')
            self.assertIn('unit3-tagging-v1', row['payload'])


if __name__ == '__main__':
    unittest.main()

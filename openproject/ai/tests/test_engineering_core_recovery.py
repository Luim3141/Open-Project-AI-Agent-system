import concurrent.futures
import json
import tempfile
import unittest
from unittest.mock import patch

from gateway import engineering, engineering_lifecycle as lifecycle
from gateway.store import canonical, digest
from test_engineering_auto_mode import make_service


class EngineeringCoreRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.service = make_service(self.tmp.name)
        self.args = {'native_id': 379, 'lock_version': 5, 'unit': engineering.UNIT}

    def stopped_run(self):
        run = engineering.admit(self.service, 18, self.args, 'owner-recovery')['id']
        engineering.claim(self.service, 20)
        saved = lifecycle.save(self.service, 20, run, {
            'stage': 'publish', 'completed_steps': [], 'terminal_known': True,
            'resumable': True, 'revision': None, 'session_id': None, 'error': None})
        engineering.finish(self.service, 20, run, {'status': 'blocked'})
        return run, saved

    def test_owner_resume_enforces_the_owned_runs_pending_native_receipts(self):
        run, saved = self.stopped_run()
        self.service.store.begin(20, 'engineering-' + run + '-child',
                                 {'action': 'engineering_native_child'})
        for actor in (20, 18):
            with self.subTest(actor=actor):
                with self.assertRaisesRegex(ValueError, 'NATIVE_OUTCOME_RECONCILIATION_REQUIRED'):
                    lifecycle.resume(self.service, actor, run, saved['version'])
        self.assertEqual(self.service.store.agent_run(20, 6, run).state, 'FAILED')

    def test_owner_resume_recognizes_the_owned_runs_verified_source_receipt(self):
        run, saved = self.stopped_run()
        item = {'id': 382, 'lockVersion': 1, 'description': {'raw': 'published source'},
                '_links': {'project': {'href': '/api/v3/projects/6'}}}
        with self.service.store.connect() as db:
            row = db.execute('SELECT payload FROM ai_queue WHERE id=?', (run,)).fetchone()
            contract = json.loads(row[0])
            contract.update(native_id=382, source_version=0, spec_sha256=digest('original'))
            db.execute('UPDATE ai_queue SET payload=? WHERE id=?', (canonical(contract), run))
        key = 'engineering-' + run + '-child'
        self.service.store.begin(20, key, {'project_id': 6, 'method': 'PATCH',
            'path': '/api/v3/work_packages/382', 'payload': {}})
        self.service.store.finish(20, key, item)
        native, who = self.service.native_actor(18)
        native._packages[382] = item
        with patch.object(self.service, 'native_actor', return_value=(native, who)):
            result = lifecycle.resume(self.service, 18, run, saved['version'])
        self.assertEqual(result['id'], run)

    def test_pause_between_preflight_and_atomic_claim_keeps_the_run_queued(self):
        run = engineering.admit(self.service, 20, self.args, 'pause-race')['id']
        original = self.service.store.claim_run
        def pause_then_claim(*args, **kwargs):
            engineering.control(self.service, 20, 'PAUSED')
            return original(*args, **kwargs)
        with patch.object(self.service.store, 'claim_run', side_effect=pause_then_claim):
            self.assertIsNone(engineering.claim(self.service, 20))
        signal = lifecycle.signal(self.service.store, 20, run)
        self.assertEqual(signal['mode'], 'PAUSED')
        self.assertEqual(signal['queue_state'], 'queued')

    def test_auto_claim_keeps_one_global_execution_slot(self):
        run = engineering.admit(self.service, 20, self.args, 'auto-claim')['id']
        with self.service.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='AUTO' WHERE project=6")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: engineering.claim(self.service, 20), range(2)))
        claimed = [result for result in results if result]
        self.assertEqual([result['id'] for result in claimed], [run])


if __name__ == '__main__':
    unittest.main()

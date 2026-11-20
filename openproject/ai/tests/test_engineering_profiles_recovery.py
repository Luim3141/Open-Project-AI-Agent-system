"""Offline workforce projection regressions; receipts are synthetic and Store is temporary."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from gateway.engineering import build_workforce_profiles
from gateway.store import Store, canonical


class WorkforceProfilesRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name))
        self.service = SimpleNamespace(store=self.store)

    def run_row(self, identifier, project=6, engine='openclaw', state='finished', result=None, actor=20):
        with self.store.connect() as db:
            db.execute('INSERT INTO ai_queue VALUES(?,?,?,?,?,?,?,?)',
                       (identifier, actor, canonical({'project_id': project, 'engine': engine}), state, 1.0, None, 0, 'engineering'))
            db.execute('INSERT INTO ai_runs VALUES(?,?,?,?,?)',
                       (identifier, actor, 'running' if state == 'executing' else 'done', canonical(result or {}), 1.0))

    def receipt(self, identifier, run_id, role, at=1.0, actor=20, **values):
        self.store.provider_receipt({'id': identifier, 'project': 'google-billing-project', 'actor': actor,
                                     'run_id': run_id, 'agent': role, 'at': at, 'state': 'LIVE_SUCCESS',
                                     'model': 'recorded-model', 'provider': 'google', 'session_id': 'recorded-session',
                                     'usage': {'totalTokenCount': 17}, **values})

    def profiles(self, configured_model='configured-only-model'):
        return {p['agent']: p for p in build_workforce_profiles(self.service, configured_model)}

    def test_empty_store_has_no_fabricated_runtime_or_acceptance_evidence(self):
        profiles = self.profiles()
        self.assertEqual(set(profiles), {'supervisor', 'pm', 'ba', 'dev', 'reviewer', 'qa'})
        for role, profile in profiles.items():
            self.assertEqual(profile['status'], 'STANDBY')
            for key in ['openclaw_session', 'last_execution', 'last_error', 'skills_loaded', 'evidence']:
                self.assertIn('NOT VERIFIED', profile[key], (role, key, profile[key]))
            if role != 'supervisor':
                self.assertIn('NOT VERIFIED', profile['actual_model_id'])
        self.assertIn('LOCAL_DETERMINISTIC', profiles['supervisor']['actual_model_id'])
        self.assertNotIn('configured-only-model', json.dumps(profiles))

    def test_receipt_scope_excludes_other_project_engine_and_actor(self):
        self.run_row('valid')
        self.run_row('project5', project=5)
        self.run_row('other-engine', engine='gemini')
        self.receipt('valid-receipt', 'valid', 'dev', at=10)
        self.receipt('project5-receipt', 'project5', 'dev', at=20, model='wrong-project')
        self.receipt('engine-receipt', 'other-engine', 'dev', at=30, model='wrong-engine')
        self.receipt('actor-receipt', 'valid', 'dev', at=40, actor=19, model='wrong-actor')
        profile = self.profiles()['dev']
        self.assertEqual(profile['actual_model_id'], 'recorded-model')
        self.assertEqual(profile['last_execution'], 'valid')
        self.assertIn('valid-receipt', profile['evidence'])

    def test_latest_receipt_uses_timestamp_instead_of_uuid_order(self):
        self.run_row('old')
        self.run_row('new')
        self.receipt('zzzz-old', 'old', 'pm', at=10, model='old-model')
        self.receipt('aaaa-new', 'new', 'pm', at=20, model='latest-model', session_id='latest-session')
        profile = self.profiles()['pm']
        self.assertEqual(profile['actual_model_id'], 'latest-model')
        self.assertEqual(profile['openclaw_session'], 'latest-session')
        self.assertEqual(profile['last_execution'], 'new')
        self.assertIn('aaaa-new', profile['evidence'])

    def test_reviewer_and_qa_show_actual_llm_receipts_and_errors(self):
        self.run_row('delivery')
        self.receipt('review-receipt', 'delivery', 'reviewer', model='review-model')
        self.receipt('qa-receipt', 'delivery', 'qa', model='qa-model', state='PROVIDER_ERROR', error='HTTP_429')
        profiles = self.profiles()
        self.assertEqual(profiles['reviewer']['actual_model_id'], 'review-model')
        self.assertEqual(profiles['reviewer']['provider'], 'google')
        self.assertEqual(profiles['qa']['actual_model_id'], 'qa-model')
        self.assertEqual(profiles['qa']['last_error'], 'HTTP_429')
        self.assertIn('PROVIDER_ERROR', profiles['qa']['evidence'])
        self.assertIn('17', profiles['reviewer']['evidence'])
        self.assertIn('NOT VERIFIED', profiles['reviewer']['skills_loaded'])

    def test_only_explicit_active_role_is_running(self):
        self.run_row('delivery', state='executing', result={'agent': 'dev', 'status': 'running'})
        self.run_row('unrelated', project=5, state='executing', result={'agent': 'qa', 'status': 'running'})
        profiles = self.profiles()
        self.assertEqual([role for role, p in profiles.items() if p['status'] == 'RUNNING'], ['dev'])

    def lifecycle_event(self, run_id, role, event_type, project=6, actor=20):
        from gateway.execution_events import append
        scope = SimpleNamespace(run_id=run_id, actor_id=actor, project_id=project, trace_id='fixture-trace')
        with self.store.connect() as db:
            append(db, scope, event_type, agent=role)

    def test_planning_events_show_only_current_role_without_result_agent(self):
        self.run_row('planning', state='executing', result={'stage': 'PLANNING'})
        self.lifecycle_event('planning', 'ba', 'AGENT_STARTED')
        self.assertEqual([r for r, p in self.profiles().items() if p['status'] == 'RUNNING'], ['ba'])
        self.lifecycle_event('planning', 'ba', 'AGENT_COMPLETED')
        self.lifecycle_event('planning', 'pm', 'AGENT_STARTED')
        self.assertEqual([r for r, p in self.profiles().items() if p['status'] == 'RUNNING'], ['pm'])
        self.lifecycle_event('planning', 'pm', 'AGENT_COMPLETED')
        self.assertFalse(any(p['status'] == 'RUNNING' for p in self.profiles().values()))

    def test_failed_lifecycle_event_overrides_stale_result_agent(self):
        self.run_row('planning', state='executing', result={'agent': 'pm'})
        self.lifecycle_event('planning', 'pm', 'AGENT_STARTED')
        self.lifecycle_event('planning', 'pm', 'AGENT_FAILED')
        self.assertEqual(self.profiles()['pm']['status'], 'STANDBY')

    def test_lifecycle_events_from_finished_or_out_of_scope_queue_are_excluded(self):
        for run_id, state, project, engine in [('finished', 'finished', 6, 'openclaw'),
                                                ('queued', 'queued', 6, 'openclaw'),
                                                ('project5', 'executing', 5, 'openclaw'),
                                                ('other-engine', 'executing', 6, 'gemini')]:
            self.run_row(run_id, state=state, project=project, engine=engine)
            self.lifecycle_event(run_id, 'ba', 'AGENT_STARTED', project=project)
        self.run_row('active', state='executing')
        self.lifecycle_event('active', 'qa', 'AGENT_STARTED', actor=19)
        self.lifecycle_event('active', 'dev', 'AGENT_STARTED', project=5)
        self.assertFalse(any(p['status'] == 'RUNNING' for p in self.profiles().values()))

    def test_finished_role_is_not_running_and_missing_receipt_fields_are_unknown(self):
        self.run_row('delivery', result={'agent': 'qa', 'status': 'succeeded'})
        self.receipt('partial', 'delivery', 'qa', model=None, provider=None, session_id=None, state=None)
        profile = self.profiles()['qa']
        self.assertEqual(profile['status'], 'STANDBY')
        for key in ['actual_model_id', 'provider', 'openclaw_session', 'last_error']:
            self.assertIn('NOT VERIFIED', profile[key])

    def test_projection_is_read_only(self):
        self.run_row('delivery')
        self.receipt('receipt', 'delivery', 'ba')
        with self.store.connect() as db:
            before = list(db.iterdump())
        self.profiles()
        with self.store.connect() as db:
            self.assertEqual(list(db.iterdump()), before)


if __name__ == '__main__':
    unittest.main()

"""Unit tests for Engineering Reporting System (Milestone 7)."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from gateway import engineering
from gateway.engineering_reporting import (
    generate_report,
    list_reports,
    get_report,
    collect_factual_metrics,
    format_iso,
)
from gateway.service import Service
from gateway.store import Store


class NativeMock:
    def __init__(self):
        self.deadline = 9999999999

    def identity(self, actor):
        if actor == 18:
            return {'user_id': 18, 'role': 'AI_SYSTEM_OWNER', 'capabilities': ['AI_SYSTEM_OWNER']}
        elif actor == 20:
            return {'user_id': 20, 'role': 'PM', 'capabilities': None}
        return {'user_id': actor, 'role': 'UNKNOWN', 'capabilities': None}

    def package(self, native_id):
        return {
            'id': native_id,
            'lockVersion': 1,
            'subject': f'Task {native_id}',
            'status': {'id': 7, 'name': 'In Progress'},
            '_links': {'project': {'href': '/api/v3/projects/6'}}
        }

    def packages(self):
        return [
            {'id': 379, 'lockVersion': 1, 'subject': 'Develop Mini Task Manager Application', 'status': {'name': 'In Progress'}},
            {'id': 380, 'lockVersion': 1, 'subject': 'Unit 1: Create/List', 'status': {'name': 'Review'}},
            {'id': 381, 'lockVersion': 1, 'subject': 'Unit 2: CRUD Web', 'status': {'name': 'Review'}},
        ]

    def call(self, path, method='GET', payload=None):
        if path == '/api/v3/projects/6':
            return {'id': 6, 'identifier': 'ai-dev-demo', 'active': True}
        return {}


class EngineeringReportingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        creds = Path(self.tmp.name) / "credentials.json"
        creds.write_text(json.dumps({'18': 'token-18', '20': 'token-20', '19': 'token-19'}))
        self.store = Store(Path(self.tmp.name))
        self.config = {
            'project_id': 5,
            'users': {'18': 'AI_SYSTEM_OWNER', '19': 'PM', '20': 'BA'},
            'openproject_url': 'http://127.0.0.1:18088',
            'engineering': {'enabled': True, 'actors': {'20': 'PM', '18': 'AI_SYSTEM_OWNER'}}
        }
        self.service = Service(
            self.store,
            self.config,
            Path(self.tmp.name) / 'workspaces',
            native_factory=lambda url, cred, proj: NativeMock()
        )
        engineering.setup(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_report_timestamps_preserve_instant_and_timezone_offset(self):
        stamp = datetime(2026, 11, 2, 3, 30, tzinfo=timezone.utc).timestamp()
        self.assertEqual(format_iso(stamp), '2026-11-02T10:30:00+07:00')
        self.assertEqual(datetime.fromisoformat(format_iso(stamp)).timestamp(), stamp)
        self.assertEqual(format_iso(stamp, 'UTC'), '2026-11-02T03:30:00+00:00')
        self.assertEqual(format_iso(0, 'UTC'), '1970-01-01T00:00:00+00:00')
        self.assertIsNone(format_iso(None))

    @patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[])
    def test_provider_usage_uses_scoped_generation_receipts_without_count_token_double_count(self, fetch):
        with self.store.connect() as db:
            for run, project in [('engineering-run', 6), ('other-project-run', 5)]:
                db.execute('INSERT INTO ai_queue(id,actor,payload,state,created) VALUES(?,?,?,?,?)',
                           (run, 20, json.dumps({'project_id': project}), 'finished', time.time()))
                db.execute('INSERT INTO ai_runs VALUES(?,?,?,?,?)', (run,20,'finished','{}',time.time()))
            db.execute('INSERT INTO requests(actor,key,hash,state,result) VALUES(?,?,?,?,?)',
                       (20,'legacy-engineering-run-token','fixture','done','{"totalTokenCount":9999}'))
        def receipt(identifier, phase, tokens, run='engineering-run'):
            self.store.provider_receipt({'id':identifier,'project':'provider-policy','run_id':run,
                'actor':20,'phase':phase,'state':'LIVE_SUCCESS',
                'usage':{'totalTokenCount':tokens} if tokens is not None else None})
        receipt('count','countTokens',100)
        receipt('gen','generateContent',150)
        receipt('gen','generateContent',150)  # Durable upsert must not double count replay.
        receipt('other','generateContent',5000,'other-project-run')
        scoped=engineering.scoped_service(self.service,6)
        runs=collect_factual_metrics(scoped,NativeMock())['runs']
        self.assertEqual(runs['estimated_tokens_consumed'],150)
        self.assertTrue(runs['usage_complete'])
        receipt('unknown','generateContent',None)
        runs=collect_factual_metrics(scoped,NativeMock())['runs']
        self.assertEqual(runs['estimated_tokens_consumed'],150)
        self.assertFalse(runs['usage_complete'])
        self.assertEqual(runs['usage_missing_calls'],1)
        with self.store.connect() as db:db.execute('DELETE FROM gemini_call_receipts')
        runs=collect_factual_metrics(scoped,NativeMock())['runs']
        self.assertIsNone(runs['estimated_tokens_consumed'])
        self.assertFalse(runs['usage_complete'])

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_collect_factual_metrics(self, mock_fetch):
        mock_fetch.return_value = [
            {"number": 1, "title": "PR 1", "state": "open", "is_merged": False, "merge_target": "UNMERGED", "head_sha": "abc12345", "base_ref": "main"},
            {"number": 2, "title": "PR 2", "state": "closed", "is_merged": True, "merge_target": "FEATURE_BRANCH (v1)", "head_sha": "def67890", "base_ref": "v1"},
        ]
        scoped = engineering.scoped_service(self.service, 6)
        metrics = collect_factual_metrics(scoped, NativeMock())

        self.assertEqual(metrics["project_id"], 6)
        self.assertEqual(metrics["github"]["total_prs"], 2)
        self.assertEqual(metrics["github"]["open_prs"], 1)
        self.assertEqual(metrics["github"]["merged_prs"], 1)
        self.assertEqual(metrics["work_packages"]["total_items"], 3)

    @patch('gateway.engineering_github_sync.fetch_pull_requests', side_effect=RuntimeError('synthetic-secret'))
    def test_unavailable_sources_are_unknown_not_zero_or_invented_parent(self, fetch):
        scoped = engineering.scoped_service(self.service, 6)
        with patch.object(NativeMock, 'packages', side_effect=RuntimeError('synthetic-secret')):
            report = generate_report(scoped, 18)
        self.assertEqual(report['source_status'], 'PARTIAL')
        self.assertIsNone(report['metrics']['work_packages']['total_items'])
        self.assertIsNone(report['metrics']['work_packages']['parent_379'])
        self.assertIsNone(report['metrics']['github']['total_prs'])
        self.assertNotIn('Develop Mini Task Manager Application', report['narrative'])
        self.assertNotIn('synthetic-secret', json.dumps(report))
        self.assertIn('Chưa có dữ liệu', report['narrative'])

    @patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[])
    def test_bounded_narrative_includes_newest_native_source(self, fetch):
        scoped=engineering.scoped_service(self.service,6)
        packages=[{'id':n,'lockVersion':1,'subject':f'Task {n}','status':{'name':'Review'}} for n in range(379,391)]
        with patch.object(NativeMock,'packages',return_value=packages):report=generate_report(scoped,20)
        self.assertIn('[WP #390](/work_packages/390/activity)',report['narrative'])
        self.assertEqual(report['metrics']['work_packages']['total_items'],12)

    @patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[])
    def test_reports_link_exact_sources_and_revalidate_native_revision(self, fetch):
        scoped = engineering.scoped_service(self.service, 6)
        report = generate_report(scoped, 18)
        self.assertIn('/work_packages/380/activity', report['narrative'])
        fresh = get_report(scoped, 18, report['id'])
        self.assertTrue(fresh['source_versions_current'])
        changed = NativeMock().packages()
        changed[1]['lockVersion'] = 2
        with patch.object(NativeMock, 'packages', return_value=changed):
            self.assertFalse(get_report(scoped, 18, report['id'])['source_versions_current'])
        with patch.object(NativeMock, 'packages', return_value=changed[:1]):
            hidden = get_report(scoped, 18, report['id'])
            listed = list_reports(scoped, 18)['reports'][0]
        self.assertTrue(hidden['data_hidden'])
        self.assertNotIn('narrative', hidden)
        self.assertTrue(listed['data_hidden'])
        self.assertFalse(listed['narrative'])
        self.assertFalse(listed['metrics'])

    @patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[])
    def test_absent_parent_is_not_invented_when_other_sources_are_available(self, fetch):
        scoped = engineering.scoped_service(self.service, 6)
        with patch.object(NativeMock, 'packages', return_value=NativeMock().packages()[1:]):
            report = generate_report(scoped, 18)
        self.assertIsNone(report['metrics']['work_packages']['parent_379'])
        self.assertIn('Chưa có dữ liệu', report['narrative'])

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_generate_report_on_demand_and_persistence(self, mock_fetch):
        mock_fetch.return_value = []
        scoped = engineering.scoped_service(self.service, 6)

        # Generate report as Owner (18)
        report = generate_report(scoped, 18, "ON_DEMAND", include_narrative=False)
        self.assertIn("id", report)
        self.assertEqual(report["report_type"], "ON_DEMAND")
        self.assertEqual(report["generated_by"], 18)
        self.assertEqual(report["generated_by_role"], "AI_SYSTEM_OWNER")
        self.assertIn("Tổng Quan Vận Hành", report["narrative"])

        # Check retrieval from DB
        retrieved = get_report(scoped, 18, report["id"])
        self.assertEqual(retrieved["id"], report["id"])
        self.assertEqual(retrieved["title"], report["title"])
        self.assertEqual(list_reports(scoped, 18)["reports"][0]["narrative"], retrieved["narrative"])
        for value in [report['generated_at_iso'], list_reports(scoped,18)['reports'][0]['created_iso']]:
            self.assertLess(abs(datetime.fromisoformat(value).timestamp()-report['generated_at']),1)
            self.assertTrue(value.endswith('+07:00'))

    @patch("gateway.engineering_github_sync.fetch_pull_requests", return_value=[])
    def test_factual_report_does_not_require_or_claim_provider_verification(self, mock_fetch):
        scoped = engineering.scoped_service(self.service, 6)
        with patch.object(scoped.gemini, "settings", side_effect=AssertionError("PROVIDER_MUST_NOT_BE_CHECKED")):
            report = generate_report(scoped, 18, include_narrative=False)
        self.assertTrue(report["narrative"].strip())
        for unverified_claim in ("$0.00", "341 WPs nguyên vẹn", "Hệ thống sẵn sàng"):
            self.assertNotIn(unverified_claim, report["narrative"])

    @patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[])
    def test_requested_ai_narrative_is_generated_and_persisted(self, mock_fetch):
        scoped=engineering.scoped_service(self.service,6)
        with patch.object(scoped.gemini,'structured',return_value=MagicMock(text='Theo dõi PR đang mở.')) as generate:
            report=generate_report(scoped,20,include_narrative=True)
        self.assertEqual(generate.call_count,1)
        call=generate.call_args
        self.assertEqual(call.kwargs['scope'].actor_id,20)
        self.assertEqual(call.kwargs['scope'].run_id,report['id'])
        self.assertEqual(call.kwargs['budget'].config.max_model_calls,1)
        self.assertEqual(call.kwargs['budget'].config.max_http_attempts,2)
        self.assertEqual(call.kwargs['budget'].config.max_output_tokens,1800)
        self.assertNotIn('Task 380',call.args[0])
        self.assertEqual(report['ai_narrative_status'],'GENERATED')
        self.assertIn('Theo dõi PR đang mở.',report['narrative'])
        self.assertEqual(get_report(scoped,20,report['id'])['ai_narrative_status'],'GENERATED')

    @patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[])
    def test_requested_ai_narrative_failure_is_explicit_and_redacted(self, mock_fetch):
        scoped=engineering.scoped_service(self.service,6)
        with patch.object(scoped.gemini,'structured',side_effect=RuntimeError('synthetic-secret')):
            report=generate_report(scoped,20,include_narrative=True)
        self.assertEqual(report['ai_narrative_status'],'UNAVAILABLE')
        self.assertIn('không khả dụng',report['narrative'])
        self.assertNotIn('synthetic-secret',report['narrative'])

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_generate_report_daily_and_weekly(self, mock_fetch):
        mock_fetch.return_value = []
        scoped = engineering.scoped_service(self.service, 6)

        # Daily report
        daily = generate_report(scoped, 20, "DAILY")
        self.assertEqual(daily["report_type"], "DAILY")
        self.assertIn("Daily Report", daily["title"])

        # Weekly report
        weekly = generate_report(scoped, 20, "WEEKLY")
        self.assertEqual(weekly["report_type"], "WEEKLY")
        self.assertIn("Weekly Report", weekly["title"])

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_list_reports_and_pagination(self, mock_fetch):
        mock_fetch.return_value = []
        scoped = engineering.scoped_service(self.service, 6)

        # Generate 3 reports
        for i in range(3):
            generate_report(scoped, 18, "ON_DEMAND")

        # List reports
        listing = list_reports(scoped, 18, limit=2, offset=0)
        self.assertEqual(listing["total"], 3)
        self.assertEqual(len(listing["reports"]), 2)

        # Second page
        listing2 = list_reports(scoped, 18, limit=2, offset=2)
        self.assertEqual(len(listing2["reports"]), 1)

    def test_invalid_report_type_rejected(self):
        scoped = engineering.scoped_service(self.service, 6)
        with self.assertRaises(ValueError):
            generate_report(scoped, 18, "INVALID_TYPE")

    @patch("gateway.engineering_github_sync.fetch_pull_requests")
    def test_dispatch_via_service_execute_actor(self, mock_fetch):
        mock_fetch.return_value = []
        scoped = engineering.scoped_service(self.service, 6)

        # 1. engineering_report_generate
        gen_res = scoped.execute_actor(18, {
            'action': 'engineering_report_generate',
            'arguments': {'report_type': 'DAILY', 'include_narrative': False}
        })
        self.assertIn('result', gen_res)
        report_id = gen_res['result']['id']

        # 2. engineering_report_list
        list_res = scoped.execute_actor(18, {
            'action': 'engineering_report_list',
            'arguments': {'limit': 5, 'offset': 0}
        })
        self.assertIn('result', list_res)
        self.assertGreaterEqual(list_res['result']['total'], 1)

        # 3. engineering_report_get
        get_res = scoped.execute_actor(18, {
            'action': 'engineering_report_get',
            'arguments': {'id': report_id}
        })
        self.assertIn('result', get_res)
        self.assertEqual(get_res['result']['id'], report_id)

    def test_unauthorized_actor_rejected(self):
        scoped = engineering.scoped_service(self.service, 6)
        with self.assertRaises(PermissionError):
            scoped.execute_actor(19, {
                'action': 'engineering_report_generate',
                'arguments': {'report_type': 'DAILY'}
            })


if __name__ == '__main__':
    unittest.main()

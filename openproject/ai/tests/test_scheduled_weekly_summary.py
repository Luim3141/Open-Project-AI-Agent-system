"""Signed machine schedules persist actor-scoped Native reports, never human approval or model calls."""
import time
import unittest
from unittest.mock import patch

from gateway.store import Store
from gateway.weekly_report import scheduled_week
from tests import test_daily_brief as fixtures


class ScheduledWeeklySummaryTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.DailyBriefTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)

    def command(self,**changes):
        return self.f.command(kind='weekly_summary',request_key=scheduled_week(time.time())[1],**changes)

    def test_signed_schedule_persists_each_authorized_actor_report_and_deduplicates(self):
        with patch.object(self.f.service.gemini,'sdk_client',side_effect=AssertionError('NO_MODEL')):
            response=self.f.post(self.command());self.assertEqual(response.status_code,200,response.text)
            receipt=response.json()['result']
            self.assertEqual((receipt['state'],receipt['ready'],receipt['targets']),('COMPLETED',5,5))
            self.assertIsNone(receipt['actor_id'])
            self.assertFalse(receipt['native_write_allowed'])
            self.assertEqual(self.f.post(self.command()).json()['result'],receipt)
            self.assertEqual(len(self.f.calls),5)
            restarted=Store(self.f.root)
            for report in receipt['reports']:
                saved=restarted.report(report['actor'],self.f.service.config['project_id'],report['report_id'])
                self.assertEqual(saved['sha256'],report['report_sha256'])
            with restarted.connect() as db:
                self.assertEqual(db.execute('select count(*) from proposals').fetchone()[0],0)
                self.assertEqual(db.execute('select count(*) from gemini_usage').fetchone()[0],0)

    def test_role_revocation_is_partial_and_request_cannot_choose_actor_or_project(self):
        self.f.state.roles.pop(8)
        receipt=self.f.post(self.command()).json()['result']
        self.assertEqual((receipt['status'],receipt['ready']),('PARTIAL',4))
        self.assertEqual(next(r for r in receipt['reports'] if r['actor']==8),{'actor':8,'state':'DENIED'})
        for claims in [{'actor_id':7},{'project_id':99},{'auto_execute':True}]:
            self.assertEqual(self.f.post({**self.command(),**claims}).status_code,422)

    def test_wrong_week_and_reserved_status_namespace_are_rejected(self):
        document=self.command();document['request_key']='weekly:2000-W01'
        self.assertEqual(self.f.post(document).status_code,422)
        document=self.command();document['kind']='status'
        self.assertEqual(self.f.post(document).status_code,422)

    def test_concurrent_duplicate_schedule_collects_once_and_restart_does_not_fabricate_completion(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as workers:
            replies=list(workers.map(lambda _:self.f.post(self.command()),range(2)))
        self.assertTrue(all(r.status_code==200 for r in replies))
        self.assertEqual(len(self.f.calls),5)
        self.assertEqual(self.f.post(self.command()).json()['result']['ready'],5)
        with self.f.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from automation_runs').fetchone()[0],1)

    def test_interrupted_collector_is_failed_and_never_replayed_as_a_success(self):
        receipt,_=self.f.store.begin_automation(self.command(),project=self.f.service.config['project_id'],targets=5)
        self.assertEqual(Store(self.f.root).fail_daily_brief(),1)
        result=self.f.post(self.command()).json()['result']
        self.assertEqual(result['run_id'],receipt['run_id'])
        self.assertEqual((result['state'],result['status']),('FAILED','INTERRUPTED_NO_REPLAY'))
        self.assertEqual(self.f.calls,[])

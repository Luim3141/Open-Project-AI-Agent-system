"""Weekly metrics must not invent status transition times from last modification."""
import unittest
from datetime import date

from gateway.weekly_report import generate_weekly_report


class WeeklyAccuracyTests(unittest.TestCase):
    def item(self,identifier,updated,status='DONE',percent=100):
        return {'id':identifier,'lockVersion':1,'subject':'Synthetic weekly fixture','updatedAt':updated,
            'percentageDone':percent,'_links':{'status':{'title':status},'type':{'title':'Task'},
                'assignee':{'href':'/api/v3/users/7','title':'Fixture'}}}

    def report(self,items):
        return generate_weekly_report(items,{7:{'name':'Fixture','role':'PM'}},7,'PM',date(2026,10,17),project_id=5)

    def test_percent_complete_does_not_override_native_workflow_status(self):
        from gateway.sprint_report import _is_closed
        from gateway.pm_agent import _is_closed as pm_closed
        item=self.item(12,'2026-10-16T10:00:00Z',status='NEW')
        self.assertFalse(_is_closed(item))
        self.assertFalse(pm_closed(item))

    def test_updated_done_item_is_not_proof_it_was_closed_this_week(self):
        result=self.report([self.item(12,'2026-10-16T10:00:00Z')])
        counts=result['weekly_summary']['raw_counts']
        self.assertIsNone(counts['closed_this_week'])
        self.assertIsNone(counts['throughput_velocity'])
        self.assertEqual(counts['closed_updated_in_window'],1)
        self.assertEqual(result['data_quality'],'PARTIAL_STATUS_HISTORY_UNAVAILABLE')

    def test_rolling_seven_days_use_bangkok_dates_and_exclude_future_updates(self):
        items=[self.item(12,'2026-10-10T20:00:00Z'),self.item(13,'2026-10-17T22:00:00Z'),
            self.item(14,'2026-10-10T12:00:00Z')]
        result=self.report(items)
        self.assertEqual(result['window_start'],'2026-10-11')
        self.assertEqual(result['weekly_summary']['raw_counts']['closed_updated_in_window'],1)

    def test_weekly_service_uses_native_actor_and_persists_only_role_scoped_member_data(self):
        import tempfile
        from pathlib import Path
        from gateway.store import Store
        from gateway.service import Service
        rows=[self.item(12,'2026-10-16T10:00:00Z'),self.item(13,'2026-10-16T10:00:00Z',status='NEW')]
        rows[1]['_links']['assignee']={'href':'/api/v3/users/8','title':'BA fixture'}
        class Native:
            def __init__(self,url,credential,project):
                self.role=credential
            def identity(self,actor):
                return {'user_id':actor,'role':self.role}
            def packages(self):
                return rows
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);store=Store(root);pm=store.issue_token(7,'PM','PM');ba=store.issue_token(8,'BA','BA')
            service=Service(store,{'users':{'7':'PM','8':'BA'},'project_id':5,'gateway_mode':'native',
                'openproject_url':'http://127.0.0.1:8088'},root/'workspace',Native)
            command={'action':'weekly_summary','arguments':{'as_of_date':'2026-10-17'}}
            result=service.execute(ba,command)['result']
            self.assertEqual(set(result['member_breakdown']),{'8'})
            self.assertFalse(result['model_used'])
            saved=store.report(8,5,result['report_id'])
            self.assertEqual(set(saved['document']['member_breakdown']),{'8'})
            self.assertEqual(set(service.execute(pm,command)['result']['member_breakdown']),{'7','8'})
            for arguments in ({'as_of_date':7},{'with_ai_summary':True},{'user_id':7}):
                with self.assertRaises(ValueError):
                    service.execute(ba,{'action':'weekly_summary','arguments':arguments})

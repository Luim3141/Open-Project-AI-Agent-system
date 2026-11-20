"""Synthetic dependencies: scheduling links are not evidence of an actual blocked state."""
import unittest
from datetime import date

from gateway.sprint_report import generate_sprint_report


def item(identifier, status='NEW', description='', actor=7):
    return {'id':identifier,'lockVersion':1,'subject':f'Fixture {identifier}',
        'description':{'raw':description},'_links':{'status':{'title':status},
            'assignee':{'href':f'/api/v3/users/{actor}','title':'Fixture'}}}


def relation(identifier, source, target, kind):
    return {'id':identifier,'type':kind,'_links':{
        'from':{'href':f'/api/v3/work_packages/{source}'},
        'to':{'href':f'/api/v3/work_packages/{target}'}}}


class SprintAccuracyTests(unittest.TestCase):
    def test_acceptance_criteria_and_unblocked_status_are_not_current_blockers(self):
        from gateway.pm_agent import analyze_blockers
        from gateway.role_alerts import AlertEngine
        from gateway.sprint_readiness import evaluate_sprint_readiness
        rows=[item(1,'UNBLOCKED','AC: Không bị chặn bởi #2. Nếu bị chặn, cần cảnh báo.'),item(2)]
        report=generate_sprint_report(rows)['report']
        self.assertEqual(report['blocked'],[])
        self.assertEqual(analyze_blockers(rows)[0],[])
        alerts=AlertEngine().evaluate(rows,7,'PM')
        self.assertFalse(any(a['type']=='BLOCKER' for a in alerts['alerts']))
        self.assertEqual(evaluate_sprint_readiness(rows)['blocked_packages'],[])

    def test_typed_relations_preserve_direction_and_separate_scheduling_from_blocks(self):
        rows=[item(1),item(2),item(3,'DONE'),item(4),item(5)]
        links=[relation(11,1,2,'follows'),relation(12,4,1,'blocked'),
            relation(13,3,5,'blocks'),relation(14,1,999,'blocks')]
        report=generate_sprint_report(rows,relations=links)['report']
        self.assertEqual([(p['id'],p['blocker_ids']) for p in report['blocked']],[(4,[1])])
        self.assertEqual(report['dependencies'],[{'id':1,'prerequisite_ids':[2],'relation_ids':[11]}])
        self.assertNotIn('999',str(report))
        self.assertEqual(report['dependency_data_quality'],'NATIVE_RELATIONS_READ')

    def test_non_pm_sees_only_own_dependency_detail_and_explicit_status_stays_blocked(self):
        rows=[item(1,actor=8),item(2),item(3,'BLOCKED','Bị chặn bởi #2; xem #1.',actor=8)]
        links=[relation(11,1,2,'follows'),relation(12,2,1,'follows')]
        report=generate_sprint_report(rows,actor_id=7,actor_role='BA',relations=links)['report']
        self.assertEqual([p['id'] for p in report['dependencies']],[2])
        self.assertEqual(report['blocked'],[])
        pm=generate_sprint_report(rows,relations=links)['report']
        self.assertEqual(pm['blocked'][0]['blocker_ids'],[2])

    def test_missing_relation_data_is_not_reported_as_verified_on_track(self):
        result=generate_sprint_report([item(1)],as_of_date=date(2026,10,23))['report']
        self.assertEqual(result['dependency_data_quality'],'UNAVAILABLE')
        self.assertNotEqual(result['sprint_health']['status'],'ON_TRACK')

    def test_native_relations_are_batched_scoped_and_filter_cross_project_endpoints(self):
        import json
        from urllib.parse import urlsplit,parse_qs
        from gateway.native import Native
        class Probe(Native):
            paths=[]
            def collection(self,path):
                self.paths.append(path)
                return [relation(11,1,2,'follows'),relation(12,1,999,'blocks')]
        native=Probe('http://127.0.0.1:8088','synthetic',5)
        self.assertEqual(native.relations([item(1),item(2)]),[relation(11,1,2,'follows')])
        filters=json.loads(parse_qs(urlsplit(native.paths[0]).query)['filters'][0])
        self.assertEqual(filters,[{'involved':{'operator':'=','values':['1','2']}}])
        self.assertEqual(native.relations([]),[])

    def test_service_persists_only_scoped_detail_and_rejects_actor_injection(self):
        import tempfile
        from pathlib import Path
        from gateway.store import Store
        from gateway.service import Service
        rows=[item(1),item(2,actor=8)]
        links=[relation(11,1,2,'blocked'),relation(12,2,1,'follows')]
        class Native:
            def __init__(self,url,credential,project):
                self.role=credential
            def identity(self,actor):
                return {'user_id':actor,'role':self.role}
            def packages(self):
                return rows
            def relations(self,packages):
                return links
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);store=Store(root)
            pm=store.issue_token(7,'PM','PM');ba=store.issue_token(8,'BA','BA')
            service=Service(store,{'users':{'7':'PM','8':'BA'},'project_id':5,'gateway_mode':'native',
                'openproject_url':'http://127.0.0.1:8088'},root/'workspace',Native)
            command={'action':'sprint_risks','arguments':{'as_of_date':'2026-10-23'}}
            result=service.execute(ba,command)['result']
            self.assertEqual(result['report']['blocked'],[])
            self.assertEqual([d['id'] for d in result['report']['dependencies']],[2])
            saved=store.report(8,5,result['report_id'])
            self.assertEqual(saved['document']['report'],result['report'])
            self.assertEqual(len(service.execute(pm,command)['result']['report']['blocked']),1)
            for arguments in ({'actor_id':7},{'relations':[]},{'as_of_date':7}):
                with self.assertRaises(ValueError):
                    service.execute(ba,{'action':'sprint_risks','arguments':arguments})


if __name__=='__main__':
    unittest.main()

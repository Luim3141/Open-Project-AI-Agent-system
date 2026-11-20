"""Own dated children may derive parent dates; unrelated model changes remain a hold."""
import copy
import unittest
from types import SimpleNamespace

from gateway.native_wbs import parent_reschedule
from gateway.native_wbs_hierarchy import capture_parent
from gateway.store import canonical,digest
from tests import test_native_wbs as fixtures


class ScheduledParentEffectsTests(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.NativeWbsTests();self.h.setUp();self.addCleanup(self.h.doCleanups)
        self.plan=self.h.plan();self.node=self.plan['spec']['nodes'][0]
        self.plan['spec']['nodes']=[self.node]
        self.plan['spec']['_hierarchy_readback']=1
        self.before={'id':376,'lockVersion':0,'subject':'Parent','startDate':None,'dueDate':None,
            'derivedStartDate':None,'derivedDueDate':None,'duration':None,'scheduleManually':True,
            'createdAt':'2026-10-26T00:00:00.000Z','updatedAt':'2026-10-26T00:00:00.000Z',
            '_links':{'children':[]}}
        self.item=copy.deepcopy(self.before);self.attributes={'id':376,'project_id':5,'lock_version':0,
            'subject':'Parent','start_date':None,'due_date':None,'duration':None,'schedule_manually':True,
            'updated_at':self.before['updatedAt']}
        self.calendar=1
        def call(path,*args,**kwargs):
            state={'attributes':copy.deepcopy(self.attributes),'parent_id':None}
            return {'id':376,'actor_id':18,'project_id':5,'lock_version':self.item['lockVersion'],
                'snapshot':state,'snapshot_sha256':digest(canonical(state)),'working_duration':self.calendar}
        self.native=SimpleNamespace(call=call,package=lambda identifier:copy.deepcopy(self.item))
        self.children=[]

    def child(self,key,identifier,day,version):
        node={'key':key,'parent':self.node['key'],'start_date':day,'due_date':day}
        self.plan['spec']['nodes'].append(node)
        proposal_key='scheduled-'+key
        capture_parent(self.h.service,self.plan,self.native,376,proposal_key)
        receipt={'id':identifier,'lockVersion':0,'createdAt':f'2026-10-26T00:00:0{identifier-376}.000Z',
            'startDate':day,'dueDate':day,'_links':{'parent':{'href':'/api/v3/work_packages/376'}}}
        self.children.append({'key':key,'native_id':identifier,'state':'VERIFIED','receipt':{'result':receipt},
            'proposal':{'command':{'idempotency_key':proposal_key,'arguments':{'start_date':day,'due_date':day}}}})
        dates=[row['receipt']['result']['startDate'] for row in self.children];self.calendar=len(set(dates))
        self.item.update(lockVersion=version,startDate=min(dates),dueDate=max(dates),derivedStartDate=min(dates),
            derivedDueDate=max(dates),duration=f'P{self.calendar}D',scheduleManually=False,updatedAt=receipt['createdAt'])
        self.item['_links']['children']=[{'href':f'/api/v3/work_packages/{row["native_id"]}'} for row in self.children]
        self.attributes.update(lock_version=version,start_date=min(dates),due_date=max(dates),duration=self.calendar,
            schedule_manually=False,updated_at=receipt['createdAt'])

    def proof(self):
        return parent_reschedule(self.h.service,self.plan,self.native,self.node,{'receipt':{'result':self.before}},
            self.item,[{'state':'NATIVE_CONFIRMED'},*self.children])

    def test_exact_native_two_save_first_child_and_later_child_chain(self):
        self.child('dated-a',377,'2026-10-26',2)
        first=self.proof();self.assertIsNotNone(first)
        self.assertEqual(first['kind'],'NATIVE_DATED_CHILD_MODEL_CHAIN')
        self.child('dated-b',378,'2026-10-27',3)
        self.assertIsNotNone(self.proof())
        self.assertIsNotNone(self.proof(),'A read retry must reuse immutable proofs')

    def test_business_edit_unknown_child_extra_version_and_bad_calendar_are_not_parent_effects(self):
        for change in ['subject','hidden','version','unknown_child','date','calendar']:
            with self.subTest(change=change):
                self.setUp()
                self.child('dated-a',377,'2026-10-26',2)
                if change=='subject':self.attributes['subject']='Unapproved'
                if change=='hidden':self.attributes['custom_field']='Unapproved'
                if change=='version':self.item['lockVersion']=self.attributes['lock_version']=3
                if change=='unknown_child':self.item['_links']['children'].append({'href':'/api/v3/work_packages/999'})
                if change=='date':self.item['dueDate']=self.attributes['due_date']='2026-10-28'
                if change=='calendar':self.calendar=10
                self.assertIsNone(self.proof())

    def test_expanded_parent_changes_do_not_change_the_verified_work_package(self):
        self.item['_embedded']={'parent':{'lockVersion':1}}
        self.child('dated-a',377,'2026-10-26',2)
        self.assertIsNotNone(self.proof())
        self.item['_embedded']['parent']['lockVersion']=2
        self.assertIsNotNone(self.proof())


if __name__=='__main__':unittest.main()

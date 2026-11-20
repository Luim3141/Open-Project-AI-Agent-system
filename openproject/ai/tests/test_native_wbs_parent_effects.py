"""Native first-child scheduling changes must be proved, never treated as arbitrary drift."""
import copy
import unittest
from tests import test_native_wbs as wbs


class NativeWbsParentEffectsTests(unittest.TestCase):
    def setUp(self):
        self.h=wbs.NativeWbsTests();self.h.setUp();self.addCleanup(self.h.doCleanups)
        original=self.h.native.call
        def call(native,path,method='GET',payload=None):
            result=original(native,path,method,payload)
            if method=='POST' and path=='/api/v3/work_packages':
                row=self.h.native.rows[result['id']];index=len(native.writes)
                row.update(createdAt=f'2026-10-24T00:00:0{index}.000Z',updatedAt=f'2026-10-24T00:00:0{index}.000Z',scheduleManually=True)
                parent=payload['_links'].get('parent',{}).get('href')
                if parent:
                    p=self.h.native.rows[int(parent.rsplit('/',1)[-1])]
                    p['_links'].setdefault('children',[]).append({'href':f'/api/v3/work_packages/{row["id"]}','title':row['subject']})
                    if p['scheduleManually']:
                        p.update(lockVersion=p['lockVersion']+1,scheduleManually=False,updatedAt=f'2026-10-24T00:00:0{index}.100Z')
                        native.activities.setdefault(p['id'],[]).append({'id':5000+index,'version':p['lockVersion']+1,'createdAt':p['updatedAt'],
                            '_links':{'user':{'href':'/api/v3/users/18'},'workPackage':{'href':parent}},'details':[]})
            return result
        self.h.native.call=call
        self.plan=self.h.plan()

    def approve_next(self,key):
        p=self.h.next(self.plan,key)['proposal'];r=self.h.service.decide_proposal(self.h.tokens[18],p['id'],'approve',p['hash'])
        self.h.verify_sync(r);return r['result']['id']

    def refresh_parent(self,identifier):
        key='parent-refresh-'+str(identifier);self.h.store.begin(18,key,'read');self.h.store.finish(18,key,{},knowledge_id=identifier)
        claim=self.h.store.claim_knowledge_sync();self.assertEqual(claim['native_id'],identifier)
        version=self.h.native.rows[identifier]['lockVersion']
        self.h.store.finish_knowledge_sync(claim,{'native_id':identifier,'lock_version':version,'vector_indexed':True,
            'canonical':{'native_id':identifier,'lock_version':version,'vector_indexed':True}})

    def progress(self):return self.h.call('wbs_get',{'id':self.plan['id']})['progress']

    def test_first_child_requires_current_parent_rag_and_then_allows_exact_next_node(self):
        epic=self.approve_next('epic');task=self.approve_next('task')
        self.assertEqual(self.progress()['state'],'RAG_PENDING')
        self.refresh_parent(epic)
        p=self.progress();self.assertEqual(p['state'],'READY_TO_PROPOSE')
        self.assertEqual(p['nodes'][0]['native_parent_change']['from_version'],0)
        self.assertEqual(p['nodes'][0]['native_parent_change']['to_version'],1)
        self.assertEqual(p['nodes'][0]['native_parent_change']['verified_child_ids'],[task])
        subtask=self.approve_next('subtask');self.assertEqual(self.progress()['state'],'RAG_PENDING')
        self.refresh_parent(task);self.assertEqual(self.progress()['state'],'VERIFIED_COMPLETED')
        self.assertEqual(len(self.h.native.writes),3)

    def test_parent_business_drift_extra_version_or_unknown_child_stays_blocked(self):
        epic=self.approve_next('epic');self.approve_next('task');self.refresh_parent(epic)
        baseline=copy.deepcopy(self.h.native.rows[epic])
        self.assertEqual(self.progress()['state'],'READY_TO_PROPOSE')
        for mutate in [lambda r:r.update(subject='Different'),lambda r:r.update(lockVersion=2),
                       lambda r:r.update(dueDate='2026-12-01'),lambda r:r.update(customField99='unapproved'),
                       lambda r:r['_links'].update(assignee={'href':'/api/v3/users/21'}),
                       lambda r:r['_links']['children'].append({'href':'/api/v3/work_packages/999'})]:
            with self.subTest(mutation=mutate):
                self.h.native.rows[epic]=copy.deepcopy(baseline);mutate(self.h.native.rows[epic])
                self.assertEqual(self.h.next(self.plan,'blocked-'+str(id(mutate)))['state'],'SOURCE_CHANGED')
                self.assertEqual(len(self.h.native.writes),2)

    def test_missing_foreign_or_unrelated_native_activity_cannot_explain_version_change(self):
        epic=self.approve_next('epic');self.approve_next('task');self.refresh_parent(epic)
        baseline=copy.deepcopy(self.h.native.activities[epic]);self.assertEqual(self.progress()['state'],'READY_TO_PROPOSE')
        for mutate in [lambda rows:rows.clear(),lambda rows:rows[0]['_links']['user'].update(href='/api/v3/users/19'),
                       lambda rows:rows[0].update(createdAt='2026-10-23T00:00:00.000Z'),
                       lambda rows:rows[0].update(version=3)]:
            self.h.native.activities[epic]=copy.deepcopy(baseline);mutate(self.h.native.activities[epic])
            self.assertEqual(self.progress()['state'],'SOURCE_CHANGED')


if __name__=='__main__':unittest.main()

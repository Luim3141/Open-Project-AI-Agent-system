"""Merged Native journals must not hide unrelated parent changes."""
import unittest

from gateway.native import NativeError
from gateway.native_wbs_hierarchy import read
from gateway.store import canonical,digest
from tests.test_native_wbs_parent_effects import NativeWbsParentEffectsTests


class WbsHierarchyReadbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture=NativeWbsParentEffectsTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.h=self.fixture.h;original=self.h.native.call;self.extra={};self.corrupt=None
        def call(native,path,method='GET',payload=None):
            if path=='/api/v3/qldapm/capabilities':
                return {'project_id':5,'enforced':True,'wbs_hierarchy_readback_version':1}
            if path.startswith('/api/v3/qldapm/wbs_hierarchy/'):
                row=self.h.native.rows[int(path.rsplit('/',1)[-1])]
                attributes={'id':row['id'],'project_id':5,'lock_version':row['lockVersion'],
                    'schedule_manually':row['scheduleManually'],'updated_at':row['updatedAt'],
                    'subject':row['subject'],'description':row['description'],**self.extra}
                state={'attributes':attributes,'parent_id':row.get('_links',{}).get('parent',{}).get('href')}
                result={'id':row['id'],'project_id':5,'actor_id':18,'lock_version':row['lockVersion'],
                    'snapshot':state,'snapshot_sha256':digest(canonical(state))}
                if self.corrupt:self.corrupt(result)
                return result
            result=original(native,path,method,payload)
            if path=='/api/v3/work_packages' and method=='POST':
                # OpenProject may merge its automatic scheduling journal into version 1.
                self.h.native.activities.clear()
            return result
        self.h.native.call=call
        draft=self.h.draft(key='model-proof-draft')
        self.fixture.plan=self.h.call('wbs_adopt',{'id':draft['id'],'hash':draft['hash']},18,'model-proof-plan')

    def test_merged_journal_tree_advances_with_exact_model_proof_and_current_rag(self):
        epic=self.fixture.approve_next('epic');task=self.fixture.approve_next('task')
        self.assertEqual(self.fixture.progress()['state'],'RAG_PENDING')
        self.fixture.refresh_parent(epic)
        result=self.fixture.progress();self.assertEqual(result['state'],'READY_TO_PROPOSE')
        self.assertEqual(result['nodes'][0]['native_parent_change']['kind'],'NATIVE_FIRST_CHILD_MODEL_READBACK')
        proposal=self.h.next(self.fixture.plan,'subtask-proposal')['proposal']
        self.assertEqual(proposal['command']['arguments']['source_references'],[{'work_package_id':task,'lock_version':0}])
        receipt=self.h.service.decide_proposal(self.h.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.h.verify_sync(receipt);self.fixture.refresh_parent(task)
        self.assertEqual(self.fixture.progress()['state'],'VERIFIED_COMPLETED')
        self.assertFalse(self.h.native.activities);self.assertEqual(len(self.h.native.writes),3)

    def test_model_only_business_change_is_not_explained_by_automatic_scheduling(self):
        epic=self.fixture.approve_next('epic');self.fixture.approve_next('task');self.fixture.refresh_parent(epic)
        self.assertEqual(self.fixture.progress()['state'],'READY_TO_PROPOSE')
        self.extra['hidden_custom_field']='unapproved'
        self.assertEqual(self.fixture.progress()['state'],'SOURCE_CHANGED')
        self.assertEqual(len(self.h.native.writes),2)

    def test_missing_private_before_proof_blocks_parent_change(self):
        epic=self.fixture.approve_next('epic');self.fixture.approve_next('task');self.fixture.refresh_parent(epic)
        with self.h.store.connect() as db:db.execute("DELETE FROM wbs_documents WHERE json_extract(document,'$.kind')='hierarchy_before'")
        with self.assertRaisesRegex(ValueError,'WBS_PARENT_PROOF_REQUIRED'):self.fixture.progress()

    def test_readback_rejects_forgery_and_malformed_snapshots(self):
        epic=self.fixture.approve_next('epic')
        mutations=[lambda r:r.update(actor_id=19),lambda r:r.update(id=True),lambda r:r.update(project_id=6),
            lambda r:r.update(lock_version=True),lambda r:r.update(snapshot_sha256='0'*64),
            lambda r:r.update(snapshot=None),lambda r:r['snapshot'].update(attributes=[])]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.corrupt=mutation
                with self.assertRaises(NativeError):read(self.h.native('fixture','owner',5),18,epic)


if __name__=='__main__':unittest.main()

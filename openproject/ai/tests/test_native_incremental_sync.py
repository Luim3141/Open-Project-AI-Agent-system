"""Native read fixture + real durable SQLite/outbox/ingester; no Main or Native writes."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.native import NativeError
from gateway.service import Service
from gateway.store import Store
from tests.test_rag_recovery import VectorFixture


class NativeIncrementalSyncTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.store=Store(self.root)
        self.pm=self.store.issue_token(7,'PM','PM');self.ba=self.store.issue_token(8,'BA','BA')
        class Native:
            rows=[{'id':12,'lockVersion':1,'subject':'Incremental contract','description':{'raw':'Initial requirements'},'_links':{}}]
            activities=[]
            fail=False
            def __init__(self,url,credential,project):self.role=credential
            def identity(self,actor):return {'user_id':actor,'role':self.role}
            def packages(self):
                if self.fail:raise NativeError(503,'ISOLATED_COLLECTION_FAILURE')
                return copy.deepcopy(self.rows)
            def package(self,identifier):
                for row in self.rows:
                    if row['id']==identifier:return copy.deepcopy(row)
                raise NativeError(404,'ISOLATED_NATIVE_NOT_VISIBLE')
            def collection(self,path):
                if path.endswith('/activities'):return copy.deepcopy(self.activities)
                raise AssertionError(path)
            def call(self,*args,**kwargs):raise AssertionError('No Native write or direct API bypass permitted')
        self.native=Native
        self.config={'users':{'7':'PM','8':'BA'},'project_id':5,'gateway_mode':'native','openproject_url':'http://127.0.0.1:8088'}
        self.vector=VectorFixture();self.addCleanup(patch.stopall)
        patch('gateway.vector_client.VectorClient',return_value=self.vector).start()
        self.service=self.restart()

    def restart(self):return Service(Store(self.root),self.config,self.root/'workspace',self.native)

    def scan(self,key):
        return self.service.execute(self.pm,{'action':'knowledge_incremental_sync','arguments':{},'idempotency_key':key})['result']

    def test_native_revision_is_queued_once_survives_restart_and_retrieves_verified_new_content(self):
        self.service.sync_canonical_native(7,12)
        first=self.scan('initial-scan')
        self.assertEqual(first['changed'],0)
        self.assertEqual(first['visible'],1)
        self.native.rows[0].update(lockVersion=2,description={'raw':'Updated incremental acceptance marker'})
        changed=self.scan('changed-scan')
        self.assertEqual(changed['changed'],1)
        job=changed['jobs'][0]['id']
        self.service=self.restart()
        self.assertEqual(self.store.knowledge_sync(7,job)['state'],'pending')
        self.assertTrue(self.service.process_knowledge_sync())
        self.assertEqual(self.store.knowledge_sync(7,job)['state'],'verified')
        self.assertEqual(self.scan('duplicate-scan')['changed'],0)
        result=self.service.execute(self.pm,{'action':'knowledge_search','arguments':{'query':'incremental acceptance','native_ids':[12]}})['result']
        self.assertTrue(result['items'])
        self.assertEqual({i['lock_version'] for i in result['items']},{2})
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_sync').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM proposals').fetchone()[0],0)

    def test_native_create_hash_change_and_duplicate_event_do_not_duplicate_refresh_jobs(self):
        created=self.scan('created')
        self.assertEqual(created['changed'],1)
        again=self.scan('created-again')
        self.assertEqual(again['jobs'][0]['id'],created['jobs'][0]['id'])
        self.assertTrue(self.service.process_knowledge_sync())
        self.native.rows[0]['description']['raw']='Changed hash without a version assumption'
        changed=self.scan('hash-change')
        self.assertEqual(changed['changed'],1)
        self.assertNotEqual(changed['jobs'][0]['id'],created['jobs'][0]['id'])
        self.assertTrue(self.service.process_knowledge_sync())
        self.assertEqual(self.scan('settled')['changed'],0)

    def test_comment_only_add_edit_and_removal_sync_without_a_work_package_version_change(self):
        self.service.sync_canonical_native(7,12)
        self.assertEqual(self.scan('comments-baseline')['changed'],0)
        for index,comments in enumerate([
                [{'id':100,'comment':{'raw':'New journal acceptance marker'}}],
                [{'id':100,'comment':{'raw':'Edited journal replacement marker'}}],
                []]):
            self.native.activities=comments
            report=self.scan('comment-change-'+str(index))
            self.assertEqual(report['changed'],1)
            self.assertTrue(self.service.process_knowledge_sync())
            self.assertEqual(self.store.knowledge_sync(7,report['jobs'][0]['id'])['state'],'verified')
            self.assertEqual(self.scan('comment-repeat-'+str(index))['changed'],0)
            from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
            documents=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.root/'knowledge.sqlite'))).query_documents('5')
            own=next(d for d in documents if d.source_id=='actor:7:wp:12')
            self.assertEqual(own.metadata['lock_version'],1)
            self.assertEqual(own.metadata['activity_ids'],[a['id'] for a in comments])
            shared=next(d for d in documents if d.source_id=='op:wp:12')
            self.assertNotIn('journal',shared.content)
            if comments:self.assertIn(comments[0]['comment']['raw'],own.content)
            else:self.assertNotIn('journal',own.content)

    def test_comment_changes_outside_the_snippet_and_same_revision_replay_are_not_lost(self):
        self.service.sync_canonical_native(7,12)
        self.native.activities=[{'id':100,'comment':{'raw':'x'*800+'first'}}]
        first=self.scan('long-comment');self.service.process_knowledge_sync()
        self.native.activities[0]['comment']['raw']='x'*800+'second'
        changed=self.scan('long-comment-edit')
        self.assertEqual(changed['changed'],1)
        self.assertNotEqual(changed['jobs'][0]['id'],first['jobs'][0]['id'])
        self.assertEqual(self.scan('long-comment-duplicate')['jobs'][0]['id'],changed['jobs'][0]['id'])
        self.service=self.restart();self.assertTrue(self.service.process_knowledge_sync())
        self.assertEqual(self.scan('long-comment-settled')['changed'],0)

    def test_comment_access_failure_cannot_commit_a_partial_inventory(self):
        self.service.sync_canonical_native(7,12);before=self.scan('activities-before')
        with patch.object(self.native,'collection',side_effect=NativeError(403,'ISOLATED_ACTIVITY_DENIED')):
            with self.assertRaises(NativeError):self.scan('activities-denied')
        after=self.service.execute(self.pm,{'action':'knowledge_incremental_status','arguments':{}})['result']
        self.assertEqual(after['generation'],before['generation'])

    def test_actor_comment_snapshot_is_not_shared_and_stale_activity_sets_are_not_retrieved(self):
        self.native.activities=[{'id':100,'comment':{'raw':'privatenonce journalmarker'}}]
        self.scan('private-comment');self.service.process_knowledge_sync()
        def search(token):
            return self.service.execute(token,{'action':'knowledge_search','arguments':{'query':'privatenonce journalmarker'}})['result']['items']
        self.assertTrue(search(self.pm))
        self.config['users']['9']='PM'
        another=self.store.issue_token(9,'PM','PM')
        self.assertEqual(search(another),[])
        self.native.activities.append({'id':101,'comment':{'raw':'Newer activity changes the snapshot'}})
        self.assertEqual(search(self.pm),[])
        self.scan('newer-comment');self.service.process_knowledge_sync()
        self.assertTrue(search(self.pm))
        with patch.object(self.native,'collection',side_effect=NativeError(403,'ACTIVITY_PERMISSION_REVOKED')):
            self.assertEqual(search(self.pm),[])

    def test_updated_at_detects_changes_outside_the_bounded_activity_audit_and_audit_rotates(self):
        import datetime,time
        template=copy.deepcopy(self.native.rows[0])
        self.native.rows=[{**copy.deepcopy(template),'id':i,'updatedAt':'2026-01-01T00:00:00Z'} for i in range(100,140)]
        for row in self.native.rows:self.service.sync_canonical_native(7,row['id'])
        first=self.scan('bounded-baseline')
        self.assertEqual(first['changed'],0)
        self.assertEqual(len(first['activity_audit_ids']),32)
        target=next(row for row in self.native.rows if row['id']==130)
        target['updatedAt']=datetime.datetime.fromtimestamp(time.time()+1,datetime.timezone.utc).isoformat()
        with patch.object(self.native,'collection',autospec=True,return_value=[]) as activities:
            second=self.scan('bounded-new-comment-timestamp')
        self.assertNotIn(130,second['activity_audit_ids'])
        self.assertEqual([j['native_id'] for j in second['jobs']],[130])
        self.assertLessEqual(activities.call_count,32)
        self.assertEqual(set(first['activity_audit_ids'])|set(second['activity_audit_ids']),set(range(100,140)))

    def test_visibility_withdrawal_excludes_retrieval_but_never_deletes_points(self):
        self.service.sync_canonical_native(7,12);self.scan('visible')
        points=copy.deepcopy(self.vector.points);self.native.rows=[]
        withdrawn=self.scan('withdrawn')
        self.assertEqual(withdrawn['visibility_withdrawn_ids'],[12])
        self.assertEqual(withdrawn['physical_deletion'],'DENIED_WITHOUT_TRUSTED_DELETE_PROOF')
        self.assertEqual(self.vector.points,points)
        search=self.service.execute(self.pm,{'action':'knowledge_search','arguments':{'query':'requirements'}})['result']
        self.assertEqual(search['items'],[])
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT visible FROM native_index_cursor WHERE native_id=12').fetchone()[0],0)

    def test_failed_or_invalid_native_collection_cannot_mark_sources_withdrawn(self):
        self.service.sync_canonical_native(7,12);first=self.scan('before-failure')
        self.native.fail=True
        with self.assertRaises(NativeError):self.scan('failed-read')
        self.native.fail=False
        self.native.rows*=2
        with self.assertRaisesRegex(NativeError,'NATIVE_INDEX_INVALID_COLLECTION'):self.scan('duplicate-native-id')
        status=self.service.execute(self.pm,{'action':'knowledge_incremental_status','arguments':{}})['result']
        self.assertEqual(status['inventory_sha256'],first['inventory_sha256'])
        self.assertEqual(status['generation'],first['generation'])

    def test_authorization_claims_and_other_actor_inventory_are_not_accepted(self):
        with self.assertRaises(PermissionError):
            self.service.execute(self.ba,{'action':'knowledge_incremental_sync','arguments':{},'idempotency_key':'ba-denied'})
        self.scan('private-inventory')
        own=self.service.execute(self.ba,{'action':'knowledge_incremental_status','arguments':{}})['result']
        self.assertEqual(own['state'],'NOT_OBSERVED')
        for action in ['knowledge_incremental_sync','knowledge_incremental_status']:
            with self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):
                self.service.execute(self.pm,{'action':action,'arguments':{'actor_id':8,'authority':'machine','approved':True},'idempotency_key':'forged'})

    def test_backoff_is_not_reset_by_a_repeated_scan_and_worker_survives_restart(self):
        first=self.scan('new-outbox');identifier=first['jobs'][0]['id']
        self.vector.fail_upsert=True
        self.service.process_knowledge_sync()
        before=self.store.knowledge_sync(7,identifier)
        self.assertEqual(before['state'],'retry')
        self.service=self.restart();self.scan('repeat-failure')
        after=self.store.knowledge_sync(7,identifier)
        self.assertEqual((after['state'],after['attempts'],after['next_at']),(before['state'],before['attempts'],before['next_at']))
        self.vector.fail_upsert=False
        with self.store.connect() as db:db.execute('UPDATE knowledge_sync SET next_at=0 WHERE id=?',(identifier,))
        self.service.process_knowledge_sync()
        self.assertEqual(self.store.knowledge_sync(7,identifier)['state'],'verified')

    def test_automatic_existing_worker_persists_a_machine_scan_without_a_webhook(self):
        import time
        self.service.sync_canonical_native(7,12)
        self.config['native_incremental_sync']={'enabled':True,'actor':7}
        self.service.start_knowledge_worker()
        try:
            for _ in range(40):
                status=self.service.execute(self.pm,{'action':'knowledge_incremental_status','arguments':{}})['result']
                if status['state']=='OBSERVED':break
                time.sleep(0.05)
            self.assertEqual(status['authority'],'machine')
            self.assertEqual(status['visible'],1)
            self.assertEqual(status['changed'],0)
        finally:
            self.service.stop_knowledge_worker()
            # Finish the fixture thread before restoring patches and deleting its SQLite directory.
            self.service._knowledge_thread.join(timeout=15)
            self.assertFalse(self.service._knowledge_thread.is_alive())

    def test_project5_scan_failure_does_not_starve_project6_refresh(self):
        from types import SimpleNamespace
        self.config['native_incremental_sync']={'enabled':True,'actor':7}
        self.config['engineering']={'enabled':True}
        engineering=SimpleNamespace(config={'project_id':6})
        calls=[]
        def scan(target,actor,authority):
            calls.append((target.config['project_id'],actor,authority))
            self.service._knowledge_stop.set()  # One deterministic worker iteration.
            if target is self.service:
                raise NativeError(503,'ISOLATED_PROJECT5_SCAN_FAILURE')
        with patch.object(self.service,'process_knowledge_sync'), \
                patch('gateway.notification_delivery.process_pending'), \
                patch('gateway.n8n_lifecycle_outbox.deliver_pending'), \
                patch('gateway.native_incremental.scan',side_effect=scan), \
                patch('gateway.engineering.scoped_service',return_value=engineering), \
                patch('gateway.engineering_reporting.check_and_run_scheduled_reports'):
            self.service.start_knowledge_worker()
            self.service._knowledge_thread.join(timeout=5)
            self.assertFalse(self.service._knowledge_thread.is_alive())
        self.assertEqual(calls,[(5,7,'machine'),(6,20,'machine')])

    def test_project6_scan_failure_does_not_starve_reporting_tick(self):
        from types import SimpleNamespace
        self.config['native_incremental_sync']={'enabled':True,'actor':7}
        self.config['engineering']={'enabled':True}
        engineering=SimpleNamespace(config={'project_id':6})
        def scan(target,actor,authority):
            if target is engineering:
                self.service._knowledge_stop.set()
                raise NativeError(503,'ISOLATED_PROJECT6_SCAN_FAILURE')
        with patch.object(self.service,'process_knowledge_sync'), \
                patch('gateway.notification_delivery.process_pending'), \
                patch('gateway.n8n_lifecycle_outbox.deliver_pending'), \
                patch('gateway.native_incremental.scan',side_effect=scan), \
                patch('gateway.engineering.scoped_service',return_value=engineering), \
                patch('gateway.engineering_reporting.check_and_run_scheduled_reports') as reports:
            self.service.start_knowledge_worker()
            self.service._knowledge_thread.join(timeout=5)
            self.assertFalse(self.service._knowledge_thread.is_alive())
            reports.assert_called_once_with(engineering,20)

    def test_absent_source_survives_restart_and_reappears_without_destructive_tombstone(self):
        self.service.sync_canonical_native(7,12);self.scan('before-withdrawal')
        rows=copy.deepcopy(self.native.rows);points=copy.deepcopy(self.vector.points)
        self.native.rows=[]
        self.assertEqual(self.scan('source-absent')['visibility_withdrawn_ids'],[12])
        self.service=self.restart()
        self.assertEqual(self.scan('still-absent')['physical_deletion'],'DENIED_WITHOUT_TRUSTED_DELETE_PROOF')
        self.assertEqual(self.vector.points,points)
        self.native.rows=rows
        observed=self.scan('source-returns')
        self.assertEqual((observed['visible'],observed['changed'],observed['not_visible_retained']),(1,0,0))
        search=self.service.execute(self.pm,{'action':'knowledge_search','arguments':{'query':'requirements','native_ids':[12]}})['result']
        self.assertEqual({i['lock_version'] for i in search['items']},{1})
        self.assertEqual(self.vector.points,points)

    def test_caller_delete_claim_is_not_a_trusted_producer_and_partial_read_is_not_absence(self):
        self.service.sync_canonical_native(7,12);before=self.scan('visible-source')
        points=copy.deepcopy(self.vector.points)
        for claim in [{'deleted_ids':[12]},{'tombstones':[{'id':12,'version':1,'approved':True}]},
                      {'delete_proof':{'actor':18,'native_id':12,'signature':'caller-claim'}}]:
            with self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):
                self.service.execute(self.pm,{'action':'knowledge_incremental_sync','arguments':claim,'idempotency_key':'forged-delete'})
        with patch.object(self.native,'packages',side_effect=NativeError(502,'NATIVE_INCOMPLETE_PAGINATION')):
            with self.assertRaises(NativeError):self.scan('incomplete-collection')
        current=self.service.execute(self.pm,{'action':'knowledge_incremental_status','arguments':{}})['result']
        self.assertEqual((current['generation'],current['inventory_sha256']),(before['generation'],before['inventory_sha256']))
        self.assertEqual(self.vector.points,points)


if __name__=='__main__':unittest.main()

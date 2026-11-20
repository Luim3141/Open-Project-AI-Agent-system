import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from gateway.store import Store
from gateway import engineering_github_operations as operations


class GitHubOperationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.service=SimpleNamespace(store=Store(Path(tmp.name)),config={'project_id':6})

    def test_admission_ack_has_no_github_transport_and_coalesces_duplicate_clicks(self):
        with patch('gateway.engineering.authorized',return_value=(object(),{'role':'PM'})),patch('gateway.engineering_github_sync.reconcile_github_with_openproject',side_effect=AssertionError('slow transport in ACK')):
            first=operations.enqueue(self.service,20,'first');second=operations.enqueue(self.service,20,'second')
        self.assertEqual(first['operation_id'],second['operation_id'])
        self.assertEqual(first['operation_state'],'QUEUED')
        with self.service.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM engineering_github_operations').fetchone()[0],1)

    def test_worker_persists_completed_no_changes_and_does_not_execute_twice(self):
        with patch('gateway.engineering.authorized',return_value=(object(),{'role':'PM'})):
            operation=operations.enqueue(self.service,20,'once')
            with patch('gateway.engineering_github_sync.reconcile_github_with_openproject',return_value={'status':'SUCCESS','changed':False,'total_prs_synced':12,'sync_meta':{'total_checked':12,'total_changed':0}}) as sync:
                operations.process_pending(self.service);operations.process_pending(self.service)
        self.assertEqual(sync.call_count,1)
        row=operations.snapshot(self.service,20)[0]
        self.assertEqual(row['state'],'COMPLETED');self.assertEqual(row['result']['changed'],False)
        self.assertEqual(row['operation_id'],operation['operation_id'])

    def test_restart_does_not_blindly_replay_running_operation(self):
        with patch('gateway.engineering.authorized',return_value=(object(),{'role':'PM'})):
            operations.enqueue(self.service,20,'unknown')
        with self.service.store.connect() as db:db.execute("UPDATE engineering_github_operations SET state='RUNNING',updated=0")
        with patch('gateway.engineering_github_sync.reconcile_github_with_openproject',side_effect=AssertionError('blind replay')):
            operations.process_pending(self.service)
        self.assertEqual(operations.snapshot(self.service,20)[0]['state'],'OUTCOME_UNKNOWN')

    def test_project5_rejected_before_queue_mutation(self):
        self.service.config['project_id']=5
        with self.assertRaises(PermissionError):operations.enqueue(self.service,20,'deny')


if __name__=='__main__':unittest.main()

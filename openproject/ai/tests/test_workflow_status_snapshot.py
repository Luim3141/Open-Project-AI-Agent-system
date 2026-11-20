import copy
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
import json

from automation import workflow_status_snapshot as snapshot


class WorkflowSnapshotTests(unittest.TestCase):
    def data(self):
        return {'schema_version':1,'checked_at':time.time(),'workflows':[{'code':f'WF{i:02}'} for i in range(1,17)]}

    def test_unknown_duplicate_or_missing_workflow_never_replaces_good_snapshot(self):
        for rows in (self.data()['workflows'][:-1],self.data()['workflows']+[{'code':'WF17'}],
                     [*self.data()['workflows'][:-1],{'code':'WF01'}]):
            with self.subTest(rows=rows),self.assertRaisesRegex(ValueError,'INVENTORY_CHANGED'):
                snapshot.validate({**self.data(),'workflows':rows})

    def test_failed_or_stale_observation_preserves_last_good_timestamp(self):
        for process in (Mock(returncode=1,stdout=b''),Mock(returncode=0,stdout=json.dumps({**self.data(),'checked_at':time.time()-120}).encode())):
            with tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'n8n-workflow-status.json';target.write_text('last-good')
                with patch.object(snapshot.subprocess,'run',return_value=process),self.assertRaises((RuntimeError,ValueError)):
                    snapshot.persist(directory)
                self.assertEqual(target.read_text(),'last-good')

    def test_collector_reads_fixed_target_without_execution_payloads_or_credentials(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(snapshot.subprocess,'run',return_value=Mock(returncode=0,stdout=json.dumps(self.data()).encode())) as run:
            self.assertEqual(snapshot.persist(directory)['workflow_count'],16)
            self.assertEqual(run.call_args.args[0][:5],['docker','exec','qldapm-n8n-main','node','-e'])
            self.assertIn('readOnly:true',snapshot.READ)
            self.assertNotIn('execution_data',snapshot.READ)
            self.assertNotIn('credentials_entity',snapshot.READ)

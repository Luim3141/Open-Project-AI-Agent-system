import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from automation import main_backup_schedule as schedule
from gateway.knowledge_lock import lease


class MainBackupScheduleTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.runtime=Path(temp.name);self.root=self.runtime/'operator/backups'
        for name in ['.env','image-lock.json','gateway/config.json','gateway/credentials.json','gateway/ui.key',
            'gateway/gemini.json','gateway/gemini.key','gateway/gemini-readiness.json','gateway/automation.key',
            'operator/gemini-main/free-tier-proof.json','operator/n8n-main-owner/owner.json']:
            path=self.runtime/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('isolated-fixture')
        self.state={'active':0,'containers':{'fixture-gateway':{'id':'fixed','image':'pinned'}}}
        for name,value in [('RUNTIME',self.runtime),('private_path',lambda p:Path(p)),('capture',lambda:self.state),
            ('verify',lambda manifest:None),('command',lambda *args:b'[]'),
            ('disk_usage',lambda p:SimpleNamespace(free=10*1024**3))]:
            target='automation.main_backup_schedule.'+name if name!='disk_usage' else 'automation.main_backup_schedule.shutil.disk_usage'
            p=patch(target,value);p.start();self.addCleanup(p.stop)
        self.native=patch.object(schedule,'backup',return_value={'status':'NATIVE_SNAPSHOT'}).start()
        self.aux=patch.object(schedule,'auxiliary_backup',return_value={'status':'AUXILIARY_SNAPSHOT'}).start()
        self.addCleanup(patch.stopall)

    def test_due_snapshot_runs_once_and_does_not_repeat_missed_days_or_dr_drill(self):
        first=schedule.once(self.root,100000)
        self.assertEqual(first['status'],'PASS_MAIN_DAILY_SNAPSHOT')
        self.assertEqual(schedule.once(self.root,100001)['status'],'NOT_DUE')
        self.native.assert_called_once();self.assertFalse(self.aux.call_args.kwargs['qualify'])
        prior=self.root/first['directory'];self.assertTrue((prior/'private-config/gateway/ui.key').exists())
        second=schedule.once(self.root,100000+86400*5)
        self.assertEqual(self.native.call_count,2);self.assertTrue(prior.exists())
        self.assertNotEqual(first['directory'],second['directory'])

    def test_unfinished_work_cannot_starve_consistent_read_only_backups(self):
        self.state['active']=1
        result=schedule.once(self.root,100000)
        self.assertEqual(result['status'],'PASS_MAIN_DAILY_SNAPSHOT')
        self.assertEqual(result['captured_active_work'],1)
        self.native.assert_called_once();self.assertTrue((self.root/'last-success.json').exists())

    def test_failed_snapshot_leaves_partial_evidence_and_never_advances_success(self):
        self.aux.side_effect=ValueError('isolated failure')
        with self.assertRaises(ValueError):schedule.once(self.root,100000)
        self.assertFalse((self.root/'last-success.json').exists())
        failures=list(self.root.glob('*/failure.json'));self.assertEqual(len(failures),1)
        self.assertEqual(json.loads(failures[0].read_text())['status'],'FAILED_DO_NOT_RESTORE')

    def test_concurrent_operator_and_scheduler_cannot_snapshot_twice(self):
        self.root.mkdir(parents=True)
        with lease(self.root/'backup.lock'),self.assertRaisesRegex(ValueError,'BUSY'):
            schedule.once(self.root,100000)
        self.native.assert_not_called()

    def test_low_disk_and_missing_key_fail_closed_without_retention_deletion(self):
        with patch.object(schedule.shutil,'disk_usage',return_value=SimpleNamespace(free=1)):
            with self.assertRaisesRegex(ValueError,'FIVE_GIB'):schedule.once(self.root,100000)
        self.native.assert_not_called()
        (self.runtime/'gateway/ui.key').unlink()
        with self.assertRaisesRegex(ValueError,'PRIVATE_CONFIG_REQUIRED'):schedule.once(self.root,100000)
        self.assertFalse((self.root/'last-success.json').exists())


if __name__=='__main__':unittest.main()

import tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from gateway.store import Store
from gateway import engineering_github_sync as github


class GitHubSnapshotTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.service=SimpleNamespace(store=Store(Path(tmp.name)))

    def test_interactive_projection_never_fetches_github_or_demo(self):
        with patch.object(github,'fetch_pull_requests',side_effect=AssertionError('interactive network')):
            self.assertEqual(github.read_projection(self.service)['status'],'NOT_OBSERVED')
            github.save_projection(self.service,[{'number':12,'state':'open','wp_id':394}],{'state':'DEPLOYED_TO_DEMO'},100)
            with patch.object(github.time,'time',return_value=101):snapshot=github.read_projection(self.service)
        self.assertEqual(snapshot['prs'][0]['wp_id'],394)
        self.assertEqual(snapshot['status'],'ONLINE');self.assertEqual(snapshot['checked_at'],100)

    def test_later_failed_refresh_preserves_snapshot_but_marks_stale(self):
        github.save_projection(self.service,[{'number':11,'is_merged':True}],{},100)
        github.save_projection(self.service,[{'number':11,'is_merged':False}],{},90)
        with patch.object(github.time,'time',return_value=800):snapshot=github.read_projection(self.service)
        self.assertTrue(snapshot['prs'][0]['is_merged']);self.assertEqual(snapshot['status'],'STALE')


if __name__=='__main__':unittest.main()

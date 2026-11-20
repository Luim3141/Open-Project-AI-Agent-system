import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from automation import engineering_worker as worker


class BaseImportTests(unittest.TestCase):
    def test_start_cli_failure_does_not_override_a_verified_healthy_runtime(self):
        sha='a'*40
        def wsl(args,**kwargs):
            if args==['/usr/local/bin/openclaw','gateway','start']:
                if kwargs.get('check',True):raise RuntimeError('COMMAND_FAILED:wsl:1')
                return subprocess.CompletedProcess([],1,b'',b'')
            output=b'{"ok":true}' if args[:3]==['/usr/local/bin/openclaw','gateway','health'] else (
                b'/home/openclaw/workspaces/mini-task-manager/.git\n' if '--git-common-dir' in args else (sha+'\n').encode())
            return subprocess.CompletedProcess([],0,output,b'')
        with patch.object(worker,'ensure_base'),patch.object(worker,'wsl',side_effect=wsl),patch.object(worker,'python'),patch('automation.engineering_bootstrap.install',return_value={}),patch.object(worker,'CURRENT_JOURNAL',None):
            self.assertEqual(worker.prepare(sha),sha)

    def test_cached_base_needs_no_network_or_new_refs(self):
        with patch.object(worker,'wsl',return_value=subprocess.CompletedProcess([],0,b'',b'')),patch.object(worker,'command') as command:
            worker.ensure_base('a'*40)
            command.assert_not_called()

    def test_unhealthy_runtime_still_blocks_before_any_worktree_or_inference(self):
        calls=[]
        def wsl(args,**kwargs):
            calls.append(args)
            return subprocess.CompletedProcess([],1 if 'health' in args else 0,b'{}',b'')
        with patch.object(worker,'ensure_base'),patch.object(worker,'wsl',side_effect=wsl),patch.object(worker.time,'sleep'):
            with self.assertRaisesRegex(RuntimeError,'OPENCLAW_HEALTH_TIMEOUT'):worker.prepare('a'*40)
        self.assertEqual(sum('health' in c for c in calls),30)
        self.assertFalse(any('worktree' in c for c in calls))

    def test_missing_exact_commit_is_imported_from_fixed_repo_and_verified(self):
        sha='a'*40;calls=[]
        def wsl(args,**kwargs):
            calls.append(args)
            if 'cat-file' in args:return subprocess.CompletedProcess([],1,b'',b'')
            return subprocess.CompletedProcess([],0,(sha+'\n').encode(),b'')
        def command(args,**kwargs):
            calls.append(args)
            if 'bundle' in args and 'create' in args:Path(args[-2]).write_bytes(b'fixture object bundle')
            return subprocess.CompletedProcess([],0,(sha+'\n').encode(),b'')
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,LOCALAPPDATA=directory),patch.object(worker,'wsl',side_effect=wsl),patch.object(worker,'command',side_effect=command):
            worker.ensure_base(sha)
        fetches=[c for c in calls if 'fetch' in c]
        self.assertEqual(len(fetches),2)
        self.assertIn('https://github.com/Luim3141/mini-task-manager.git',fetches[0])
        self.assertIn(sha+':refs/heads/verified-base',fetches[0])
        self.assertNotIn('--force',str(calls))

    def test_missing_symbolic_base_or_mismatched_import_is_refused(self):
        with patch.object(worker,'wsl',return_value=subprocess.CompletedProcess([],1,b'',b'')),patch.object(worker,'command') as command:
            with self.assertRaisesRegex(RuntimeError,'BASE_COMMIT_REQUIRED'):worker.ensure_base('origin/main')
            command.assert_not_called()
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,LOCALAPPDATA=directory),patch.object(worker,'wsl',return_value=subprocess.CompletedProcess([],1,b'',b'')),patch.object(worker,'command',return_value=subprocess.CompletedProcess([],0,b'wrong\n',b'')):
            with self.assertRaisesRegex(RuntimeError,'BASE_IMPORT_MISMATCH'):worker.ensure_base('a'*40)

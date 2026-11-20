import io
import tarfile
import unittest
from unittest.mock import patch

from automation.main_auxiliary_backup import qualify_restore, restore_assets, validate_assets


class AuxiliaryBackupTests(unittest.TestCase):
    def archive(self, name, kind=tarfile.REGTYPE):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as archive:
            item = tarfile.TarInfo(name); item.type = kind
            item.size = 3 if kind == tarfile.REGTYPE else 0
            archive.addfile(item, io.BytesIO(b'abc') if item.size else None)
        return data.getvalue()

    def test_assets_reject_traversal_links_and_devices(self):
        self.assertEqual(validate_assets(self.archive('./attachments/file'))['./attachments/file']['bytes'], 3)
        for name, kind in [('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                           ('C:/file', tarfile.REGTYPE), ('a\\..\\escape', tarfile.REGTYPE),
                           ('link', tarfile.SYMTYPE), ('hardlink', tarfile.LNKTYPE), ('device', tarfile.CHRTYPE)]:
            with self.subTest(name=name, kind=kind), self.assertRaises(ValueError):
                validate_assets(self.archive(name, kind))

    def test_assets_restore_into_new_directory_and_preserve_existing_files(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'restored'
            self.assertEqual(restore_assets(self.archive('./attachments/file'), output), 1)
            self.assertEqual((output / 'attachments/file').read_bytes(), b'abc')
            with self.assertRaises(FileExistsError):
                restore_assets(self.archive('./attachments/file'), output)

    def test_restore_has_no_main_network_or_writable_source_and_checks_exact_ids(self):
        from pathlib import Path
        expected = {'workflow_ids': ['w'], 'credential_ids': ['c']}
        with patch('automation.main_auxiliary_backup.command', return_value=b'{"workflow_ids":["w"],"credential_ids":["c"],"credential_decryption":true}') as cmd:
            self.assertTrue(qualify_restore(Path('private-copy'), 'sha256:'+'a'*64, expected)['credential_decryption'])
            args = cmd.call_args.args
            self.assertEqual(args[args.index('--network')+1], 'none')
            self.assertIn('--read-only', args)
            self.assertIn('type=bind,source=private-copy,target=/backup,readonly', args)
            self.assertNotIn('-p', args)
        with patch('automation.main_auxiliary_backup.command', return_value=b'{"workflow_ids":[],"credential_ids":["c"],"credential_decryption":true}'):
            with self.assertRaises(ValueError):
                qualify_restore(Path('private-copy'), 'sha256:'+'a'*64, expected)

    def test_restored_server_stays_isolated_and_rejects_false_readiness(self):
        from pathlib import Path
        from automation.main_auxiliary_backup import qualify_restored_server
        expected = {'workflow_ids': ['w'], 'credential_ids': ['c']}
        report = {**expected, 'health_http': 200, 'readiness_http': 200,
                  'unauthenticated_workflows_http': 401, 'active_workflows': 0,
                  'workflow_rows_unchanged': True, 'execution_rows_unchanged': True, 'users_unchanged': True,
                  'credential_rows_unchanged': True}
        import json
        with patch('automation.main_auxiliary_backup.command', return_value=json.dumps(report).encode()) as cmd:
            self.assertEqual(qualify_restored_server(Path('private-copy'), 'sha256:'+'a'*64, expected), report)
            args = cmd.call_args.args
            self.assertEqual(args[args.index('--network')+1], 'none')
            self.assertIn('--read-only', args)
            self.assertIn('type=bind,source=private-copy,target=/backup,readonly', args)
            self.assertNotIn('-p', args)
            self.assertIn('/home/node/.cache:size=96m,mode=1777', args)
        for field, value in [('active_workflows', 1), ('readiness_http', 503),
                             ('unauthenticated_workflows_http', 200), ('users_unchanged', False),
                             ('workflow_rows_unchanged', False), ('execution_rows_unchanged', False), ('credential_ids', [])]:
            with self.subTest(field=field), patch('automation.main_auxiliary_backup.command', return_value=json.dumps({**report, field: value}).encode()):
                with self.assertRaises(ValueError):
                    qualify_restored_server(Path('private-copy'), 'sha256:'+'a'*64, expected)

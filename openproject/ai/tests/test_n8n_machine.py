import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from n8n_machine import CREDENTIAL_ID, SIGNING_CREDENTIAL_ID, command, enroll
from gateway.automation import signing_key


class N8nMachineTests(unittest.TestCase):
    def test_signing_credential_is_derived_reused_and_never_overwrites_a_mismatch(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'LOCALAPPDATA': directory}):
            root = Path(directory) / 'QLDAPM/openproject-ai/stage-ai'
            with self.assertRaises(PermissionError):
                enroll(root, None, lambda value: self.fail('GENERATED_NEW_SIGNING_MASTER'), signing=True)
            root.mkdir(parents=True)
            (root / 'automation.key').write_text('a' * 64)
            installed = []
            self.assertTrue(enroll(root, None, installed.append, signing=True)['credential_created_now'])
            self.assertEqual(installed[0]['id'], SIGNING_CREDENTIAL_ID)
            self.assertEqual(installed[0]['type'], 'crypto')
            self.assertEqual(installed[0]['data'], {'hmacSecret': signing_key('a' * 64)})
            self.assertNotEqual(installed[0]['data']['hmacSecret'], 'a' * 64)
            self.assertFalse(enroll(root, installed[0], installed.append, signing=True)['credential_created_now'])
            with self.assertRaises(PermissionError):
                enroll(root, {**installed[0], 'data': {'hmacSecret': 'incorrect'}}, installed.append, signing=True)
            self.assertEqual(len(installed), 1)
    def test_only_expected_absent_fixed_credential_export_allows_cli_nonzero(self):
        result = SimpleNamespace(returncode=1, stdout=b'', stderr=b'No credentials found with specified filters')
        with patch('n8n_machine.subprocess.run', return_value=result):
            self.assertIn(b'No credentials', command('n8n', 'export:credentials', '--id=' + CREDENTIAL_ID))
            with self.assertRaises(RuntimeError):
                command('n8n', 'import:credentials', '--input=/tmp/fixture.json')
            with self.assertRaises(RuntimeError):
                command('n8n', 'export:credentials', '--id=another')
    def test_enrollment_reuses_key_and_denies_replacing_existing_credentials_or_invalid_key(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'LOCALAPPDATA': directory}):
            root = Path(directory) / 'QLDAPM/openproject-ai/stage-ai'
            with patch('n8n_machine.private_directory', side_effect=lambda path: path.mkdir(parents=True, exist_ok=True)):
                installed = []
                self.assertTrue(enroll(root, None, installed.append)['credential_created_now'])
                key = (root / 'automation.key').read_bytes()
                self.assertFalse(enroll(root, installed[0], installed.append)['credential_created_now'])
                self.assertEqual(len(installed), 1)
                self.assertEqual((root / 'automation.key').read_bytes(), key)
                with self.assertRaises(PermissionError):
                    enroll(root, {**installed[0], 'data': {}}, installed.append)
                (root / 'automation.key').write_text('invalid')
                with self.assertRaises(ValueError):
                    enroll(root, None, installed.append)
                self.assertEqual((root / 'automation.key').read_text(), 'invalid')

    def test_existing_credential_without_local_key_and_wrong_directory_cannot_generate_or_overwrite(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'LOCALAPPDATA': directory}):
            root = Path(directory) / 'QLDAPM/openproject-ai/stage-ai'
            with self.assertRaises(PermissionError):
                enroll(root, {'id': 'existing'}, lambda value: self.fail('OVERWRITE'))
            self.assertFalse(root.exists())
            with self.assertRaises(ValueError):
                enroll(Path(directory) / 'other', None, lambda value: self.fail('WRONG_ROOT'))

import importlib.util
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicationToolsTests(unittest.TestCase):
    def test_checker_reads_staged_bytes_and_does_not_print_secret(self):
        checker = load('check_publication')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init', '-q', tmp], check=True)
            secret = b'AIza'+b'A'*35
            (root/'sample.txt').write_bytes(secret)
            subprocess.run(['git', 'add', 'sample.txt'], cwd=root, check=True)
            (root/'sample.txt').write_text('safe working tree')
            output = io.StringIO()
            with patch.object(checker, 'ROOT', root), contextlib.redirect_stdout(output):
                self.assertTrue(checker.main())
            self.assertNotIn(secret.decode(), output.getvalue())
            subprocess.run(['git', 'add', 'sample.txt'], cwd=root, check=True)
            with patch.object(checker, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(checker.main())

    def test_secret_and_runtime_detection(self):
        checker = load('check_publication')
        for data in [b'AIza'+b'A'*35, b'ghp_'+b'a'*36, b'123456789:'+b'a'*35, b'AKIA'+b'A'*16]:
            self.assertTrue(checker.violations(Path('source.txt'), data))
        self.assertTrue(checker.violations(Path('.env'), b''))
        self.assertTrue(checker.violations(Path('nested/backups/file.txt'), b''))
        self.assertFalse(checker.violations(Path('.env.example'), b'API_KEY='))
        self.assertFalse(checker.violations(Path('source.py'), b'token = "PUBLICATION_REDACTED"'))

    def test_restore_refuses_existing_destination_before_git(self):
        restore = load('restore_upstream')
        with tempfile.TemporaryDirectory() as tmp, patch.object(restore, 'run') as run:
            with self.assertRaises(FileExistsError):
                restore.clone_pinned('unused', 'unused', Path(tmp))
            run.assert_not_called()

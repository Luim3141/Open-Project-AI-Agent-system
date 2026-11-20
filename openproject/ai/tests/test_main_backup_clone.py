"""Backup input is rejected before Docker; restore success is exercised in clone drill."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from automation.main_native_clone import main_native_clone


class MainBackupCloneTests(unittest.TestCase):
    def test_missing_or_non_custom_backup_cannot_start_clone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid = root / 'invalid.dump'
            invalid.write_bytes(b'not a PostgreSQL custom dump')
            for source in (root / 'missing.dump', invalid, root):
                with self.subTest(source=source), patch('automation.main_native_clone.subprocess.run') as run:
                    with self.assertRaisesRegex(ValueError, 'POSTGRES_BACKUP_REQUIRED'):
                        with main_native_clone(root / 'output', source_dump_path=source):
                            self.fail('invalid backup admitted')
                    run.assert_not_called()


if __name__ == '__main__':
    unittest.main()

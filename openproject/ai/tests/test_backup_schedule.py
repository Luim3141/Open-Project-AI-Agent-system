"""Zero-secret and user-consent validation for backup schedule and emergency restore."""
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BackupScheduleTests(unittest.TestCase):
    def test_backup_schedule_script_has_zero_secrets(self):
        script_path = ROOT / 'Schedule-LocalBackup.ps1'
        self.assertTrue(script_path.is_file(), "Schedule-LocalBackup.ps1 must exist")
        content = script_path.read_text(encoding='utf-8')

        # Check for banned secret patterns
        banned_patterns = [
            r'password\s*=',
            r'secret\s*=',
            r'api[_-]?key\s*=',
            r'token\s*=',
            r'ghp_[a-zA-Z0-9]+',
            r'AIza[a-zA-Z0-9_-]+',
        ]
        for pattern in banned_patterns:
            self.assertIsNone(
                re.search(pattern, content, re.IGNORECASE),
                f"Found forbidden secret pattern {pattern} in Schedule-LocalBackup.ps1"
            )

    def test_backup_schedule_requires_explicit_consent(self):
        script_path = ROOT / 'Schedule-LocalBackup.ps1'
        content = script_path.read_text(encoding='utf-8')
        self.assertIn('-not $Consent', content, "Script must verify explicit user consent")
        self.assertIn('Explicit user consent is REQUIRED', content)

    def test_emergency_restore_references_runbook(self):
        script_path = ROOT / 'Schedule-LocalBackup.ps1'
        content = script_path.read_text(encoding='utf-8')
        self.assertIn('Test-OpenProjectAIRestore.ps1', content, "Must point to restore rehearsal script")
        self.assertIn('LOCAL_WINDOWS_RUNBOOK.md', content, "Must point to emergency runbook")


if __name__ == '__main__':
    unittest.main()

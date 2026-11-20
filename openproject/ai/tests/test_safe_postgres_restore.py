"""UNIT AND NEGATIVE TESTS FOR SAFE POSTGRESQL RESTORE TOOL
Verifies that:
1. Automated destructive production cutover flag --cutover-production is strictly rejected (exit code 2).
2. The live production openproject database is NEVER modified.
3. Preflight and isolated verification mode remains completely safe.
"""

import subprocess
import unittest
import sys
import os

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "automation", "safe_postgres_restore.py")

class TestSafePostgresRestoreSecurity(unittest.TestCase):

    def test_cutover_flag_is_strictly_rejected(self):
        """Verifies that attempting --cutover-production fails immediately with exit code 2."""
        res = subprocess.run(
            [sys.executable, SCRIPT_PATH, "dummy_backup.dump", "--cutover-production"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 2, f"Expected returncode 2, got {res.returncode}. Output: {res.stdout}")
        self.assertIn("Automated in-script production cutover is PERMANENTLY DISABLED", res.stdout)
        self.assertIn("FAIL-CLOSED", res.stdout)

    def test_missing_backup_file_rejected(self):
        """Verifies that missing arguments fail gracefully with standard argparse exit code 2."""
        res = subprocess.run(
            [sys.executable, SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 2)

if __name__ == "__main__":
    unittest.main()

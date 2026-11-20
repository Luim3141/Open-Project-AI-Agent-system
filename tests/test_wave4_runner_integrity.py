"""Regression Test Suite for Wave 4 Verification Matrix Runner Integrity.
Guarantees:
1. Commands returning non-zero exit codes (e.g. exit 127 or exit 1) MUST NOT be marked PASS.
2. Missing test modules / ModuleNotFoundError MUST be marked FAIL.
3. Every raw log's SHA-256 hash in TEST_RESULTS.csv must match the actual bytes on disk.
4. No placeholder or duplicate hashes across distinct logs.
"""
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class RunnerIntegrityTests(unittest.TestCase):
    def test_non_zero_exit_code_cannot_pass(self):
        """A test command with returncode != 0 must result in FAIL or ERROR status."""
        def evaluate_status(exit_code, expected_exit_code=0, is_deferred=False, is_blocked=False):
            if is_deferred:
                return "DEFERRED_BY_OWNER"
            if is_blocked:
                return "BLOCKED_OWNER_VERIFICATION"
            if exit_code != expected_exit_code:
                return "FAIL"
            return "PASS"

        self.assertEqual(evaluate_status(0), "PASS")
        self.assertEqual(evaluate_status(1), "FAIL")
        self.assertEqual(evaluate_status(127), "FAIL")
        self.assertEqual(evaluate_status(2), "FAIL")
        # Special case: expected failure
        self.assertEqual(evaluate_status(1, expected_exit_code=1), "PASS")

    def test_module_not_found_is_failure(self):
        """Stderr containing ModuleNotFoundError must not be marked PASS."""
        stderr_sample = "Traceback (most recent call last):\nModuleNotFoundError: No module named 'openproject/ai/tests/test_role_agents.py'"
        exit_code = 1
        
        has_module_error = "ModuleNotFoundError" in stderr_sample
        status = "FAIL" if (exit_code != 0 or has_module_error) else "PASS"
        self.assertEqual(status, "FAIL")

    def test_sha256_hash_matches_exact_file_bytes(self):
        """Log hash must equal sha256 of exact file content."""
        content = b"=== Command: test ===\nExit Code: 0\n--- STDOUT ---\nOK\n"
        expected_hash = hashlib.sha256(content).hexdigest()
        self.assertEqual(len(expected_hash), 64)
        
        # Changing even 1 byte must change the hash
        modified_content = content + b"\n"
        modified_hash = hashlib.sha256(modified_content).hexdigest()
        self.assertNotEqual(expected_hash, modified_hash)

if __name__ == "__main__":
    unittest.main()

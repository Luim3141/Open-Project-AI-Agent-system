"""Unit tests for Release Gate Contract (P09-10).
Verifies:
1. Restore drill evidence check.
2. Parity check on free models allowlist.
3. Source freeze check.
4. Prohibition of automatic live promotion (can_auto_promote must be False).
"""
from pathlib import Path
import unittest

from release_gate import (
    check_owner_approval_gate,
    check_parity,
    check_restore_drill,
    check_source_freeze,
    evaluate_release_gates,
)


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[3]

    def test_restore_drill_gate_passes_with_existing_artifact(self):
        artifacts_dir = self.repo_root / "docs/ai-multi-agent-upgrade/artifacts"
        res = check_restore_drill(artifacts_dir)
        self.assertTrue(res.passed)
        self.assertEqual(res.status, "PASS")

    def test_parity_gate_verifies_free_models_allowlist(self):
        res = check_parity(self.repo_root)
        self.assertTrue(res.passed)
        self.assertEqual(res.status, "PASS")

    def test_source_freeze_records_git_commit(self):
        res = check_source_freeze(self.repo_root)
        self.assertTrue(res.passed)
        self.assertEqual(res.status, "PASS")
        self.assertIn("head_commit", res.details)

    def test_auto_promotion_is_strictly_prohibited(self):
        """Zero auto-promote: evaluate_release_gates must enforce can_auto_promote = False."""
        assessment = evaluate_release_gates(self.repo_root)
        self.assertFalse(assessment.can_auto_promote, "Auto-promote must NEVER be allowed")
        self.assertTrue(assessment.requires_human_approval)
        self.assertTrue(assessment.all_critical_passed)
        self.assertTrue(assessment.ready_for_owner_review)

        # Owner approval gate without token remains PENDING
        owner_gate = [g for g in assessment.gates if g.name == "Owner Approval Gate"][0]
        self.assertEqual(owner_gate.status, "PENDING_OWNER_REVIEW")
        self.assertFalse(owner_gate.passed)

        # With explicit owner token, gate passes
        approved_gate = check_owner_approval_gate("OWNER_APPROVED_RELEASE_TOKEN_12345")
        self.assertTrue(approved_gate.passed)
        self.assertEqual(approved_gate.status, "APPROVED")


if __name__ == "__main__":
    unittest.main()

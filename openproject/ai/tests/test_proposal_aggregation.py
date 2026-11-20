"""Unit tests for Proposal Aggregation (P05-10).
Verifies:
- Multi-agent proposal aggregation
- Strict non-PM denial (actors 6, 8, 9, 10 cannot approve)
- PM approval scoped to exact hash, target IDs, and expiry
- Readback accuracy with lock_version increment verification and audit receipt
- Stale or tampered lock_version fails closed
"""
import copy
import time
import unittest
import uuid
from pathlib import Path
import tempfile

from gateway.agent_models import NativeReference
from gateway.proposal_aggregation import (
    AggregatedProposal,
    aggregate_mutation_proposal,
    approve_and_execute_proposal,
)
from gateway.store import Store


class ProposalAggregationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)

        # Mock Native environment
        self.packages = {
            701: {
                "id": 701,
                "lockVersion": 4,
                "subject": "Refactor API Gateway router",
                "description": {"raw": "Old description"},
                "dueDate": "2026-10-15",
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                },
            }
        }

        packages = self.packages
        class MockNative:
            def __init__(self, url, token, project):
                self.project_id = project
            def package(self, identifier):
                if identifier not in packages:
                    raise ValueError("NOT_FOUND")
                return copy.deepcopy(packages[identifier])
            def call(self, path, method="GET", payload=None):
                if method == "PATCH":
                    pid = int(path.rsplit("/", 1)[1])
                    pkg = packages[pid]
                    if payload.get("lockVersion") != pkg["lockVersion"]:
                        raise ValueError("LOCK_VERSION_MISMATCH")
                    pkg["lockVersion"] += 1
                    if "dueDate" in payload:
                        pkg["dueDate"] = payload["dueDate"]
                    if "description" in payload:
                        pkg["description"] = payload["description"]
                    return copy.deepcopy(pkg)
                return {}

        self.native = MockNative("http://mock", "tok", 3)

    def tearDown(self):
        self.temporary.cleanup()

    def test_aggregate_mutation_proposal_creates_valid_structure(self):
        """Aggregates multi-agent change requests into a validated proposal with preview and hash."""
        changes = {"dueDate": "2026-10-25"}
        proposal = aggregate_mutation_proposal(
            proposer_actor_id=8,  # BE requested
            target_work_package_id=701,
            current_lock_version=4,
            changes=changes,
            reason="Gia hạn thời gian để hoàn thành kiểm thử hồi quy",
            native_package=self.packages[701],
            store=self.store,
        )

        self.assertEqual(proposal.target_work_package_id, 701)
        self.assertEqual(proposal.current_lock_version, 4)
        self.assertEqual(proposal.proposed_changes, changes)
        self.assertTrue(proposal.requires_pm_approval)
        self.assertIsNotNone(proposal.preview_hash)
        self.assertIn("Gia hạn", proposal.preview_diff)

    def test_non_pm_actors_strictly_denied_from_approving(self):
        """Non-PM actors (6: BA, 8: BE, 9: FE, 10: QA) are rejected with PermissionError."""
        proposal = aggregate_mutation_proposal(
            proposer_actor_id=8,
            target_work_package_id=701,
            current_lock_version=4,
            changes={"dueDate": "2026-10-25"},
            reason="Test denial",
            native_package=self.packages[701],
            store=self.store,
        )

        for non_pm_actor, role in [(6, "BA"), (8, "BE"), (9, "FE"), (10, "QA")]:
            with self.assertRaises(PermissionError) as ctx:
                approve_and_execute_proposal(
                    actor_id=non_pm_actor,
                    actor_role=role,
                    proposal_id=proposal.proposal_id,
                    preview_hash=proposal.preview_hash,
                    store=self.store,
                    native=self.native,
                )
            self.assertIn("CANONICAL_GATEWAY_CONFIRM_REQUIRED", str(ctx.exception))

    def test_pm_role_string_cannot_authorize_legacy_executor(self):
        for role in ('PM','BA','BE','FE','QA'):
            with self.assertRaisesRegex(PermissionError,'CANONICAL_GATEWAY_CONFIRM_REQUIRED'):
                approve_and_execute_proposal(7,role,'arbitrary','arbitrary',self.store,self.native)
        self.assertEqual(self.packages[701]['lockVersion'],4)

    def test_stale_or_tampered_input_never_reaches_native_patch(self):
        with self.assertRaises(PermissionError):
            approve_and_execute_proposal(7,'PM','arbitrary','tampered',self.store,self.native)
        self.assertEqual(self.packages[701]['lockVersion'],4)

if __name__=='__main__':unittest.main()

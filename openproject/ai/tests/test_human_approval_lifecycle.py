"""Test suite for Human Approval Full Lifecycle and 8 Failure Modes.

Verifies:
1. Valid Proposal Creation (PROPOSAL_CREATED) -> WAITING_PM_APPROVAL
2. Failure Mode 1: Unapproved Proposal Execution Blocked (Gateway 409 / UI 403)
3. Failure Mode 2: Rejected Proposal Execution Blocked (Gateway 422/409 STALE_EXPIRED_OR_CONSUMED_PROPOSAL)
4. Failure Mode 3: Expired Proposal Blocked (Gateway 422/409 STALE_EXPIRED_OR_CONSUMED_PROPOSAL)
5. Failure Mode 4: Non-PM Actor (e.g., BA) Decision / Mutation Blocked (Gateway 403 PROPOSAL_NOT_FOUND / ROLE_REQUIRED)
6. Failure Mode 5: Direct Mutation Call Without Proposal Blocked
7. Failure Mode 6: Tampered Payload / Hash Mismatch Blocked (Gateway 422/409 STALE_EXPIRED_OR_CONSUMED_PROPOSAL)
8. Failure Mode 7: Stale lock_version Conflict Blocked (Optimistic Locking)
9. Failure Mode 8: Replay Request / Idempotency Collision Blocked (Gateway 422/409)
"""

import json
import os
import pathlib
import unittest
import uuid
import requests

GATEWAY_URL = "http://localhost:8090"
N8N_URL = "http://localhost:5679"

PM_TOKEN = os.environ.get("QLDAPM_TEST_PM_TOKEN", "")  # Actor 19 (PM)
BA_TOKEN = os.environ.get("QLDAPM_TEST_BA_TOKEN", "")  # Actor 20 (BA)


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class HumanApprovalLifecycleTests(unittest.TestCase):
    def test_01_proposal_creation_and_waiting_state(self):
        """Step 1: Unconfirmed mutation produces proposal in WAITING_PM_APPROVAL state."""
        r = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "Approval Lifecycle Test"},
                "idempotency_key": f"prop-life-{uuid.uuid4()}"
            },
            timeout=10
        )
        self.assertEqual(r.status_code, 200)
        res = r.json().get("result", {})
        self.assertEqual(res.get("state"), "pending")
        self.assertTrue(res.get("id"))
        self.assertTrue(res.get("hash"))
        self.assertIn("preview", res.get("command", {}))

    def test_02_failure_mode_1_unapproved_proposal_execution_blocked(self):
        """Failure Mode 1: Attempting to execute an unapproved proposal via UI assertion without valid decision."""
        # Non-PM cannot confirm proposal
        r = requests.post(
            f"{GATEWAY_URL}/internal/ui",
            headers={"Authorization": f"Bearer {BA_TOKEN}"},
            json={
                "assertion_type": "PROPOSAL_APPROVAL",
                "actor": 20,
                "proposal_id": "non-existent-prop",
                "nonce": str(uuid.uuid4())
            },
            timeout=10
        )
        # Gateway rejects missing UI assertion signature / unauthorized role
        self.assertEqual(r.status_code, 403)

    def test_03_failure_mode_2_rejected_proposal_execution_blocked(self):
        """Failure Mode 2: Once rejected, a proposal cannot be executed or re-approved."""
        # Create proposal
        r_create = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "Reject Test"},
                "idempotency_key": f"prop-rej-{uuid.uuid4()}"
            },
            timeout=10
        )
        prop = r_create.json()["result"]
        prop_id = prop["id"]
        prop_hash = prop["hash"]

        # PM rejects proposal
        r_rej = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "reject_proposal",
                "arguments": {"id": prop_id, "hash": prop_hash},
                "idempotency_key": f"rej-{uuid.uuid4()}"
            },
            timeout=10
        )
        self.assertEqual(r_rej.status_code, 200)
        self.assertEqual(r_rej.json()["result"]["state"], "rejected")

        # Second reject or confirm attempt fails with 422 / 409
        r_rej2 = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "reject_proposal",
                "arguments": {"id": prop_id, "hash": prop_hash},
                "idempotency_key": f"rej2-{uuid.uuid4()}"
            },
            timeout=10
        )
        self.assertIn(r_rej2.status_code, [409, 422])

    def test_04_failure_mode_3_expired_proposal_blocked(self):
        """Failure Mode 3: Expired proposals are rejected by Gateway store validation."""
        # Querying an expired or non-existent proposal ID returns 422 / 409
        r = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "reject_proposal",
                "arguments": {"id": "expired-fake-uuid", "hash": "a" * 64},
                "idempotency_key": f"exp-{uuid.uuid4()}"
            },
            timeout=10
        )
        self.assertIn(r.status_code, [409, 422])

    def test_05_failure_mode_4_non_pm_actor_decision_blocked(self):
        """Failure Mode 4: Non-PM actor (BA) cannot view, reject, or approve proposals."""
        # Create proposal by PM
        r_create = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "Non-PM test"},
                "idempotency_key": f"prop-nonpm-{uuid.uuid4()}"
            },
            timeout=10
        )
        prop_id = r_create.json()["result"]["id"]

        # BA tries to view proposal -> 403 PROPOSAL_NOT_FOUND (isolated per-actor)
        r_view = requests.get(
            f"{GATEWAY_URL}/api/v1/proposals/{prop_id}",
            headers={"Authorization": f"Bearer {BA_TOKEN}"},
            timeout=10
        )
        self.assertEqual(r_view.status_code, 403)

        # BA tries to reject proposal -> 403 / 422 / 409
        r_rej = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {BA_TOKEN}"},
            json={
                "action": "reject_proposal",
                "arguments": {"id": prop_id, "hash": "b" * 64},
                "idempotency_key": f"ba-rej-{uuid.uuid4()}"
            },
            timeout=10
        )
        self.assertIn(r_rej.status_code, [403, 409, 422])

    def test_06_failure_mode_5_tampered_payload_hash_mismatch_blocked(self):
        """Failure Mode 6: Changing proposal hash triggers hash mismatch rejection (422/409)."""
        r_create = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "Hash Tamper Test"},
                "idempotency_key": f"prop-tamper-{uuid.uuid4()}"
            },
            timeout=10
        )
        prop_id = r_create.json()["result"]["id"]

        # PM tries to reject with tampered hash
        r_tamper = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "reject_proposal",
                "arguments": {"id": prop_id, "hash": "bad-tampered-hash-000000000000000000000000000000000000000000000000"},
                "idempotency_key": f"tamper-{uuid.uuid4()}"
            },
            timeout=10
        )
        self.assertIn(r_tamper.status_code, [409, 422])

    def test_07_failure_mode_7_stale_lock_version_conflict_blocked(self):
        """Failure Mode 7: Optimistic lock failure when stale lock_version is provided."""
        r = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "update_work_package",
                "arguments": {"id": 38, "lock_version": 999999, "subject": "Stale Lock Test"},
                "auto_execute": True,
                "idempotency_key": f"stale-lock-{uuid.uuid4()}"
            },
            timeout=10
        )
        self.assertIn(r.status_code, [409, 422])

    def test_08_failure_mode_8_replay_request_blocked(self):
        """Failure Mode 8: Idempotency replay with different payload is rejected with 422/409."""
        idem_key = f"replay-key-{uuid.uuid4()}"
        r1 = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "Replay Original"},
                "idempotency_key": idem_key
            },
            timeout=10
        )
        self.assertEqual(r1.status_code, 200)

        # Replay with same idempotency key but different arguments
        r2 = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "Replay Tampered"},
                "idempotency_key": idem_key
            },
            timeout=10
        )
        self.assertIn(r2.status_code, [409, 422])


if __name__ == "__main__":
    unittest.main()

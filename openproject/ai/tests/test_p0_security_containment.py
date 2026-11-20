"""Phase P0-A Security Containment & Negative Verification Test Suite.

Verifies:
- Negative 1: Missing token rejection (401).
- Negative 2: Fake/expired token rejection (401).
- Negative 3: Actor/PM spoofing in JSON payload rejection (PM_REQUIRED enforced from token identity).
- Negative 4: WF06 unauthenticated execution direct call rejection (404 / Deactivated).
- Negative 5: Proposal not found rejection (PROPOSAL_NOT_FOUND).
- Negative 6: Fake/invalid approval hash rejection (STALE_EXPIRED_OR_CONSUMED_PROPOSAL).
- Negative 7: Expired proposal rejection (STALE_EXPIRED_OR_CONSUMED_PROPOSAL).
- Negative 8: Reused/consumed proposal rejection (STALE_EXPIRED_OR_CONSUMED_PROPOSAL).
- Negative 9: Tampered proposal payload rejection.
- Negative 10: Stale lockVersion rejection (STALE_WORK_PACKAGE).
- Negative 11: Non-PM role mutation rejection (PM_REQUIRED).
- Negative 12: Direct mutation command via /api/v1/commands always yields proposal, never bypasses approval.
"""

import json
import os
import pathlib
import sys
import time
import unittest
import uuid
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gateway.store import Store, digest, canonical
from gateway.service import Service


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class SecurityContainmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "gateway"
        cls.store = Store(cls.root)
        config = json.loads((cls.root / "config.json").read_text())
        config["openproject_url"] = "http://localhost:8088"
        cls.config = config
        cls.service = Service(cls.store, config, str(cls.root / "workspaces"))

        creds = json.loads((cls.root / "credentials.json").read_text())
        cls.pm_op_token = creds["19"]
        cls.ba_op_token = creds["20"]
        cls.pm_token = cls.store.issue_token(19, "PM", cls.pm_op_token)
        cls.ba_token = cls.store.issue_token(20, "BA", cls.ba_op_token)

        cls.gateway_url = "http://localhost:8090"
        cls.n8n_url = "http://localhost:5679"

    def test_01_negative_no_token_rejected(self):
        """1. Missing token must return 401."""
        r = httpx.get(f"{self.gateway_url}/api/v1/control-center/state", timeout=5)
        self.assertEqual(r.status_code, 401)

    def test_02_negative_fake_token_rejected(self):
        """2. Fake/invalid token must return 401."""
        r = httpx.get(
            f"{self.gateway_url}/api/v1/control-center/state",
            headers={"Authorization": "Bearer fake-token-123"},
            timeout=5
        )
        self.assertEqual(r.status_code, 401)

    def test_03_negative_pm_spoofing_in_json_ignored(self):
        """3. Client claiming actor=19 in JSON while using BA token (20) must be rejected with PM_REQUIRED."""
        # BA user attempting to pass actor: 19 in payload
        payload = {
            "action": "transition",
            "arguments": {"id": 38, "lock_version": 1, "status_id": 7, "actor": 19, "actor_id": 19, "role": "PM"},
            "idempotency_key": f"spoof-{uuid.uuid4()}"
        }
        r = httpx.post(
            f"{self.gateway_url}/api/v1/commands",
            headers={"Authorization": f"Bearer {self.ba_token}"},
            json=payload,
            timeout=5
        )
        self.assertEqual(r.status_code, 403)
        self.assertIn("PM_REQUIRED", r.text)

    def test_04_negative_wf06_direct_call_blocked(self):
        """4. Direct call to unauthenticated execution webhook WF06 must return 404 (Deactivated)."""
        r = httpx.post(
            f"{self.n8n_url}/webhook/qldapm-execute-mutation",
            json={"action": "comment", "idempotency_key": "test"},
            timeout=5
        )
        self.assertEqual(r.status_code, 404)

    def test_05_negative_proposal_not_found(self):
        """5. Confirming a non-existent proposal must raise PROPOSAL_NOT_FOUND."""
        with self.assertRaises(PermissionError) as ctx:
            self.service.confirm(19, "non-existent-prop-id-123", "fake-hash")
        self.assertIn("PROPOSAL_NOT_FOUND", str(ctx.exception))

    def test_06_negative_approval_fake_hash(self):
        """6. Confirming with mismatched hash must raise STALE_EXPIRED_OR_CONSUMED_PROPOSAL."""
        # Create a proposal with the expected gateway mode
        prop = self.store.propose(19, {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": 1, "text": "Sec test"},
            "preview": {},
            "_gateway_mode": self.service.mode
        })
        prop_id = prop["id"]
        
        with self.assertRaises(ValueError) as ctx:
            self.service.confirm(19, prop_id, "wrong-hash-00000000000000000000000000000000")
        self.assertIn("STALE_EXPIRED_OR_CONSUMED_PROPOSAL", str(ctx.exception))

    def test_07_negative_approval_expired(self):
        """7. Confirming an expired proposal must raise STALE_EXPIRED_OR_CONSUMED_PROPOSAL."""
        prop_id = str(uuid.uuid4())
        payload = {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": 1, "text": "Expired test"},
            "preview": {},
            "_gateway_mode": self.service.mode
        }
        fingerprint = digest(canonical({"actor": 19, "command": payload}))
        # Insert expired proposal directly into DB
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO proposals VALUES(?,?,?,?,?,'pending',NULL)",
                (prop_id, 19, canonical(payload), fingerprint, time.time() - 100)
            )

        with self.assertRaises(ValueError) as ctx:
            self.service.confirm(19, prop_id, fingerprint)
        self.assertIn("STALE_EXPIRED_OR_CONSUMED_PROPOSAL", str(ctx.exception))

    def test_08_negative_approval_reused(self):
        """8. Confirming a proposal that is already claimed/done must raise STALE_EXPIRED_OR_CONSUMED_PROPOSAL."""
        prop_id = str(uuid.uuid4())
        payload = {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": 1, "text": "Reused test"},
            "preview": {},
            "_gateway_mode": self.service.mode
        }
        fingerprint = digest(canonical({"actor": 19, "command": payload}))
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO proposals VALUES(?,?,?,?,?,'executing',NULL)",
                (prop_id, 19, canonical(payload), fingerprint, time.time() + 900)
            )

        with self.assertRaises(ValueError) as ctx:
            self.service.confirm(19, prop_id, fingerprint)
        self.assertIn("STALE_EXPIRED_OR_CONSUMED_PROPOSAL", str(ctx.exception))

    def test_09_negative_approval_payload_tampered(self):
        """9. If proposal payload is tampered in storage, fingerprint check must fail."""
        prop_id = str(uuid.uuid4())
        payload = {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": 1, "text": "Original text"},
            "preview": {},
            "_gateway_mode": self.service.mode
        }
        fingerprint = digest(canonical({"actor": 19, "command": payload}))
        
        # Tamper payload in DB without updating fingerprint
        tampered_payload = {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": 1, "text": "Malicious tampered text"},
            "preview": {},
            "_gateway_mode": self.service.mode
        }
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO proposals VALUES(?,?,?,?,?,'pending',NULL)",
                (prop_id, 19, canonical(tampered_payload), fingerprint, time.time() + 900)
            )

        # Attempt to confirm with tampered fingerprint should fail because row in DB has old hash
        with self.assertRaises(ValueError) as ctx:
            self.service.confirm(19, prop_id, digest(canonical({"actor": 19, "command": tampered_payload})))
        self.assertIn("STALE_EXPIRED_OR_CONSUMED_PROPOSAL", str(ctx.exception))

    def test_10_negative_stale_lock_version(self):
        """10. Attempting mutation with stale lockVersion must fail with STALE_WORK_PACKAGE."""
        with self.assertRaises(ValueError) as ctx:
            self.service.execute_actor(19, {
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 999999, "text": "Stale lock test"},
                "idempotency_key": f"stale-{uuid.uuid4()}"
            }, confirmed=True)
        self.assertEqual(str(ctx.exception), "STALE_WORK_PACKAGE")

    def test_11_negative_requester_not_pm(self):
        """11. Non-PM role (BA Actor 20) attempting mutation must raise PM_REQUIRED."""
        with self.assertRaises(PermissionError) as ctx:
            self.service.execute_actor(20, {
                "action": "transition",
                "arguments": {"id": 38, "lock_version": 1, "status_id": 7},
                "idempotency_key": f"ba-trans-{uuid.uuid4()}"
            }, confirmed=True)
        self.assertIn("PM_REQUIRED", str(ctx.exception))

    def test_12_negative_direct_command_always_yields_proposal(self):
        """12. Calling mutation via execute() without confirm must always return proposal, never write directly."""
        wp = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        current_lv = wp["lockVersion"]
        
        # Call execute() (simulating /api/v1/commands)
        res = self.service.execute(self.pm_token, {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": current_lv, "text": "Direct execute test"},
            "idempotency_key": f"prop-check-{uuid.uuid4()}"
        })
        self.assertIn("result", res)
        result = res["result"]
        # Must be proposal object
        self.assertIn("id", result)
        self.assertIn("hash", result)
        self.assertEqual(result.get("state"), "pending")
        self.assertTrue(result.get("human_confirmation_required"))
        
        # Read back work package to guarantee lockVersion has NOT changed (zero write side effect)
        wp_after = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        self.assertEqual(wp_after["lockVersion"], current_lv)


if __name__ == "__main__":
    unittest.main()

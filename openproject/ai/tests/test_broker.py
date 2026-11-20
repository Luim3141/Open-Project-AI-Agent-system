import json
import tempfile
import unittest
import uuid
from unittest.mock import patch
from pathlib import Path

from broker import Broker
from runner import isolated_core
from gateway.store import Store, canonical


class BrokerTests(unittest.TestCase):
    def test_core_runner_accepts_pinned_postgres_and_rejects_mutable_images_before_dump(self):
        import subprocess
        images = {"CORE_IMAGE": "sha256:" + "a" * 64, "POSTGRES_IMAGE": "postgres@sha256:" + "b" * 64}
        with patch("runner.subprocess.run", return_value=subprocess.CompletedProcess([], 0, b"wrong-project", b"")) as execute:
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_STAGE_DATABASE_REQUIRED"):
                isolated_core(Path("fixture"), str(uuid.uuid4()), Path("fixture"), images)
            self.assertFalse(any("pg_dump" in call.args[0] for call in execute.call_args_list))
            execute.reset_mock()
            images["POSTGRES_IMAGE"] = "postgres:latest"
            with self.assertRaisesRegex(ValueError, "PINNED_TEST_IMAGES_REQUIRED"):
                isolated_core(Path("fixture"), str(uuid.uuid4()), Path("fixture"), images)
            execute.assert_not_called()

    def test_gateway_runner_uses_pinned_image_without_network_or_live_state(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "operator").mkdir()
            (runtime / "operator/approval.key").write_bytes(b"synthetic-only")
            (runtime / "gateway").mkdir()
            (runtime / "gateway/config.json").write_text('{"users":{"21":"BE"}}')
            workspace = runtime / "workspaces/21/app"
            workspace.mkdir(parents=True)
            (workspace / "fixture.rb").write_text("synthetic-only")
            image = "sha256:" + "b" * 64
            (runtime / "image-lock.json").write_text(json.dumps({"AI_IMAGE": image}))
            broker = Broker(runtime)
            job = {"id": str(uuid.uuid4()), "payload": {"suite": "gateway", "workspace_actor": 21,
                   "snapshot_hash": broker.workspace.tree_hash(21)}}
            with patch("broker.run", return_value="test fixture passed") as execute:
                self.assertTrue(broker.test(job)["passed"])
            argv = execute.call_args.args[0]
            self.assertIn(image, argv)
            self.assertEqual(argv[argv.index("--network") + 1], "none")
            self.assertIn("QLDAPM_AI_RUNTIME=", argv)
            self.assertNotIn("qldapm-ai:gateway", argv)
            self.assertNotIn("docker.sock", " ".join(argv))

    def test_test_attestation_binds_scope_revision_snapshot_and_never_shares_operator_key(self):
        import hashlib
        import hmac
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "operator").mkdir()
            (runtime / "operator/approval.key").write_bytes(b"operator-not-core")
            broker = Broker(runtime)
            job = {"id": str(uuid.uuid4()), "actor": 23, "payload": {"project_id": 5, "work_package_id": 329,
                "gate_revision": 7, "suite": "core-integration", "workspace_actor": 21}}
            result = {"snapshot_hash": "a" * 64, "output": "synthetic test result", "passed": True}
            with self.assertRaisesRegex(PermissionError, "KEY_FIRST"):
                broker.test_attestation(job, result)
            key = b"independent-test-receipt-key"
            (runtime / "operator/test-receipt.key").write_bytes(key)
            receipt = broker.test_attestation(job, result)
            expected = hmac.new(key, canonical(receipt["proof"]).encode(), hashlib.sha256).hexdigest()
            self.assertEqual(receipt["signature"], expected)
            self.assertEqual(receipt["proof"]["gate_revision"], 7)
            self.assertEqual(receipt["proof"]["snapshot_hash"], "a" * 64)
            self.assertNotIn("output", receipt["proof"])
            self.assertNotEqual(receipt["signature"], hmac.new(b"operator-not-core", canonical(receipt["proof"]).encode(), hashlib.sha256).hexdigest())
            job["payload"]["suite"] = "gateway"
            with self.assertRaisesRegex(ValueError, "WORKSPACE_TEST_RECEIPT_REQUIRED"):
                broker.test_attestation(job, result)

    def test_unknown_previous_job_quarantines_the_next_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "operator").mkdir()
            (runtime / "operator/approval.key").write_bytes(b"operator-only-test-key")
            broker = Broker(runtime)
            old = broker.store.enqueue(20, "restore", {})
            new = broker.store.enqueue(20, "backup", {})
            with broker.store.connect() as db:
                db.execute("UPDATE jobs SET state='failed_or_unknown' WHERE id=?", (old["id"],))
            with self.assertRaisesRegex(PermissionError, "OPERATOR_RECONCILIATION_REQUIRED"):
                broker.process(new["id"])
            from unittest.mock import patch
            with patch("builtins.input", return_value="wrong"):
                with self.assertRaisesRegex(PermissionError, "NOT_RECONCILED"):
                    broker.resolve(old["id"], old["hash"])
            with patch("builtins.input", return_value=old["hash"]), patch("broker.getpass.getuser", return_value="test-operator"):
                broker.resolve(old["id"], old["hash"])
            self.assertEqual(broker.inspect(old["id"])["state"], "operator_reconciled")
            self.assertEqual(broker.inspect(new["id"])["state"], "queued")
            self.assertTrue((runtime / "operator" / (old["id"] + ".reconciliation.json")).is_file())
            record = json.loads((runtime / "operator" / (old["id"] + ".reconciliation.json")).read_text())
            self.assertEqual(record["proof"]["operator"], "test-operator")

    def test_operator_proof_cannot_be_forged_and_snapshot_is_private_normalized_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "operator").mkdir()
            (runtime / "operator/approval.key").write_bytes(b"operator-only-test-key")
            workspace = runtime / "workspaces/21/app"
            workspace.mkdir(parents=True)
            source = workspace / "example.rb"
            source.write_bytes(b"first\r\nsecond\r\n")
            broker = Broker(runtime)
            job = broker.store.enqueue(20, "backup", {})
            with self.assertRaisesRegex(PermissionError, "LOCAL_APPROVAL"):
                broker.authorized(job)
            proof = {"id": job["id"], "hash": job["hash"], "expires": 9999999999}
            (runtime / "operator" / (job["id"] + ".approval.json")).write_text(canonical({"proof": proof, "signature": "forged"}))
            with self.assertRaisesRegex(PermissionError, "INVALID"):
                broker.authorized(job)
            snapshot = broker.snapshot(21, broker.workspace.tree_hash(21), str(uuid.uuid4()))
            self.assertEqual((snapshot / "app/example.rb").read_bytes(), b"first\nsecond\n")
            self.assertEqual(source.read_bytes(), b"first\r\nsecond\r\n")
            with self.assertRaisesRegex(ValueError, "WORKSPACE_CHANGED"):
                broker.snapshot(21, "wrong-hash", str(uuid.uuid4()))


if __name__ == "__main__":
    unittest.main()

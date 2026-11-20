import hashlib
import hmac
import json
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from broker import Broker
from gateway.store import canonical, digest
from release import verify_proof, verify_candidate, deployment_hash


class ReleaseTests(unittest.TestCase):
    def test_changed_gateway_image_invalidates_the_qualified_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "operator").mkdir()
            evidence = runtime / "stage-backups/fixture/restore-result.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text('{"passed":true,"syntheticOnly":true}')
            key = b"synthetic-qualification-key"
            identifier = str(uuid.uuid4())
            pair = {"image": "sha256:" + "a" * 64, "gateway_image": "sha256:" + "b" * 64}
            proof = {"id": identifier, "passed": True, "expires": time.time() + 60, **pair,
                     "restore_evidence": str(evidence), "restore_hash": hashlib.sha256(evidence.read_bytes()).hexdigest()}
            record = {"proof": proof, "signature": hmac.new(key, canonical(proof).encode(), hashlib.sha256).hexdigest()}
            (runtime / "operator" / (identifier + ".qualification.json")).write_text(canonical(record))
            parameters = {"qualification_id": identifier, "qualification_hash": digest(canonical(proof))}
            with patch("release.candidate", return_value=pair):
                self.assertEqual(verify_candidate(runtime, key, parameters)["gateway_image"], pair["gateway_image"])
            with patch("release.candidate", return_value={**pair, "gateway_image": "sha256:" + "c" * 64}):
                with self.assertRaisesRegex(PermissionError, "QUALIFIED_CANDIDATE_CHANGED"):
                    verify_candidate(runtime, key, parameters)

    def test_cutover_argv_requires_local_approval_and_unchanged_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "operator").mkdir()
            key = b"operator-only-test-key"
            (runtime / "operator/approval.key").write_bytes(key)
            broker = Broker(runtime)
            created = broker.store.enqueue(20, "release", {"qualification_id": str(uuid.uuid4()), "qualification_hash": "a" * 64})
            job = broker.inspect(created["id"])
            qualified = {"image": "sha256:" + "b" * 64, "gateway_image": "sha256:" + "e" * 64, "commit": "c" * 40}
            with patch("broker.verify_candidate", return_value=qualified), patch("broker.powershell", return_value="pwsh"), \
                    patch("broker.run", return_value="dry-run") as command:
                with self.assertRaisesRegex(PermissionError, "LOCAL_APPROVAL_REQUIRED"):
                    broker.operation(job)
                command.assert_not_called()
                proof = {"id": job["id"], "hash": job["hash"], "expires": time.time() + 60, "before_hash": "d" * 64,
                         "deployment_hash": "f" * 64}
                signature = hmac.new(key, canonical(proof).encode(), hashlib.sha256).hexdigest()
                (runtime / "operator" / (job["id"] + ".approval.json")).write_text(canonical({"proof": proof, "signature": signature}))
                with patch.object(broker, "configuration", return_value={"hash": "changed"}):
                    with self.assertRaisesRegex(ValueError, "CONFIGURATION_CHANGED"):
                        broker.operation(job)
                command.assert_not_called()
                with patch.object(broker, "configuration", return_value={"hash": proof["before_hash"]}), \
                        patch("broker.deployment_hash", return_value="changed"):
                    with self.assertRaisesRegex(PermissionError, "DEPLOYMENT_CHANGED"):
                        broker.operation(job)
                command.assert_not_called()
                with patch.object(broker, "configuration", return_value={"hash": proof["before_hash"]}), \
                        patch("broker.deployment_hash", return_value=proof["deployment_hash"]):
                    result = broker.operation(job)
                argv = command.call_args.args[0]
                self.assertEqual(argv[argv.index("-Image") + 1], qualified["image"])
                self.assertEqual(argv[argv.index("-GatewayImage") + 1], qualified["gateway_image"])
                self.assertEqual(argv[argv.index("-BeforeHash") + 1], proof["before_hash"])
                self.assertEqual(argv[argv.index("-DeploymentHash") + 1], proof["deployment_hash"])
                self.assertEqual(argv[argv.index("-ReleaseId") + 1], job["id"])
                self.assertEqual(result["image"], qualified["image"])
                self.assertEqual(result["gateway_image"], qualified["gateway_image"])

    def test_deployment_changes_invalidate_approval_without_exposing_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime, project = Path(directory) / "ai", Path(directory) / "core"
            for base in (runtime, project):
                base.mkdir()
                (base / ".env").write_text("synthetic-only")
            (runtime / "gateway").mkdir()
            (runtime / "gateway/credentials.json").write_text('{"21":"synthetic-token"}')
            first = deployment_hash(runtime, project)
            self.assertRegex(first, "^[a-f0-9]{64}$")
            (runtime / "gateway/credentials.json").write_text('{"21":"different-synthetic-token"}')
            self.assertNotEqual(first, deployment_hash(runtime, project))
            for name in ("gateway/gemini.key", "operator/gemini-free/production-proof.json"):
                path = runtime / name
                path.parent.mkdir(parents=True, exist_ok=True)
                before = deployment_hash(runtime, project)
                path.write_text("synthetic-only")
                self.assertNotEqual(before, deployment_hash(runtime, project), "Gemini activation material must bind release approval")
            (runtime / "gateway/config.json").mkdir()
            with self.assertRaisesRegex(PermissionError, "DEPLOYMENT_FILE_DENIED"):
                deployment_hash(runtime, project)

    def test_release_requires_exact_signed_unexpired_qualification(self):
        with tempfile.TemporaryDirectory() as directory:
            operator = Path(directory)
            identifier = str(uuid.uuid4())
            key = b"operator-only-key"
            parameters = {"qualification_id": identifier, "qualification_hash": "missing"}
            with self.assertRaisesRegex(PermissionError, "QUALIFICATION_REQUIRED"):
                verify_proof(operator, key, parameters)
            proof = {"id": identifier, "passed": True, "expires": time.time() + 60,
                     "image": "sha256:" + "a" * 64, "gateway_image": "sha256:" + "c" * 64, "commit": "b" * 40}
            path = operator / (identifier + ".qualification.json")
            path.write_text(canonical({"proof": proof, "signature": "forged"}))
            parameters["qualification_hash"] = digest(canonical(proof))
            with self.assertRaisesRegex(PermissionError, "QUALIFICATION_INVALID"):
                verify_proof(operator, key, parameters)
            def write():
                path.write_text(canonical({"proof": proof, "signature": hmac.new(key, canonical(proof).encode(), hashlib.sha256).hexdigest()}))
            write()
            self.assertEqual(verify_proof(operator, key, parameters)["image"], proof["image"])
            gateway_image = proof.pop("gateway_image")
            parameters["qualification_hash"] = digest(canonical(proof))
            write()
            with self.assertRaisesRegex(PermissionError, "QUALIFICATION_INVALID"):
                verify_proof(operator, key, parameters)
            proof["gateway_image"] = gateway_image
            parameters["qualification_hash"] = digest(canonical(proof))
            write()
            parameters["qualification_hash"] = "changed"
            with self.assertRaisesRegex(PermissionError, "QUALIFICATION_INVALID"):
                verify_proof(operator, key, parameters)
            proof["expires"] = 0
            parameters["qualification_hash"] = digest(canonical(proof))
            write()
            with self.assertRaisesRegex(PermissionError, "QUALIFICATION_INVALID"):
                verify_proof(operator, key, parameters)
            with self.assertRaisesRegex(ValueError, "QUALIFICATION_PARAMETERS"):
                verify_proof(operator, key, {"qualification_id": "../escape", "qualification_hash": "x"})


if __name__ == "__main__":
    unittest.main()

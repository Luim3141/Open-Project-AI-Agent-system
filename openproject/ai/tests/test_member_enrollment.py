import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import provision_member_tokens as enrollment
from gateway.store import Store
from gateway.local_operator import execute


class EnrollmentSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "gateway").mkdir()
        (self.root / "operator").mkdir()
        (self.root / "gateway/config.json").write_text(json.dumps({"project_id": 5, "users": {"19": "BA-PM", "20": "PM"}}))
        (self.root / "gateway/credentials.json").write_text("{}")
        self.store = Store(self.root / "gateway")
        wire = patch("provision_member_tokens.ContainerState.call", side_effect=lambda operation, **arguments:
                     execute({"operation": operation, "arguments": arguments}, self.root / "gateway"))
        wire.start()
        self.addCleanup(wire.stop)
        self.runtime = patch.object(enrollment, "RUNTIME", self.root)
        self.runtime.start()
        self.addCleanup(self.runtime.stop)
        self.addCleanup(self.temp.cleanup)

    def test_new_enrollment_allowed(self):
        enrollment.guard_enrollment()

    def test_existing_credentials_and_bearers_preserved(self):
        credential_path = self.root / "gateway/credentials.json"
        credential_path.write_text('{"19":"existing-native-secret"}')
        with self.assertRaises(RuntimeError):
            enrollment.guard_enrollment()
        self.assertEqual(json.loads(credential_path.read_text())["19"], "existing-native-secret")
        credential_path.write_text("{}")
        token_path = enrollment.token_file(20)
        token_path.write_text("existing-bearer-secret")
        with self.assertRaises(RuntimeError):
            enrollment.guard_enrollment()
        self.assertEqual(token_path.read_text(), "existing-bearer-secret")

    def test_existing_token_row_preserved(self):
        with self.store.connect() as db:
            db.execute("INSERT INTO tokens(hash,user_id) VALUES('synthetic',19)")
        with self.assertRaises(AssertionError):
            enrollment.guard_enrollment()

    def test_docker_failure_does_not_disclose_output(self):
        result = subprocess.CompletedProcess([], 1, "secret-token", "secret-token")
        with patch.object(enrollment.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "^DOCKER_OPERATION_FAILED_1$"):
                enrollment.docker("exec")

    def test_backend_mutations_denied(self):
        native = enrollment.BackendNative("http://web:8080", "test-secret", 5)
        with self.assertRaises(PermissionError):
            native.call("/api/v3/work_packages", method="POST", payload={})

    def test_resume_outside_private_directory_denied(self):
        with self.assertRaises(ValueError):
            enrollment.register_existing(self.root)

    def test_resume_does_not_replace_existing_native_credential(self):
        directory = self.root / "operator" / ("enrollment-" + "a" * 32)
        directory.mkdir()
        (directory / "user-19.api-token").write_text("opapi-" + "a" * 64)
        mapping = self.root / "gateway/credentials.json"
        mapping.write_text('{"19":"existing-native-secret"}')
        with patch.object(enrollment.BackendNative, "identity", return_value={"role": "BA-PM"}):
            with self.assertRaises(AssertionError):
                enrollment.register_existing(directory)
        self.assertEqual(json.loads(mapping.read_text())["19"], "existing-native-secret")


if __name__ == "__main__":
    unittest.main()

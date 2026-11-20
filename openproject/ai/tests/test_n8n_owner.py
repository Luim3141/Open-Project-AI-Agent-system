import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from n8n_owner import LocalN8n, NoRedirect, provision


class FixtureN8n:
    base = "http://localhost:25678"
    def __init__(self, setup=True):
        self.setup, self.cookie, self.calls, self.saved = setup, "", [], None
    def request(self, path, payload=None):
        self.calls.append(path)
        if path == "/rest/settings":
            return {"userManagement": {"showSetupOnFirstLoad": self.setup}}
        if path == "/rest/owner/setup":
            if not self.setup:
                raise AssertionError("MUST_NOT_REPLACE_EXISTING_OWNER")
            self.saved, self.setup = payload, False
            return {"role": "global:owner"}
        if path == "/rest/login":
            assert payload["password"] == self.saved["password"]
            self.cookie = "n8n-auth=synthetic-private-cookie"
            return {"role": "global:owner", "email": self.saved["email"]}
        raise AssertionError("UNEXPECTED_ENDPOINT")


class N8nOwnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "QLDAPM/openproject-ai/operator/n8n-owner"
        self.environment = patch.dict(os.environ, {"LOCALAPPDATA": self.temporary.name})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.permissions = patch("n8n_owner.private_directory", side_effect=lambda root: root.mkdir(parents=True, exist_ok=True))
        self.permissions.start()
        self.addCleanup(self.permissions.stop)

    def test_bootstrap_then_login_reuses_same_private_secret_without_setup_again(self):
        client = FixtureN8n()
        self.assertTrue(provision(self.root, client)["owner_created_now"])
        original = (self.root / "owner.json").read_bytes()
        result = provision(self.root, client)
        self.assertFalse(result["owner_created_now"])
        self.assertEqual((self.root / "owner.json").read_bytes(), original)
        self.assertEqual(client.calls.count("/rest/owner/setup"), 1)
        state = json.loads(original)
        self.assertNotIn(state["password"], json.dumps(result))
        self.assertNotIn(client.cookie, json.dumps(result))
        self.assertTrue(any(c.isupper() for c in state["password"]))
        self.assertTrue(any(c.isdigit() for c in state["password"]))

    def test_existing_owner_without_saved_access_is_never_claimed_or_reset(self):
        client = FixtureN8n(False)
        with self.assertRaisesRegex(PermissionError, "OWNER_EXISTS"):
            provision(self.root, client)
        self.assertFalse((self.root / "owner.json").exists())
        self.assertEqual(client.calls, ["/rest/settings"])

    def test_credentials_cannot_be_saved_outside_private_operator_directory(self):
        with self.assertRaisesRegex(ValueError, "PRIVATE_OPERATOR_CHILD"):
            provision(Path(self.temporary.name) / "workspace", FixtureN8n())

    def test_external_origins_redirects_and_non_owner_endpoints_are_denied(self):
        for origin in ("https://example.com", "http://192.168.1.2:5678", "http://localhost:5678/redirect", "http://user:pass@localhost:5678"):
            with self.assertRaises(ValueError):
                LocalN8n(origin)
        with self.assertRaises(ValueError):
            LocalN8n().request("/rest/license/activate", {})
        with self.assertRaises(ValueError):
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")

    def test_changed_endpoint_or_invalid_private_state_fails_without_replacement(self):
        client = FixtureN8n()
        provision(self.root, client)
        path = self.root / "owner.json"
        state = json.loads(path.read_text())
        state["endpoint"] = "https://example.com"
        path.write_text(json.dumps(state))
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "DOCUMENT_INVALID"):
            provision(self.root, client)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(client.calls.count("/rest/owner/setup"), 1)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json
import time
import subprocess
import os
import change_member_roles as correction

from gateway.native import Native
from gateway.service import Service
from gateway.store import Store, canonical, digest


class RoleChangeTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Local role apply uses the Windows operator lease; covered by host tests.")
    def test_operator_apply_updates_only_roles_and_pins_candidate_with_private_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            runtime, project = base / "ai", base / "project"
            (runtime / "operator").mkdir(parents=True)
            project.mkdir()
            state = runtime / "gateway"
            store = Store(state)
            bearer = store.issue_token(20, "PM", "synthetic-native")
            files = [project / "accounts.json", project / "bootstrap.json", state / "config.json", runtime / ".env", runtime / "image-lock.json"]
            files[0].write_text(json.dumps({"users": [{"email": "hiepk40c@gmail.com", "role": "BA-PM", "password": "one"},
                                                    {"email": "2101minhkhai@gmail.com", "role": "PM", "password": "two"}]}))
            files[1].write_text(json.dumps({"users": {"hiepk40c@gmail.com": 19, "2101minhkhai@gmail.com": 20}}))
            files[2].write_text(json.dumps({"project_id": 5, "users": {"19": "BA-PM", "20": "PM"}}))
            files[3].write_text("AI_IMAGE=old\nSECRET_KEY_BASE=synthetic-only\n")
            files[4].write_text('{"AI_IMAGE":"old"}')
            image = "sha256:" + "a" * 64
            path = runtime / "operator/member-role-change-fixture.json"
            native_result = {"before_hash": "fixture-before"}
            with patch.object(correction, "RUNTIME", runtime), patch.object(correction, "PROJECT", project), \
                 patch.object(correction, "FILES", files), patch.object(correction.sys.stdin, "isatty", return_value=True), \
                 patch.object(correction, "native", side_effect=[native_result, {"result": "applied"}]), \
                 patch.object(correction, "run", return_value=image), \
                 patch.object(correction.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout="")):
                packet = {"expires": time.time() + 60, "desired": correction.DESIRED, "files": correction.file_hashes(),
                          "native": native_result, "image": image}
                packet["hash"] = digest(canonical(packet))
                path.write_text(json.dumps(packet))
                with patch("builtins.input", return_value=packet["hash"]):
                    correction.apply(path)
            self.assertEqual(json.loads(files[2].read_text())["users"], {"19": "PM", "20": "BA"})
            self.assertEqual([u["password"] for u in json.loads(files[0].read_text())["users"]], ["one", "two"])
            self.assertEqual(files[3].read_text(), "AI_IMAGE=" + image + "\nSECRET_KEY_BASE=synthetic-only\n")
            self.assertEqual(store.authenticate(bearer)["role"], "BA")
            self.assertEqual(store.credential(20), "synthetic-native")
            self.assertTrue((path.with_suffix("") / "completed.json").exists())

    def test_sync_preserves_secrets_other_members_and_hostname(self):
        accounts = {"users": [{"email": "hiepk40c@gmail.com", "login": "ba-pm", "password": "private1", "role": "BA-PM"},
                              {"email": "2101minhkhai@gmail.com", "login": "pm", "password": "private2", "role": "PM"},
                              {"email": "be@fixture.invalid", "role": "BE"}]}
        bootstrap = {"users": {"hiepk40c@gmail.com": 19, "2101minhkhai@gmail.com": 20}, "roles": {"BA-PM": 23, "PM": 22}}
        config = {"project_id": 5, "users": {"19": "BA-PM", "20": "PM", "21": "BE"}, "hosts": ["existing.invalid"]}
        accounts, bootstrap, config = correction.synchronize(accounts, bootstrap, config)
        self.assertEqual([a["role"] for a in accounts["users"]], ["PM", "BA", "BE"])
        self.assertEqual([a["password"] for a in accounts["users"][:2]], ["private1", "private2"])
        self.assertEqual(config["hosts"], ["existing.invalid"])
        self.assertEqual(bootstrap["roles"], {"BA": 23, "PM": 22})

    def test_noninteractive_apply_never_calls_native_or_docker(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "operator").mkdir()
            path = runtime / "operator/member-role-change-test.json"
            packet = {"desired": correction.DESIRED, "expires": time.time() + 60}
            packet["hash"] = digest(canonical(packet))
            path.write_text(json.dumps(packet))
            with patch.object(correction, "RUNTIME", runtime), patch.object(correction.sys.stdin, "isatty", return_value=False), \
                 patch.object(correction, "native") as native, patch.object(correction, "run") as docker:
                with self.assertRaisesRegex(PermissionError, "HUMAN_LOCAL_CONSOLE_REQUIRED"):
                    correction.apply(path)
                native.assert_not_called()
                docker.assert_not_called()

    def identity(self, roles):
        native = Native("http://web:8080", "synthetic", 5)
        member = {"_links": {"principal": {"href": "/api/v3/users/20"},
                             "roles": [{"title": "QLDAPM " + role} for role in roles]}}
        with patch.object(native, "call", side_effect=[{"id": 20, "admin": False}, {"identifier": "qldapm-local"}]), \
             patch.object(native, "collection", return_value=[member]):
            return native.identity(20)

    def test_ba_is_recognized_without_pm_union(self):
        self.assertEqual(self.identity(["BA"])["role"], "BA")
        self.assertEqual(self.identity(["BA", "PM"])["role"], "PM")
        self.assertEqual(self.identity(["BA", "BA-PM"])["role"], "BA")

    def test_downgraded_actor_cannot_propose_admin_job_with_old_bearer(self):
        class CurrentBA:
            def __init__(self, *args): pass
            def identity(self, expected): return {"user_id": expected, "role": "BA", "project_id": 5}
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            bearer = store.issue_token(20, "PM", "synthetic")
            service = Service(store, {"users": {"20": "BA"}, "project_id": 5, "openproject_url": "http://web:8080"},
                              Path(directory) / "workspaces", CurrentBA)
            self.assertEqual(service.execute(bearer, {"action": "identity"})["result"]["role"], "BA")
            with self.assertRaisesRegex(PermissionError, "PM_REQUIRED"):
                service.execute(bearer, {"action": "propose_operation", "arguments": {"operation": "backup", "parameters": {}},
                                        "idempotency_key": "downgraded-actor"})
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 0)

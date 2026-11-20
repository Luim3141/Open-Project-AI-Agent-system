import json
import subprocess
import sys
import tempfile
import time
import unittest
import io
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from gateway.ai_worker import run_isolated
from gateway.gemini import ProviderError, SMOKE_PROMPT


class AIWorkerTests(unittest.TestCase):
    def test_run_consent_is_scoped_to_routine_actions_and_selected_or_new_ids(self):
        from gateway.ai_worker import main
        for consent in (False, True):
            with self.subTest(consent=consent), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "config.json").write_text('{"gateway_mode":"native","project_id":3}')
                calls = []
                test = self
                class Provider:
                    def settings(self): return {"data_scope": "project-metadata-only"}
                    def run(self, prompt, execute, **options):
                        test.assertEqual(options["allow_routine_writes"], consent)
                        execute("get_work_package", {"id": 99})
                        if consent:
                            with test.assertRaisesRegex(PermissionError, "CREATE_PARENT_OUTSIDE_USER_SCOPE"):
                                execute("create_work_package", {"parent_id": 99})
                        execute("create_work_package", {})
                        execute("update_work_package", {"id": 12})
                        if consent:
                            with test.assertRaisesRegex(PermissionError, "OUTSIDE_USER_SCOPE"):
                                execute("update_work_package", {"id": 99})
                        else:
                            execute("update_work_package", {"id": 99, "auto_execute": True})
                        execute("propose_operation", {"operation": "release"})
                        return {"verified_fixture": True}
                class FixtureService:
                    def __init__(self, store, *args):
                        self.mode, self.store, self.gemini = "native", store, Provider()
                        self.config = args[0]
                    def execute_actor(self, actor, command):
                        if command["action"] == "identity":
                            return {"result": {"role": "PM"}}
                        if command["action"] == "get_permissions":
                            return {"result": {"tools": []}}
                        calls.append(command)
                        return {"result": {"id": 12}}
                payload = {"root": folder, "workspaces": folder, "actor": 7, "prompt": "synthetic", "id": "fixture",
                           "allow_routine_writes": consent, "write_scope_ids": list(range(1, 9))}
                output = io.BytesIO()
                with patch("gateway.service.Service", FixtureService), patch("sys.stdin", SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode()))), patch("sys.stdout", SimpleNamespace(buffer=output)):
                    main()
                self.assertTrue(json.loads(output.getvalue())["result"]["verified_fixture"])
                self.assertFalse(calls[0]["auto_execute"])
                self.assertEqual(calls[1]["auto_execute"], consent)
                self.assertEqual(calls[2]["auto_execute"], consent)
                self.assertFalse(calls[-1]["auto_execute"], "Deploy proposal must never inherit routine consent")

    def test_real_private_worker_refuses_disabled_provider_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "config.json").write_text(json.dumps({"users": {}, "project_id": 5,
                "openproject_url": "http://127.0.0.1:8091"}))
            (root / "gemini.json").write_text('{"enabled":false}')
            with self.assertRaisesRegex(ProviderError, "DISABLED"):
                run_isolated(root, root / "workspaces", 21, SMOKE_PROMPT, "fixture-disabled")

    def test_real_process_timeout_prevents_a_late_tool_side_effect(self):
        original = subprocess.run
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "must-not-exist"
            def wire(argv, **options):
                self.assertEqual(argv[1:], ["-m", "gateway.ai_worker"])
                self.assertEqual(options["timeout"], 600)
                # OS-boundary fixture simulates a stuck tool; no model, credential, or arbitrary production command.
                return original([sys.executable, "-c", "import pathlib,sys,time; time.sleep(0.7); pathlib.Path(sys.argv[1]).touch()",
                    str(marker)], capture_output=True, timeout=0.1)
            with patch("gateway.ai_worker.subprocess.run", wire), self.assertRaisesRegex(ProviderError, "DEADLINE"):
                run_isolated(Path(folder), Path(folder), 21, SMOKE_PROMPT, "fixture-timeout")
            time.sleep(0.8)
            self.assertFalse(marker.exists(), "Timed-out tool process must not continue writing")


if __name__ == "__main__":
    unittest.main()

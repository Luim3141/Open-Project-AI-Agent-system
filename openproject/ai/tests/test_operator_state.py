import concurrent.futures
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.local_operator import execute
from gateway.store import Store
from operator_state import ContainerState, OfflineState, require_offline


class OperatorStateTests(unittest.TestCase):
    def test_queue_claim_is_atomic_and_unknown_outcome_blocks_next_job(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = Store(root)
            first, second = [store.enqueue(8, "test", {}) for _ in range(2)]
            def claim(job):
                try:
                    execute({"operation": "broker_job", "arguments": {"operation": "claim",
                        "identifier": job["id"], "state": None, "result": None}}, root)
                    return job
                except PermissionError:
                    return None
            with concurrent.futures.ThreadPoolExecutor(2) as pool:
                winners = [job for job in pool.map(claim, [first, second]) if job]
            self.assertEqual(len(winners), 1)
            winner = winners[0]
            store.broker_job("finish", winner["id"], "failed_or_unknown", {"error": "timeout"})
            other = second if first == winner else first
            with self.assertRaisesRegex(PermissionError, "RECONCILIATION"):
                store.broker_job("claim", other["id"])
            store.broker_job("reconcile", winner["id"])
            store.broker_job("claim", other["id"])
            store.broker_job("finish", other["id"], "done", {"passed": True})
            self.assertEqual(store.job(8, other["id"])["result"], {"passed": True})
            with self.assertRaisesRegex(ValueError, "CHANGED"):
                store.broker_job("finish", other["id"], "done", {"passed": False})

    def test_local_protocol_rejects_sql_secret_reads_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for packet in [{"operation": "sql", "arguments": {"query": "DELETE FROM jobs"}},
                           {"operation": "credential", "arguments": {"actor": 8}},
                           {"operation": "revoke_token", "arguments": {"token": "fake", "command": "shell"}}]:
                with self.assertRaisesRegex(ValueError, "DENIED"):
                    execute(packet, root)
            self.assertFalse((root / "gateway.sqlite").exists())

    def test_offline_recovery_is_explicit_pinned_and_refuses_running_gateway_or_token_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "PINNED"):
                OfflineState(directory, "python:latest")
            offline = OfflineState(directory, "sha256:" + "a" * 64)
            with self.assertRaisesRegex(PermissionError, "RECOVERY_ONLY"):
                offline.call("issue_token", user_id=8, role="BE", op_token="synthetic")
            with self.assertRaisesRegex(PermissionError, "RECOVERY_ONLY"):
                offline.broker_job("claim", "synthetic")
            with patch("operator_state.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "running", "")) as execute:
                with self.assertRaisesRegex(PermissionError, "STOP_GATEWAY_FIRST"):
                    offline.broker_job("queued")
                self.assertEqual(len(execute.call_args_list), 1)

    def test_maintenance_blocks_confirmation_and_token_issuance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.json").write_text('{"maintenance":true}')
            for operation, arguments in [("issue_token", {"user_id":8,"role":"BE","op_token":"fake"}),
                                         ("confirm_proposal", {"actor":8,"token":"fake","identifier":"fake","fingerprint":"fake"})]:
                with self.assertRaisesRegex(PermissionError, "MAINTENANCE"):
                    execute({"operation":operation,"arguments":arguments}, root)

    def test_wrong_mount_timeout_and_stopped_gateway_never_fallback_to_host_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = ContainerState(root)
            mounts = [{"Destination": "/state", "RW": True, "Source": str(root)}]
            with patch("operator_state.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "[]", "")):
                with self.assertRaisesRegex(PermissionError, "MOUNT_MISMATCH"):
                    store.broker_job("queued")
            with patch("operator_state.subprocess.run", side_effect=[subprocess.CompletedProcess([], 0, json.dumps(mounts), ""),
                                                                      subprocess.TimeoutExpired("fixed operator", 60)]):
                with self.assertRaises(subprocess.TimeoutExpired):
                    store.broker_job("queued")
            with patch("operator_state.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "running\n", "")):
                with self.assertRaisesRegex(PermissionError, "STOP_GATEWAY_FIRST"):
                    require_offline("synthetic")
            self.assertFalse((root / "gateway.sqlite").exists())

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from broker import Broker
from gateway.store import Store
from operator_state import ContainerState


class BrokerInterruptionTests(unittest.TestCase):
    def test_result_survives_lost_queue_connection_and_requires_local_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "operator").mkdir()
            (root / "operator/approval.key").write_bytes(b"fake-private-key")
            source = root / "workspaces/21/app"
            source.mkdir(parents=True)
            (source / "fixture.rb").write_text("synthetic")
            db = Store(root / "gateway")
            db.issue_token(21, "PM", "synthetic-native")
            (db.root / "config.json").write_text('{"project_id":5,"users":{"21":"PM"}}')
            (root / "image-lock.json").write_text(json.dumps({"AI_IMAGE": "sha256:" + "a" * 64}))
            transport = ContainerState(db.root)
            broker = Broker(root, store=transport)
            job = db.enqueue(21, "test", {"suite": "gateway", "workspace_actor": 21, "snapshot_hash": "AT_EXECUTION"})
            def wire(command, **args):
                if command == "broker_job" and args["operation"] == "finish":
                    raise RuntimeError("synthetic queue connection lost")
                return getattr(db, command)(**args)
            with patch.object(transport, "call", side_effect=wire), patch("broker.BackendNative.identity", return_value={"role": "PM"}), \
                 patch("broker.run", return_value="synthetic fixed runner passed"):
                with self.assertRaisesRegex(RuntimeError, "connection lost"):
                    broker.process(job["id"])
            self.assertEqual(db.job(21, job["id"])["state"], "running")
            packet = json.loads((root / "operator" / (job["id"] + ".result.json")).read_text())
            self.assertTrue(packet["proof"]["result"]["passed"])
            self.assertTrue(packet["proof"]["queue_confirmation_required"])
            local = Broker(root)
            with patch("builtins.input", return_value=job["hash"]), patch("broker.getpass.getuser", return_value="fixture-operator"):
                local.resolve(job["id"], job["hash"])
            self.assertEqual(db.job(21, job["id"])["state"], "operator_reconciled")
            second = db.enqueue(21, "test", {})
            db.broker_job("claim", second["id"])
            with self.assertRaisesRegex(PermissionError, "WITHOUT_RECEIPT"):
                local.resolve(second["id"], second["hash"])

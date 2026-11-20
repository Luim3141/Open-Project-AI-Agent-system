"""Synthetic Windows/Linux WAL reproduction; never opens a project runtime."""
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from gateway.store import Store
from operator_state import ContainerState, OfflineState
from broker import Broker
import json
import re


def main(image, mode="--reproduce"):
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
        raise ValueError("PINNED_FIXTURE_IMAGE_REQUIRED")
    name = "qldapm-wal-fixture-" + str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix="qldapm-wal-") as directory:
        root = Path(directory)
        program = """
import time
import json
from pathlib import Path
from gateway.store import Store
s=Store('/state')
jobs=[s.enqueue(8,'test',{'suite':'gateway'}) for _ in range(3)]
token=s.issue_token(8,'BE','synthetic-never-used-native')
Path('/state/fixture.json').write_text(json.dumps({'jobs':jobs,'token':token}))
with s.connect() as db:
    print('READY', flush=True)
    for i in range(300):
        s.record(8, 'synthetic_linux', i, 'ok')
        time.sleep(0.1)
"""
        try:
            subprocess.run(["docker", "run", "--pull", "never", "-d", "--name", name, "--network", "none", "--read-only",
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "128m", "--pids-limit", "32",
                "-v", f"{root}:/state", image, "python", "-c", program], check=True, capture_output=True)
            for _ in range(50):
                if b"READY" in subprocess.run(["docker", "logs", name], capture_output=True).stdout:
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError("FIXTURE_NOT_READY")
            if mode == "--broker":
                state = ContainerState(root, name)
                (root / "operator").mkdir()
                (root / "operator/approval.key").write_bytes(b"synthetic-operator-only-key")
                fixture = json.loads((root / "fixture.json").read_text())
                broker = Broker(root, store=state)
                for job in fixture["jobs"]:
                    assert broker.inspect(job["id"])["actor"] == 8
                    state.broker_job("claim", job["id"])
                    state.broker_job("finish", job["id"], "done", {"passed": True, "detail": "kiểm thử giả"})
                    assert json.loads(broker.inspect(job["id"])["result"])["detail"] == "kiểm thử giả"
                    state.record(8, "synthetic_broker", job["id"], "done")
                assert state.broker_job("queued") == []
                assert state.broker_job("unresolved") is None
                assert state.call("token_count", actors=[8]) == 1
                state.call("revoke_token", token=fixture["token"])
                denied = subprocess.run(["docker", "exec", name, "python", "-c",
                    "import json; from gateway.store import Store; s=Store('/state'); "
                    "s.authenticate(json.loads(open('/state/fixture.json').read())['token'])"], capture_output=True)
                assert denied.returncode and b"INVALID_OR_EXPIRED_TOKEN" in denied.stderr
            elif mode == "--linux-only":
                subprocess.run(["docker", "exec", name, "python", "-c",
                    "from gateway.store import Store; s=Store('/state'); [s.record(8,'synthetic_broker',i,'ok') for i in range(20)]"],
                    check=True, capture_output=True)
            else:
                store = Store(root)
                for i in range(20):
                    store.record(8, "synthetic_windows", i, "ok")
            probe = subprocess.run(["docker", "exec", name, "python", "-c",
                "from gateway.store import Store; Store('/state').record(8,'after_host','fixture','ok')"], capture_output=True)
            if probe.returncode:
                logs = subprocess.run(["docker", "logs", name], capture_output=True)
                raise RuntimeError("LINUX_AFTER_HOST_FAILED: " + logs.stderr.decode()[-500:] + probe.stderr.decode()[-200:])
            if mode == "--broker":
                subprocess.run(["docker", "stop", name], check=True, capture_output=True)
                offline = OfflineState(root, image, name)
                assert offline.broker_job("queued") == []
                assert offline.broker_job("inspect", fixture["jobs"][0]["id"])["state"] == "done"
                offline.record(8, "synthetic_offline", "fixture", "checked")
            print("Concurrent Store PASS (mode=" + mode + "; synthetic only).")
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)


if __name__ == "__main__":
    if len(sys.argv) not in {2, 3} or (len(sys.argv) == 3 and sys.argv[2] not in {"--reproduce", "--linux-only", "--broker"}):
        raise ValueError("EXPECTED_PINNED_IMAGE_AND_DIAGNOSTIC_MODE")
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "--reproduce")

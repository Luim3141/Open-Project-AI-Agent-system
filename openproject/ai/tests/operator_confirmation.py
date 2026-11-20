"""Local operator protocol against synthetic core identities; no ticket/live writes."""
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import uuid
import re
from pathlib import Path

from operator_state import ContainerState


def main(runtime, image):
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
        raise ValueError("PINNED_FIXTURE_IMAGE_REQUIRED")
    credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
    project = json.loads((runtime / "stage/bootstrap.json").read_text())["project_id"]
    be, qa = credentials["BE"], credentials["QA"]
    name = "qldapm-operator-fixture-" + str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix="qldapm-operator-") as directory:
        root = Path(directory)
        state, workspace = root / "gateway", root / "workspaces"
        state.mkdir()
        target = workspace / str(be["id"]) / "app/fixture.rb"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"before\n")
        (state / "config.json").write_text(json.dumps({"project_id": project,
            "openproject_url": "http://staging-web:8080", "users": {str(be["id"]): "BE", str(qa["id"]): "QA"}}))
        try:
            subprocess.run(["docker", "run", "--pull", "never", "-d", "--name", name, "--network", "qldapm-ai-stage_stage",
                "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "192m", "--pids-limit", "32",
                "-v", f"{state}:/state", "-v", f"{workspace}:/workspaces", image, "python", "-c",
                "from gateway.store import Store; import time; Store('/state'); print('READY',flush=True); time.sleep(120)"],
                check=True, capture_output=True)
            for _ in range(30):
                if b"READY" in subprocess.run(["docker", "logs", name], capture_output=True).stdout:
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError("SYNTHETIC_FIXTURE_NOT_READY")
            store = ContainerState(state, name)
            token = store.call("issue_token", user_id=be["id"], role="BE", op_token=be["token"])
            qa_token = store.call("issue_token", user_id=qa["id"], role="QA", op_token=qa["token"])
            try:
                store.call("issue_token", user_id=be["id"], role="PM", op_token=be["token"])
            except RuntimeError:
                pass
            else:
                raise AssertionError("WRONG_ROLE_ENROLLMENT_ACCEPTED")
            command = {"action": "write_code", "arguments": {"path": "app/fixture.rb", "content": "after\n",
                       "expected_hash": hashlib.sha256(b"before\n").hexdigest()}, "idempotency_key": "synthetic-code-proposal"}
            program = """
import json,sys
from gateway.service import Service
from gateway.store import Store
p=json.load(sys.stdin)
s=Service(Store('/state'),json.load(open('/state/config.json')),'/workspaces')
print(json.dumps(s.execute(p['token'],p['command'])['result']))
"""
            result = subprocess.run(["docker", "exec", "-i", name, "python", "-c", program],
                                    input=json.dumps({"token": token, "command": command}), text=True, capture_output=True, timeout=60)
            if result.returncode:
                raise RuntimeError("SYNTHETIC_PROPOSAL_FAILED; no upstream/token output")
            proposal = json.loads(result.stdout)
            assert target.read_bytes() == b"before\n"
            preview = store.call("preview_proposal", actor=be["id"], token=token, identifier=proposal["id"])
            assert preview["hash"] == proposal["hash"]
            try:
                store.call("confirm_proposal", actor=qa["id"], token=qa_token, identifier=proposal["id"], fingerprint=proposal["hash"])
            except RuntimeError:
                pass
            else:
                raise AssertionError("WRONG_ACTOR_CONFIRMATION_ACCEPTED")
            store.call("confirm_proposal", actor=be["id"], token=token, identifier=proposal["id"], fingerprint=proposal["hash"])
            assert target.read_bytes() == b"after\n"
            try:
                store.call("confirm_proposal", actor=be["id"], token=token, identifier=proposal["id"], fingerprint=proposal["hash"])
            except RuntimeError:
                pass
            else:
                raise AssertionError("REPLAY_CONFIRMATION_ACCEPTED")
            assert target.read_bytes() == b"after\n"
            print("Local operator native identity/token/role/proposal/independent actor/replay PASS; synthetic code only, no ticket/live writes.")
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])

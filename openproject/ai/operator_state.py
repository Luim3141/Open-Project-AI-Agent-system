"""Host CLI state access stays in the Linux gateway's SQLite/locking domain."""
import json
import subprocess
import re
from pathlib import Path

from gateway.store import canonical


class ContainerState:
    def __init__(self, root, container="qldapm-ai-gateway-1"):
        self.root = Path(root).resolve()
        self.container = container

    def call(self, command, **arguments):
        packet = canonical({"operation": command, "arguments": arguments})
        if len(packet.encode()) > 1048576:
            raise ValueError("LOCAL_OPERATOR_PAYLOAD_LIMIT")
        check = subprocess.run(["docker", "inspect", "--format", "{{json .Mounts}}", self.container],
                               capture_output=True, text=True, timeout=15)
        if check.returncode:
            raise PermissionError("GATEWAY_STATE_UNAVAILABLE; no host SQLite fallback")
        def normal(path):
            return str(path).replace("\\", "/").rstrip("/").casefold()
        if not any(m["Destination"] == "/state" and m["RW"] and normal(m["Source"]) == normal(self.root)
                   for m in json.loads(check.stdout)):
            raise PermissionError("GATEWAY_STATE_MOUNT_MISMATCH")
        result = subprocess.run(["docker", "exec", "-i", self.container, "python", "-m", "gateway.local_operator"],
                                input=packet, capture_output=True, text=True, encoding="utf-8", timeout=60)
        return decode(result)

    def broker_job(self, operation, identifier=None, state=None, result=None):
        return self.call("broker_job", operation=operation, identifier=identifier, state=state, result=result)

    def record(self, actor, action, target, outcome):
        return self.call("record", actor=actor, action=action, target=target, outcome=outcome)

    def credential(self, actor):
        return json.loads((self.root / "credentials.json").read_text())[str(actor)]


def decode(result):
    if result.returncode:
        raise RuntimeError("LOCAL_STATE_FAILED_OR_UNKNOWN; inspect receipts, no auto retry or host SQLite fallback")
    if len(result.stdout.encode()) > 1048576:
        raise ValueError("LOCAL_OPERATOR_RESULT_LIMIT")
    return json.loads(result.stdout)["result"]


class OfflineState(ContainerState):
    """Explicit recovery after Stop only; a one-shot Linux process, not a gateway restart."""
    def __init__(self, root, image, container="qldapm-ai-gateway-1"):
        super().__init__(root, container)
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
            raise ValueError("PINNED_OFFLINE_IMAGE_REQUIRED")
        self.image = image

    def call(self, command, **arguments):
        if command not in {"broker_job", "record"}:
            raise PermissionError("OFFLINE_QUEUE_RECOVERY_ONLY")
        if command == "broker_job" and arguments.get("operation") not in {"inspect", "queued", "unresolved", "reconcile"}:
            raise PermissionError("OFFLINE_QUEUE_RECOVERY_ONLY")
        require_offline(self.container)
        packet = canonical({"operation": command, "arguments": arguments})
        if len(packet.encode()) > 1048576:
            raise ValueError("LOCAL_OPERATOR_PAYLOAD_LIMIT")
        source = Path(__file__).resolve().parent / "gateway"
        result = subprocess.run(["docker", "run", "--rm", "--pull", "never", "-i", "--network", "none", "--read-only",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "128m", "--pids-limit", "32",
            "--mount", f"type=bind,source={self.root},target=/state",
            "--mount", f"type=bind,source={source},target=/trusted/gateway,readonly", "--workdir", "/trusted", "-e", "PYTHONPATH=/trusted",
            self.image, "python", "-m", "gateway.local_operator"],
            input=packet, capture_output=True, text=True, encoding="utf-8", timeout=60)
        return decode(result)


def require_offline(container):
    """Offline-only helpers must stop before opening Windows SQLite or changing secrets."""
    result = subprocess.run(["docker", "ps", "-a", "--filter", "name=^/" + container + "$", "--format", "{{.State}}"],
                            capture_output=True, text=True, timeout=15)
    if result.returncode or result.stdout.strip() not in {"", "exited", "created", "dead"}:
        raise PermissionError("STOP_GATEWAY_FIRST; offline helper refused, state unchanged")

"""Fixed local targets using existing personal PM credentials, never bootstrap admin."""
import json
import os
import subprocess
from pathlib import Path

from gateway.native import NativeError


class Target:
    def __init__(self, name):
        if name not in {"live", "staging"}:
            raise ValueError("TARGET_NOT_ALLOWED")
        self.name = name
        runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
        if name == "live":
            bootstrap = runtime.parent / "openproject/bootstrap.json"
            self.container, self.base, self.actor = "qldapm-ai-gateway-1", "http://web:8080", 19
            self.token = json.loads((runtime / "gateway/credentials.json").read_text())["19"]
            expected_label = "qldapm-ai"
        else:
            bootstrap = runtime / "stage/bootstrap.json"
            self.container, self.base = "qldapm-ai-stage-staging-gateway-1", "http://staging-web:8080"
            actor = json.loads((runtime / "stage/test-credentials.json").read_text())["PM"]
            self.actor, self.token = actor["id"], actor["token"]
            expected_label = "qldapm-ai-stage"
        self.bootstrap = json.loads(bootstrap.read_text())
        self.project = int(self.bootstrap["project_id"])
        label = subprocess.check_output(["docker", "inspect", "--format",
            '{{index .Config.Labels "com.docker.compose.project"}}', self.container], text=True, timeout=15).strip()
        if label != expected_label or self.project != (5 if name == "live" else 3):
            raise ValueError("TARGET_INSTANCE_MISMATCH")
        identity = self.call("/api/v3/users/me")
        if identity.get("id") != self.actor or identity.get("admin"):
            raise ValueError("PERSONAL_PM_REQUIRED")
        program = "from gateway.native import Native; import json,sys; d=json.load(sys.stdin); print(json.dumps(Native(d['base'],d['token'],d['project']).identity(d['actor'])))"
        result = self._execute(program, {"base": self.base, "token": self.token, "project": self.project, "actor": self.actor})
        if result.get("role") != "PM":
            raise ValueError("NATIVE_PM_ROLE_REQUIRED")

    def _execute(self, program, data):
        try:
            result = subprocess.run(["docker", "exec", "-i", self.container, "python", "-c", program],
                input=json.dumps(data), capture_output=True, text=True, encoding="utf-8", timeout=100)
        except subprocess.TimeoutExpired:
            raise TimeoutError('LOCAL_NATIVE_TRANSPORT_TIMEOUT') from None
        if result.returncode:
            raise RuntimeError("LOCAL_NATIVE_TRANSPORT_FAILED")
        try:
            return json.loads(result.stdout)
        except (ValueError, UnicodeError):
            raise RuntimeError('LOCAL_NATIVE_TRANSPORT_INVALID_RESPONSE') from None

    def call(self, path, method="GET", payload=None):
        if method not in {"GET", "POST", "PATCH"} or not path.startswith("/api/v3/") or any(c in path for c in ("..", "\\", "#")):
            raise ValueError("NATIVE_OPERATION_DENIED")
        program = """
import json,re,sys
from gateway.native import Native,NativeError
d=json.load(sys.stdin)
try:
 native=Native(d['base'],d['token'],d['project'])
 if d['method'] != 'GET':
  identity=native.identity(d['actor'])
  if identity['role'] != 'PM':
   raise NativeError(403,'NATIVE_PM_ROLE_CHANGED')
 print(json.dumps({'result':native.call(d['path'],d['method'],d['payload'])}))
except NativeError as e:
 print(json.dumps({'status':e.status,'codes':re.findall(r'QLDAPM_[A-Z_]+',str(e))}))
except PermissionError:
 print(json.dumps({'status':403,'codes':['PERSONAL_NATIVE_IDENTITY_DENIED']}))
"""
        result = self._execute(program, {"base": self.base, "token": self.token, "project": self.project,
                                        "path": path, "method": method, "payload": payload, "actor": self.actor})
        if "status" in result:
            raise NativeError(result["status"], ";".join(result["codes"]) or "NATIVE_REQUEST_REJECTED")
        return result["result"]

    def collection(self, path):
        rows, identifiers = [], set()
        for page in range(1, 1001):
            value = self.call(path + ("&" if "?" in path else "?") + f"pageSize=100&offset={page}")
            elements = value.get("_embedded", {}).get("elements")
            if not isinstance(elements, list) or type(value.get("total")) is not int:
                raise ValueError("NATIVE_COLLECTION_INCOMPLETE")
            for row in elements:
                identifier = row.get("id")
                if identifier is None or identifier in identifiers:
                    raise ValueError("NATIVE_DUPLICATE_ID")
                rows.append(row); identifiers.add(identifier)
            if len(rows) == value["total"]:
                return rows
            if not elements or len(rows) > value["total"]:
                raise ValueError("NATIVE_COLLECTION_INCOMPLETE")
        raise ValueError("NATIVE_PAGINATION_LIMIT")

    def packages(self):
        return self.collection(f"/api/v3/projects/{self.project}/work_packages")

"""Trusted host broker. Only this local process has Docker/operator authority."""
import argparse
import getpass
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from provision_member_tokens import BackendNative
from gateway.store import Store, canonical, digest
from gateway.workspace import Workspace
from runner import isolated_core
from release import verify_candidate, deployment_hash
from operator_state import ContainerState, OfflineState

ROOT = Path(__file__).resolve().parent
PROJECT_RUNTIME = Path(os.environ.get("LOCALAPPDATA", "")) / "QLDAPM/openproject"
BASE_IMAGE = "openproject/openproject:17.9.1-slim@sha256:2beeecac788d4f423c46a95ffbd04e6479491938b9924b610e9f47d81a38303c"
ADMIN_ACTIONS = {"user", "role", "workflow", "type", "status", "field", "settings", "delete_work_package"}


def run(argv, timeout=900, input_data=None):
    result = subprocess.run(argv, input=input_data, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    if result.returncode:
        raise RuntimeError(f"COMMAND_FAILED_{result.returncode}: " + result.stderr[-2000:])
    return result.stdout[-64000:]


def powershell():
    executable = shutil.which("pwsh")
    if not executable:
        raise RuntimeError("POWERSHELL_7_REQUIRED")
    return executable


def backup_manifest(parameters):
    ServiceArguments.exact(parameters, {"backup_path"})
    backup = Path(parameters["backup_path"]).resolve()
    base = (PROJECT_RUNTIME / "backups").resolve()
    if backup == base or not backup.is_relative_to(base) or not backup.is_dir():
        raise ValueError("BACKUP_PATH_DENIED")
    files = sorted(backup.rglob("*"))
    if len(files) > 100:
        raise ValueError("BACKUP_MANIFEST_LIMIT")
    manifest = []
    for path in files:
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()) or not path.resolve().is_relative_to(backup):
            raise ValueError("BACKUP_LINK_DENIED")
        if path.is_file():
            if path.stat().st_nlink != 1:
                raise ValueError("BACKUP_LINK_DENIED")
            fingerprint = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1048576), b""):
                    fingerprint.update(block)
            manifest.append((path.relative_to(backup).as_posix(), fingerprint.hexdigest()))
    if not {"database.dump", "assets.tar.gz"} <= {name for name, value in manifest}:
        raise ValueError("BACKUP_INCOMPLETE")
    return digest(canonical(manifest))


class Broker:
    def __init__(self, runtime, test_images=None, store=None):
        self.runtime = Path(runtime)
        self.test_images = test_images
        live_runtime = Path(os.environ.get("LOCALAPPDATA", "")) / "QLDAPM/openproject-ai"
        if store is None and self.runtime.resolve() == live_runtime.resolve():
            store = ContainerState(self.runtime / "gateway")
        self.store = store if store is not None else Store(self.runtime / "gateway")
        self.workspace = Workspace(self.runtime / "workspaces")
        self.key = (self.runtime / "operator/approval.key").read_bytes()

    def inspect(self, identifier):
        if not re.fullmatch(r"[a-f0-9-]{36}", identifier):
            raise ValueError("INVALID_JOB_ID")
        record = self.store.broker_job("inspect", identifier)
        record["payload"] = json.loads(record["payload"])
        expected = digest(canonical({"actor": record["actor"], "action": record["action"], "payload": record["payload"]}))
        if expected != record["hash"]:
            raise ValueError("JOB_INTEGRITY_ERROR")
        return record

    def approve(self, identifier, expected_hash):
        job = self.inspect(identifier)
        if job["hash"] != expected_hash or job["state"] != "queued":
            raise ValueError("JOB_CHANGED_OR_ALREADY_EXECUTED")
        print(canonical({k: job[k] for k in ("id", "action", "actor", "payload", "hash")}))
        before = self.configuration(job) if job["action"] in ADMIN_ACTIONS | {"release"} else None
        if job["action"] == "release":
            qualification = verify_candidate(self.runtime, self.key, job["payload"])
            deployment = deployment_hash(self.runtime, PROJECT_RUNTIME)
            print(canonical({"qualified_commit": qualification["commit"], "qualified_image": qualification["image"],
                             "qualified_gateway_image": qualification["gateway_image"],
                             "limitations": qualification["limitations"]}))
            print(canonical({"deployment_hash": deployment}))
        if before:
            print(canonical(before))
        restore_hash = backup_manifest(job["payload"]) if job["action"] == "restore" else None
        if restore_hash:
            print(canonical({"backup_manifest_hash": restore_hash}))
        print("Live change may restart services or migrate data. Review backup/rollback first.")
        if input("Type the full job SHA256 to authorize this exact operation: ").strip() != expected_hash:
            raise PermissionError("NOT_APPROVED")
        proof = {"id": identifier, "hash": expected_hash, "expires": time.time() + 21600, "operator": getpass.getuser()}
        if before:
            proof["before_hash"] = before["hash"]
        if job["action"] == "release":
            proof["deployment_hash"] = deployment
        if restore_hash:
            proof["backup_manifest_hash"] = restore_hash
        signature = hmac.new(self.key, canonical(proof).encode(), hashlib.sha256).hexdigest()
        path = self.runtime / "operator" / f"{identifier}.approval.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(canonical({"proof": proof, "signature": signature}), encoding="utf-8")
        temporary.replace(path)

    def authorized(self, job):
        path = self.runtime / "operator" / f"{job['id']}.approval.json"
        if not path.exists():
            raise PermissionError("LOCAL_APPROVAL_REQUIRED")
        record = json.loads(path.read_text())
        expected = hmac.new(self.key, canonical(record["proof"]).encode(), hashlib.sha256).hexdigest()
        proof = record["proof"]
        if (not hmac.compare_digest(expected, record["signature"]) or proof["id"] != job["id"] or
                proof["hash"] != job["hash"] or proof["expires"] <= time.time()):
            raise PermissionError("APPROVAL_INVALID_OR_EXPIRED")
        return proof

    def admin(self, request):
        path = self.runtime / "operator" / f"admin-{uuid.uuid4()}.json"
        path.write_text(canonical(request), encoding="utf-8")
        argv = ["docker", "compose", "--project-name", "qldapm-openproject", "--env-file", str(PROJECT_RUNTIME / ".env"),
                "-f", str(ROOT.parent / "compose.yml")]
        active = PROJECT_RUNTIME / "active-volumes.yml"
        if active.exists():
            argv += ["-f", str(active)]
        bridge = PROJECT_RUNTIME / "ui-bridge.yml"
        if bridge.exists():
            argv += ["-f", str(bridge)]
        argv += ["run", "--rm", "--no-deps", "-v", f"{self.runtime / 'operator'}:/operator",
                 "-v", f"{ROOT / 'core'}:/trusted:ro", "-e", f"QLDAPM_REQUEST=/operator/{path.name}",
                 "web", "bundle", "exec", "rails", "runner", "/trusted/admin_operation.rb"]
        return run(argv, timeout=300)

    def configuration(self, job):
        output = self.admin({"action": "inspect", "parameters": {}, "actor": job["actor"]})
        return json.loads(next(line for line in reversed(output.splitlines()) if line.startswith('{"configuration"')))

    def snapshot(self, actor, fingerprint, job_id):
        if self.workspace.tree_hash(actor) != fingerprint:
            raise ValueError("WORKSPACE_CHANGED_SINCE_PROPOSAL")
        target = self.runtime / "snapshots" / job_id / str(actor)
        if target.exists():
            raise ValueError("SNAPSHOT_ALREADY_EXISTS")
        shutil.copytree(self.runtime / "workspaces" / str(actor), target)
        if Workspace(target.parent).tree_hash(actor) != fingerprint:
            raise ValueError("SNAPSHOT_RACED_WITH_WRITE")
        # Windows checkout CRLF breaks multiline ERB compilation; canonicalize only the private Linux test copy.
        for path in target.rglob("*"):
            if path.is_file() and path.suffix in {".rb", ".erb", ".rake"}:
                data = path.read_bytes()
                if b"\r\n" in data:
                    path.write_bytes(data.replace(b"\r\n", b"\n"))
        return target

    def test(self, job):
        payload = job["payload"]
        if set(payload) not in ({"suite", "snapshot_hash", "workspace_actor"},
                {"suite", "snapshot_hash", "workspace_actor", "project_id", "work_package_id", "gate_revision"}):
            raise ValueError("TEST_PARAMETERS_DENIED")
        if "work_package_id" in payload and payload["suite"] == "gateway":
            raise ValueError("WORKSPACE_TEST_RECEIPT_REQUIRED")
        source_actor = int(payload["workspace_actor"])
        config = json.loads((self.runtime / "gateway/config.json").read_text())
        if str(source_actor) not in config["users"]:
            raise ValueError("WORKSPACE_ACTOR_DENIED")
        # Hash on the host, not during HTTP over Docker's slow Windows bind mount.
        fingerprint = self.workspace.tree_hash(source_actor) if payload["snapshot_hash"] == "AT_EXECUTION" else payload["snapshot_hash"]
        snapshot = self.snapshot(source_actor, fingerprint, job["id"])
        name = "qldapm-ai-test-" + job["id"]
        common = ["docker", "run", "--rm", "--name", name, "--network", "none", "--cpus", "2", "--memory", "4g",
                  "--pids-limit", "256", "--user", "1000:1000", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--read-only",
                  "--tmpfs", "/tmp:size=128m", "--mount", f"type=bind,source={snapshot},target=/snapshot,readonly",
                  "--mount", f"type=bind,source={ROOT},target=/trusted,readonly"]
        try:
            if payload["suite"] == "gate-policy":
                # Tests are trusted; only the implementation is selected from the actor's immutable snapshot.
                output = run(common + ["--entrypoint", "ruby", "-e", "QLDAPM_POLICY=/snapshot/app/models/qldapm/gate_policy.rb",
                                       BASE_IMAGE, "/trusted/core/test_policy.rb"])
            elif payload["suite"] == "gateway":
                images = self.test_images or json.loads((self.runtime / "image-lock.json").read_text())
                image = images["AI_IMAGE"]
                if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
                    raise ValueError("PINNED_GATEWAY_IMAGE_REQUIRED")
                output = run(common + ["--entrypoint", "python", "--tmpfs", "/app/tmp",
                    "--mount", f"type=bind,source={ROOT.parent / 'scripts'},target=/scripts,readonly",
                    "-e", "PYTHONPATH=/app:/trusted", "-e", "QLDAPM_AI_RUNTIME=", "-e", "LOCALAPPDATA=/tmp",
                    image, "-m", "unittest", "discover", "-s", "/trusted/tests", "-v"])
            elif payload["suite"] == "core-integration":
                output = isolated_core(snapshot, job["id"], self.runtime, self.test_images)
            else:
                raise ValueError("TEST_SUITE_DENIED")
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "stop", "--time", "2", name], capture_output=True)
            raise RuntimeError("TEST_TIMEOUT") from None
        result = {"suite": payload["suite"], "workspace_actor": source_actor, "snapshot_hash": fingerprint,
                  "normalized_snapshot_hash": Workspace(snapshot.parent).tree_hash(source_actor), "output": output, "passed": True}
        if "work_package_id" in payload:
            result["attestation"] = self.test_attestation(job, result)
        return result

    def test_attestation(self, job, result):
        if job["payload"]["suite"] not in {"gate-policy", "core-integration"}:
            raise ValueError("WORKSPACE_TEST_RECEIPT_REQUIRED")
        key_path = self.runtime / "operator/test-receipt.key"
        if not key_path.is_file():
            raise PermissionError("PREPARE_LOCAL_TEST_RECEIPT_KEY_FIRST")
        proof = {"job_id": job["id"], "actor_id": job["actor"], **{k: job["payload"][k] for k in
            ("project_id", "work_package_id", "gate_revision", "suite", "workspace_actor")},
            "snapshot_hash": result["snapshot_hash"], "output_hash": digest(result["output"]), "passed": result["passed"],
            "finished_at": int(time.time())}
        return {"proof": proof, "signature": hmac.new(key_path.read_bytes(), canonical(proof).encode(), hashlib.sha256).hexdigest()}

    def process(self, identifier):
        job = self.inspect(identifier)
        unresolved = self.store.broker_job("unresolved")
        if unresolved:
            raise PermissionError("OPERATOR_RECONCILIATION_REQUIRED: " + unresolved["id"])
        config = json.loads((self.runtime / "gateway/config.json").read_text())
        actor = job["actor"]
        # Read-only native identity remains verifiable while the UI proxy is in maintenance.
        native = BackendNative("http://web:8080", self.store.credential(actor), config["project_id"])
        who = native.identity(actor)
        if str(actor) not in config["users"] or who["role"] != config["users"][str(actor)]:
            raise PermissionError("CURRENT_MEMBERSHIP_REQUIRED")
        if job["action"] != "test":
            if who["role"] != "PM":
                raise PermissionError("PM_REQUIRED")
            job["approval"] = self.authorized(job)
        elif who["role"] != "PM":
            raise PermissionError("TEST_ROLE_REQUIRED")
        self.store.broker_job("claim", identifier)
        try:
            result = self.test(job) if job["action"] == "test" else self.operation(job)
            state = "done"
        except Exception as error:
            result, state = {"error": type(error).__name__, "message": str(error)[:3000]}, "failed_or_unknown"
        proof = {"id": identifier, "job_hash": job["hash"], "actor": actor, "action": job["action"],
                 "payload": job["payload"], "state": state, "result": result, "queue_confirmation_required": True}
        signature = hmac.new(self.key, canonical(proof).encode(), hashlib.sha256).hexdigest()
        path = self.runtime / "operator" / f"{identifier}.result.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(canonical({"proof": proof, "signature": signature}), encoding="utf-8")
        temporary.replace(path)
        # Persist host evidence before a release may leave the gateway stopped or unreachable.
        self.store.broker_job("finish", identifier, state, result)
        self.store.record(actor, "broker_" + job["action"], identifier, state)
        print(canonical({"id": identifier, "state": state, "result": result}))

    def resolve(self, identifier, expected_hash):
        job = self.inspect(identifier)
        if job["hash"] != expected_hash or job["state"] not in {"running", "failed_or_unknown"}:
            raise ValueError("EXACT_UNKNOWN_JOB_REQUIRED")
        if job["state"] == "running":
            receipt_path = self.runtime / "operator" / (identifier + ".result.json")
            if not receipt_path.is_file():
                raise PermissionError("RUNNING_JOB_WITHOUT_RECEIPT_DENIED")
            receipt = json.loads(receipt_path.read_text())
            signature = hmac.new(self.key, canonical(receipt["proof"]).encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, receipt["signature"]) or receipt["proof"]["id"] != identifier or receipt["proof"]["job_hash"] != expected_hash:
                raise PermissionError("INVALID_OPERATOR_RESULT_RECEIPT")
        print(canonical({k: job[k] for k in ("id", "action", "actor", "hash", "state")}))
        print("Confirm actual Docker/native state and rollback first. This acknowledges the outcome; it never retries the job.")
        if input("Type the full job SHA256 after local reconciliation: ").strip() != expected_hash:
            raise PermissionError("NOT_RECONCILED")
        self.store.broker_job("reconcile", identifier)
        proof = {"id": identifier, "job_hash": expected_hash, "operator": getpass.getuser(), "at": time.time(), "outcome": "operator_reconciled"}
        path = self.runtime / "operator" / (identifier + ".reconciliation.json")
        path.write_text(canonical({"proof": proof, "signature": hmac.new(self.key, canonical(proof).encode(), hashlib.sha256).hexdigest()}), encoding="utf-8")
        self.store.record(None, "operator_reconciliation", identifier, "acknowledged_not_retried")

    def watch(self):
        last_error = {}
        stop = self.runtime / "operator/broker.stop"
        while not stop.exists():
            queued = self.store.broker_job("queued")
            for row in queued:
                if stop.exists():
                    return
                identifier = row["id"]
                if row["action"] != "test" and not (self.runtime / "operator" / f"{identifier}.approval.json").exists():
                    continue
                try:
                    self.process(identifier)
                    last_error.pop(identifier, None)
                except Exception as error:
                    if last_error.get(identifier) != str(error):
                        print(canonical({"id": identifier, "waiting": str(error)[:300]}), flush=True)
                        last_error[identifier] = str(error)
            time.sleep(5)

    def operation(self, job):
        action, parameters = job["action"], job["payload"]
        manage = ROOT.parents[0] / "Manage-OpenProject.ps1"
        if action in {"backup", "start", "stop", "restore"}:
            argv = [powershell(), "-NoProfile", "-File", str(manage), "-Action", action.title()]
            if action == "restore":
                proof = self.authorized(job)
                if backup_manifest(parameters) != proof.get("backup_manifest_hash"):
                    raise PermissionError("APPROVED_BACKUP_MANIFEST_CHANGED")
                ServiceArguments.exact(parameters, {"backup_path"})
                backup = Path(parameters["backup_path"]).resolve()
                if not backup.is_relative_to((PROJECT_RUNTIME / "backups").resolve()):
                    raise ValueError("BACKUP_PATH_DENIED")
                run([powershell(), "-NoProfile", "-File", str(manage), "-Action", "Backup"], timeout=1800)
                argv += ["-BackupPath", str(backup), "-ReplaceLocalData"]
            else:
                ServiceArguments.exact(parameters, set())
                if action == "start":
                    argv += ["-LocalOnly"]
            return {"operation": action, "output": run(argv, timeout=1800)}
        if action in ADMIN_ACTIONS:
            proof = job["approval"]
            if self.configuration(job)["hash"] != proof.get("before_hash"):
                raise ValueError("CONFIGURATION_CHANGED_SINCE_APPROVAL")
            # A backup precedes every approved administrative mutation.
            run([powershell(), "-NoProfile", "-File", str(manage), "-Action", "Backup"], timeout=1800)
            output = self.admin({"action": action, "parameters": parameters, "actor": job["actor"],
                                 "before_hash": proof["before_hash"]})
            return {"operation": action, "output": output}
        if action == "build":
            ServiceArguments.exact(parameters, {"workspace_actor", "snapshot_hash"})
            actor = int(parameters["workspace_actor"])
            config = json.loads((self.runtime / "gateway/config.json").read_text())
            if config["users"].get(str(actor)) not in {"BE", "FE"}:
                raise ValueError("DEVELOPER_WORKSPACE_REQUIRED")
            snapshot = self.snapshot(actor, parameters["snapshot_hash"], job["id"])
            tag = "qldapm-openproject:ai-" + job["id"]
            output = run(["docker", "build", "-f", str(ROOT.parent / "upstream/openproject/docker/prod/Dockerfile"),
                          "-t", tag, str(snapshot)], timeout=1800)
            image = run(["docker", "image", "inspect", "--format", "{{.Id}}", tag]).strip()
            return {"image": image, "source_hash": parameters["snapshot_hash"], "output": output}
        if action == "release":
            qualification = verify_candidate(self.runtime, self.key, parameters)
            proof = self.authorized(job)
            if self.configuration(job)["hash"] != proof.get("before_hash"):
                raise ValueError("CONFIGURATION_CHANGED_SINCE_APPROVAL")
            if deployment_hash(self.runtime, PROJECT_RUNTIME) != proof.get("deployment_hash"):
                raise PermissionError("APPROVED_DEPLOYMENT_CHANGED")
            return {"operation": action, "commit": qualification["commit"], "image": qualification["image"],
                    "gateway_image": qualification["gateway_image"],
                    "output": run([powershell(), "-NoProfile", "-File", str(ROOT / "Release-OpenProjectAI.ps1"),
                                   "-Image", qualification["image"], "-GatewayImage", qualification["gateway_image"], "-ReleaseId", job["id"],
                                   "-BeforeHash", proof["before_hash"], "-DeploymentHash", proof["deployment_hash"],
                                   "-ActorId", str(job["actor"])], timeout=3600)}
        raise ValueError("OPERATION_DENIED")


class ServiceArguments:
    @staticmethod
    def exact(parameters, fields):
        if set(parameters) != fields:
            raise ValueError("OPERATOR_PARAMETERS_DENIED")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preview", "approve", "process", "watch", "resolve"])
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--job")
    parser.add_argument("--hash")
    parser.add_argument("--offline-state", action="store_true", help="explicit preview/resolve after Stop; never processes jobs")
    args = parser.parse_args()
    if args.offline_state:
        if args.action not in {"preview", "resolve"}:
            raise PermissionError("OFFLINE_PREVIEW_OR_RESOLVE_ONLY")
        image = json.loads((Path(args.runtime) / "image-lock.json").read_text())["AI_IMAGE"]
        store = OfflineState(Path(args.runtime) / "gateway", image)
    else:
        store = ContainerState(Path(args.runtime) / "gateway")
    broker = Broker(args.runtime, store=store)
    if args.action in {"preview", "approve"}:
        if args.action == "preview":
            job = broker.inspect(args.job)
            print(canonical({k: job[k] for k in ("id", "actor", "action", "payload", "hash", "state")}))
        else:
            broker.approve(args.job, args.hash)
        return
    lock_path = Path(args.runtime) / "operator/broker.lock"
    with lock_path.open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        if args.action == "watch":
            broker.watch()
        elif args.action == "resolve":
            broker.resolve(args.job, args.hash)
        else:
            broker.process(args.job)


if __name__ == "__main__":
    main()

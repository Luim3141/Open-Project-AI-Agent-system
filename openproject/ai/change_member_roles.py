"""Fixed owner-only role correction. No HTTP/MCP route; human types the exact hash locally."""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from contextlib import ExitStack, closing
from pathlib import Path

from gateway.store import canonical, digest
from operator_state import require_offline

ROOT = Path(__file__).resolve().parent
RUNTIME = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
PROJECT = RUNTIME.parent / "openproject"
SCRIPT = ROOT.parent / "scripts/change-member-roles.rb"
DESIRED = {"19": "PM", "20": "BA"}
FILES = [PROJECT / "accounts.json", PROJECT / "bootstrap.json", RUNTIME / "gateway/config.json",
         RUNTIME / ".env", RUNTIME / "image-lock.json"]


def run(*args):
    result = subprocess.run(args, capture_output=True, timeout=300)
    if result.returncode:
        raise RuntimeError("OPERATION_FAILED; inspect private backup, never paste credential-bearing output")
    return result.stdout.decode().strip()


def native(mode="preview", before_hash=None):
    args = ["docker", "exec", "-e", "QLDAPM_ROLE_MODE=" + mode]
    if before_hash:
        args += ["-e", "QLDAPM_ROLE_BEFORE_HASH=" + before_hash]
    output = run(*args, "qldapm-openproject-web-1", "bundle", "exec", "rails", "runner", "/qldapm/change-member-roles.rb")
    return json.loads(output.splitlines()[-1])


def file_hashes():
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in FILES + [SCRIPT, Path(__file__), ROOT / "gateway/native.py"]}


def write_json(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(canonical(data), encoding="utf-8")
    temporary.replace(path)


def synchronize(accounts, bootstrap, config):
    expected = {"hiepk40c@gmail.com": (19, "PM"), "2101minhkhai@gmail.com": (20, "BA")}
    matched = set()
    for account in accounts["users"]:
        email = account["email"].lower()
        if email in expected:
            actor, role = expected[email]
            if bootstrap["users"][email] != actor:
                raise ValueError("IDENTITY_MAPPING_CHANGED")
            account["role"] = role
            matched.add(email)
    if matched != set(expected) or config["project_id"] != 5:
        raise ValueError("WRONG_INSTANCE_OR_ACCOUNTS")
    config["users"].update(DESIRED)
    if "BA-PM" in bootstrap.get("roles", {}):
        bootstrap["roles"]["BA"] = bootstrap["roles"].pop("BA-PM")
    return accounts, bootstrap, config


def preview():
    current = native()
    if current["before"]["project_id"] != 5 or [u["id"] for u in current["before"]["users"]] != [19, 20]:
        raise ValueError("WRONG_INSTANCE")
    image = run("docker", "image", "inspect", "--format", "{{.Id}}", "qldapm-ai:role-change")
    if not image.startswith("sha256:"):
        raise ValueError("CANDIDATE_IMAGE_REQUIRED")
    native_hash = run("docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL",
                      "--entrypoint", "python", image, "-c",
                      "import hashlib; print(hashlib.sha256(open('/app/gateway/native.py','rb').read()).hexdigest())")
    if native_hash != hashlib.sha256((ROOT / "gateway/native.py").read_bytes()).hexdigest():
        raise ValueError("CANDIDATE_SOURCE_MISMATCH")
    packet = {"native": current, "files": file_hashes(), "image": image, "desired": DESIRED,
              "expires": time.time() + 3600}
    packet["hash"] = digest(canonical(packet))
    path = RUNTIME / "operator" / ("member-role-change-" + uuid.uuid4().hex + ".json")
    write_json(path, packet)
    print(canonical({"preview": str(path), "hash": packet["hash"], "image": image, "desired": DESIRED,
                     "apply": "python change_member_roles.py apply --preview PRIVATE_PREVIEW_PATH",
                     "live_changed": False}))


def apply(path):
    path = Path(path).resolve()
    if path.parent != (RUNTIME / "operator").resolve() or not path.name.startswith("member-role-change-"):
        raise ValueError("PREVIEW_PATH_DENIED")
    packet = json.loads(path.read_text())
    expected_hash = packet.pop("hash")
    if digest(canonical(packet)) != expected_hash or packet["expires"] < time.time() or packet["desired"] != DESIRED:
        raise ValueError("PREVIEW_CHANGED_OR_EXPIRED")
    if not sys.stdin.isatty():
        raise PermissionError("HUMAN_LOCAL_CONSOLE_REQUIRED")
    print(canonical({"hash": expected_hash, "desired": DESIRED, "image": packet["image"],
                     "impact": "rename BA role, swap membership, synchronize runtime, replace AI gateway only",
                     "unchanged": "emails/logins/password/TOTP/tokens/329 work packages/Jira/core image"}))
    if input("Type the exact hash to approve this live change: ").strip() != expected_hash:
        raise PermissionError("APPROVAL_MISMATCH")
    # Match the broker lock and the existing project-manager leases. Never kill a running job.
    import msvcrt
    with ExitStack() as stack:
        for lease in [RUNTIME / "operator/broker.lock", PROJECT / "operator.lock", PROJECT / "release.lock"]:
            handle = stack.enter_context(lease.open("a+b"))
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        require_offline("qldapm-ai-gateway-1")
        with closing(sqlite3.connect(RUNTIME / "gateway/gateway.sqlite")) as db:
            if db.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('done')").fetchone()[0]:
                raise ValueError("PENDING_JOB_REQUIRES_OPERATOR_RECONCILIATION")
        if file_hashes() != packet["files"] or native()["before_hash"] != packet["native"]["before_hash"]:
            raise ValueError("STATE_CHANGED_CREATE_NEW_PREVIEW")
        image = run("docker", "image", "inspect", "--format", "{{.Id}}", packet["image"])
        if image != packet["image"]:
            raise ValueError("IMAGE_CHANGED")
        accounts, bootstrap, config = synchronize(*[json.loads(p.read_text()) for p in FILES[:3]])
        backup = path.with_suffix("")
        backup.mkdir()
        for index, file in enumerate(FILES):
            shutil.copy2(file, backup / (str(index) + "-" + file.name))
        with closing(sqlite3.connect(RUNTIME / "gateway/gateway.sqlite")) as source, closing(sqlite3.connect(backup / "gateway.sqlite")) as target:
            source.backup(target)
        with (backup / "database.dump").open("wb") as dump:
            result = subprocess.run(["docker", "exec", "qldapm-openproject-db-1", "pg_dump", "-U", "postgres", "-Fc", "openproject"],
                                    stdout=dump, stderr=subprocess.PIPE, timeout=300)
        if result.returncode:
            raise RuntimeError("BACKUP_FAILED_NO_MUTATION")
        compose = ["docker", "compose", "--project-name", "qldapm-ai", "--env-file", str(RUNTIME / ".env"), "-f", str(ROOT / "compose.yml")]
        run(*compose, "--profile", "public", "stop", "tunnel", "gateway")
        write_json(backup / "approval.json", {"hash": expected_hash, "approved_at": time.time(), "status": "approved"})
        # Partial failures deliberately leave AI stopped. Do not retry with a new approval or restore blindly.
        result = native("apply", packet["native"]["before_hash"])
        write_json(backup / "native-result.json", result)
        for file, data in zip(FILES[:3], [accounts, bootstrap, config]):
            write_json(file, data)
        env = FILES[3].read_text().splitlines()
        if sum(line.startswith("AI_IMAGE=") for line in env) != 1:
            raise ValueError("ENV_IMAGE_AMBIGUOUS_AI_REMAINS_STOPPED")
        temporary = FILES[3].with_suffix(".tmp")
        temporary.write_text("\n".join("AI_IMAGE=" + packet["image"] if line.startswith("AI_IMAGE=") else line for line in env) + "\n")
        temporary.replace(FILES[3])
        manifest = json.loads(FILES[4].read_text())
        manifest["AI_IMAGE"] = packet["image"]
        write_json(FILES[4], manifest)
        with closing(sqlite3.connect(RUNTIME / "gateway/gateway.sqlite")) as db, db:
            db.executemany("UPDATE tokens SET role=? WHERE user_id=?", [(role, int(actor)) for actor, role in DESIRED.items()])
        write_json(backup / "completed.json", {"applied": True, "gateway_restart_required": True, "desired": DESIRED})
        print(canonical({"applied": True, "backup": str(backup), "desired": DESIRED,
                         "next": "Manage-OpenProjectAI.ps1 -Action Start -LocalOnly; verify real identities"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preview", "apply"])
    parser.add_argument("--preview")
    args = parser.parse_args()
    try:
        preview() if args.action == "preview" else apply(args.preview)
    except Exception as error:
        print(canonical({"failed": True, "error_type": type(error).__name__, "live_applied_not_assumed": True}))
        sys.exit(1)

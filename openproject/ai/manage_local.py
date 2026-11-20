"""Local credential registration only. Never exposed as an HTTP/MCP tool."""
import argparse
import getpass
import json
import os
import secrets
import shutil
import subprocess
import hashlib
from pathlib import Path

from gateway.native import Native
from gateway.store import Store, canonical
from gateway.workspace import Workspace
from operator_state import ContainerState, require_offline

MAIN_HOSTS = ["127.0.0.1:18089", "localhost:18089", "127.0.0.1:8090", "localhost:8090",
              "gateway:8090", "qldapm-ai-gateway-1:8090"]


def initialize(runtime, project_runtime):
    runtime = Path(runtime)
    state = runtime / "gateway"
    state.mkdir(parents=True, exist_ok=True)
    bootstrap = json.loads((Path(project_runtime) / "bootstrap.json").read_text())
    accounts = json.loads((Path(project_runtime) / "accounts.json").read_text())
    roles = {str(bootstrap["users"][account["email"].lower()]): account["role"] for account in accounts["users"]}
    config = {"project_id": bootstrap["project_id"], "users": roles, "openproject_url": "http://web:8080",
              "source_field": bootstrap["fields"]["Source ID"], "type_ids": list(bootstrap["types"].values()),
              "status_ids": list(bootstrap["statuses"].values()),
              "hosts": MAIN_HOSTS.copy(), "maintenance": False}
    if not (state / "config.json").exists():
        (state / "config.json").write_text(canonical(config), encoding="utf-8")
    if not (state / "credentials.json").exists():
        (state / "credentials.json").write_text("{}", encoding="utf-8")
    Store(state)
    for folder in ("workspaces", "operator", "stage", "snapshots"):
        (runtime / folder).mkdir(exist_ok=True)
    key = runtime / "operator" / "approval.key"
    if not key.exists():
        key.write_text(secrets.token_hex(32), encoding="utf-8")
    stage = runtime / "stage"
    if not (stage / "accounts.json").exists():
        fake = {"admin": {"login": "stage-owner", "password": "Aa1!" + secrets.token_urlsafe(24)}, "users": [
            {"login": account["login"], "role": account["role"], "email": account["login"] + "@stage.invalid",
             "password": "Aa1!" + secrets.token_urlsafe(24)} for account in accounts["users"]]}
        (stage / "accounts.json").write_text(canonical(fake), encoding="utf-8")
    # WBS contains business data only. Production identities/tokens/TOTP are never copied to staging.
    source = Path(project_runtime) / "wbs-snapshot.csv"
    (stage / "wbs-snapshot.csv").write_bytes(source.read_bytes())


def environment(runtime, project_runtime):
    runtime = Path(runtime)
    source = dict(line.split("=", 1) for line in (Path(project_runtime) / ".env").read_text().splitlines() if "=" in line)
    image = lambda name: subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", name], text=True).strip()
    path = runtime / ".env"
    old = dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line) if path.exists() else {}
    values = {"AI_RUNTIME": runtime.as_posix(), "AI_IMAGE": image("qldapm-ai:gateway"),
              "CORE_IMAGE": image("qldapm-openproject:17.9.1-gates"), "CLOUDFLARED_IMAGE": source["CLOUDFLARED_IMAGE"],
              "POSTGRES_IMAGE": source["POSTGRES_IMAGE"], "POSTGRES_PASSWORD": old.get("POSTGRES_PASSWORD", secrets.token_hex(24)),
              "SECRET_KEY_BASE": old.get("SECRET_KEY_BASE", secrets.token_hex(64))}
    path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")
    manifest = {key: value for key, value in values.items() if key.endswith("IMAGE")}
    (runtime / "image-lock.json").write_text(canonical(manifest), encoding="utf-8")


def workspaces(runtime, source):
    config = json.loads((Path(runtime) / "gateway/config.json").read_text())
    manifest_path = Path(runtime) / "operator/workspace-baselines.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for actor in config["users"]:
        target = Path(runtime) / "workspaces" / actor
        if not target.exists():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns(".git", ".env*", "node_modules", "log", "tmp", "vendor"))
        overlay = Path(__file__).parent / "core/overlay"
        upstream = Path(__file__).parent.parent / "upstream/openproject"
        for item in overlay.rglob("*"):
            if not item.is_file():
                continue
            relative = item.relative_to(overlay).as_posix()
            destination = Workspace(Path(runtime) / "workspaces").path(actor, relative)
            fingerprint = hashlib.sha256(item.read_bytes()).hexdigest()
            previous = manifest.get(actor, {}).get(relative)
            if destination.exists() and destination.read_bytes() == item.read_bytes():
                manifest.setdefault(actor, {})[relative] = fingerprint
                continue
            baseline = upstream / relative
            if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != previous and (not baseline.exists() or destination.read_bytes() != baseline.read_bytes()):
                raise ValueError(f"WORKSPACE_ALREADY_EDITED: actor={actor} path={relative}; merge manually")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)
            manifest.setdefault(actor, {})[relative] = fingerprint
        print(f"Actor {actor}: isolated workspace prepared")
    temporary = manifest_path.with_suffix(".tmp")
    temporary.write_text(canonical(manifest), encoding="utf-8")
    temporary.replace(manifest_path)


def register(runtime, user_id):
    state = Path(runtime) / "gateway"
    config = json.loads((state / "config.json").read_text())
    if str(user_id) not in config["users"]:
        raise ValueError("ONLY_THE_FIVE_MEMBERS_CAN_REGISTER")
    credential = getpass.getpass("OpenProject API token (hidden; no password): ")
    native = Native("http://127.0.0.1:18088", credential, config["project_id"])
    identity = native.identity(user_id)
    if identity["role"] != config["users"][str(user_id)]:
        raise ValueError("ROLE_MISMATCH")
    bearer = ContainerState(state).call("issue_token", user_id=user_id, role=identity["role"], op_token=credential)
    output = Path(runtime) / "operator" / f"user-{user_id}.token"
    output.write_text(bearer, encoding="utf-8")
    print(f"Registered user {user_id}. Private token file: {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["initialize", "register", "revoke", "hosts", "environment", "workspaces"])
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--project-runtime")
    parser.add_argument("--user-id", type=int)
    parser.add_argument("--host")
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.action == "initialize":
        require_offline("qldapm-ai-gateway-1")
        initialize(args.runtime, args.project_runtime)
    elif args.action == "register":
        register(args.runtime, args.user_id)
    elif args.action == "environment":
        environment(args.runtime, args.project_runtime)
    elif args.action == "workspaces":
        workspaces(args.runtime, args.source)
    elif args.action == "revoke":
        token = getpass.getpass("Gateway token to revoke: ")
        ContainerState(Path(args.runtime) / "gateway").call("revoke_token", token=token)
    elif args.action == "hosts":
        path = Path(args.runtime) / "gateway/config.json"
        config = json.loads(path.read_text())
        config["hosts"] = MAIN_HOSTS + ([args.host] if args.host else [])
        config["maintenance"] = False
        temporary = path.with_suffix(".tmp")
        temporary.write_text(canonical(config), encoding="utf-8")
        temporary.replace(path)


if __name__ == "__main__":
    main()

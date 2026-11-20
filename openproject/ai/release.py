"""Local qualification and sealed evidence; no HTTP/MCP enrollment or approval surface."""
import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

from gateway.store import canonical, digest

ROOT = Path(__file__).resolve().parent
FORK = ROOT.parent / "development/core"
UPSTREAM = "c7ec3efaeb2740944b0368b267901b568d6f2144"


def deployment_hash(runtime, project):
    manifest = []
    files = {Path(runtime): (".env", "image-lock.json", "gateway/config.json", "gateway/credentials.json",
                            "gateway/ui.key", "gateway/gemini.json", "gateway/gemini.key",
                            "operator/gemini-free/production-proof.json", "operator/test-receipt.key"),
             Path(project): (".env", "active-volumes.yml", "ui-bridge.yml")}
    for base, names in files.items():
        for name in names:
            path = base / name
            if any(parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction())
                   for parent in (path, *path.parents)):
                raise PermissionError("DEPLOYMENT_FILE_DENIED")
            if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
                raise PermissionError("DEPLOYMENT_FILE_DENIED")
            manifest.append((str(path), hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None))
    return digest(canonical(manifest))


def verify_proof(operator, key, parameters):
    if set(parameters) != {"qualification_id", "qualification_hash"} or not re.fullmatch(
            r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", str(parameters["qualification_id"])):
        raise ValueError("QUALIFICATION_PARAMETERS_DENIED")
    path = Path(operator) / (parameters["qualification_id"] + ".qualification.json")
    if not path.is_file():
        raise PermissionError("QUALIFICATION_REQUIRED")
    record = json.loads(path.read_text())
    proof = record["proof"]
    signature = hmac.new(key, canonical(proof).encode(), hashlib.sha256).hexdigest()
    if (not hmac.compare_digest(signature, record["signature"]) or proof.get("id") != parameters["qualification_id"] or
            digest(canonical(proof)) != parameters["qualification_hash"] or proof.get("passed") is not True or
            proof.get("expires", 0) <= time.time() or
            not re.fullmatch(r"sha256:[a-f0-9]{64}", str(proof.get("gateway_image", "")))):
        raise PermissionError("QUALIFICATION_INVALID_OR_EXPIRED")
    return proof


def execute(argv, timeout=900, env=None):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout, env=env)
    if result.returncode:
        raise RuntimeError("QUALIFICATION_CHECK_FAILED: " + " ".join(argv[:3]) + "\n" +
                           (result.stdout + result.stderr)[-5000:])
    return result.stdout


def candidate(runtime):
    commit = execute(["git", "-C", str(FORK), "rev-parse", "HEAD"]).strip()
    if execute(["git", "-C", str(FORK), "status", "--porcelain"]):
        raise ValueError("CLEAN_COMMITTED_CORE_REQUIRED")
    overlay = ROOT / "core/overlay"
    paths = {p.relative_to(overlay).as_posix() for p in overlay.rglob("*") if p.is_file()}
    changed = set(execute(["git", "-C", str(FORK), "diff", "--name-only", UPSTREAM, commit]).splitlines())
    if not changed <= paths:
        raise ValueError("FULL_CORE_BUILD_QUALIFICATION_REQUIRED_FOR_NON_OVERLAY_CHANGES")
    for relative in paths:
        if (FORK / relative).read_bytes().replace(b"\r\n", b"\n") != (overlay / relative).read_bytes().replace(b"\r\n", b"\n"):
            raise ValueError("FORK_OVERLAY_MISMATCH: " + relative)
    image = execute(["docker", "inspect", "--format", "{{.Image}}", "qldapm-ai-stage-staging-web-1"]).strip()
    gateway_image = execute(["docker", "inspect", "--format", "{{.Image}}", "qldapm-ai-stage-staging-gateway-1"]).strip()
    if any(not re.fullmatch(r"sha256:[a-f0-9]{64}", value) for value in (image, gateway_image)):
        raise ValueError("PINNED_STAGING_IMAGES_REQUIRED")
    execute(["docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges:true", "--mount", f"type=bind,source={ROOT / 'gateway'},target=/trusted,readonly",
             "--entrypoint", "python", gateway_image, "-c",
             "from pathlib import Path; import hashlib; "
             "files=list(Path('/trusted').glob('*.py')); assert files; "
             "assert {p.name for p in files}=={p.name for p in Path('/app/gateway').glob('*.py')}; "
             "assert all(hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((Path('/app/gateway')/p.name).read_bytes()).digest() for p in files)"])
    # Verify the immutable image contains the exact overlay being qualified.
    execute(["docker", "run", "--rm", "--network", "none", "--user", "1000:1000", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges:true", "--mount", f"type=bind,source={ROOT / 'core'},target=/trusted,readonly",
             "--entrypoint", "ruby", image, "/trusted/image_manifest.rb"], timeout=60)
    paths = sorted(p for p in ROOT.rglob("*") if p.is_file() and
                   not any(part in {".venv", "__pycache__", ".git"} for part in p.relative_to(ROOT).parts) and
                   p.suffix in {".py", ".rb", ".erb", ".ps1", ".yml", ".txt"})
    manifest = [(p.relative_to(ROOT).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    manifest.append(("core/Dockerfile", hashlib.sha256((ROOT / "core/Dockerfile").read_bytes()).hexdigest()))
    manifest.append(("Dockerfile", hashlib.sha256((ROOT / "Dockerfile").read_bytes()).hexdigest()))
    manifest.append(("Dockerfile.gateway-patch", hashlib.sha256((ROOT / "Dockerfile.gateway-patch").read_bytes()).hexdigest()))
    for path in sorted((ROOT.parent / "scripts").rglob("*")):
        if path.is_file() and path.suffix in {".py", ".rb"}:
            manifest.append(("../scripts/" + path.relative_to(ROOT.parent / "scripts").as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    for name in ("Manage-OpenProject.ps1", "compose.yml", "Caddyfile"):
        manifest.append(("../" + name, hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest()))
    return {"commit": commit, "image": image, "gateway_image": gateway_image, "harness_hash": digest(canonical(manifest)),
            "migration_hash": hashlib.sha256((ROOT / "core/migrate_snapshot.rb").read_bytes()).hexdigest()}


def verify_candidate(runtime, key, parameters):
    proof = verify_proof(Path(runtime) / "operator", key, parameters)
    current = candidate(runtime)
    if any(proof.get(field) != value for field, value in current.items()):
        raise PermissionError("QUALIFIED_CANDIDATE_CHANGED")
    restore_path = Path(proof["restore_evidence"]).resolve()
    if not restore_path.is_relative_to((Path(runtime) / "stage-backups").resolve()) or hashlib.sha256(
            restore_path.read_bytes()).hexdigest() != proof["restore_hash"]:
        raise PermissionError("RESTORE_EVIDENCE_CHANGED")
    return proof


def qualify(runtime):
    runtime = Path(runtime)
    original = candidate(runtime)
    key = (runtime / "operator/approval.key").read_bytes()
    identifier = str(uuid.uuid4())
    folder = runtime / "operator/qualifications" / identifier
    folder.mkdir(parents=True)
    compose = ["docker", "compose", "--project-name", "qldapm-ai-stage", "--env-file", str(runtime / ".env"),
               "-f", str(ROOT / "stage.yml"), "-f", str(ROOT / "deep-ai.stage.yml")]
    python = str(ROOT / ".venv/Scripts/python.exe")
    checks = {}
    environment = {**os.environ, "CORE_IMAGE": original["image"], "AI_IMAGE": original["gateway_image"]}
    def check(name, argv, timeout=900):
        print("Qualifying: " + name, flush=True)
        output = execute(argv, timeout, env=environment)
        (folder / (name + ".log")).write_text(output, encoding="utf-8")
        checks[name] = {"passed": True, "output_hash": digest(output)}
    check("unit", [python, "-m", "unittest", "discover", "-s", "tests", "-v"])
    check("backup_lease", ["pwsh", "-NoProfile", "-File", str(ROOT / "tests/Test-BackupLease.ps1")])
    check("release_pair_fixture", ["pwsh", "-NoProfile", "-File", str(ROOT / "tests/Test-ReleasePair.ps1")])
    check("broker_linux_queue", [python, "-m", "tests.cross_os_store", original["gateway_image"], "--broker"])
    check("operator_confirmation", [python, "-m", "tests.operator_confirmation", str(runtime), original["gateway_image"]])
    for name, script in [("migration_roles", "migrate_roles_test.rb"), ("migration", "migrate_snapshot.rb"), ("release_verify", "release_verify.rb"),
                         ("integration", "integration.rb"), ("concurrency", "concurrency.rb")]:
        check(name, compose + ["exec", "-T", "-e", "QLDAPM_TEST_ONLY=true", "staging-web", "bundle", "exec", "rails", "runner", "/qldapm-core/" + script])
    check("policy", ["docker", "run", "--rm", "--network", "none", "--user", "1000:1000", "--read-only", "--cap-drop", "ALL",
                     "--mount", f"type=bind,source={ROOT / 'core'},target=/trusted,readonly", "--entrypoint", "ruby",
                     original["image"], "/trusted/test_policy.rb"])
    for name, script in (("insights_metrics", "test_insights.rb"), ("test_receipts", "test_test_receipt.rb")):
        check(name, ["docker", "run", "--rm", "--network", "none", "--user", "1000:1000", "--read-only", "--cap-drop", "ALL",
            "--tmpfs", "/tmp:size=32m", "--mount", f"type=bind,source={ROOT / 'core'},target=/trusted,readonly",
            "--entrypoint", "bundle", original["image"], "exec", "ruby", "/trusted/" + script])
    check("deep_ui_insights", compose + ["exec", "-T", "staging-web", "bundle", "exec", "rails", "runner", "/qldapm-core/deep_stage_test.rb"])
    check("admin", compose + ["exec", "-T", "staging-web", "bundle", "exec", "rails", "runner", "/qldapm-core/admin_stage_test.rb"])
    source_check = folder / "source-comparison"
    source_check.mkdir()
    check("source_comparison", compose + ["run", "--rm", "--no-deps", "-v", f"{source_check}:/backup",
        "staging-web", "bundle", "exec", "rails", "runner", "/qldapm-core/source_comparison_test.rb"])
    check("api", [python, "-m", "tests.stage_api", str(runtime)])
    try:
        check("write", [python, "-m", "tests.stage_write", str(runtime)])
    finally:
        check("cleanup", compose + ["exec", "-T", "staging-web", "bundle", "exec", "rails", "runner", "/qldapm-core/cleanup_stage_test.rb"])
    check("transport_main", [python, "-m", "tests.stage_transport", str(runtime), "--main"])
    # Isolated transport uses 18092; release the staging port, never stop production to run acceptance.
    check("stop_staging_gateway", ["docker", "stop", "qldapm-ai-stage-staging-gateway-1"], 60)
    try:
        check("transport_local", [python, "-m", "tests.stage_transport", str(runtime)])
    finally:
        check("restart_staging_gateway", ["docker", "start", "qldapm-ai-stage-staging-gateway-1"], 60)
    check("sandbox", [python, "-m", "tests.sandbox", str(runtime), original["image"], original["gateway_image"]], 1800)
    backups_before = set((runtime / "stage-backups").glob("*/restore-result.json"))
    check("restore", ["pwsh", "-NoProfile", "-File", str(ROOT / "Test-OpenProjectAIRestore.ps1"), "-Image", original["image"]], 1800)
    new_backups = set((runtime / "stage-backups").glob("*/restore-result.json")) - backups_before
    if len(new_backups) != 1:
        raise ValueError("EXACT_RESTORE_EVIDENCE_REQUIRED")
    restore_path = new_backups.pop()
    restore = json.loads(restore_path.read_text(encoding="utf-8-sig"))
    if restore.get("passed") is not True or restore.get("syntheticOnly") is not True or restore.get("image") != original["image"] or restore.get("tables", 0) < 33:
        raise ValueError("RESTORE_PROOF_INCOMPLETE")
    check("release_pair_docker", ["pwsh", "-NoProfile", "-File", str(ROOT / "tests/Test-ReleasePairDocker.ps1"),
        "-Image", original["image"], "-GatewayImage", original["gateway_image"], "-BackupPath", str(restore_path.parent), "-OfficialOrigin"], 3600)
    # Complete local evidence first; failed remote acceptance still prevents sealing a release proof.
    check("stop_staging_gateway_remote", ["docker", "stop", "qldapm-ai-stage-staging-gateway-1"], 60)
    try:
        check("transport_remote", [python, "-m", "tests.stage_transport", str(runtime), "--remote"])
    finally:
        check("restart_staging_gateway_remote", ["docker", "start", "qldapm-ai-stage-staging-gateway-1"], 60)
    if candidate(runtime) != original:
        raise ValueError("CANDIDATE_CHANGED_DURING_QUALIFICATION")
    proof = {"id": identifier, "passed": True, "synthetic_only": True, "checks": checks, **original,
             "expires": time.time() + 86400, "restore_evidence": str(restore_path),
             "restore_hash": hashlib.sha256(restore_path.read_bytes()).hexdigest(),
             "limitations": ["Real user TOTP and Codex acceptance remain human steps", "Live cutover/rollback glue is not live-tested by qualification",
                             "Official binary upgrade rehearsal uses reconstructed synthetic original schema, not a production database clone",
                             "Full-core non-overlay builds not qualified by this pipeline"]}
    signature = hmac.new(key, canonical(proof).encode(), hashlib.sha256).hexdigest()
    path = runtime / "operator" / (identifier + ".qualification.json")
    path.write_text(canonical({"proof": proof, "signature": signature}), encoding="utf-8")
    print(canonical({"qualification_id": identifier, "qualification_hash": digest(canonical(proof)), **original}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--check-deployment-hash")
    args = parser.parse_args()
    if args.check_deployment_hash:
        project = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject"
        if deployment_hash(args.runtime, project) != args.check_deployment_hash:
            raise PermissionError("APPROVED_DEPLOYMENT_CHANGED")
        print("Approved deployment unchanged.")
        raise SystemExit(0)
    # One host qualifier/processor at a time, using the same broker lock.
    with (Path(args.runtime) / "operator/broker.lock").open("a+b") as lock:
        if sys.platform == "win32":
            import msvcrt
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        qualify(args.runtime)

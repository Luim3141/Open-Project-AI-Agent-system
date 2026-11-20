"""Host-only enrollment of one n8n status credential. No native identity, key rotation or general command tool."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import uuid

from n8n_owner import LocalN8n, check_primary_backup, private_directory, provision
from gateway.automation import signing_key

CREDENTIAL_ID = "qldapmMachineStatus"
SIGNING_CREDENTIAL_ID = "qldapmCommandHmac"
CONTAINER = "qldapm-ai-stage-n8n-1"


def command(*args, payload=None):
    result = subprocess.run(["docker", "exec", *( ["-i"] if payload is not None else []), CONTAINER, *args],
                            input=payload, capture_output=True, timeout=90)
    absent = (args[:3] in {("n8n", "export:credentials", "--id=" + value) for value in (CREDENTIAL_ID, SIGNING_CREDENTIAL_ID)}
              and b"No credentials found with specified filters" in result.stdout + result.stderr)
    if result.returncode and not absent:
        raise RuntimeError("N8N_MACHINE_OPERATOR_COMMAND_FAILED")
    return result.stdout + result.stderr if absent else result.stdout


def credential(path, identifier=CREDENTIAL_ID):
    if identifier not in {CREDENTIAL_ID, SIGNING_CREDENTIAL_ID}:
        raise ValueError('FIXED_MACHINE_CREDENTIAL_REQUIRED')
    result = command("n8n", "export:credentials", "--id=" + identifier, "--decrypted", "--output=" + path)
    document = json.loads(command("node", "-e",
        "const f=require('fs');process.stdout.write(f.existsSync(process.argv[1])?f.readFileSync(process.argv[1]):'null')", path))
    if document is None and b"No credentials found with specified filters" in result:
        return None
    if not isinstance(document, list) or len(document) != 1 or document[0].get("id") != identifier:
        raise ValueError("N8N_MACHINE_CREDENTIAL_EXPORT_NOT_VERIFIED")
    return document[0]


def enroll(root, existing, install, signing=False):
    expected_root = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/stage-ai"
    if root.resolve() != expected_root.resolve():
        raise ValueError("STAGING_MACHINE_KEY_DIRECTORY_REQUIRED")
    path = root / "automation.key"
    if signing and not path.exists():
        raise PermissionError('STATUS_KEY_ENROLLMENT_REQUIRED_FIRST')
    if not path.exists() and existing is not None:
        raise PermissionError("EXISTING_N8N_CREDENTIAL_WITHOUT_SAVED_KEY; never overwrite or rotate")
    if not path.exists():
        private_directory(root)
        with path.open("x", encoding="ascii") as stream:
            stream.write(secrets.token_hex(32))
    if path.is_symlink() or path.stat().st_size != 64:
        raise ValueError("MACHINE_KEY_INVALID_DO_NOT_REPLACE")
    key = path.read_text(encoding="ascii")
    if not re.fullmatch("[a-f0-9]{64}", key):
        raise ValueError("MACHINE_KEY_INVALID_DO_NOT_REPLACE")
    expected = {'hmacSecret': signing_key(key)} if signing else {"name": "X-QLDAPM-Machine-Key", "value": key}
    kind, identifier = ('crypto', SIGNING_CREDENTIAL_ID) if signing else ('httpHeaderAuth', CREDENTIAL_ID)
    if existing is not None:
        if existing.get("type") != kind or existing.get("data") != expected:
            raise PermissionError("N8N_MACHINE_CREDENTIAL_MISMATCH; never overwrite or rotate")
    else:
        install({"id": identifier, "name": "QLDAPM status command HMAC" if signing else "QLDAPM Gateway status read only", "type": kind, "data": expected})
    return {"passed": True, "credential_created_now": existing is None, "same_key_reused": True,
            "native_credentials_shared": False, "scope": "status:trigger" if signing else "status:read", "machine_is_human_approval": False}


def run(backup, signing=False):
    check_primary_backup(backup)
    runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
    provision(runtime / "operator/n8n-owner", LocalN8n())
    results = []
    for mode in ([False, True] if signing else [False]):
        identifier = SIGNING_CREDENTIAL_ID if mode else CREDENTIAL_ID
        prefix = "/tmp/qldapm-machine-" + str(uuid.uuid4())
        output, incoming = prefix + "-export.json", prefix + "-import.json"
        try:
            existing = credential(output, identifier)
            def install(document):
                command("node", "-e", "require('fs').writeFileSync(process.argv[1],require('fs').readFileSync(0),{flag:'wx',mode:384})",
                        incoming, payload=json.dumps([document]).encode())
                command("n8n", "import:credentials", "--input=" + incoming)
                actual = credential(output, identifier)
                if actual is None or actual.get("type") != document["type"] or actual.get("data") != document["data"]:
                    raise ValueError("N8N_MACHINE_ENROLLMENT_READBACK_FAILED")
            results.append(enroll(runtime / "stage-ai", existing, install, signing=mode))
        finally:
            command("node", "-e", "for(const p of process.argv.slice(1)){if(!/^\\/tmp\\/qldapm-machine-[a-f0-9-]+-(export|import)\\.json$/.test(p))throw Error('scope');require('fs').rmSync(p,{force:true})}", output, incoming)
    return {'passed': True, 'credentials': results} if signing else results[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument('--signing', action='store_true', help='Also enroll the purpose-derived built-in Crypto HMAC credential')
    options = parser.parse_args()
    try:
        print(json.dumps(run(options.backup, options.signing)))
    except Exception as error:
        print(json.dumps({"passed": False, "error_type": type(error).__name__, "no_rotation_or_retry": True}))
        raise SystemExit(1)

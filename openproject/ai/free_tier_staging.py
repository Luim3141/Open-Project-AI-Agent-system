"""Local, human-only Free Tier enrollment. Never touches production or changes Google billing."""
import argparse
import getpass
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
import warnings
from pathlib import Path

from gateway.gemini import Gemini, MODEL, ProviderError, SMOKE_PROMPT
from gateway.store import Store, canonical, digest
from operator_state import require_offline


def private_directory(path):
    for part in [path, *path.parents]:
        if part.exists() and (part.is_symlink() or getattr(part.stat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise PermissionError("RUNTIME_REPARSE_POINT_DENIED")
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        identity = subprocess.check_output(["whoami"], text=True).strip()
        subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", identity + ":(OI)(CI)F", "SYSTEM:(OI)(CI)F"],
                       check=True, capture_output=True)
    else:
        path.chmod(0o700)


def save(path, value):
    if path.exists() and (path.is_symlink() or getattr(path.stat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise PermissionError("RUNTIME_REPARSE_POINT_DENIED")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as file:
        file.write(value)
    if os.name != "nt":
        temporary.chmod(0o600)
    temporary.replace(path)


def enroll(state, stdin_key=False, replace_key=False):
    key_path = state / "gemini.key"
    model = json.loads((state / "gemini.json").read_text()).get("model", MODEL) if (state / "gemini.json").is_file() else MODEL
    if not isinstance(model, str) or not re.fullmatch(r"gemini-[a-z0-9.-]{1,80}", model):
        raise ValueError("GEMINI_MODEL_INVALID")
    save(state / "gemini.json", canonical({"enabled": False, "model": model}))
    if key_path.exists() and not replace_key:
        print("Existing staging key retained; no key displayed or replaced.")
    else:
        key = None
        if stdin_key:
            key = sys.stdin.read(513)
        elif not replace_key:
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            if not sys.stdin.isatty():
                raise PermissionError("RUN_IN_INTERACTIVE_LOCAL_TERMINAL_FOR_HIDDEN_KEY_ENTRY")
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                key = getpass.getpass("Paste your EXISTING Gemini API key here (hidden, Enter saves): ")
        key = key.strip()
        # This is a local truncation check, not proof that Google accepts the credential.
        if not 20 <= len(key) <= 512 or not key.isascii() or any(c.isspace() or not c.isprintable() for c in key):
            raise ValueError("INVALID_KEY_FORMAT; paste the full existing API key in the hidden local prompt")
        save(key_path, key)
    print("Existing key saved outside Git with private ACL. Gemini OFF; no Google API call made.")


def verify(state, operator):
    model = json.loads((state / "gemini.json").read_text()).get("model", MODEL)
    if not isinstance(model, str) or not re.fullmatch(r"gemini-[a-z0-9.-]{1,80}", model):
        raise ValueError("GEMINI_MODEL_INVALID")
    if not (state / "gemini.key").is_file():
        raise ValueError("ENROLL_EXISTING_KEY_FIRST")
    print("MANUAL official-console verification, not automatic billing verification.")
    print("https://aistudio.google.com/api-keys : identify the exact project of the existing key; do not create a key.")
    print("https://aistudio.google.com/projects : require Free Tier for that project. Do NOT Set up billing.")
    print("https://console.cloud.google.com/billing : check the SAME project's billing is not enabled; do not change it.")
    print("https://ai.google.dev/gemini-api/terms : review Unpaid Services; no personal/confidential/sensitive data.")
    print("Use the SAME Google account/profile on AI Studio and Cloud Console. These links do not open automatically.")
    while True:
        project = input("Project ID (example: qldapm-demo-123; NOT numeric Project number; Ctrl-C cancels): ").strip()
        if re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project):
            break
        print("PROJECT_ID_REQUIRED: Project number is numeric; Project ID is 6-30 lowercase letters/digits/hyphens, starting with a letter.")
        print("Open https://console.cloud.google.com/ in your chosen profile; copy the Project ID of the SAME key's project. Key retained; Gemini stays OFF.")
    print("Scope: fixed connectivity probe and one public Scrum example; no arbitrary chat or project data.")
    if input("Only after inspecting all official pages, type FREE_NO_BILLING_PUBLIC_DEMO_ONLY: ").strip() != "FREE_NO_BILLING_PUBLIC_DEMO_ONLY":
        raise PermissionError("FREE_TIER_NOT_VERIFIED")
    quota = {}
    print("Open AI Studio Dashboard > Rate limits; select the SAME project and " + model + ".")
    for name in ("rpm", "tpm", "rpd"):
        value = input("Actual " + name.upper() + " from the selected project/model (unknown => Ctrl-C): ").strip()
        if not value.isdecimal() or not 2 <= int(value) <= 1000000000:
            raise ValueError("ACTUAL_QUOTA_REQUIRED; no guessed defaults")
        quota[name] = int(value)
    reference = Path(input("Local screenshot/export path documenting project/tier/billing/quota (NO key screenshot): ").strip().strip('"'))
    if not reference.is_absolute() or not reference.is_file() or reference.is_symlink():
        raise ValueError("LOCAL_VERIFICATION_EVIDENCE_REQUIRED")
    policy = {"model": model, "project": project, "tier": "Free", "billing_enabled": False,
              "terms_reviewed": True, "data_scope": "public-demo-only", "quota": quota,
              "checked_at": time.time(), "verification_method": "manual-official-console",
              "evidence_reference": str(reference), "evidence_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
              "key_sha256": digest((state / "gemini.key").read_text().strip())}
    fingerprint = digest(canonical(policy))
    print(canonical({"project": project, "model": model, "tier": "Free", "limits_90_percent": {n: v * 9 // 10 for n, v in quota.items()},
                     "expires_in_seconds": 3600, "scope": policy["data_scope"], "hash": fingerprint}))
    if input("Type that exact hash to record this local human verification: ").strip() != fingerprint:
        raise PermissionError("NOT_CONFIRMED")
    save(operator / "free-tier-proof.json", canonical(policy))
    save(state / "gemini.json", canonical({"enabled": False, "model": model}))
    # Manual recheck clears the circuit only; persisted usage is never reset by enrollment/reverification.
    with Store(state).connect() as db:
        db.execute("DELETE FROM gemini_blocks WHERE project=?", (project,))
    print("Manual evidence recorded for one hour; Gemini still OFF. No Google API call made.")


def authorize_continuous(state, operator, evidence, user_authorization):
    """Historical paid-consent route is intentionally retired under FREE_ONLY."""
    raise PermissionError("PAID_API_DISABLED; legacy continuous billing consent cannot be recorded or enabled")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["authorize-continuous", "configure-model", "enroll", "verify", "status", "smoke", "enable", "disable"])
    parser.add_argument("--evidence", type=Path, help="authorize-continuous only; user's local billing image")
    parser.add_argument("--user-authorization", type=Path, help="authorize-continuous only; exact owner's continuing-use/cost consent")
    parser.add_argument("--model", help="configure-model only; disables provider and requires fresh matching Free quota proof")
    parser.add_argument("--stdin-key", action="store_true", help="enroll only; pipe from the wizard's hidden local prompt, never argv")
    parser.add_argument("--replace-key", action="store_true", help="enroll only; re-enter the full existing key locally, keep provider OFF")
    args = parser.parse_args()
    if (args.action == "authorize-continuous") != (args.evidence is not None and args.user_authorization is not None) or (
            args.action != "authorize-continuous" and (args.evidence is not None or args.user_authorization is not None)):
        raise ValueError("CONTINUOUS_AUTHORIZATION_FILES_REQUIRED_ONLY_FOR_AUTHORIZE_CONTINUOUS")
    if (args.action == "configure-model") != (args.model is not None):
        raise ValueError("MODEL_ONLY_FOR_CONFIGURE_MODEL")
    if args.stdin_key and args.action != "enroll":
        raise ValueError("STDIN_KEY_ONLY_FOR_ENROLL")
    if args.replace_key and args.action != "enroll":
        raise ValueError("REPLACE_KEY_ONLY_FOR_ENROLL")
    runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
    state, operator = runtime / "stage-ai", runtime / "operator/gemini-free"
    require_offline("qldapm-ai-stage-staging-gateway-1")
    model = json.loads((state / "gemini.json").read_text()).get("model", MODEL) if (state / "gemini.json").is_file() else MODEL
    if args.action == "configure-model":
        if not re.fullmatch(r"gemini-[a-z0-9.-]{1,80}", args.model):
            raise ValueError("GEMINI_MODEL_INVALID")
        private_directory(state)
        save(state / "gemini.json", canonical({"enabled": False, "model": args.model}))
        print("Staging model saved/OFF. Key and usage retained; verify the exact model's Free quota before any call.")
        return
    if args.action == "status":
        os.environ["QLDAPM_AI_ENVIRONMENT"] = "staging"
        os.environ["QLDAPM_GEMINI_FREE_PROOF"] = str(operator / "free-tier-proof.json")
        enabled, reason, policy, circuit_latched = False, "pending verification", {}, False
        try:
            policy = Gemini(state).settings(require_enabled=False)
            if (state / "gateway.sqlite").is_file():
                row = Store(state).gemini_block(policy["project"])
                if row:
                    circuit_latched = True
                    raise ProviderError("GEMINI_CIRCUIT_OPEN; no outbound request; last_error=" + row["reason"])
            enabled = json.loads((state / "gemini.json").read_text()).get("enabled") is True
            reason = "persistent Free-only authorization, not live billing verification" if Gemini.continuous_authorized(policy) else "manual official-console proof, not automatic billing verification"
            if not enabled:
                reason += "; provider remains OFF"
        except ProviderError as error:
            reason = str(error)
        print(canonical({"model": model, "key_present": (state / "gemini.key").is_file(),
                         "proof_present": (operator / "free-tier-proof.json").is_file(),
                         "gemini": {"project-business-content": "ON_PROJECT_BUSINESS", "project-metadata-only": "ON_PROJECT_METADATA", "public-demo-only": "ON_PUBLIC_DEMO"}.get(policy.get("data_scope"), "ON_SMOKE_ONLY") if enabled else "OFF", "reason": reason,
                         "circuit_latched": circuit_latched, "network_checked": False,
                         "project_tier": policy.get("tier", "UNKNOWN"), "quota": policy.get("quota", "UNKNOWN"),
                         "limits": policy.get("limits", "UNSET"),
                         "authorization_mode": "continuous-free-only" if policy.get("authorization") else "one-hour-free-proof",
                         "expires": None if policy.get("authorization") else policy.get("checked_at", 0) + 3600,
                         "production_changed": False}))
        return
    private_directory(state)
    private_directory(operator)
    if args.action == "authorize-continuous":
        os.environ["QLDAPM_AI_ENVIRONMENT"] = "staging"
        os.environ["QLDAPM_GEMINI_FREE_PROOF"] = str(operator / "free-tier-proof.json")
        authorize_continuous(state, operator, args.evidence, args.user_authorization)
    elif args.action == "enroll":
        enroll(state, args.stdin_key, args.replace_key)
    elif args.action == "verify":
        verify(state, operator)
    elif args.action == "disable":
        save(state / "gemini.json", canonical({"enabled": False, "model": model}))
        print("Staging Gemini OFF. Production untouched.")
    else:
        os.environ["QLDAPM_AI_ENVIRONMENT"] = "staging"
        os.environ["QLDAPM_GEMINI_FREE_PROOF"] = str(operator / "free-tier-proof.json")
        try:
            gemini = Gemini(state)
            policy = gemini.settings(require_enabled=False)
            proof_hash = digest((operator / "free-tier-proof.json").read_text())
            if args.action == "smoke":
                save(state / "gemini.json", canonical({"enabled": True, "model": model}))
                result = gemini.run(SMOKE_PROMPT, lambda *args: None)
                save(operator / "smoke-result.json", canonical({"passed": True, "at": time.time(), "proof_hash": proof_hash,
                     "key_sha256": policy["key_sha256"], "model": model, "result": result}))
                print("Google fixed-text smoke PASS; staging remains OFF until enable. No ticket/code/personnel/tool data sent.")
            else:
                result = json.loads((operator / "smoke-result.json").read_text())
                if (result.get("passed") is not True or result.get("proof_hash") != proof_hash or
                        result.get("key_sha256") != policy["key_sha256"] or not 0 <= time.time() - result.get("at", 0) < 3600):
                    raise PermissionError("FRESH_SMOKE_REQUIRED")
                save(state / "gemini.json", canonical({"enabled": True, "model": model}))
                print("Staging ON; scope=" + policy["data_scope"] + "; authorization=" + ("persistent Free-only, no paid fallback" if gemini.continuous_authorized(policy) else "one-hour Free proof") + ". Existing key/usage retained; no Google billing change.")
        except Exception:
            save(state / "gemini.json", canonical({"enabled": False, "model": model}))
            raise
        finally:
            if args.action == "smoke":
                save(state / "gemini.json", canonical({"enabled": False, "model": model}))


if __name__ == "__main__":
    try:
        main()
    except (ProviderError, ValueError, PermissionError) as error:
        print(canonical({"failed": True, "error": str(error), "production_changed": False}))
        raise SystemExit(1)
    except Exception as error:
        print(canonical({"failed": True, "error_type": type(error).__name__, "production_changed": False}))
        raise SystemExit(1)

"""Local human-only credential enrollment and proposal confirmation. Never a MCP tool."""
import argparse
import json
import os
import secrets
from pathlib import Path

from gateway.gemini import MODEL
from gateway.store import canonical
from operator_state import ContainerState


def provider(state):
    raise PermissionError("PRODUCTION_PROVIDER_ENROLLMENT_DISABLED; use free_tier_staging.py enroll, no billing change")


def confirm(runtime, actor, identifier):
    store = ContainerState(runtime / "gateway")
    token = (runtime / "operator" / f"user-{actor}.token").read_text().strip()
    preview = store.call("preview_proposal", actor=actor, token=token, identifier=identifier)
    print(canonical(preview))
    if input("Type the exact preview SHA256 to confirm this change: ").strip() != preview["hash"]:
        raise PermissionError("NOT_CONFIRMED")
    print(canonical(store.call("confirm_proposal", actor=actor, token=token, identifier=identifier, fingerprint=preview["hash"])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["provider", "disable-provider", "prepare-ui", "confirm"])
    parser.add_argument("--runtime", default=str(Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"))
    parser.add_argument("--user-id", type=int)
    parser.add_argument("--proposal")
    args = parser.parse_args()
    runtime = Path(args.runtime)
    state = runtime / "gateway"
    if not (state / "config.json").is_file():
        raise ValueError("INITIALIZE_AI_RUNTIME_FIRST")
    if args.action == "provider":
        provider(state)
    elif args.action == "disable-provider":
        (state / "gemini.json").write_text(canonical({"enabled": False, "model": MODEL}), encoding="utf-8")
        print("Gemini disabled. Local reports and MCP still available.")
    elif args.action == "prepare-ui":
        target = state / "ui.key"
        if not target.exists():
            target.write_text(secrets.token_hex(32), encoding="utf-8")
        test_key = runtime / "operator/test-receipt.key"
        if not test_key.exists():
            test_key.write_text(secrets.token_hex(32), encoding="utf-8")
        print("Separate UI/test receipt keys prepared; no live Compose change. Mount only these files read-only in core; never the operator approval key.")
    else:
        if not args.user_id or not args.proposal:
            raise ValueError("USER_AND_PROPOSAL_REQUIRED")
        confirm(runtime, args.user_id, args.proposal)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Do not print upstream HTTP/debug objects which might contain credentials.
        print(canonical({"failed": True, "error_type": type(error).__name__, "live_success_not_assumed": True}))
        raise SystemExit(1)

"""Fixed stdin protocol invoked only by the trusted host; not an HTTP/MCP route."""
import json
import sys
from pathlib import Path

from .store import Store, canonical


def execute(packet, root=Path("/state"), workspaces=Path("/workspaces")):
    if set(packet) != {"operation", "arguments"} or not isinstance(packet["arguments"], dict):
        raise ValueError("LOCAL_OPERATOR_PACKET_DENIED")
    action, args = packet["operation"], packet["arguments"]
    fields = {"broker_job": {"operation", "identifier", "state", "result"},
              "record": {"actor", "action", "target", "outcome"},
              "issue_token": {"user_id", "role", "op_token"}, "revoke_token": {"token"}, "token_count": {"actors"},
              "preview_proposal": {"actor", "token", "identifier"},
              "confirm_proposal": {"actor", "token", "identifier", "fingerprint"}}
    if action not in fields or set(args) != fields[action]:
        raise ValueError("LOCAL_OPERATOR_OPERATION_DENIED")
    store = Store(root)
    if action == "broker_job":
        return store.broker_job(**args)
    if action == "record":
        return store.record(**args)
    if action == "token_count":
        actors = args["actors"]
        if not isinstance(actors, list) or not 1 <= len(actors) <= 20 or any(type(a) is not int for a in actors):
            raise ValueError("ACTORS_DENIED")
        with store.connect() as db:
            return sum(db.execute("SELECT COUNT(*) FROM tokens WHERE user_id=?", (a,)).fetchone()[0] for a in actors)
    if action == "revoke_token":
        return store.revoke_token(**args)
    config = json.loads((root / "config.json").read_text())
    if config.get("maintenance") is True:
        raise PermissionError("GATEWAY_MAINTENANCE; no enrollment or proposal confirmation")
    if action == "issue_token":
        from .native import Native
        identity = Native(config["openproject_url"], args["op_token"], config["project_id"]).identity(args["user_id"])
        if identity["role"] != args["role"] or config["users"].get(str(args["user_id"])) != identity["role"]:
            raise PermissionError("CURRENT_MEMBERSHIP_REQUIRED")
        return store.issue_token(**args)
    from .service import Service
    if store.authenticate(args["token"])["user_id"] != args["actor"]:
        raise PermissionError("IDENTITY_MISMATCH")
    service = Service(store, config, workspaces)
    if action == "preview_proposal":
        return service.execute(args["token"], {"action": "get_proposal", "arguments": {"id": args["identifier"]}})["result"]
    return service.confirm(args["actor"], args["identifier"], args["fingerprint"])


def main():
    try:
        raw = sys.stdin.buffer.read(1048577)
        if len(raw) > 1048576:
            raise ValueError("LOCAL_OPERATOR_PAYLOAD_LIMIT")
        result = canonical({"result": execute(json.loads(raw))})
        if len(result.encode()) > 1048576:
            raise ValueError("LOCAL_OPERATOR_RESULT_LIMIT")
        print(result)
    except Exception as error:
        # Never return upstream messages, request contents, or credentials.
        print(canonical({"error_type": type(error).__name__, "error": "LOCAL_STATE_OPERATION_FAILED; reconcile before retry"}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

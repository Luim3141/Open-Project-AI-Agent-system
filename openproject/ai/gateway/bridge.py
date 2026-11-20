"""UI-only actor assertions: separate from Bearer and privileged operator approval."""
import hashlib
import hmac
import json
import time

from .store import canonical


def verify_assertion(store, config, body, signature):
    key_path = store.root / "ui.key"
    if not key_path.is_file() or len(body) > 1048576:
        raise PermissionError("UI_BRIDGE_DISABLED")
    expected = hmac.new(key_path.read_bytes(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("UI_ASSERTION_INVALID")
    payload = json.loads(body)
    if set(payload) != {"actor", "project", "audience", "at", "nonce", "operation", "command"}:
        raise PermissionError("UI_ASSERTION_INVALID")
    projects = {config['project_id']}
    if config.get('engineering',{}).get('enabled') is True:
        projects.add(6)
    if payload["audience"] != "qldapm-ai-ui" or type(payload['project']) is not int or payload["project"] not in projects or abs(time.time() - payload["at"]) > 30:
        raise PermissionError("UI_ASSERTION_EXPIRED_OR_PROJECT")
    users = config.get('engineering',{}).get('actors',{}) if payload['project']==6 else config['users']
    if str(payload["actor"]) not in users or not isinstance(payload["nonce"], str) or not 16 <= len(payload["nonce"]) <= 100:
        raise PermissionError("UI_ACTOR_DENIED")
    if payload["operation"] not in {"command", "confirm", "qa_review", "phase_review"}:
        raise PermissionError("UI_OPERATION_DENIED")
    store.consume_nonce(payload["nonce"], time.time() + 60)
    return payload

"""n8n machine authority: fixed local status read only, never a human actor or business command."""
import hmac
import hashlib
import json
import re
import time

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Literal

from starlette.responses import JSONResponse
from .monitoring import MONITOR_PATH

HEADER = "x-qldapm-machine-key"
STATUS_PATH = "/internal/automation/status"
COMMAND_PATH = "/internal/automation/commands"
SIGNATURE_HEADER = "x-qldapm-command-signature"


class AutomationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1]
    kind: Literal["status", "daily_brief", "weekly_summary", "workflow_error"]
    request_key: str = Field(min_length=16, max_length=100, pattern=r"^[A-Za-z0-9:_-]+$")
    nonce: str = Field(min_length=16, max_length=100, pattern=r"^[A-Za-z0-9:_-]+$")
    issued_at: int = Field(ge=0, le=999999999999)


def signing_key(key):
    return hmac.new(key.encode("ascii"), b"QLDAPM-AUTOMATION-SIGNING-V1", hashlib.sha256).hexdigest()


def signing_message(command):
    return ("QLDAPM-AUTOMATION-COMMAND-V1\nPOST\n" + COMMAND_PATH + "\n1\n" + command["kind"] + "\n"
            + command["request_key"] + "\n" + command["nonce"] + "\n" + str(command["issued_at"])).encode("utf-8")


def authenticate(root, provided):
    path = root / "automation.key"
    try:
        if path.is_symlink() or path.stat().st_size != 64:
            raise ValueError()
        expected = path.read_text(encoding="ascii")
        if (not re.fullmatch("[a-f0-9]{64}", expected) or not re.fullmatch("[a-f0-9]{64}", provided)
                or not hmac.compare_digest(expected, provided)):
            raise ValueError()
        return expected
    except (OSError, ValueError, UnicodeError):
        raise PermissionError("INVALID_MACHINE_AUTH") from None


def command_response(root, store, scope, headers, body, service=None):
    try:
        if scope.get('query_string') or headers.get('authorization'):
            raise PermissionError('MACHINE_SCOPE_DENIED')
        key = authenticate(root, headers.get(HEADER, ''))
        payload = json.loads(body)
        if not isinstance(payload, dict) or type(payload.get('version')) is not int:
            raise ValueError('INVALID_COMMAND')
        command = AutomationCommand.model_validate(payload).model_dump()
        signature = headers.get(SIGNATURE_HEADER, '')
        expected = hmac.new(signing_key(key).encode('ascii'), signing_message(command), hashlib.sha256).hexdigest()
        if not re.fullmatch('[a-f0-9]{64}', signature) or not hmac.compare_digest(signature, expected):
            raise PermissionError('INVALID_COMMAND_SIGNATURE')
        elapsed = time.time() - command['issued_at']
        if not -15 <= elapsed <= 60:
            raise PermissionError('COMMAND_EXPIRED_OR_FUTURE')
        if command['kind'] == 'daily_brief':
            if service is None:
                raise PermissionError('DAILY_BRIEF_SERVICE_UNAVAILABLE')
            result = service.daily_brief(command)
        elif command['kind'] == 'weekly_summary':
            if service is None:
                raise PermissionError('WEEKLY_SUMMARY_SERVICE_UNAVAILABLE')
            from .weekly_report import collect_scheduled
            result = collect_scheduled(service,command)
        elif command['kind'] == 'workflow_error':
            if service is None:
                raise PermissionError('WORKFLOW_PROJECT_UNAVAILABLE')
            result = store.begin_automation(command, project=service.config['project_id'])[0]
        else:
            if command['request_key'].startswith(('daily:', 'weekly:', 'error:')):
                raise ValueError('AUTOMATION_NAMESPACE_RESERVED')
            result = store.accept_automation_status(command)
        return JSONResponse({'result': result, 'correlation_id': result['trace_id']})
    except PermissionError as error:
        code, status = str(error), 401 if str(error) == 'INVALID_MACHINE_AUTH' else 403
    except (ValueError, ValidationError):
        code, status = 'INVALID_AUTOMATION_COMMAND', 422
    store.record(None, 'automation_command_denied', 'automation', code)
    return JSONResponse({'error': code, 'source': 'gateway'}, status_code=status)


def status_response(root, store, scope, headers, service=None):
    if (scope["path"] not in {STATUS_PATH,MONITOR_PATH} or scope["method"] != "GET" or scope.get("query_string")
            or headers.get("authorization") or headers.get("content-length", "0") not in {"", "0"}
            or headers.get("transfer-encoding")):
        store.record(None, "automation_access_denied", "automation", "SCOPE_DENIED")
        return JSONResponse({"error": "MACHINE_SCOPE_DENIED", "source": "gateway"}, status_code=403)
    try:
        authenticate(root, headers.get(HEADER, ""))
    except PermissionError:
        store.record(None, "automation_access_denied", "automation", "INVALID_AUTH")
        return JSONResponse({"error": "INVALID_MACHINE_AUTH", "source": "gateway"}, status_code=401)
    if scope['path'] == MONITOR_PATH:
        from .monitoring import snapshot
        try:
            if service is None:
                raise PermissionError('MONITOR_SERVICE_REQUIRED')
            return JSONResponse(snapshot(service))
        except PermissionError:
            return JSONResponse({'error':'MONITOR_SCOPE_DENIED','source':'gateway'},status_code=403)
        except (ValueError,OSError):
            return JSONResponse({'error':'MONITOR_BUSY_OR_RECEIPT_UNAVAILABLE','source':'gateway'},status_code=503)
    correlation = store.record(None, "automation_status", "gateway", "ok")
    return JSONResponse({"result": {"component": "gateway", "status": "ok", "authority": "machine",
        "actor_id": None, "scopes": ["status:read"], "native_write_allowed": False, "model_calls": 0},
        "correlation_id": correlation})

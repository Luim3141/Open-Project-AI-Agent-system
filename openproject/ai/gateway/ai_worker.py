"""Fixed private worker: process termination bounds the entire model/tool run, not only HTTP."""
import json
import subprocess
import sys
from pathlib import Path

from .gemini import ProviderError
from . import RUN_TIMEOUT_SECONDS, RUN_ROUND_LIMITS
from .presentation import action_requested
from .agent_trace import bind_run, reset_run, trace_event


def run_isolated(root, workspaces, actor, prompt, identifier, allow_routine_writes=False, write_scope_ids=None, engine='gemini',business_read_only=False):
    payload = {"root": str(root), "workspaces": str(workspaces), "actor": actor, "prompt": prompt, "id": identifier,
               "allow_routine_writes": allow_routine_writes, "write_scope_ids": write_scope_ids or []}
    if engine != 'gemini':
        payload['engine'] = engine
    if business_read_only:payload['business_read_only']=True
    timeout=RUN_TIMEOUT_SECONDS
    if business_read_only:timeout=180
    consent=Path(root)/'business-acceptance.json'
    if engine=='gemini' and consent.exists() and json.loads(consent.read_text()).get('actor')==actor:
        import sqlite3,time
        with sqlite3.connect('file:'+str(Path(root)/'gateway.sqlite')+'?mode=ro',uri=True) as db:
            row=db.execute('select created from ai_runs where id=? and actor=?',(identifier,actor)).fetchone()
        if not row:raise ProviderError('OWNER_STORED_RUN_REQUIRED')
        timeout=max(0.01,min(180,180-(time.time()-row[0])))
    try:
        response = subprocess.run([sys.executable, "-m", "gateway.ai_worker"],
            input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8", timeout=timeout,
            cwd=Path(__file__).resolve().parents[1])
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for this child; partial tool receipts remain UNKNOWN, never replayed.
        raise ProviderError("GEMINI_RUN_DEADLINE; worker stopped; reconcile tool receipts, no automatic retry") from None
    if response.returncode or len(response.stdout.encode()) > 1048576:
        raise ProviderError("GEMINI_WORKER_FAILED_OR_OUTPUT_LIMIT")
    try:
        document = json.loads(response.stdout)
        if set(document) == {"error"} and isinstance(document["error"], str) and len(document["error"]) < 1000:
            raise ProviderError(document["error"])
        if set(document) != {"result"} or not isinstance(document["result"], dict):
            raise ValueError()
        return document["result"]
    except (ValueError, TypeError):
        raise ProviderError("GEMINI_WORKER_MALFORMED") from None


def main():
    from .service import Service
    from .store import Store
    trace_token = None
    try:
        data = sys.stdin.buffer.read(1048577)
        payload = json.loads(data)
        engine = payload.pop('engine','gemini')
        business_read_only=payload.pop('business_read_only',False)
        if type(business_read_only) is not bool or business_read_only and payload.get('allow_routine_writes'):
            raise PermissionError('READ_ONLY_WRITE_CONSENT_DENIED')
        if engine not in {'gemini','supervisor','supervisor_gemini'}:
            raise ValueError('AI_ENGINE_INVALID')
        if (len(data) > 1048576 or set(payload) != {"root", "workspaces", "actor", "prompt", "id", "allow_routine_writes", "write_scope_ids"} or
                type(payload["allow_routine_writes"]) is not bool or
                not isinstance(payload["write_scope_ids"], list) or
                any(type(identifier) is not int or identifier <= 0 for identifier in payload["write_scope_ids"]) or
                type(payload["actor"]) is not int or payload["actor"] <= 0 or
                not isinstance(payload["prompt"], str) or not 1 <= len(payload["prompt"]) <= 8000):
            raise ValueError()
        root = Path(payload["root"])
        service = Service(Store(root), json.loads((root / "config.json").read_text()), payload["workspaces"])
        if engine in {'supervisor','supervisor_gemini'}:
            document = {'result':service.run_supervisor(payload['actor'],payload['id'],live=engine=='supervisor_gemini')}
            sys.stdout.buffer.write(json.dumps(document,ensure_ascii=False).encode('utf-8'))
            return
        trace_token = bind_run(service.store, payload["actor"], service.config["project_id"], payload["id"])
        trace_event("worker", "start")
        service.gemini.settings()
        identity = service.execute_actor(payload["actor"], {"action": "identity"})["result"]
        permissions = service.execute_actor(payload["actor"], {"action": "get_permissions"})["result"]
        if payload["allow_routine_writes"] and service.mode != "native":
            raise PermissionError("NATIVE_MODE_REQUIRED_FOR_RUN_WRITE_CONSENT")
        if business_read_only:
            from .business_runs import read_analysis
            document={'result':read_analysis(service,payload)}
            sys.stdout.buffer.write(json.dumps(document,ensure_ascii=False).encode('utf-8'))
            return
        from .business_acceptance import BusinessAcceptance
        acceptance=BusinessAcceptance.load(service,payload)
        from .business_runs import ProviderBudget, READ_TOOLS, link_command, load
        context={**payload,'business_read_only':business_read_only}
        provider=ProviderBudget(service,context)
        try:load(service.store,payload['actor'],service.config['project_id'],payload['id']);registered=True
        except PermissionError:registered=False
        index = 0
        allowed_ids = set(payload["write_scope_ids"])
        business = service.gemini.settings().get("data_scope") == "project-business-content"
        def execute(action, arguments):
            nonlocal index
            index += 1
            if business_read_only and action not in READ_TOOLS:raise PermissionError('READ_ONLY_TOOL_DENIED')
            if acceptance:arguments=acceptance.command(action,arguments)
            auto = payload["allow_routine_writes"] and action in {"create_work_package", "update_work_package", "comment", "transition"}
            if auto and business and not action_requested(payload["prompt"], action):
                raise PermissionError("AI_WRITE_ACTION_NOT_REQUESTED")
            if auto and action != "create_work_package" and arguments.get("id") not in allowed_ids:
                service.store.record(payload["actor"], "ai_scope_denied", "request_scope", "outside_user_scope")
                raise PermissionError("AI_WRITE_TARGET_OUTSIDE_USER_SCOPE")
            if auto and action == "create_work_package" and arguments.get("parent_id") is not None and arguments['parent_id'] not in allowed_ids:
                raise PermissionError("AI_CREATE_PARENT_OUTSIDE_USER_SCOPE")
            if business and action == "get_work_package":
                arguments = {**arguments, "include_context": True}
            if business and action == "list_work_packages":
                arguments = {"limit": 30, **arguments}
            if business and action == "create_work_package":
                arguments = {"source_id": f"ai-{payload['id']}-{index}", **arguments}
            key=acceptance.create_key if acceptance and action=='create_work_package' else f"ai-{payload['id']}-{index}"
            if registered and action in {'create_work_package','update_work_package','comment','transition'}:
                link_command(service,payload['actor'],payload['id'],key,approved=False)
            result = service.execute_actor(payload["actor"], {"action": action, "arguments": arguments,
                "idempotency_key":key,"auto_execute": False})
            if auto and action == "create_work_package" and type(result.get("result", {}).get("id")) is int:
                allowed_ids.add(result["result"]["id"])
            return result
        document = {"result": service.gemini.run(payload["prompt"], execute, allow_routine_writes=False,
                max_rounds=RUN_ROUND_LIMITS[service.store.run_class(payload["actor"], payload["id"])],
                actor_role=identity["role"],
                permitted_tools=[tool["name"] for tool in permissions["tools"] if tool["allowed"] and (not business_read_only or tool['name'] in READ_TOOLS)],
                write_scope_ids=payload["write_scope_ids"], progress=lambda result: service.store.progress_run(payload["actor"], payload["id"], result),
                **({'acceptance':acceptance} if acceptance else {'provider':provider} if registered else {}))}
    except ProviderError as error:
        document = {"error": str(error)}
    except Exception:
        document = {"error": "GEMINI_WORKER_FAILED; reconcile tool receipts, no automatic retry"}
    finally:
        reset_run(trace_token)
    output = json.dumps(document, ensure_ascii=False)
    if len(output.encode()) > 1048576:
        output = '{"error":"GEMINI_WORKER_OUTPUT_LIMIT"}'
    sys.stdout.buffer.write(output.encode("utf-8"))


if __name__ == "__main__":
    main()

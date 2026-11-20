import contextvars
import asyncio
import json
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .native import NativeError
from .catalog import description
from .service import Command, MUTATIONS, Service
from .store import Store, digest
from .bridge import verify_assertion
from .gemini import ProviderError
from .permissions import allowed
from .agent_models import AgentProgress, AgentRunPage, AgentTracePage
from .automation import HEADER as MACHINE_HEADER, COMMAND_PATH, STATUS_PATH, MONITOR_PATH, AutomationCommand, command_response, status_response

bearer_context = contextvars.ContextVar("qldapm_bearer")


def openapi_document():
    document = {"openapi": "3.1.0", "info": {"title": "QLDAPM AI", "version": "1.1.0"},
        "paths": {"/api/v1/commands": {"post": {"security": [{"bearerAuth": []}],
            "requestBody": {"required": True, "content": {"application/json": {"schema": Command.model_json_schema()}}},
            "responses": {str(status): {"description": label} for status, label in
                [(200, "Result and correlation ID"), (401, "Invalid token"), (403, "Denied"), (409, "Conflict"), (422, "Invalid command"), (429, "Quota or rate limit"), (503, "Unavailable; source identifies gateway/openproject/gemini")]}}}},
        "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}}}}
    for path in ("/api/v1/ai-runs/{id}", "/api/v1/proposals/{id}", "/api/v1/insights"):
        operation = {"security": [{"bearerAuth": []}], "responses": {"200": {"description": "Actor-scoped data"},
            "403": {"description": "Denied"}}}
        operation["parameters"] = ([{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}] if "{id}" in path else
            [{"name": "user_id", "in": "query", "schema": {"type": "integer"}},
             {"name": "days", "in": "query", "schema": {"type": "integer", "enum": [7, 30, 90], "default": 30}}])
        document["paths"][path] = {"get": operation}
    document["paths"]["/api/v1/ai-runs"] = {"post": {"security": [{"bearerAuth": []}],
        "parameters": [{"name": "Idempotency-Key", "in": "header", "required": True, "schema": {"type": "string"}}],
        "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "additionalProperties": False,
            "required": ["prompt"], "properties": {"prompt": {"type": "string", "minLength": 1, "maxLength": 8000},
                "engine": {"type":"string","enum":["gemini","gemini_read","supervisor","supervisor_gemini"],"default":"gemini","description":"supervisor is local; supervisor_gemini uses bounded live specialists and proposal-only writes with separate exact PM approval; gemini preserves legacy business tools; gemini_read is read-only"},
                "run_class": {"type": "string", "enum": ["interactive", "agent", "report", "system"], "default": "interactive", "description": "Scheduling priority and model round bound only; does not change identity, permissions or write consent"},
                "context_task_id": {"type": "string", "format": "uuid", "description": "Own stored task reference; requires conversation_id, fresh native ACL/version and unexpired task. Read-only exact follow-up; never write consent"},
                "conversation_id": {"type": "string", "format": "uuid", "description": "Must match the stored actor/project/task conversation; required with context_task_id"},
                "allow_routine_writes": {"type": "boolean", "default": False, "description": "Legacy scope selection only; all writes produce proposals requiring a separate authenticated PM decision"},
                "write_scope_ids": {"type": "array", "items": {"type": "integer", "minimum": 1}, "default": [], "description": "User-selected existing work package IDs permitted to change in this run, without a fixed count; newly created IDs are tracked locally"}}}}}},
        "responses": {"200": {"description": "Run receipt; poll GET"}, "503": {"description": "Provider disabled/unavailable"}}}}
    document["paths"]["/api/v1/proposals/{id}/decision"] = {"post": {
        "security": [{"bearerAuth": []}], "summary": "PM decision for own exact proposal; approval executes once",
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
        "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object",
            "additionalProperties": False, "required": ["decision", "hash"], "properties": {
                "decision": {"type": "string", "enum": ["approve", "reject"]},
                "hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}}}}},
        "responses": {"200": {"description": "Persisted decision/result; Native readback is separate from RAG verification"},
            "403": {"description": "PM/actor denied"}, "409": {"description": "Changed, expired, consumed or uncertain proposal"},
            "422": {"description": "Invalid decision"}}}}
    document['paths']['/api/v1/knowledge-feedback/{id}/decision'] = {'post':{
        'security':[{'bearerAuth':[]}],'summary':'Independent Manager exact-hash feedback review; no Native write or note promotion',
        'parameters':[{'name':'id','in':'path','required':True,'schema':{'type':'string','format':'uuid'}}],
        'requestBody':{'required':True,'content':{'application/json':{'schema':{'type':'object','additionalProperties':False,
            'required':['decision','hash'],'properties':{'decision':{'type':'string','enum':['accept','reject']},
            'hash':{'type':'string','pattern':'^[a-f0-9]{64}$'}}}}}},
        'responses':{str(s):{'description':d} for s,d in [(200,'Source-bound decision'),(401,'Unauthenticated'),(403,'Role/source/self-review denied'),(409,'Changed or consumed feedback'),(422,'Invalid payload'),(503,'Source unavailable')]}}}
    import copy
    document['paths']['/api/v1/qa-evidence/{id}/decision'] = copy.deepcopy(document['paths']['/api/v1/knowledge-feedback/{id}/decision'])
    document['paths']['/api/v1/qa-evidence/{id}/decision']['post']['summary'] = 'Independent exact-hash manual review or QA-then-Manager signed automated evidence review; no Native write'
    document['paths']['/api/v1/native-phases/{id}/decision'] = copy.deepcopy(document['paths']['/api/v1/knowledge-feedback/{id}/decision'])
    document['paths']['/api/v1/native-phases/{id}/decision']['post']['summary'] = 'Independent Manager exact source-phase review; separate proposal approval still required for Native writes'
    schemas = document["components"].setdefault("schemas", {})
    for model in (AgentProgress, AgentRunPage, AgentTracePage):
        definition = model.model_json_schema(ref_template="#/components/schemas/{model}")
        schemas.update(definition.pop("$defs", {}))
        schemas[model.__name__] = definition
    for path, model in (("/api/v1/agent-runs", AgentRunPage), ("/api/v1/agent-runs/{id}", AgentProgress),
                        ("/api/v1/agent-runs/{id}/trace", AgentTracePage)):
        parameters = []
        if "{id}" in path:
            parameters.append({"name": "id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}})
        if model != AgentProgress:
            parameters += [{"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}},
                           {"name": "offset", "in": "query", "schema": {"type": "integer", "minimum": 0, "maximum": 2147483647, "default": 0}}]
        document["paths"][path] = {"get": {"security": [{"bearerAuth": []}], "parameters": parameters,
            "description": "Actor/project-scoped metadata only. No execution retry or business mutation.",
            "responses": {"200": {"description": "Own metadata and correlation ID", "content": {"application/json": {"schema": {
                "type": "object", "required": ["result", "correlation_id"], "additionalProperties": False,
                "properties": {"result": {"$ref": "#/components/schemas/" + model.__name__}, "correlation_id": {"type": "string", "format": "uuid"}}}}}},
                "401": {"description": "Authentication required"}, "403": {"description": "Denied or not found in own scope"},
                "422": {"description": "Invalid ID or page"}}}}
    document["components"]["securitySchemes"]["machineStatusAuth"] = {
        "type": "apiKey", "in": "header", "name": MACHINE_HEADER,
        "description": "Separate local n8n key; deterministic status/fixed-five daily reads only, never a human bearer or business write permission"}
    document["paths"][STATUS_PATH] = {"get": {"security": [{"machineStatusAuth": []}],
        "description": "Internal machine Gateway liveness only; no native/provider probe, actor, query or request body.",
        "responses": {"200": {"description": "Gateway liveness and correlation ID; zero model calls"},
                      "401": {"description": "Machine authentication required"}, "403": {"description": "Machine scope denied"},
                      "429": {"description": "Machine rate limited"}}}}
    document['paths'][MONITOR_PATH] = {'get':{'security':[{'machineStatusAuth':[]}],
        'description':'Fixed Main health probes and Gateway cgroup/backlog; persisted SHA256 receipt per15minute bucket, one local BGE-M3 embedding, zero provider/Native writes. No caller target/body/query/human authority.',
        'responses':{'200':{'description':'Persisted HEALTHY/DEGRADED report; observed_at/cached distinguish freshness'},
            '401':{'description':'Machine authentication required'},'403':{'description':'Scope denied'},'503':{'description':'Monitor busy or receipt unavailable'}}}}
    document['paths'][COMMAND_PATH] = {'post': {'security': [{'machineStatusAuth': []}],
        'description': 'Internal signed status, fixed-five daily_brief read or fixed workflow_error metadata;60second expiry/15second future tolerance, durable idempotency, no caller actor/LLM/business write. daily_brief requires daily:YYYY-MM-DD; workflow_error requires error:<known-workflow>:<execution-or-activation>:YYYY-MM-DD in Asia/Bangkok, no raw errors.',
        'parameters': [{'name': 'x-qldapm-command-signature', 'in': 'header', 'required': True, 'schema': {'type': 'string', 'pattern': '^[a-f0-9]{64}$'}}],
        'requestBody': {'required': True, 'content': {'application/json': {'schema': AutomationCommand.model_json_schema()}}},
        'responses': {str(code): {'description': text} for code,text in [(200,'Same durable receipt on duplicate'),(401,'Machine auth required'),(403,'Signature, scope, expiry or replay denied'),(413,'Payload too large'),(422,'Invalid command'),(429,'Rate limited')]}}}
    return document


def create_app(root=None, service=None):
    root = Path(root or os.environ.get("QLDAPM_AI_RUNTIME", "/state"))
    store = service.store if service else Store(root)
    config = service.config if service else json.loads((root / "config.json").read_text())
    service = service or Service(store, config, os.environ.get("QLDAPM_AI_WORKSPACES", "/workspaces"))
    mcp = FastMCP("qldapm-openproject", stateless_http=True, json_response=True,
                  transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
    # Host/Origin checks and authentication cover REST and MCP in one outer middleware.
    for name in Command.model_fields["action"].annotation.__args__:
        if not allowed("PM", name, service.mode) and name != 'qa_evidence_capture':
            continue
        def make_tool(action):
            async def tool(arguments: dict, idempotency_key: str | None = None, auto_execute: bool = False, project_id: int | None = None) -> dict:
                return await run_in_threadpool(service.execute, bearer_context.get(),
                    {"action": action, "arguments": arguments, "idempotency_key": idempotency_key, "auto_execute": auto_execute, "project_id":project_id})
            return tool
        mcp.add_tool(make_tool(name), name=name, description=description(name),
                     annotations={"readOnlyHint": name not in MUTATIONS, "destructiveHint": False, "openWorldHint": False})

    @mcp._mcp_server.list_tools()
    async def actor_tools():
        identity = await run_in_threadpool(service.execute, bearer_context.get(), {"action": "identity"})
        return [tool for tool in await mcp.list_tools() if allowed(identity["result"]["role"], tool.name, service.mode)]

    async def command(request):
        try:
            payload = Command.model_validate(await request.json())
            result = await run_in_threadpool(service.execute, bearer_context.get(), payload.model_dump())
            return JSONResponse(result)
        except PermissionError as error:
            return JSONResponse({"error": str(error)}, status_code=403)
        except (ValueError, KeyError) as error:
            return JSONResponse({"error": str(error)[:500]}, status_code=409 if "STALE" in str(error) else 422)
        except NativeError as error:
            return JSONResponse({"error": str(error), "source": error.source}, status_code=error.status)
        except ProviderError as error:
            return JSONResponse({"error": str(error), "source": error.source}, status_code=error.status)

    async def ui_bridge(request):
        try:
            assertion = request.scope["qldapm_ui_assertion"]
            actor, payload = assertion["actor"], assertion["command"]
            if assertion['project']==6 and assertion['operation']!='command':
                raise PermissionError('ENGINEERING_BRIDGE_OPERATION_DENIED')
            if assertion["operation"] == "confirm":
                service.keys(payload, {"id", "hash"}, {"id", "hash"})
                result = await run_in_threadpool(service.confirm, actor, payload["id"], payload["hash"])
            elif assertion["operation"] == "qa_review":
                from .native_qa import decide_actor
                service.keys(payload, {"id", "hash", "decision"}, {"id", "hash", "decision"})
                result = {'result': await run_in_threadpool(decide_actor, service, actor,
                    payload['id'], payload['decision'], payload['hash'])}
            elif assertion['operation']=='phase_review':
                from .native_phase import review
                service.keys(payload,{'id','hash','decision'},{'id','hash','decision'})
                result={'result':await run_in_threadpool(review,service,actor,payload['id'],payload['decision'],payload['hash'])}
            else:
                if assertion['project']==6:
                    payload={**payload,'project_id':6}
                result = await run_in_threadpool(service.execute_actor, actor, payload)
            return JSONResponse(result)
        except PermissionError as error:
            return JSONResponse({"error": str(error)}, status_code=403)
        except (ValueError, KeyError) as error:
            err_str = str(error)
            status_code = 409 if any(k in err_str for k in ("STALE", "CONFLICT", "ACTIVE", "LOCKED")) else 422
            return JSONResponse({"error": err_str[:500], "code": err_str.split()[0] if err_str else "ERROR"}, status_code=status_code)
        except (NativeError, ProviderError) as error:
            return JSONResponse({"error": str(error), "source": error.source}, status_code=error.status)

    async def proposal_decision(request):
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise ValueError("PROPOSAL_DECISION_OBJECT_REQUIRED")
            service.keys(payload, {"decision", "hash"}, {"decision", "hash"})
            result = await run_in_threadpool(service.decide_proposal, bearer_context.get(), request.path_params["id"],
                payload["decision"], payload["hash"])
            return JSONResponse(result)
        except PermissionError as error:
            return JSONResponse({"error": str(error)}, status_code=403)
        except (ValueError, KeyError, TypeError) as error:
            return JSONResponse({"error": str(error)[:500]}, status_code=409)
        except (NativeError, ProviderError) as error:
            return JSONResponse({"error": str(error), "source": error.source}, status_code=error.status)

    async def feedback_decision(request):
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise ValueError('FEEDBACK_DECISION_OBJECT_REQUIRED')
            service.keys(payload, {'decision','hash'}, {'decision','hash'})
            result = await run_in_threadpool(service.decide_feedback, bearer_context.get(), request.path_params['id'],
                payload['decision'], payload['hash'])
            return JSONResponse({'result':result})
        except PermissionError as error:
            return JSONResponse({'error':str(error)},status_code=403)
        except (ValueError,KeyError,TypeError) as error:
            return JSONResponse({'error':str(error)[:500]},status_code=422)
        except NativeError as error:
            return JSONResponse({'error':str(error),'source':error.source},status_code=error.status)

    async def phase_decision(request):
        try:
            payload=await request.json()
            if not isinstance(payload,dict):raise ValueError('PHASE_DECISION_OBJECT_REQUIRED')
            service.keys(payload,{'decision','hash'},{'decision','hash'})
            from .native_phase import review
            actor=service.store.authenticate(bearer_context.get())['user_id']
            result=await run_in_threadpool(review,service,actor,request.path_params['id'],payload['decision'],payload['hash'])
            return JSONResponse({'result':result})
        except PermissionError as error:return JSONResponse({'error':str(error)},status_code=403)
        except (ValueError,KeyError,TypeError) as error:return JSONResponse({'error':str(error)[:500]},status_code=422)
        except NativeError as error:return JSONResponse({'error':str(error),'source':error.source},status_code=error.status)

    async def qa_decision(request):
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise ValueError('QA_DECISION_OBJECT_REQUIRED')
            service.keys(payload, {'decision','hash'}, {'decision','hash'})
            result = await run_in_threadpool(service.decide_qa_evidence, bearer_context.get(), request.path_params['id'],
                payload['decision'], payload['hash'])
            return JSONResponse({'result':result})
        except PermissionError as error:
            return JSONResponse({'error':str(error)},status_code=403)
        except (ValueError,KeyError,TypeError) as error:
            return JSONResponse({'error':str(error)[:500]},status_code=422)
        except NativeError as error:
            return JSONResponse({'error':str(error),'source':error.source},status_code=error.status)

    async def schema(request):
        return JSONResponse(openapi_document())

    async def resource(request):
        try:
            project=None
            if "/agent-runs" in request.url.path:
                action = "get_agent_trace" if request.url.path.endswith("/trace") else "get_agent_run" if "id" in request.path_params else "list_agent_runs"
                arguments, key = dict(request.query_params), None
                if "id" in request.path_params:
                    arguments["id"] = request.path_params["id"]
                    from .engineering import project_for_run
                    actor=store.authenticate(bearer_context.get())['user_id']
                    project=project_for_run(service,actor,arguments['id'])
                for name in ("limit", "offset"):
                    if name in arguments:
                        arguments[name] = int(arguments[name])
            elif request.method == "POST":
                action, arguments = "start_ai_run", await request.json()
                key = request.headers.get("idempotency-key")
            elif "/control-center" in request.url.path:
                binding = store.authenticate(bearer_context.get())
                actor = binding["user_id"]
                result = await run_in_threadpool(service.control_center_state, actor, dict(request.query_params))
                return JSONResponse({"result": result, "correlation_id": str(uuid.uuid4())})
            elif request.url.path.endswith("/insights"):
                action, arguments, key = "get_insights", dict(request.query_params), None
            else:
                action = "get_ai_run" if "/ai-runs/" in request.url.path else "get_proposal"
                arguments, key = {"id": request.path_params["id"]}, None
            result = await run_in_threadpool(service.execute, bearer_context.get(), {"action": action, "arguments": arguments, "idempotency_key": key,'project_id':project})
            return JSONResponse(result)
        except PermissionError as error:
            return JSONResponse({"error": str(error)}, status_code=403)
        except (ValueError, KeyError) as error:
            return JSONResponse({"error": str(error)[:500]}, status_code=422)
        except (ProviderError, NativeError) as error:
            return JSONResponse({"error": str(error), "source": error.source}, status_code=error.status)

    @asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            store.fail_daily_brief()
            service.start_dispatcher()
            service.start_knowledge_worker()
            try:
                yield
            finally:
                await run_in_threadpool(service.stop_knowledge_worker)
                await run_in_threadpool(service.stop_dispatcher)

    app = Starlette(routes=[Route("/health", lambda request: JSONResponse({"status": "ok"})),
                            Route("/api/v1/commands", command, methods=["POST"]),
                            Route("/api/v1/ai-runs", resource, methods=["POST"]),
                            Route("/api/v1/ai-runs/{id}", resource), Route("/api/v1/proposals/{id}", resource),
                            Route("/api/v1/proposals/{id}/decision", proposal_decision, methods=["POST"]),
                            Route('/api/v1/knowledge-feedback/{id}/decision',feedback_decision,methods=['POST']),
                            Route('/api/v1/qa-evidence/{id}/decision',qa_decision,methods=['POST']),
                            Route('/api/v1/native-phases/{id}/decision',phase_decision,methods=['POST']),
                            Route("/api/v1/agent-runs", resource), Route("/api/v1/agent-runs/{id}", resource),
                            Route("/api/v1/agent-runs/{id}/trace", resource),
                            Route("/api/v1/control-center/state", resource),
                            Route("/api/v1/insights", resource),
                            Route("/internal/ui", ui_bridge, methods=["POST"]),
                            Route("/api/v1/openapi.json", schema), Mount("/", app=mcp.streamable_http_app())], lifespan=lifespan)
    return Security(app, root, store, config, service)


class Security:
    def __init__(self, app, root, store, config, service):
        self.app, self.root, self.store, self.config = app, root, store, config
        self.service = service
        self.requests = defaultdict(deque)
        self.global_requests = deque()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        config_path = self.root / "config.json"
        config = json.loads(config_path.read_text()) if config_path.exists() else self.config
        allowed = set(config.get("hosts", ["127.0.0.1:8090", "localhost:8090", "gateway:8090"]))
        host = headers.get("host", "")
        origin = headers.get("origin")
        error, status, machine, provider = None, 401, False, False
        now = time.monotonic()
        while self.global_requests and now - self.global_requests[0] > 60:
            self.global_requests.popleft()
        if len(self.global_requests) >= 300:
            return await JSONResponse({"error": "RATE_LIMITED"}, status_code=429)(scope, receive, send)
        self.global_requests.append(now)
        if host not in allowed or (origin and origin not in {"https://" + h for h in allowed} | {"http://127.0.0.1:8090", "http://localhost:8090", "http://127.0.0.1:18089", "http://localhost:18089"}):
            error, status = "HOST_OR_ORIGIN_DENIED", 403
        elif scope["path"] == "/health":
            return await self.app(scope, receive, send)
        elif config.get("maintenance", False):
            error, status = "MAINTENANCE", 503
        elif scope['path']=='/internal/engineering/provider':
            machine,provider,token=True,True,''
        elif scope["path"].startswith("/internal/automation/") or MACHINE_HEADER in headers:
            queue = self.requests["automation"]
            while queue and now - queue[0] > 60:
                queue.popleft()
            if len(queue) >= 30:
                return await JSONResponse({"error": "RATE_LIMITED"}, status_code=429)(scope, receive, send)
            queue.append(now)
            from .n8n_lifecycle_outbox import PATH as LIFECYCLE_PATH
            from .integration_events import PATH as INTEGRATION_PATH
            if scope['path'] in {COMMAND_PATH,LIFECYCLE_PATH,INTEGRATION_PATH} and scope['method'] == 'POST':
                machine, token = True, ''
            else:
                response = await run_in_threadpool(status_response,self.root,self.store,scope,headers,self.service)
                return await response(scope, receive, send)
        elif scope["path"] == "/internal/ui":
            token = ""
        else:
            auth = headers.get("authorization", "")
            token = auth[7:] if auth.startswith("Bearer ") else ""
            try:
                binding = self.store.authenticate(token)
                queue = self.requests[digest(token)]
                now = time.monotonic()
                while queue and now - queue[0] > 60:
                    queue.popleft()
                if len(queue) >= 60:
                    error, status = "RATE_LIMITED", 429
                queue.append(now)
            except PermissionError:
                error = "INVALID_OR_EXPIRED_TOKEN"
        if error:
            self.store.record(None, "access_denied", scope["path"][:100], error)
            return await JSONResponse({"error": error, "source": "gateway"}, status_code=status)(scope, receive, send)
        body, size = [], 0
        body_deadline = time.monotonic() + (5 if machine else 15)
        while True:
            try:
                message = await asyncio.wait_for(receive(), timeout=max(0, body_deadline - time.monotonic()))
            except TimeoutError:
                return await JSONResponse({"error": "BODY_TIMEOUT"}, status_code=408)(scope, receive, send)
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > (8192 if machine else 1048576):
                return await JSONResponse({"error": "PAYLOAD_TOO_LARGE"}, status_code=413)(scope, receive, send)
            body.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        if machine:
            if provider:
                from .engineering_provider import response as provider_response
                response=await run_in_threadpool(provider_response,self.service,self.root,scope,headers,b''.join(body))
            elif scope['path'] == LIFECYCLE_PATH:
                from .n8n_lifecycle_outbox import observation_response
                response = await run_in_threadpool(observation_response,self.store,config,scope,headers,b''.join(body))
            elif scope['path'] == INTEGRATION_PATH:
                from .integration_events import response as integration_response
                response = await run_in_threadpool(integration_response,self.service,scope,headers,b''.join(body))
            else:
                response = await run_in_threadpool(command_response, self.root, self.store, scope, headers, b''.join(body), self.service)
            return await response(scope, receive, send)
        consumed = False
        if scope["path"] == "/internal/ui":
            try:
                scope["qldapm_ui_assertion"] = verify_assertion(self.store, config, b"".join(body), headers.get("x-qldapm-signature", ""))
            except (PermissionError, ValueError, KeyError, TypeError) as error:
                self.store.record(None, "ui_access_denied", "/internal/ui", type(error).__name__)
                return await JSONResponse({"error": "UI_ASSERTION_DENIED"}, status_code=403)(scope, receive, send)
        async def replay():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": b"".join(body), "more_body": False}
            return await receive()
        context = bearer_context.set(token)
        try:
            async def audited_send(message):
                if message["type"] == "http.response.start":
                    actor = scope.get("qldapm_ui_assertion", {}).get("actor") if scope["path"] == "/internal/ui" else binding["user_id"]
                    self.store.record(actor, "transport", scope["path"][:100], str(message["status"]))
                await send(message)
            await self.app(scope, replay, audited_send)
        finally:
            bearer_context.reset(context)


app = create_app() if os.environ.get("QLDAPM_AI_RUNTIME") else None

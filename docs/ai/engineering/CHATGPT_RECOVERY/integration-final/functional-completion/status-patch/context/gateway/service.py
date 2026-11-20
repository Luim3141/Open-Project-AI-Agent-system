import json
import re
import threading
import uuid
import hashlib
import hmac
import logging
import time
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .native import Native, NativeError
from .store import canonical, digest
from .workspace import Workspace
from .gemini import Gemini, ProviderError
from .ai_worker import run_isolated
from .presentation import requested_ids, action_requested, error_info, execution_report, safe_text
from .permissions import require, allowed, business_manager, AI_SYSTEM_OWNER, NATIVE_PERMISSIONS, SANDBOX_ONLY
from . import RUN_ROUND_LIMITS
from .local_queries import match_query, read_result, execute_query
from .agent_trace import bind_run, bind_proposal, current_run, reset_run
from . import daily_brief


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["engineering_report_schedule_get", "engineering_report_schedule_update", "engineering_notifications_list", "engineering_notifications_dismiss", "engineering_report_generate", "engineering_report_list", "engineering_report_get", "engineering_github_sync", "engineering_plan", "engineering_cancel", "engineering_resume", "engineering_status", "engineering_run_once", "engineering_control", "delete_work_package", "update_dependency", "delete_dependency", "create_dependency", "identity", "list_work_packages", "get_work_package", "get_project_options", "analyze", "create_work_package",
                    "update_work_package", "comment", "transition", "get_gate", "change_gate", "list_code",
                    "read_code", "write_code", "request_test", "propose_operation", "get_job", "request_status", "reconcile_request", "get_configuration",
                    "get_proposal", "reject_proposal", "get_assistant_status", "get_action_history", "start_ai_run", "get_ai_run", "get_insights", "get_permissions",
                    "list_agent_runs", "get_agent_run", "get_agent_trace", "cancel_agent_run", "knowledge_ingest", "knowledge_search", "knowledge_deindex", "knowledge_integrity", "weekly_summary", "sprint_risks", "get_report", "knowledge_sync_status", "knowledge_sync_retry", "get_control_center", "get_execution_monitor", "list_execution_monitors", "owner_inspect", "knowledge_file_ingest", "knowledge_file_search", "knowledge_file_read", "knowledge_incremental_sync", "knowledge_incremental_status", "knowledge_feedback_submit", "knowledge_feedback_get", "knowledge_feedback_apply", "bug_triage", "bug_propose", "wbs_draft", "wbs_get", "wbs_adopt", "wbs_next", "wbs_from_ba", "qa_evidence_capture", "qa_evidence_get", "qa_transition_prepare", "qa_test_run", "qa_test_get", "qa_evidence_from_run", "qa_evidence_list", "phase_draft", "phase_get", "phase_list", "phase_transition_prepare", "qa_application_proof_verify", "qa_application_proof_admit"]
    arguments: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=100)
    auto_execute: bool = Field(default=False, description="Legacy field; true is denied. PM must confirm the exact proposal separately.")
    project_id: int | None = Field(default=None, gt=0, strict=True)


MUTATIONS = {"engineering_run_once", "engineering_control", "delete_work_package", "update_dependency", "delete_dependency", "create_dependency", "reject_proposal", "create_work_package", "update_work_package", "comment", "transition", "change_gate", "write_code",
             "request_test", "propose_operation", "start_ai_run", "knowledge_ingest", "knowledge_deindex", "knowledge_sync_retry", "cancel_agent_run", "knowledge_file_ingest", "knowledge_incremental_sync", "knowledge_feedback_submit", "knowledge_feedback_apply", "bug_propose", "wbs_draft", "wbs_adopt", "wbs_next", "wbs_from_ba", "qa_evidence_capture", "qa_transition_prepare", "qa_test_run", "qa_evidence_from_run", "qa_application_proof_admit", "phase_draft", "phase_transition_prepare"}
PROPOSED_WRITES = {"delete_work_package", "update_dependency", "delete_dependency", "create_dependency", "create_work_package", "update_work_package", "comment", "transition", "change_gate", "write_code"}


class Service:
    def __init__(self, store, config, workspaces, native_factory=Native):
        self.store, self.config = store, config
        self.workspace = Workspace(workspaces)
        self.native_factory = native_factory
        self.gemini = Gemini(store.root)
        self._queue_guard = threading.Lock()
        self._queue_thread = None
        self._queue_stop = threading.Event()
        self._knowledge_stop = threading.Event()
        self._knowledge_thread = None
        self._native_scan_at = 0
        self._reporting_tick_at = 0
        self.mode = config.get("gateway_mode", "strict")
        if self.mode not in {"strict", "native"}:
            raise ValueError("GATEWAY_MODE_INVALID")
        from .workflow_pause import _global_pause_controller
        self.pause_controller = _global_pause_controller

    def execute(self, bearer, command):
        command = Command.model_validate(command)
        binding = self.store.authenticate(bearer)
        return self.execute_actor(binding["user_id"], command.model_dump())

    def native_actor(self, actor, deadline=None):
        native = self.native_factory(self.config["openproject_url"], self.store.credential(actor), self.config["project_id"])
        if deadline is not None:
            native.deadline = min(getattr(native, 'deadline', deadline), deadline)
        identity = native.identity(actor)
        if identity['role'] == AI_SYSTEM_OWNER and not (actor == 18 and self.config['project_id'] in (5, 6)
                and AI_SYSTEM_OWNER in identity.get('capabilities', [])):
            raise PermissionError('AI_SYSTEM_OWNER_CAPABILITY_REQUIRED')
        if str(actor) not in self.config["users"] or identity["role"] != self.config["users"][str(actor)]:
            raise PermissionError("USER_NOT_REGISTERED_OR_ROLE_CHANGED")
        return native, identity

    def daily_brief(self, command):
        return daily_brief.collect(self, command)

    def sprint_report(self, actor, args=None):
        args = args or {}
        self.keys(args, {"as_of_date", "sprint_id"}, set())
        if 'sprint_id' in args and (type(args['sprint_id']) is not int or args['sprint_id'] <= 0):
            raise ValueError('POSITIVE_NATIVE_SPRINT_ID_REQUIRED')
        native, identity = self.native_actor(actor)
        items = native.packages()
        selected, sprint = items, None
        if 'sprint_id' in args:
            sprint = next((row for row in native.sprints() if row['id'] == args['sprint_id']), None)
            if sprint is None:
                raise PermissionError('NATIVE_SPRINT_NOT_VISIBLE')
            selected = [item for item in items if (item.get('_links', {}).get('sprint') or {}).get('href')
                == f"/api/v3/sprints/{args['sprint_id']}"]
        as_of_date = None
        if "as_of_date" in args:
            try:
                if not isinstance(args['as_of_date'],str):
                    raise ValueError()
                as_of_date = date.fromisoformat(args["as_of_date"])
            except ValueError:
                raise ValueError("INVALID_AS_OF_DATE")
        user_map = {int(u_id): {"name": f"User {u_id}", "role": u_role} for u_id, u_role in self.config.get("users", {}).items()}
        from .sprint_report import generate_sprint_report
        report = generate_sprint_report(
            packages=selected,
            as_of_date=as_of_date,
            user_map=user_map,
            actor_id=actor,
            actor_role=identity["role"],
            project_id=self.config.get("project_id", 3),
            relations=native.relations(items),
            dependency_packages=items,
            sprint=sprint,
        )
        if sprint is not None:
            report['sprint'] = sprint
        return {**report,**self.store.save_report(actor,self.config['project_id'],'sprint_risk',report,items)}

    def role_alerts(self, actor, args=None):
        args = args or {}
        self.keys(args, {"as_of_date"}, set())
        native, identity = self.native_actor(actor)
        items = native.packages()
        as_of_date = None
        if "as_of_date" in args:
            try:
                as_of_date = date.fromisoformat(args["as_of_date"])
            except ValueError:
                raise ValueError("INVALID_AS_OF_DATE")
        from .role_alerts import _global_engine
        return _global_engine.evaluate(
            packages=items,
            actor_id=actor,
            actor_role=identity["role"],
            as_of_date=as_of_date,
            project_id=self.config.get("project_id", 3),
        )

    def workload_detection(self, actor, args=None):
        args = args or {}
        native, identity = self.native_actor(actor)
        items = native.packages()
        user_map = {int(u_id): {"name": f"User {u_id}", "role": u_role} for u_id, u_role in self.config.get("users", {}).items()}
        from .workload_detector import detect_workload_imbalance
        return detect_workload_imbalance(
            packages=items,
            users=user_map,
            project_id=self.config.get("project_id", 3),
        )

    def sprint_readiness(self, actor, args=None):
        args = args or {}
        native, identity = self.native_actor(actor)
        items = native.packages()
        from .sprint_readiness import evaluate_sprint_readiness
        return evaluate_sprint_readiness(
            packages=items,
            project_id=str(self.config.get("project_id", "QLDAPM")),
        )

    def weekly_report(self, actor, args=None, *, deadline=None):
        args = args or {}
        self.keys(args, {"as_of_date", "with_ai_summary"}, set())
        native, identity = self.native_actor(actor,deadline=deadline)
        items = native.packages()
        as_of_date = None
        if "as_of_date" in args:
            try:
                if not isinstance(args['as_of_date'],str):
                    raise ValueError()
                as_of_date = date.fromisoformat(args["as_of_date"])
            except ValueError:
                raise ValueError("INVALID_AS_OF_DATE")
        with_ai_summary = args.get("with_ai_summary", False)
        if type(with_ai_summary) is not bool:
            raise ValueError('WITH_AI_SUMMARY_BOOLEAN_REQUIRED')
        user_map = {int(u_id): {"name": f"User {u_id}", "role": u_role} for u_id, u_role in self.config.get("users", {}).items()}
        from .weekly_report import generate_weekly_report
        report=generate_weekly_report(
            packages=items,
            users=user_map,
            actor_id=actor,
            actor_role=identity["role"],
            as_of_date=as_of_date,
            project_id=self.config.get("project_id", 3),
            with_ai_summary=with_ai_summary,
            gemini_service=self.gemini if with_ai_summary else None,
        )
        return {**report,**self.store.save_report(actor,self.config['project_id'],'weekly_summary',report,items)}

    def handle_requirement_change(self, actor, event):
        user_map = {int(u_id): {"name": f"User {u_id}", "role": u_role} for u_id, u_role in self.config.get("users", {}).items()}
        from .qa_change_workflow import process_requirement_change
        return process_requirement_change(event, users=user_map)

    def control_center_state(self, actor, args=None):
        args = args or {}
        self.keys(args,{'limit','offset','task_id'})
        limit = int(args.get("limit", 20))
        offset = int(args.get("offset", 0))
        project_id = self.config.get("project_id", 3)
        _, identity = self.native_actor(actor)
        role = identity["role"]
        require(role, "analyze")

        from .control_center_state import get_control_center_state
        from .agent_status import get_agents_runtime_status
        from .quota_panel import get_quota_panel_data
        from .workflow_timeline import get_task_workflow_timeline
        from .tasks_progress import get_tasks_progress_report

        state = get_control_center_state(
            store=self.store,
            actor_id=actor,
            actor_role=role,
            project_id=project_id,
            limit=limit,
            offset=offset,
            config={**self.config,'gemini_multi_agent_enabled':self.gemini.multi_agent_settings().enabled},
        )
        try:
            policy = self.gemini.settings(require_enabled=False)
        except ProviderError:
            policy = None
        state["agent_status"] = get_agents_runtime_status(self.store, project_id,actor)
        state["quota_panel"] = get_quota_panel_data(self.store, actor, project_id, self.config,policy)
        with self.store.connect() as db:
            receipts=[json.loads(row[0]) for row in db.execute(
                'SELECT document FROM gemini_call_receipts WHERE actor=? ORDER BY rowid DESC LIMIT 50',(actor,))]
        state['live_execution']={'provider':'Gemini','model':policy.get('model') if policy else None,
            'recent_actor_provider_calls':receipts,'provider_remaining_quota':'unavailable',
            'configured_live_analysis':self.gemini.multi_agent_settings().enabled,
            'billing_configuration':'BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED'}
        seen=set()
        for receipt in receipts:
            name=receipt['agent']
            if name in seen or receipt['phase']!='generateContent':continue
            seen.add(name)
            if name in state['agent_status'].get('agents',{}):
                state['agent_status']['agents'][name]['last_provider_state']=receipt['state']
        state["workflow_timeline"] = get_task_workflow_timeline(self.store, actor, project_id, args.get("task_id"))
        state["tasks_progress"] = get_tasks_progress_report()
        state['progress']=self.store.execution_history(actor,project_id,limit=limit,offset=offset)
        return state

    def execute_actor(self, actor, command, confirmed=False):
        # Called only after Bearer authentication or a verified UI/local assertion.
        command = Command.model_validate(command)
        if command.project_id is not None and command.project_id != self.config['project_id']:
            from .engineering import scoped_service
            scoped = scoped_service(self, command.project_id)
            return scoped.execute_actor(actor,command.model_copy(update={'project_id':None}).model_dump(),confirmed=confirmed)
        if self.config.get('_engineering_scope') and command.action not in {'engineering_report_schedule_get','engineering_report_schedule_update','engineering_notifications_list','engineering_notifications_dismiss','engineering_report_generate','engineering_report_list','engineering_report_get','engineering_github_sync','engineering_plan','engineering_cancel','engineering_resume','engineering_status','engineering_run_once','engineering_control','get_work_package','knowledge_ingest','knowledge_search','knowledge_file_ingest','knowledge_file_search','knowledge_file_read','get_ai_run','get_execution_monitor','list_execution_monitors','get_agent_run','get_agent_trace','sprint_risks','get_report','bug_triage','wbs_draft','wbs_get','get_project_options'}:
            raise PermissionError('ENGINEERING_CAPABILITY_REQUIRED')
        if command.action.startswith('engineering_'):
            from . import engineering
            from .engineering_owner_control import attempt
            if command.auto_execute or confirmed:
                raise PermissionError('ENGINEERING_EXPLICIT_OPERATION_REQUIRED')
            owner_request_key=None
            if command.action in {'engineering_control','engineering_plan','engineering_cancel','engineering_resume','engineering_run_once','engineering_github_sync','engineering_report_schedule_update','engineering_notifications_dismiss','engineering_report_generate'} and command.idempotency_key:
                # Namespace operator receipts away from Native-publication and generic command keys.
                engineering.authorized(self,actor)
                owner_request_key='owner6:'+digest(command.idempotency_key)
                try:
                    previous=self.store.begin(actor,owner_request_key,{'action':command.action,'project_id':6,'arguments':command.arguments})
                except ValueError as error:
                    if str(error)=='IDEMPOTENCY_KEY_REUSED':
                        raise ValueError('ENGINEERING_IDEMPOTENCY_CONFLICT') from None
                    if str(error)=='OUTCOME_UNKNOWN_RECONCILE_FIRST':
                        raise ValueError('ENGINEERING_COMMAND_CONFLICT_PENDING_RECONCILE_FIRST') from None
                    raise
                if previous is not None:
                    return previous
            if command.action=='engineering_status':
                self.keys(command.arguments,set(),set())
                result=engineering.status(self,actor)
            elif command.action=='engineering_control':
                self.keys(command.arguments,{'mode','expected_revision'},{'mode'})
                result=attempt(self,actor,command.arguments['mode'],lambda:engineering.control(self,actor,command.arguments['mode'],command.arguments.get('expected_revision'),command.idempotency_key),command.idempotency_key)
            elif command.action=='engineering_plan':
                from .engineering_planning import PLANNING
                self.keys(command.arguments,{'native_id','lock_version','feedback'},{'native_id','lock_version'})
                result=attempt(self,actor,'PLAN',lambda:engineering.admit(self,actor,{**command.arguments,'unit':PLANNING},command.idempotency_key),command.idempotency_key)
            elif command.action=='engineering_cancel':
                from .engineering_lifecycle import cancel
                self.keys(command.arguments,{'run_id'},{'run_id'})
                result=attempt(self,actor,'CANCEL',lambda:cancel(self,actor,command.arguments['run_id']),command.idempotency_key)
                from .engineering_owner_control import command_result
                result=command_result(self,actor,'CANCEL',result,reason='CANCEL_REQUESTED' if result['state']=='cancelling' else 'CANCEL_CONFIRMED' if result.get('cancelled') else 'RUN_ALREADY_TERMINAL',request_id=command.idempotency_key)
            elif command.action=='engineering_resume':
                from .engineering_lifecycle import resume
                self.keys(command.arguments,{'run_id','checkpoint_version'},{'run_id','checkpoint_version'})
                result=attempt(self,actor,'RESUME',lambda:resume(self,actor,command.arguments['run_id'],command.arguments['checkpoint_version']),command.idempotency_key,context=command.arguments)
                from .engineering_owner_control import command_result
                result=command_result(self,actor,'RESUME',result,reason='RESUME_ADMITTED' if result.get('mode') else 'RUN_ALREADY_TERMINAL',request_id=command.idempotency_key)
            elif command.action=='engineering_github_sync':
                self.keys(command.arguments,set(),set())
                result=attempt(self,actor,'GITHUB_SYNC',lambda:engineering.github_sync(self,actor,command.idempotency_key),command.idempotency_key)
            elif command.action=='engineering_report_schedule_get':
                from . import engineering_reporting
                self.keys(command.arguments,set(),set())
                result=engineering_reporting.get_schedule(self,actor)
            elif command.action=='engineering_report_schedule_update':
                from . import engineering_reporting
                self.keys(command.arguments,{'daily_enabled','daily_hour','daily_minute','weekly_enabled','weekly_day','weekly_hour','weekly_minute'},set())
                result=attempt(self,actor,'REPORT_SCHEDULE_UPDATE',lambda:engineering_reporting.update_schedule(self,actor,command.arguments),command.idempotency_key)
            elif command.action=='engineering_notifications_list':
                from . import engineering_reporting
                self.keys(command.arguments,{'limit','unread_only'},set())
                result=engineering_reporting.list_notifications(self,actor,int(command.arguments.get('limit',10)),bool(command.arguments.get('unread_only',False)))
            elif command.action=='engineering_notifications_dismiss':
                from . import engineering_reporting
                self.keys(command.arguments,{'id'},{'id'})
                result=attempt(self,actor,'NOTIFICATION_DISMISS',lambda:engineering_reporting.dismiss_notification(self,actor,command.arguments['id']),command.idempotency_key)
            elif command.action=='engineering_report_generate':
                from . import engineering_reporting
                self.keys(command.arguments,{'report_type','include_narrative'},set())
                result=attempt(self,actor,'REPORT_GENERATE',lambda:engineering_reporting.generate_report(self,actor,command.arguments.get('report_type','ON_DEMAND'),bool(command.arguments.get('include_narrative',False))),command.idempotency_key)
            elif command.action=='engineering_report_list':
                from . import engineering_reporting
                self.keys(command.arguments,{'limit','offset'},set())
                result=engineering_reporting.list_reports(self,actor,int(command.arguments.get('limit',10)),int(command.arguments.get('offset',0)))
            elif command.action=='engineering_report_get':
                from . import engineering_reporting
                self.keys(command.arguments,{'id'},{'id'})
                result=engineering_reporting.get_report(self,actor,command.arguments['id'])
            else:
                result=attempt(self,actor,'RUN_ONCE',lambda:engineering.admit(self,actor,command.arguments,command.idempotency_key),command.idempotency_key)
                from .engineering_owner_control import command_result
                eligible=not result.get('requires_reconciliation') and (not result.get('deduplicated') or result.get('mode') is not None)
                result=command_result(self,actor,'RUN_ONCE',result,eligible,
                    'RUN_ADMITTED' if eligible else 'RECONCILIATION_REQUIRED' if result.get('requires_reconciliation') else 'NO_ELIGIBLE_WORK',command.idempotency_key)
            if command.action in {'engineering_plan','engineering_github_sync','engineering_report_schedule_update','engineering_notifications_dismiss','engineering_report_generate'}:
                from .engineering_owner_control import command_result
                engineering.setup(self.store)
                result=command_result(self,actor,command.action.removeprefix('engineering_').upper(),result,
                    result.get('status')!='SYNC_FAILED',result.get('status') if command.action=='engineering_github_sync' else None,command.idempotency_key)
            response={'result':result,'correlation_id':self.store.record(actor,command.action,'project6','ok')}
            if owner_request_key is not None:
                self.store.finish(actor,owner_request_key,response)
            return response
        try:
            native, identity = self.native_actor(actor)
            require(identity["role"], command.action, self.mode)
            if command.auto_execute:
                raise PermissionError("PM_APPROVAL_REQUIRED; request a proposal and confirm its exact hash")
            if confirmed and command.action in PROPOSED_WRITES and not business_manager(identity["role"]):
                raise PermissionError("PM_APPROVAL_REQUIRED")
            if self.mode == "native" and command.action in {"change_gate", "get_gate"}:
                raise ValueError("CUSTOM_GATE_UNSUPPORTED_IN_NATIVE_MODE")
            if self.mode == "strict" and command.action in {"create_work_package", "update_work_package", "comment", "transition", "change_gate"}:
                try:
                    capability = native.call("/api/v3/qldapm/capabilities")
                except NativeError as error:
                    if error.status == 404:
                        raise NativeError(503, "CORE_GATES_NOT_ACTIVATED; live business writes remain disabled") from None
                    raise
                if capability.get("project_id") != self.config["project_id"] or capability.get("gate_schema") != 2 or capability.get("enforced") is not True:
                    raise NativeError(503, "CORE_GATES_NOT_VERIFIED")
            if command.action in MUTATIONS:
                if command.action == 'qa_application_proof_admit':
                    from .application_qa_intake import load_verified
                    self.keys(command.arguments, {'id'}, {'id'})
                    load_verified(self, identity, native, command.arguments['id'])
                if command.action in {'phase_draft','phase_transition_prepare'}:
                    from .native_phase import validate_request
                    phase_args=validate_request(self,actor,command.action,command.arguments)
                    if command.action=='phase_transition_prepare':
                        self.preview(identity,native,Command(action='transition',arguments=phase_args))
                if command.action == 'qa_evidence_capture' and (identity['role'] != 'QA' or current_run.get() is not None):
                    raise PermissionError('QA_NATIVE_AUTHOR_REQUIRED')
                if command.action == "start_ai_run":
                    return self.start_run(identity, command.arguments, command.model_dump(), native)
                if command.action == 'knowledge_file_ingest':
                    from .file_knowledge import load_source
                    self.keys(command.arguments, {'source_key'}, {'source_key'})
                    file_doc = load_source(self.config, identity, command.arguments['source_key'])
                if command.action == 'knowledge_incremental_sync':
                    self.keys(command.arguments, set())
                if command.action == 'knowledge_feedback_apply':
                    from .knowledge_feedback import read
                    self.keys(command.arguments, {'id'}, {'id'})
                    if not read(self,identity,native,command.arguments['id'])['source_current']:
                        raise NativeError(409,'FEEDBACK_SOURCE_CHANGED')
                if command.action == 'qa_test_run':
                    from .native_qa_runs import target
                    self.keys(command.arguments, {'native_id'}, {'native_id'})
                    target(native, command.arguments['native_id'])
                if command.action == 'create_dependency':
                    from .native_dependency import arguments
                    arguments(self,command.arguments,sealed=confirmed)
                if command.action in {'update_dependency','delete_dependency'}:
                    from .native_dependency_change import arguments
                    arguments(self,command.arguments,command.action,sealed=confirmed)
                if command.action == 'delete_work_package':
                    from .native_deletion import arguments
                    arguments(self,command.arguments,sealed=confirmed)
                    if current_run.get() is not None:raise PermissionError('NATIVE_DELETE_DIRECT_HUMAN_REQUEST_REQUIRED')
                existing = self.store.begin(actor, command.idempotency_key, command.model_dump())
                if existing and command.action == 'knowledge_file_ingest' and existing['result']['source_sha256'] != file_doc.metadata['source_sha256']:
                    raise NativeError(409, 'FILE_REVISION_CHANGED_USE_NEW_REQUEST_KEY')
                if existing is not None:
                    if existing.get('error')=='NATIVE_REJECTED':raise NativeError(existing['status'],'OPENPROJECT_'+str(existing['status']))
                    if command.action=='phase_draft':
                        from .native_phase import get
                        return {**existing,'result':get(self,actor,existing['result']['id'])}
                    if command.action in {'qa_evidence_capture', 'qa_evidence_from_run', 'qa_application_proof_admit'}:
                        from .native_qa import read
                        return {**existing,'result':read(self,identity,native,existing['result']['id'])}
                    if command.action == 'qa_test_run':
                        from .native_qa_runs import read
                        return {**existing, 'result': read(self, identity, native, existing['result']['id'])}
                    return existing
            if command.action in PROPOSED_WRITES and not confirmed:
                preview = self.preview(identity, native, command)
                binding=current_run.get()
                origin={'_origin_run_id':binding[1].run_id} if binding and binding[0].root.resolve()==self.store.root.resolve() and binding[1].actor_id==actor else {}
                result = self.store.propose(actor, {**command.model_dump(), "preview": preview, "_gateway_mode": self.mode, **origin})
            else:
                result = self.perform(identity, native, command.action, command.arguments, command.idempotency_key)
            correlation = self.store.record(actor, command.action, command.arguments.get("id", "qldapm-local"), "ok",
                version=command.arguments.get("lock_version", command.arguments.get("expected_hash")))
            response = {"result": result, "correlation_id": correlation}
            from .workflow_commands import record as observe_command
            try:
                observation=observe_command(self,actor,command,result,correlation)
                if observation:response['automation']=observation
            except Exception as error:
                logging.getLogger(__name__).warning('Command observation unavailable: %s',type(error).__name__)
                response['automation']={'state':'OBSERVATION_UNAVAILABLE','business_command_completed':True}
            if command.action in MUTATIONS:
                target = None
                if confirmed and command.action in {'delete_work_package','create_work_package','update_work_package','comment','transition','change_gate'}:
                    target = result['id'] if command.action == 'create_work_package' else command.arguments['id']
                dependency_ids = [row['id'] for row in result['readback']] if confirmed and command.action in {'create_dependency','update_dependency','delete_dependency'} else None
                if dependency_ids is not None:
                    self.store.finish(actor,command.idempotency_key,response,knowledge_ids=dependency_ids)
                else:
                    self.store.finish(actor,command.idempotency_key,response,knowledge_id=target)
            return response
        except Exception as error:
            self.store.record(actor, command.action, command.arguments.get("id", "qldapm-local"), type(error).__name__)
            if (command.action in {'delete_work_package','create_dependency','update_dependency','delete_dependency','create_work_package','update_work_package','comment','transition','qa_transition_prepare'} and
                    isinstance(error,NativeError) and error.status in {400,401,403,404,409,412,422}):
                self.store.finish(actor,command.idempotency_key,{'error':'NATIVE_REJECTED','status':error.status,'outcome_unknown':False})
            # Unknown writes remain pending; never blindly retry a timed-out POST.
            raise

    def start_run(self, who, args, command=None, native=None):
        self.keys(args, {"prompt", "allow_routine_writes", "write_scope_ids", "run_class", "context_task_id", "conversation_id", "engine"}, {"prompt"})
        engine = args.get('engine', 'gemini')
        if not isinstance(engine,str) or engine not in {'gemini','gemini_read','supervisor','supervisor_gemini'}:
            raise ValueError('AI_ENGINE_INVALID')
        business_read_only=engine=='gemini_read'
        if business_read_only and args.get('allow_routine_writes',False):raise PermissionError('READ_ONLY_WRITE_CONSENT_DENIED')
        kind = args.get("run_class", "interactive")
        if not isinstance(kind, str) or kind not in RUN_ROUND_LIMITS:
            raise ValueError("AI_QUEUE_KIND_INVALID")
        allow, scope = args.get("allow_routine_writes", False), args.get("write_scope_ids", [])
        if not isinstance(scope, list) or any(type(identifier) is not int or identifier <= 0 for identifier in scope):
            raise ValueError("RUN_WRITE_SCOPE_POSITIVE_IDS")
        if type(allow) is not bool or (allow and self.mode != "native"):
            raise PermissionError("RUN_WRITE_CONSENT_REQUIRES_NATIVE_MODE_AND_BOOLEAN")
        if not isinstance(args["prompt"], str) or not 1 <= len(args["prompt"]) <= 8000:
            raise ValueError("PROMPT_REQUIRED_MAX_8000")
        from .planner import is_write_intent
        business_write = is_write_intent(args['prompt'])
        if engine == 'gemini' and business_write and not business_manager(who['role']) and any(
                action_requested(args['prompt'], action) for action in ('create_work_package', 'update_work_package', 'transition')):
            raise PermissionError('PM_ONLY_BUSINESS_WRITE_REQUIRED')
        if allow and not scope:
            scope = requested_ids(args['prompt'])
        if business_read_only:
            scope=scope or requested_ids(args['prompt'])
            if not scope or len(scope)>10:raise ValueError('LIVE_READ_REQUIRES_1_TO_10_NATIVE_IDS')
        if engine in {'gemini','gemini_read'} and scope:
            if native is None:
                raise ValueError('NATIVE_CONTEXT_REQUIRED')
            for identifier in scope:
                native.package(identifier)
        # The explicit Supervisor engine drafts proposals; legacy Gemini business tools remain separate.
        live_requested=(engine=='supervisor_gemini' or engine=='gemini' and not (allow or scope or business_write) and self.mode=='native' and self.gemini.multi_agent_settings().enabled
                        and not match_query(args['prompt']) and not {'context_task_id','conversation_id'} & args.keys())
        if live_requested:
            if self.mode!='native' or not self.gemini.multi_agent_settings().enabled:
                raise ProviderError('GEMINI_MULTI_AGENT_DISABLED')
            if is_write_intent(args['prompt']) and not business_manager(who['role']):
                raise PermissionError('PM_ONLY_BUSINESS_WRITE_REQUIRED')
            policy=self.gemini.validate_prompt(args['prompt'])
        if engine == 'supervisor' or live_requested:
            if allow or scope or 'context_task_id' in args or 'conversation_id' in args:
                raise PermissionError('SUPERVISOR_READ_ONLY_EXPLICIT_IDS_REQUIRED')
            if len(requested_ids(args['prompt'])) > 10:
                raise ValueError('SUPERVISOR_MAX_10_EXPLICIT_IDS')
            from .agent_models import AgentTask
            from .presentation import safe_text
            if command:
                command = {**command,'arguments':{**command['arguments'],'prompt':safe_text(args['prompt'])},
                    '_input_sha256':digest(canonical(command))}
            # The command is the idempotency identity; generated task metadata must not change it.
            if command and command.get('idempotency_key'):
                with self.store.connect() as db:
                    row = db.execute('SELECT payload,result FROM requests WHERE actor=? AND key=?',
                        (who['user_id'],command['idempotency_key'])).fetchone()
                if row:
                    if json.loads(row['payload']) == command and row['result']:
                        return json.loads(row['result'])
                    raise ValueError('IDEMPOTENCY_KEY_REUSED')
            now = time.time()
            task = AgentTask(task_id=str(uuid.uuid4()), actor_id=who['user_id'],project_id=self.config['project_id'],
                conversation_id=str(uuid.uuid4()),agent='supervisor',instruction=safe_text(args['prompt']),
                run_class=kind,created_at=now,expires_at=now+600)
            self.store.create_agent_task(who['user_id'],self.config['project_id'],task)
            response = self.store.enqueue_run(who['user_id'], {'prompt':task.instruction,'engine':'supervisor_gemini' if live_requested else 'supervisor',
                'allow_routine_writes':False,'write_scope_ids':[], 'policy_sha256':digest(canonical(policy)) if live_requested else digest('LOCAL_SUPERVISOR_V1')}, command,kind,task)
            if live_requested:
                waiting=self.store.provider_wait(policy)
                if waiting:self.store.wait_queued(waiting)
            self.start_dispatcher()
            return response
        prompt = " ".join(args["prompt"].casefold().strip().rstrip("?.!").split())
        context_read_requested = prompt in {"đọc task đó", "xem task đó", "đọc công việc đó", "xem công việc đó"}
        if context_read_requested and not {"context_task_id", "conversation_id"} <= args.keys():
            raise ValueError("CONTEXT_TASK_AND_CONVERSATION_REQUIRED")
        if "context_task_id" in args or "conversation_id" in args:
            if not {"context_task_id", "conversation_id"} <= args.keys():
                raise ValueError("CONTEXT_TASK_AND_CONVERSATION_REQUIRED")
            if allow or scope:
                raise PermissionError("CONTEXT_REFERENCE_IS_READ_ONLY; select current IDs and give new write consent")
            if not context_read_requested:
                raise ValueError("CONTEXT_READ_ONLY; use explicit current IDs for other actions")
            context = {"task_id": args["context_task_id"], "conversation_id": args["conversation_id"]}
            route, current = self.context_read(who, native, context)
            result = {**read_result(who, self.config["project_id"], route, current), "context_reference": context}
            return self.store.complete_read_run(who["user_id"], result, command)
        route = None if business_read_only else match_query(args["prompt"])
        if route:
            if native is None:
                raise ValueError("NATIVE_CONTEXT_REQUIRED")
            result = execute_query(self, who, native, route)
            return self.store.complete_read_run(who["user_id"], read_result(who, self.config["project_id"], route, result), command)
        policy = self.gemini.validate_prompt(args["prompt"])
        response = self.store.enqueue_run(who["user_id"], {"prompt": args["prompt"],
            "allow_routine_writes": allow, "write_scope_ids": scope,
            "business_read_only":business_read_only,
            "native_project_id":self.config['project_id'],
            "policy_sha256": digest(canonical(policy))}, command, kind)
        if policy.get("project") and policy.get("limits"):
            waiting = self.store.provider_wait(policy)
            if waiting:
                self.store.wait_queued(waiting)
        self.start_dispatcher()
        return response

    def context_read(self, who, native, context):
        if not isinstance(context, dict) or set(context) != {"task_id", "conversation_id"}:
            raise ValueError("CONTEXT_REFERENCE_INVALID")
        try:
            if any(not isinstance(value, str) or str(uuid.UUID(value)) != value for value in context.values()):
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError("CONTEXT_IDS_INVALID") from None
        task = self.store.agent_task(who["user_id"], self.config["project_id"], context["task_id"])
        if task.conversation_id != context["conversation_id"]:
            raise PermissionError("CONTEXT_CONVERSATION_MISMATCH")
        if task.expires_at <= time.time():
            raise ValueError("CONTEXT_EXPIRED; read current work package with an explicit ID")
        if len(task.references) != 1:
            raise ValueError("CONTEXT_AMBIGUOUS; select one current work package")
        if native is None:
            raise ValueError("NATIVE_CONTEXT_REQUIRED")
        reference = task.references[0]
        route = ("read", "get_work_package", {"id": reference.work_package_id})
        current = self.perform(who, native, route[1], route[2])
        if current.get("lockVersion") != reference.lock_version:
            raise ValueError("CONTEXT_STALE; read current work package with an explicit ID")
        return route, current

    def start_dispatcher(self):
        with self._queue_guard:
            if self._queue_thread is not None:
                return
            self._queue_stop.clear()
            self.gemini.lock.acquire()
            self._queue_thread = threading.Thread(target=self.dispatch_runs, daemon=True)
            self._queue_thread.start()

    def start_knowledge_worker(self):
        if self._knowledge_thread is not None:
            return
        self._knowledge_stop.clear()
        def dispatch():
            while not self._knowledge_stop.is_set():
                from .integration_events import dispatch as dispatch_integration
                from .engineering_github_poll import dispatch as dispatch_github
                for background in (dispatch_integration,dispatch_github):
                    try:background(self)
                    except Exception as error:
                        logging.getLogger(__name__).warning('Integration tick unavailable: %s',type(error).__name__)
                try:
                    self.process_knowledge_sync()
                    from .notification_delivery import process_pending
                    process_pending(self.store)
                    from .n8n_lifecycle_outbox import deliver_pending
                    deliver_pending(self.store,self.config.get('n8n_lifecycle',{}))
                    settings = self.config.get('native_incremental_sync', {})
                    if settings.get('enabled') is True and time.monotonic() >= self._native_scan_at:
                        self._native_scan_at = time.monotonic()+60
                        if type(settings.get('actor')) is not int:
                            raise ValueError('NATIVE_INDEX_ACTOR_REQUIRED')
                        from .native_incremental import scan
                        try:
                            scan(self,settings['actor'],authority='machine')
                        except Exception as error:
                            # A failed project scan must not starve the independent Project6 cache refresh.
                            logging.getLogger(__name__).warning('Native knowledge scan unavailable for project %s: %s',
                                self.config['project_id'],type(error).__name__)
                        if self.config.get('engineering',{}).get('enabled') is True:
                            from .engineering import scoped_service
                            try:
                                scan(scoped_service(self,6),20,authority='machine')
                            except Exception as error:
                                logging.getLogger(__name__).warning('Native knowledge scan unavailable for project 6: %s',
                                    type(error).__name__)
                    # Background reporting scheduler tick (Finding B)
                    if self.config.get('engineering', {}).get('enabled') is True and time.monotonic() >= self._reporting_tick_at:
                        self._reporting_tick_at = time.monotonic() + 30
                        from .engineering import scoped_service
                        from . import engineering_reporting
                        engineering_reporting.check_and_run_scheduled_reports(scoped_service(self, 6), 20)
                except Exception as error:
                    # SQLite contention must not permanently stop the durable retry consumer.
                    logging.getLogger(__name__).warning('Knowledge worker unavailable: %s',type(error).__name__)
                self._knowledge_stop.wait(1)
        self._knowledge_thread=threading.Thread(target=dispatch,daemon=True)
        self._knowledge_thread.start()

    def stop_knowledge_worker(self):
        self._knowledge_stop.set()
        if self._knowledge_thread:
            self._knowledge_thread.join(timeout=1)

    def process_knowledge_sync(self):
        claim=self.store.claim_knowledge_sync()
        if not claim:
            return False
        token=None
        try:
            source_key = claim['request_key'].removeprefix('dependency:')
            target=self
            if source_key.startswith('native-event-6-'):
                from .engineering import scoped_service
                target=scoped_service(self,6)
            if source_key.startswith('proposal-'):
                proposal=self.store.proposal(claim['actor'],source_key[9:].split(':native:',1)[0])
                if proposal['command']['action']=='delete_work_package':
                    from .native_deletion import synchronize
                    result=synchronize(self,claim)
                    self.store.finish_knowledge_sync(claim,result)
                    self.store.record(claim['actor'],'knowledge_sync',claim['id'],'SIGNED_NATIVE_TOMBSTONE_APPLIED')
                    return True
                token=bind_proposal(self.store,claim['actor'],self.config['project_id'],proposal)
            result=target.execute_actor(claim['actor'],{'action':'knowledge_ingest','arguments':{'id':claim['native_id']},
                'idempotency_key':'rag-'+claim['id']+'-'+claim['lease']})['result']
            canonical_result=target.sync_canonical_native(claim['actor'],claim['native_id'])
            result={**result,'canonical':canonical_result,
                'vector_indexed':result.get('vector_indexed') is True and canonical_result.get('vector_indexed') is True}
            binding=current_run.get()
            if binding:result.update(run_id=binding[1].run_id,trace_id=binding[1].trace_id)
        except Exception:
            self.store.finish_knowledge_sync(claim,None,error='KNOWLEDGE_SYNC_FAILED')
            self.store.record(claim['actor'],'knowledge_sync',claim['id'],'KNOWLEDGE_SYNC_FAILED')
        else:
            self.store.finish_knowledge_sync(claim,result)
        finally:
            reset_run(token)
        return True

    def sync_canonical_native(self, actor, identifier):
        from contextlib import closing
        from dataclasses import asdict
        from .knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
        from .knowledge_ingestion import KnowledgeIngester,IngestionStatus
        from .vector_client import VectorClient
        from .openproject_loader import work_package_to_document
        native,who=self.native_actor(actor)
        require(who['role'],'knowledge_ingest',self.mode)
        item=native.package(identifier)
        document=work_package_to_document(item,str(self.config['project_id']))
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.store.root/'knowledge.sqlite')))
        with closing(VectorClient()) as vector:
            result=KnowledgeIngester(storage,vector).ingest(document)
        if result.status==IngestionStatus.FAILED:
            raise NativeError(503,'KNOWLEDGE_CANONICAL_SYNC_PENDING')
        if native.package(identifier)['lockVersion']!=item['lockVersion']:
            raise NativeError(409,'KNOWLEDGE_SOURCE_CHANGED_RETRY')
        return {**asdict(result),'native_id':identifier,'lock_version':item['lockVersion']}

    def stop_dispatcher(self):
        self._queue_stop.set()
        # Let an in-flight isolated worker reach its hard deadline; never requeue it on shutdown.
        with self._queue_guard:
            thread = self._queue_thread
        if thread:
            thread.join(timeout=1)

    def dispatch_runs(self):
        try:
            from .business_runs import resume
            resume(self)
            while not self._queue_stop.is_set():
                if self.store.queue_pending():
                    try:
                        policy = self.gemini.settings()
                        waiting = self.store.provider_wait(policy) if policy.get("project") and policy.get("limits") else None
                    except ProviderError:
                        waiting = {"queue_state": "BLOCKED_KEY_OR_MODEL", "retry_at": None}
                    if waiting:
                        local = self.store.claim_run(local_only=True)
                        if local:
                            self.process_run(local)
                            continue
                        self.store.wait_queued(waiting)
                        delay = (waiting["retry_at"] - time.time()) if waiting["retry_at"] else 30
                        self._queue_stop.wait(min(30, max(0.5, delay)))
                        continue
                run = self.store.claim_run()
                if run is None:
                    resume(self)  # Expired interrupted workers become terminal during claim_run; never replay their tools.
                    with self._queue_guard:
                        if not self.store.queue_pending():
                            self.gemini.lock.release()
                            self._queue_thread = None
                            return
                    self._queue_stop.wait(0.5)
                    continue
                self.process_run(run)
        finally:
            with self._queue_guard:
                if self._queue_thread is threading.current_thread():
                    self.gemini.lock.release()
                    self._queue_thread = None

    def process_run(self, run):
        token = bind_run(self.store, run["actor"], self.config.get("project_id"), run["id"])
        try:
            self._process_run(run)
        finally:
            reset_run(token)
            if run.get('engine') not in {'supervisor','supervisor_gemini'}:
                from .business_runs import recover_safely
                recover_safely(self,run['actor'],run['id'])

    def _process_run(self, run):
        actor, identifier = run["actor"], run["id"]
        try:
            if run.get('engine') == 'supervisor':
                result = run_isolated(self.store.root,self.workspace.root,actor,run['prompt'],identifier,engine='supervisor')
                self.store.finish_run(actor,identifier,result,'done')
                self.store.record(actor,'supervisor_run',identifier,'ok')
                return
            # ai_worker rechecks current native identity/role/permissions and Free-only policy before Gemini/tools.
            policy = self.gemini.settings()
            if run.get("policy_sha256") and run["policy_sha256"] != digest(canonical(policy)):
                raise ProviderError("GEMINI_VERIFICATION_CHANGED; queued consent not reused for another policy")
            result = run_isolated(self.store.root, self.workspace.root, actor, run["prompt"], identifier,
                                  run["allow_routine_writes"], run["write_scope_ids"],
                                  **({'engine':'supervisor_gemini'} if run.get('engine')=='supervisor_gemini' else {}),
                                  **({'business_read_only':True} if run.get('business_read_only') else {}))
            self.store.finish_run(actor, identifier, result, "done")
            self.store.record(actor, "ai_run", identifier, "ok")
        except ProviderError as error:
            progress = self.store.run(actor, identifier).get("result") or {}
            if run.get('engine') == 'supervisor':
                self.store.finish_run(actor,identifier,{**progress,'status':'failed','error':'LOCAL_AGENT_FAILED',
                    'model_used':False,'text':'Phân tích local bị gián đoạn; xem trace và gửi yêu cầu mới. Chưa có native mutation.'},'failed_or_unknown')
                self.store.record(actor,'supervisor_run',identifier,'failed')
                return
            report = execution_report(progress.get("tools", []))
            code = str(error)
            connection = ("BLOCKED_KEY_OR_MODEL" if any(value in code for value in ("DISABLED", "VERIFICATION_CHANGED", "AUTH_401", "PERMISSION_403", "MODEL_404")) else
                          "WAITING_QUOTA" if "QUOTA" in code or "EXHAUSTED" in code else
                          "INVALID_OUTPUT" if any(value in code for value in ('INCOMPLETE','STRUCTURED_RESPONSE','CLAIM_SOURCE','CITATION_INVALID','FACT_INVALID')) else
                          "LIMIT_REACHED" if "ROUND_LIMIT" in code else "OFFLINE")
            report.update(status="partial" if report["status"] in {"succeeded", "proposed", "partial"} else "failed",
                          heading=connection + " — Yêu cầu bị gián đoạn; xem kết quả từng thao tác")
            self.store.finish_run(actor, identifier, {**progress, **error_info(error), **report,
                "provider_http_status": getattr(error, "status", None), "error": code, "connection_state": connection,
                "message": connection + " — Lượt này dừng, receipt được giữ nguyên. Báo cáo native không cần Gemini; không tự gửi lại thao tác ghi."}, "failed_or_unknown")
            self.store.record(actor, "ai_run", identifier, "provider_stopped")
        except Exception:
            progress = self.store.run(actor, identifier).get("result") or {}
            self.store.finish_run(actor, identifier, {**progress, **execution_report(progress.get("tools", [])),
                "error": "AI_RUN_FAILED", "message": "Yêu cầu bị gián đoạn. Các receipt dưới đây được giữ; không tự gửi lại thao tác ghi."}, "failed_or_unknown")
            self.store.record(actor, "ai_run", identifier, "failed_or_unknown")

    def run_supervisor(self, actor, identifier, live=False):
        from .agent_models import RunScope
        from .supervisor import Supervisor
        from .agent_trace import trace_event
        native, who = self.native_actor(actor)
        run = self.store.agent_run(actor,self.config['project_id'],identifier)
        task = self.store.agent_task(actor,self.config['project_id'],run.task_id)
        if run.state != 'RUNNING' or task.agent != 'supervisor':
            raise PermissionError('SUPERVISOR_STORED_RUNNING_TASK_REQUIRED')
        scope = RunScope(**{key:getattr(run,key) for key in RunScope.model_fields})
        token = bind_run(self.store,actor,self.config['project_id'],identifier)
        try:
            context_receipt={}
            def progress(plan, step, results):
                if self.store.run(actor,identifier)['state'] != 'running':
                    raise ValueError('AGENT_CANCELLED')
                trace_event('agent',step.agent)
                self.store.progress_run(actor,identifier,{'status':'running','tools':[],
                    'text':f'Đang xử lý: {step.agent}', 'plan':plan.model_dump(),
                    'completed_steps':len(results),'current_step':step.step_id,
                    'agent_outputs':[{'step_id':s.step_id,'agent':s.agent,'result':r.model_dump()} for s,r in zip(plan.steps,results)],
                    **context_receipt,
                    **(provider.metadata() if live else {})})
            targets = sorted(set(requested_ids(task.instruction)) | {ref.work_package_id for ref in task.references})
            if len(targets) > 10:
                raise ValueError('SUPERVISOR_MAX_10_EXPLICIT_IDS')
            if targets:
                packages = [native.package(identifier) for identifier in targets]
                if len(packages) == 1 and packages[0].get('_links', {}).get('children'):
                    children_links = packages[0]['_links']['children']
                    if isinstance(children_links, list):
                        child_ids = [int(re.search(r'/(\d+)$', ch.get('href', '')).group(1)) for ch in children_links if re.search(r'/(\d+)$', ch.get('href', ''))]
                        for cid in child_ids[:9]:
                            try:
                                packages.append(native.package(cid))
                            except Exception:
                                pass
            else:
                packages = native.packages()
            provider=None
            context_receipt={'engine':'local_supervisor','source_ids':[p['id'] for p in packages[:10]],
                'source_fingerprint':digest(canonical(sorted((p['id'],p['lockVersion']) for p in packages[:10])))}
            if live:
                from .live_agents import LiveAgents
                configuration=self.gemini.multi_agent_settings()
                if not configuration.enabled:raise ProviderError('GEMINI_MULTI_AGENT_DISABLED')
                if not business_manager(who['role']) and not targets:
                    packages=[p for p in packages if p.get('_links',{}).get('assignee',{}).get('href')==f'/api/v3/users/{actor}']
                candidates={p['id']:p for p in packages}
                packages=packages[:10]
                query=safe_text(task.instruction)[:500]
                if targets:
                    search_args={'query':query,'limit':configuration.max_knowledge_items,'native_ids':[p['id'] for p in packages]}
                    knowledge=self.knowledge(who,native,'knowledge_search',search_args)['items'] if packages and configuration.max_knowledge_items else []
                    if not knowledge and packages and configuration.max_knowledge_items:
                        subject_query=safe_text(packages[0].get('subject'))[:200]
                        if subject_query:knowledge=self.knowledge(who,native,'knowledge_search',{**search_args,'query':subject_query})['items']
                    knowledge=[hit for hit in knowledge if hit['native_id'] in {p['id'] for p in packages}]
                else:
                    search_args={'query':query,'limit':configuration.max_knowledge_items}
                    knowledge=self.knowledge(who,native,'knowledge_search',search_args)['items'] if configuration.max_knowledge_items else []
                    preferred=[candidates[hit['native_id']] for hit in knowledge if hit['native_id'] in candidates]
                    packages=list({p['id']:p for p in [*preferred,*packages]}.values())[:10]
                    knowledge=[hit for hit in knowledge if hit['native_id'] in {p['id'] for p in packages}]
                # Rich context and citations share the same bounded, freshly authorized Native sources.
                packages=[self.perform(who,native,'get_work_package',{'id':p['id'],'include_context':True}) for p in packages]
                context_receipt={'engine':'gemini_supervisor','source_ids':[p['id'] for p in packages],
                    'source_fingerprint':digest(canonical(sorted((p['id'],p['lockVersion']) for p in packages)))}
                def cancelled():
                    if self.store.run(actor,identifier)['state']!='running':raise ProviderError('AGENT_CANCELLED')
                def notify(message,state):
                    previous=self.store.run(actor,identifier).get('result') or {}
                    self.store.progress_run(actor,identifier,{**previous,**context_receipt,'message':message,'queue_state':state,**provider.metadata()})
                provider=LiveAgents(self.gemini,configuration,knowledge,
                    {'selected_work_packages':len(packages),'analysis_limit':10,'sprints':native.sprints() if business_manager(who['role']) else [],'project_summary':native.summary(actor) if business_manager(who['role']) else {'scope':'assigned-to-current-actor or explicit visible IDs'},
                     'options':self.perform(who,native,'get_project_options',{}) if business_manager(who['role']) else {}},cancelled,notify)
            from .agent_registry import AgentRegistry
            registry = AgentRegistry({int(uid):{'name':f'User {uid}','role':role} for uid,role in self.config['users'].items()})
            qa_report=None
            if not live and self.mode=='native':
                from .native_qa_runs import latest_report
                qa_report=lambda native_id,version:latest_report(self,actor,native_id,version)
            orchestrator=Supervisor(registry,qa_report=qa_report)
            try:
                plan,result = orchestrator.execute_task(task,scope,packages,who['role'],progress,provider=provider)
            except ProviderError:
                if live:
                    previous=self.store.run(actor,identifier).get('result') or {}
                    self.store.progress_run(actor,identifier,{**previous,**context_receipt,**provider.metadata(),
                        'execution_mode':'PROVIDER_UNAVAILABLE','model_used':provider.metadata()['execution_mode']=='LIVE_GEMINI',
                        'partial_agent_outputs':[r.model_dump() for r in provider.outputs]})
                raise
            tools=[]
            if live and provider.operations:
                # Model suggestions create previews only. Existing server-side preview/confirm is authoritative.
                if not business_manager(who['role']) or plan.operation_type!='PROPOSAL_WRITE':raise PermissionError('PM_PREVIEW_REQUIRED')
                native,who=self.native_actor(actor)
                for index,op in enumerate(provider.operations[:3]):
                    item=native.package(op.work_package_id)
                    if item['lockVersion']!={p['id']:p['lockVersion'] for p in packages}[item['id']]:
                        raise ProviderError('GEMINI_PROPOSAL_SOURCE_STALE')
                    if op.action=='transition':
                        if op.status_id is None:raise ProviderError('GEMINI_PROPOSAL_STATUS_REQUIRED')
                        arguments={'id':item['id'],'lock_version':item['lockVersion'],'status_id':op.status_id}
                    else:
                        changes={k:v for k,v in {'subject':op.subject,'description':op.description}.items() if v is not None}
                        if not changes:raise ProviderError('GEMINI_PROPOSAL_CHANGES_REQUIRED')
                        arguments={'id':item['id'],'lock_version':item['lockVersion'],'changes':changes}
                    preview=self.execute_actor(actor,{'action':op.action,'arguments':arguments,'auto_execute':False,
                        'idempotency_key':f'live-{identifier}-{index}'})
                    tools.append({'action':op.action,'arguments':arguments,'result':preview})
                    from .execution_events import emit
                    emit('PROPOSAL_CREATED',agent='supervisor',status='REVIEW')
                    emit('APPROVAL_REQUIRED',agent='supervisor',status='REVIEW')
            metadata=provider.metadata() if live else {}
            if live:
                usage=metadata['usage'];total=sum(v.get('totalTokenCount',0) for v in usage)
                text=(f"{metadata['execution_mode']} · {metadata['model']} · {metadata['model_call_count']} model calls · {total} total tokens (provider metadata) · {metadata['duration_seconds']}s\n"
                      'Provider remaining quota: unavailable. Chỉ phân tích/đề xuất; chưa có native mutation.\n\n'+result.summary)
            else:text=result.summary
            return {'status':'failed' if result.state=='FAILED' else 'proposed' if result.state=='REVIEW' else 'succeeded',
                'heading':metadata['execution_mode']+' — Kết quả phân tích' if live else 'LOCAL_DETERMINISTIC — Kết quả phân tích',
                'text':text,'tools':tools,'engine':'gemini_supervisor' if live else 'local_supervisor','model_used':metadata.get('execution_mode')=='LIVE_GEMINI',
                **metadata,
                'agent_outputs':[{'step_id':s.step_id,'agent':s.agent,'result':r.model_dump()} for s,r in zip(plan.steps,orchestrator.outputs)],
                'plan':plan.model_dump(),'agent_result':result.model_dump(),'completed_steps':len(plan.steps),
                'source_ids':context_receipt['source_ids'],
                'source_fingerprint':context_receipt['source_fingerprint']}
        finally:
            reset_run(token)

    def knowledge(self, who, native, action, args):
        from contextlib import closing
        from .vector_client import VectorClient
        with closing(VectorClient()) as vector:
            return self._knowledge(who,native,action,args,vector)

    def _knowledge(self, who, native, action, args, vector):
        from dataclasses import asdict
        from .knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
        from .knowledge_classifier import KnowledgeDocType, classify_document
        from .knowledge_ingestion import KnowledgeIngester,IngestionStatus
        from .knowledge_search import KnowledgeSearchEngine
        from .openproject_loader import actor_work_package_document
        from .presentation import safe_text
        project, actor = self.config['project_id'],who['user_id']
        storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.store.root/'knowledge.sqlite')))
        if action in {'knowledge_ingest','knowledge_deindex'}:
            self.keys(args,{'id'},{'id'})
            if type(args['id']) is not int or args['id'] <= 0:
                raise ValueError('KNOWLEDGE_NATIVE_ID_REQUIRED')
            source = f'actor:{actor}:wp:{args["id"]}'
            if action == 'knowledge_deindex':
                return {'deleted':KnowledgeIngester(storage,vector).deindex_source(source,str(project)),'native_id':args['id']}
            item = native.package(args['id'])
            activities=native.collection(f'/api/v3/work_packages/{item["id"]}/activities')
            doc = actor_work_package_document(item,project,actor,who['role'],activities)
            try:
                result = KnowledgeIngester(storage,vector).ingest(doc)
            except ValueError as error:
                if 'KNOWLEDGE_BUSY' in str(error):
                    raise NativeError(503,'KNOWLEDGE_BUSY_RETRY_LATER') from None
                raise
            if result.status == IngestionStatus.FAILED:
                raise NativeError(503,'KNOWLEDGE_PERSISTENCE_FAILED')
            current_item=native.package(args['id'])
            current_activities=native.collection(f'/api/v3/work_packages/{item["id"]}/activities')
            current_doc=actor_work_package_document(current_item,project,actor,who['role'],current_activities)
            if current_doc.source_hash!=doc.source_hash or current_doc.metadata!=doc.metadata:
                raise NativeError(409,'KNOWLEDGE_SOURCE_CHANGED_RETRY')
            return {**asdict(result),'native_id':item['id'],'lock_version':item['lockVersion']}
        self.keys(args,{'query','limit','native_ids'},{'query'})
        if not isinstance(args['query'],str) or not 1 <= len(args['query']) <= 500:
            raise ValueError('KNOWLEDGE_QUERY_1_500')
        targets=args.get('native_ids')
        if 'native_ids' in args and (not isinstance(targets,list) or not 1 <= len(targets) <= 10 or
                any(type(identifier) is not int or identifier <= 0 for identifier in targets) or len(set(targets)) != len(targets)):
            raise ValueError('KNOWLEDGE_NATIVE_IDS_1_10_UNIQUE_POSITIVE_INTEGERS')
        # Native collection visibility/version scopes both FTS and Qdrant before retrieval.
        native_items = {item['id']:item for item in native.packages()}
        selected = {}
        for doc in storage.query_documents(str(project),who['role']):
            identifier = doc.metadata.get('native_id')
            if targets is not None and identifier not in targets:
                continue
            item = native_items.get(identifier) if type(identifier) is int else None
            own = type(doc.metadata.get('actor_id')) is int and doc.metadata['actor_id'] == actor
            shared = 'actor_id' not in doc.metadata and doc.source_id == f'op:wp:{identifier}'
            supervised = (who['role'] == AI_SYSTEM_OWNER and str(doc.metadata.get('actor_id')) in self.config['users']
                and doc.source_id == f"actor:{doc.metadata.get('actor_id')}:wp:{identifier}")
            if not item or doc.metadata.get('lock_version') != item['lockVersion'] or not (own or shared or supervised):
                continue
            if 'activity_hashes' in doc.metadata:
                try:
                    activities=native.collection(f'/api/v3/work_packages/{identifier}/activities')
                except (PermissionError,NativeError):
                    continue
                current_doc=actor_work_package_document(item,project,doc.metadata['actor_id'],doc.allowed_roles[0],activities)
                if current_doc.source_hash!=doc.source_hash or current_doc.metadata!=doc.metadata:
                    continue
            previous=selected.get(identifier)
            if previous is None or own and doc.metadata.get('activity_ids') or shared and not previous.metadata.get('activity_ids'):
                selected[identifier] = doc
        document_ids = [doc.source_hash for doc in selected.values()]
        if who['role'] == AI_SYSTEM_OWNER:
            self.store.record(actor,'owner_oversight','main:rag_sources','READ_ONLY')
        engine = KnowledgeSearchEngine(storage,vector_client=vector)
        hits = engine.search(args['query'],str(project),who['role'],
            args.get('limit',10),actor_id=actor,document_ids=document_ids)
        visible=[]
        for hit in hits:
            if hit.document_id not in document_ids or type(hit.native_id) is not int:
                continue
            try:
                item = native.package(hit.native_id)
            except (PermissionError,NativeError):
                continue
            if item['lockVersion'] != hit.lock_version:
                continue
            if 'activity_hashes' in hit.metadata:
                try:
                    activities=native.collection(f'/api/v3/work_packages/{hit.native_id}/activities')
                except (PermissionError,NativeError):
                    continue
                current_doc=actor_work_package_document(item,project,hit.metadata['actor_id'],
                    selected[hit.native_id].allowed_roles[0],activities)
                if current_doc.source_hash!=hit.document_id or current_doc.metadata!=hit.metadata:
                    continue
            visible.append({'title':safe_text(hit.title),'snippet':safe_text(hit.snippet), 'native_id':hit.native_id,
                'document_id':hit.document_id,
                'lock_version':hit.lock_version,'source_id':hit.source_id,'score':hit.score,
                'citation':f'/work_packages/{hit.native_id}','match_type':hit.match_type})
        from .knowledge_answer import retrieval_response
        return {**retrieval_response(visible,engine.dense_state),'items':visible,'store':'SQLite FTS5 + Qdrant/BGE-M3 (lexical fallback)',
            'dense_state':engine.dense_state,
            'scope':'native visibility/version before retrieval + fresh native ACL/version after retrieval','model_used':False}

    def preview(self, who, native, command):
        args = command.arguments
        if command.action == 'delete_work_package':
            from . import native_deletion
            native_deletion.arguments(self,args)
            result=native_deletion.preview(self,who,native,args,command.idempotency_key)
            args['snapshot_sha256']=result['snapshot_sha256']
            return result
        if command.action in {'update_dependency','delete_dependency'}:
            from . import native_dependency_change
            native_dependency_change.arguments(self,args,command.action)
            result=native_dependency_change.preview(self,who,native,args,command.action)
            args.update({key:result[key] for key in ['scope_hash','predecessor_id','successor_id']})
            return result
        if command.action == 'create_dependency':
            from . import native_dependency
            native_dependency.arguments(self,args)
            result = native_dependency.preview(self,who,native,args)
            args['scope_hash'] = result['scope_hash']
            return result
        if command.action == "write_code":
            self.keys(args, {"path", "content", "expected_hash", "workspace_actor"}, {"path", "content", "expected_hash"})
            if not business_manager(who["role"]) or int(args.get("workspace_actor", who["user_id"])) != who["user_id"]:
                raise PermissionError("DEVELOPER_REQUIRED")
            path = self.workspace.path(who["user_id"], args["path"])
            before = self.workspace.read(who["user_id"], args["path"]) if path.exists() else {"sha256": "NEW", "content": ""}
            if before["sha256"] != args["expected_hash"]:
                raise ValueError("STALE_CODE")
            if not isinstance(args["content"], str) or len(args["content"].encode()) > 262144:
                raise ValueError("CODE_TOO_LARGE")
            return {"before": before, "after": args["content"]}
        if command.action == "create_work_package":
            from .native_wbs import scheduling
            scheduling(args)
            if 'source_references' in args:
                from .native_wbs import validate_sources
                validate_sources(native,args)
            if args.get("parent_id"):
                native.package(args["parent_id"])
            return {"new_work_package": args, "validation": "Native permission and gate checks run again at confirmation."}
        item = native.package(args["id"])
        if args.get("lock_version") != item["lockVersion"]:
            raise ValueError("STALE_WORK_PACKAGE")
        if command.action == 'transition' and self.mode == 'native':
            self.keys(args, {'id','lock_version','status_id','qa_evidence_id','qa_evidence_hash','phase_id','phase_hash'}, {'id','lock_version','status_id'})
            if type(args['status_id']) is not int or args['status_id'] not in self.config['status_ids']:
                raise ValueError('STATUS_DENIED')
            from .native_qa import transition_guard
            transition_guard(self,who,native,item,args)
            if {'phase_id','phase_hash'} & args.keys():
                from .native_phase_bridge import preflight
                preflight(self,who,native,item,args)
        adjustments = self.date_payload(native, item, args.get("changes", {}))[1] if command.action == "update_work_package" else {}
        return {"before": {key: item.get(key) for key in ("id", "subject", "description", "startDate", "dueDate", "lockVersion", "_links")},
                "changes": args, "date_adjustments": adjustments, "validation": "Native permission and gate checks run again at confirmation."}

    def decide_feedback(self, bearer, identifier, decision, fingerprint):
        from .knowledge_feedback import decide
        return decide(self,bearer,identifier,decision,fingerprint)

    def decide_qa_evidence(self, bearer, identifier, decision, fingerprint):
        from .native_qa import decide
        return decide(self,bearer,identifier,decision,fingerprint)

    def decide_proposal(self, bearer, identifier, decision, fingerprint):
        if decision not in {"approve", "reject"} or not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            raise ValueError("PROPOSAL_DECISION_AND_EXACT_HASH_REQUIRED")
        actor = self.store.authenticate(bearer)["user_id"]
        _, identity = self.native_actor(actor)
        if not business_manager(identity["role"]):
            raise PermissionError("PM_APPROVAL_REQUIRED")
        if decision == "approve":
            return self.confirm(actor, identifier, fingerprint)
        return self.execute(bearer, {"action": "reject_proposal", "arguments": {"id": identifier, "hash": fingerprint},
            "idempotency_key": "reject-" + identifier})

    def confirm(self, actor, identifier, fingerprint):
        proposal = self.store.proposal(actor, identifier)
        if proposal["command"].get("_gateway_mode", "strict") != self.mode:
            raise PermissionError("PROPOSAL_GATEWAY_MODE_CHANGED; request a fresh preview")
        _, identity = self.native_actor(actor)
        if not business_manager(identity["role"]):
            raise PermissionError("PM_APPROVAL_REQUIRED")
        token=bind_proposal(self.store,actor,self.config['project_id'],proposal)
        try:
            command = self.store.claim_proposal(actor, identifier, fingerprint)
        except Exception:
            reset_run(token)
            raise
        command.pop("preview")
        command.pop("_gateway_mode", None)
        command.pop("_origin_run_id", None)
        command["idempotency_key"] = "proposal-" + identifier
        try:
            result = self.execute_actor(actor, command, confirmed=True)
            binding=current_run.get()
            if binding:result['origin']={'run_id':binding[1].run_id,'trace_id':binding[1].trace_id,'proposal_id':identifier}
            self.store.finish_proposal(actor, identifier, result)
            return result
        except Exception:
            self.store.finish_proposal(actor, identifier, {"error": "CONFIRMATION_FAILED_OR_UNKNOWN; inspect receipts before retry"}, "failed_or_unknown")
            raise
        finally:
            reset_run(token)

    def perform(self, who, native, action, args, request_key=None):
        actor, role = who["user_id"], who["role"]
        require(role, action, self.mode)
        if action == 'qa_application_proof_admit':
            from .application_qa_intake import admit
            self.keys(args, {'id'}, {'id'})
            return admit(self, who, native, args['id'])
        if action == 'qa_application_proof_verify':
            from .application_qa_intake import load_verified
            self.keys(args, {'id'}, {'id'})
            proof = load_verified(self, who, native, args['id'])
            return {'id': proof['id'], 'native_id': proof['source']['id'], 'version': proof['source']['version'],
                    'verdict': proof['verdict'], 'artifact_sha256': digest(canonical(proof)),
                    'status': 'TECHNICAL_PROOF_NOT_REVIEWED', 'qualification': proof['qualification'],
                    'tested_build': proof['build'], 'producer': proof['producer'], 'finished_at': proof['finished_at']}
        if action in {'phase_draft','phase_get','phase_list','phase_transition_prepare'}:
            from .native_phase import perform
            return perform(self,actor,action,args,request_key)
        if action == 'delete_work_package':
            from .native_deletion import execute
            return execute(self,who,native,args,request_key)
        if action in {'update_dependency','delete_dependency'}:
            from .native_dependency_change import execute
            return execute(self,who,native,args,request_key,action)
        if action == 'create_dependency':
            from .native_dependency import execute
            return execute(self,who,native,args,request_key)
        if action in {'qa_test_run', 'qa_test_get', 'qa_evidence_from_run'}:
            from .native_qa_runs import perform
            return perform(self, who, native, action, args, request_key)
        if action in {'qa_evidence_capture', 'qa_evidence_get', 'qa_transition_prepare', 'qa_evidence_list'}:
            from .native_qa import perform
            return perform(self,who,native,action,args,request_key)
        if action in {'wbs_draft','wbs_get','wbs_adopt','wbs_next','wbs_from_ba'}:
            from .native_wbs import perform
            return perform(self,who,native,action,args,request_key)
        if action in {'bug_triage','bug_propose'}:
            from .bug_lifecycle import triage, propose
            return triage(self,who,native,args) if action=='bug_triage' else propose(self,who,native,args,request_key)
        if action == 'owner_inspect':
            self.keys(args, {'kind','subject_actor','id','limit','offset'}, {'kind','subject_actor'})
            subject = args['subject_actor']
            if type(subject) is not int or str(subject) not in self.config['users']:
                raise PermissionError('OWNER_SUBJECT_OUTSIDE_MAIN')
            kind = args['kind']
            if kind not in {'history','progress','trace','proposal'}:
                raise ValueError('OWNER_READ_ONLY_KIND_REQUIRED')
            project = self.config['project_id']
            self.store.record(actor,'owner_oversight',f'{subject}:{kind}','READ_ONLY')
            if kind == 'history':
                data = self.store.history(subject)
            elif kind == 'progress':
                data = self.store.agent_progress(subject,project,args['id'])
            elif kind == 'trace':
                data = self.store.agent_trace_page(subject,project,args['id'],args.get('limit',20),args.get('offset',0))
            else:
                data = self.store.proposal(subject,args['id'])
                target = data['command']['arguments'].get('id') or data['command']['arguments'].get('parent_id')
                if target is not None:
                    native.package(target)
            return {'viewer_actor':actor,'subject_actor':subject,'authority':AI_SYSTEM_OWNER,
                    'can_execute_as_subject':False,'data':data}
        if action=='sprint_risks':
            self.keys(args,{'as_of_date','sprint_id'})
            return self.sprint_report(actor,args)
        if action=='weekly_summary':
            self.keys(args,{'as_of_date'})
            return self.weekly_report(actor,args)
        if action=='get_report':
            self.keys(args,{'id'},{'id'})
            try:
                if not isinstance(args['id'],str) or str(uuid.UUID(args['id']))!=args['id']:
                    raise ValueError()
            except (ValueError,TypeError,AttributeError):
                raise ValueError('REPORT_UUID_REQUIRED') from None
            report=self.store.report(actor,self.config['project_id'],args['id'])
            if report['kind'] in {'knowledge_integrity','health'}:
                require(role,'knowledge_integrity',self.mode)
            if report['document'].get('actor_role',role)!=role:
                return {'id':report['id'],'state':'SOURCE_ROLE_CHANGED','data_hidden':True}
            current={p['id']:p['lockVersion'] for p in native.packages()}
            if any(identifier not in current for identifier,version in report['references']):
                return {'id':report['id'],'state':'SOURCE_PERMISSION_CHANGED','data_hidden':True}
            return {**report,'state':'SNAPSHOT','source_versions_current':set(current)=={i for i,v in report['references']} and
                all(current[i]==v for i,v in report['references'])}
        if action=='knowledge_integrity':
            from contextlib import closing
            from .vector_client import VectorClient
            from .knowledge_integrity import reconcile
            self.keys(args,set())
            items=native.packages()
            try:
                with closing(VectorClient()) as vector:
                    report={**reconcile(self.store.root,self.config['project_id'],items,vector),'actor_role':role}
                return {**report,**self.store.save_report(actor,self.config['project_id'],'knowledge_integrity',report,items)}
            except Exception as error:
                logging.getLogger(__name__).warning('Knowledge audit unavailable: %s',type(error).__name__)
                raise NativeError(503,'KNOWLEDGE_INTEGRITY_UNAVAILABLE') from None
        if action in {'knowledge_sync_status','knowledge_sync_retry'}:
            self.keys(args,{'id'},{'id'})
            if action=='knowledge_sync_retry':
                return self.store.retry_knowledge_sync(actor,args['id'])
            return self.store.knowledge_sync(actor,args['id'])
        if action=='list_execution_monitors':
            self.keys(args,{'limit','offset','search','state','order'})
            return self.store.execution_history(actor,self.config['project_id'],**args)
        if action=='get_execution_monitor':
            self.keys(args,{'id'},{'id'})
            from .execution_monitor import project_execution
            authorized=self.perform(who,native,'get_ai_run',{'id':args['id']})
            from .business_runs import load, monitor
            try:business=load(self.store,actor,self.config['project_id'],args['id'])
            except PermissionError:business=None
            if business is not None:return monitor(self,who,authorized,business)
            if self.config.get('_engineering_scope') or self.config.get('project_id') == 6:
                with self.store.connect() as db:row=db.execute("SELECT q.actor, q.payload FROM ai_queue q WHERE q.id=? AND json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw'",(args['id'],)).fetchone()
                if row:
                    run_owner = row['actor']
                    run = self.store.agent_run(run_owner, 6, args['id'])
                    task = self.store.agent_task(run_owner, 6, run.task_id)
                    events, receipts = self.store.execution_records(run_owner, 6, args['id'])
                    from .engineering_monitor import project
                    return project(self,who,authorized,task,run,json.loads(row['payload']),receipts,events,native=native)
            run=self.store.agent_run(actor,self.config['project_id'],args['id'])
            task=self.store.agent_task(actor,self.config['project_id'],run.task_id)
            events,receipts=self.store.execution_records(actor,self.config['project_id'],args['id'])
            return project_execution(authorized,task,run,role,receipts,events).model_dump()
        if action in {'knowledge_ingest','knowledge_search','knowledge_deindex'}:
            return self.knowledge(who,native,action,args)
        if action in {'knowledge_file_ingest','knowledge_file_search','knowledge_file_read'}:
            from .file_knowledge import execute
            return execute(self, who, action, args)
        if action in {'knowledge_incremental_sync','knowledge_incremental_status'}:
            self.keys(args,set())
            from .native_incremental import scan, status
            return scan(self,actor) if action=='knowledge_incremental_sync' else status(self.store,actor,self.config['project_id'])
        if action in {'knowledge_feedback_submit','knowledge_feedback_get','knowledge_feedback_apply'}:
            from .knowledge_feedback import submit, read, apply
            if action=='knowledge_feedback_submit':return submit(self,who,native,args,request_key)
            self.keys(args,{'id'},{'id'})
            return apply(self,who,native,args['id']) if action=='knowledge_feedback_apply' else read(self,who,native,args['id'])
        if action == 'get_control_center':
            return self.control_center_state(actor,args)
        if action == 'cancel_agent_run':
            self.keys(args,{'id'},{'id'})
            return self.store.cancel_agent_run(actor,self.config['project_id'],args['id'])
        if action in {"list_agent_runs", "get_agent_run", "get_agent_trace"}:
            self.keys(args, {"limit", "offset"} if action == "list_agent_runs" else {"id"} if action == "get_agent_run" else {"id", "limit", "offset"},
                      set() if action == "list_agent_runs" else {"id"})
            if "id" in args:
                try:
                    if not isinstance(args["id"], str) or str(uuid.UUID(args["id"])) != args["id"]:
                        raise ValueError()
                except (ValueError, TypeError, AttributeError):
                    raise ValueError("AGENT_RUN_ID_INVALID") from None
            project = self.config["project_id"]
            if action == "get_agent_run":
                return self.store.agent_progress(actor, project, args["id"])
            limit, offset = args.get("limit", 20), args.get("offset", 0)
            if action == "list_agent_runs":
                return self.store.agent_runs_page(actor, project, limit, offset)
            return self.store.agent_trace_page(actor, project, args["id"], limit, offset)
        if action == "get_permissions":
            self.keys(args, set())
            actions = Command.model_fields["action"].annotation.__args__
            permissions = native.call("/api/v3/qldapm/permissions")
            def reason(name):
                if self.mode == 'native' and name in SANDBOX_ONLY:
                    return 'NATIVE_BUSINESS_OPERATOR_TOOL_DENIED'
                if not allowed(role, name, self.mode):
                    return "PM_REQUIRED"
                if self.mode == "native" and name in {"get_gate", "change_gate"}:
                    return "CUSTOM_GATE_UNSUPPORTED_IN_NATIVE_MODE"
                if name in NATIVE_PERMISSIONS and not permissions.get("effective", {}).get(NATIVE_PERMISSIONS[name], False):
                    return "NATIVE_PERMISSION_DENIED"
                return None
            return {"project_id": self.config["project_id"], "actor": actor, "role": role,
                    "tools": [{"name": name, "allowed": reason(name) is None, "reason": reason(name)} for name in actions],
                    "native": permissions}
        if action == "reject_proposal":
            self.keys(args, {"id", "hash"}, {"id", "hash"})
            self.store.reject_proposal(actor, args["id"], args["hash"])
            return self.store.proposal(actor, args["id"])
        if action == "get_action_history":
            self.keys(args, set())
            history = self.store.history(actor)
            if business_manager(role):
                if role == AI_SYSTEM_OWNER:
                    self.store.record(actor,'owner_oversight','main:project_audit','READ_ONLY')
                history["project_audit"] = self.store.project_audit(self.config["users"])
            return history
        if action == "get_assistant_status":
            self.keys(args, set())
            try:
                policy = self.gemini.settings()
                continuous = self.gemini.continuous_authorized(policy)
                provider = {"state": "authorized" if continuous else "verified", "model": policy["model"], "data_scope": policy["data_scope"],
                            "expires": None if continuous else policy["checked_at"] + 3600, "limits": policy["limits"],
                            "authorization_mode": "continuous-free-only" if continuous else "one-hour-free-proof",
                            "provider_policy": "FREE_ONLY", "paid_api_disabled": True, "auto_enable_billing": False,
                            "billing_allowed": False, "last_observed_tier": policy["tier"], "last_observed_at": policy["checked_at"],
                            "billing_checked_live": False}
                provider["readiness"] = self.gemini.readiness(policy)
                provider["authorization_state"] = provider["state"]
                readiness = provider["readiness"]
                if readiness["state"] in {"READY", "WAITING_QUOTA", "BLOCKED_KEY_OR_MODEL", "PROVIDER_UNAVAILABLE"}:
                    provider.update(state="OFFLINE" if readiness["state"] == "PROVIDER_UNAVAILABLE" else readiness["state"],
                                    retry_at=readiness.get("retry_at"))
            except ProviderError:
                provider = {"state": "BLOCKED_KEY_OR_MODEL", "authorization_state": "blocked",
                            "reason": "credential/cost/quota proof missing or invalid", "provider_policy": "FREE_ONLY",
                            "paid_api_disabled": True, "auto_enable_billing": False}
            return {"gateway": "ok", "openproject": "authenticated", "gateway_mode": self.mode, "gemini": provider,
                    "native_reporting": {"state": "NATIVE_NO_LLM", "model_used": False,
                                         "actions": ["analyze", "list_work_packages", "get_work_package"], "fresh_permissions_required": True}}
        if action == "get_proposal":
            self.keys(args, {"id"}, {"id"})
            return self.store.proposal(actor, args["id"])
        if action == "get_ai_run":
            self.keys(args, {"id"}, {"id"})
            if self.config.get('_engineering_scope'):
                with self.store.connect() as db:q_row = db.execute("SELECT actor FROM ai_queue WHERE id=? AND json_extract(payload,'$.project_id')=6",(args['id'],)).fetchone()
                run_actor = q_row['actor'] if q_row else actor
            else:
                run_actor = actor
            run = self.store.run(run_actor, args["id"])
            result = run.get("result") or {}
            if self.config.get('_engineering_scope'):
                scoped_run=self.store.agent_run(run_actor,6,args['id'])
                scoped_task=self.store.agent_task(run_actor,6,scoped_run.task_id)
                references={ref.work_package_id for ref in scoped_task.references}
                readback=result.get('native_readback') or {}
                if type(readback.get('child_id')) is int:references.add(readback['child_id'])
                references.update(v['id'] for v in readback.values() if isinstance(v,dict) and type(v.get('id')) is int)
                for identifier in references:native.package(identifier)
            if (result.get('engine') in {'local_supervisor','gemini_supervisor'} and (result.get('agent_result') or 'source_fingerprint' in result)) or result.get('partial_agent_outputs'):
                from .agent_models import AgentResult
                outputs=([result['agent_result']] if result.get('agent_result') else [])+result.get('partial_agent_outputs',[])
                evidence=[AgentResult.from_json(canonical(output)) for output in outputs]
                if any((r.actor_id != actor and not (actor == 18 and self.config.get('project_id') in (5, 6))) or r.project_id != self.config['project_id'] for r in evidence):
                    raise PermissionError('AGENT_RESULT_SCOPE_MISMATCH')
                source_ids = result.get('source_ids')
                if source_ids is not None and (not isinstance(source_ids,list) or not 0 <= len(source_ids) <= 10
                        or any(type(value) is not int or value <= 0 for value in source_ids) or len(set(source_ids)) != len(source_ids)):
                    raise PermissionError('AGENT_SOURCE_SCOPE_INVALID')
                current = [native.package(identifier) for identifier in source_ids] if source_ids is not None else native.packages()
                if digest(canonical(sorted((p['id'],p['lockVersion']) for p in current))) != result.get('source_fingerprint'):
                    return {'id':run['id'],'state':'done','result':{'status':'stale','stale':True,'text':'Dữ liệu hoặc quyền đọc đã đổi. Gửi yêu cầu phân tích mới.','tools':[]}}
                current_versions = {item['id']:item['lockVersion'] for item in current}
                for ref in (ref for item in evidence for ref in item.references):
                    if current_versions.get(ref.work_package_id) != ref.lock_version:
                        return {'id':run['id'],'state':'done','result':{'status':'stale','stale':True,'text':'Nguồn đã thay đổi. Gửi yêu cầu mới để phân tích lại.','tools':[]}}
            if result.get("source") == "native":
                route = result.get("read_route")
                if not isinstance(route, (list, tuple)) or len(route) != 3 or not (
                        route[1] in {"analyze", "list_work_packages", "get_work_package", "native_open_count"} or
                        route[0] == 'weekly' and route[1] == 'weekly_summary' and route[2] == {}):
                    raise ValueError("NATIVE_READ_RECEIPT_INVALID")
                if route[0]=='uncompleted' and route[1]=='analyze':
                    return {'id':run['id'],'state':'done','result':{'status':'stale','stale':True,'source':'native','model_used':False,
                        'text':'Cách đếm cũ chưa phân biệt đúng loại công việc và trạng thái Native. Gửi câu hỏi mới để đọc số lượng hiện tại.','tools':[]}}
                try:
                    if "context_reference" in result:
                        current_route, current = self.context_read(who, native, result["context_reference"])
                        if list(current_route) != list(route):
                            raise ValueError("CONTEXT_RECEIPT_ROUTE_MISMATCH")
                    else:
                        current = execute_query(self, who, native, route)
                except NativeError as error:
                    if error.status < 500:
                        raise
                    return {"id": run["id"], "state": "done", "result": {"status": "offline", "connection_state": "OFFLINE",
                        "source": "native", "model_used": False, "tools": [], "heading": "OFFLINE — Chưa kết nối được OpenProject",
                        "text": "Chưa xác minh được dữ liệu hiện tại. Kết quả cũ không được hiển thị như dữ liệu mới; thử đọc lại khi kết nối phục hồi."}}
                if read_result(who, self.config["project_id"], route, current)["source_fingerprint"] != result["source_fingerprint"]:
                    return {"id": run["id"], "state": "done", "result": {"status": "stale", "stale": True,
                        "source": "native", "model_used": False, "tools": [], "heading": "STALE — Cần đọc lại dữ liệu hiện tại",
                        "text": "Dữ liệu hoặc quyền xem đã thay đổi. Gửi yêu cầu mới để đọc lại OpenProject; kết quả cũ không được dùng như dữ liệu hiện tại."}}
            if result.get("tools") and "outcomes" not in result:
                calls = result["tools"]
                for call in calls:
                    if call.get("result", {}).get("error"):
                        call["result"]["message"] = "Thao tác đã bị từ chối ở lượt này; chưa có xác nhận ghi thành công. Xem receipt để kiểm tra lý do."
                run["result"] = {**result, **execution_report(calls, result.get("text", ""), result.get("claims", []))}
            from .business_runs import project_view
            return project_view(self,actor,run,native)
        if action == "get_insights":
            self.keys(args, {"user_id", "days"})
            target = int(args.get("user_id", actor))
            if str(target) not in self.config["users"] or (target != actor and not business_manager(role)):
                raise PermissionError("INSIGHTS_PM_OR_SELF_REQUIRED")
            days = int(args.get("days", 30))
            if days not in {7, 30, 90}:
                raise ValueError("INSIGHTS_WINDOW_DENIED")
            return native.call(f"/api/v3/qldapm/insights?user_id={target}&days={days}")
        if action == "start_ai_run":
            return self.start_run(who, args, native=native)["result"]
        if action == "identity":
            return who
        if action == "get_project_options":
            self.keys(args, set())
            return {"types": [{"id": row["id"], "name": row["name"]} for row in native.collection(f"/api/v3/projects/{native.project_id}/types") if row["id"] in self.config["type_ids"]],
                    "statuses": [{"id": row["id"], "name": row["name"]} for row in native.collection("/api/v3/statuses") if row["id"] in self.config["status_ids"]],
                    "priorities": [{"id": row["id"], "name": row["name"]} for row in native.collection("/api/v3/priorities")],
                    "assignee_roles": ["BA", "PM", "BE", "FE", "QA"],
                    "notice": "These options are not permission to use every transition. Native permission/form validation still applies."}
        if action == "get_configuration":
            self.keys(args, set())
            if not business_manager(role):
                raise PermissionError("PM_REQUIRED")
            return native.call("/api/v3/qldapm/configuration")
        if action in {"list_work_packages", "analyze"}:
            self.keys(args, {"query", "parent_id", "offset", "limit"} if action == "list_work_packages" else {"query", "parent_id"})
            items = native.packages()
            if "query" in args:
                if not isinstance(args["query"], str) or len(args["query"]) > 200:
                    raise ValueError("QUERY_INVALID")
                items = [item for item in items if args["query"].casefold() in item.get("subject", "").casefold()]
            if "parent_id" in args:
                items = [item for item in items if item.get("_links", {}).get("parent", {}).get("href") == f"/api/v3/work_packages/{int(args['parent_id'])}"]
            if action == "list_work_packages":
                if "limit" in args or "offset" in args:
                    offset, limit = args.get("offset", 0), args.get("limit", 30)
                    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 30:
                        raise ValueError("LIST_PAGE_INVALID")
                    return {"items": items[offset:offset + limit], "total": len(items),
                            "next_offset": offset + limit if offset + limit < len(items) else None}
                return items
            status, owners = {}, {}
            for item in items:
                name = item["_links"]["status"]["title"]
                status[name] = status.get(name, 0) + 1
                owner = item["_links"].get("assignee", {}).get("title") or "Unassigned"
                owners[owner] = owners.get(owner, 0) + 1
            today = datetime.now(timezone(timedelta(hours=7))).date().isoformat()
            from .sprint_report import _is_closed,generate_sprint_report
            overdue = [item["id"] for item in items if item.get("dueDate") and item["dueDate"] < today and not _is_closed(item)]
            summary = {"count": len(items), "by_status": status, "by_assignee": owners, "overdue_ids": overdue,
                       "limitations": ["Counts are not individual performance scores", "Estimates/points may be simulated"]}
            summary['daily_brief'] = daily_brief.visible(self.store, actor, role, self.config['project_id'], summary)
            summary['workflow_alerts'] = self.store.workflow_alerts(self.config['project_id'])
            user_map = {int(u_id): {"name": f"User {u_id}", "role": u_role} for u_id, u_role in self.config.get("users", {}).items()}
            summary['sprint_report'] = generate_sprint_report(
                packages=items,
                as_of_date=None,
                user_map=user_map,
                actor_id=actor,
                actor_role=role,
                project_id=self.config.get("project_id", 3),
            )
            from .role_alerts import _global_engine
            summary['role_alerts'] = _global_engine.evaluate(
                packages=items,
                actor_id=actor,
                actor_role=role,
                as_of_date=None,
                project_id=self.config.get("project_id", 3),
            )
            from .workload_detector import detect_workload_imbalance
            summary['workload_detector'] = detect_workload_imbalance(
                packages=items,
                users=user_map,
                project_id=self.config.get("project_id", 3),
            )
            from .sprint_readiness import evaluate_sprint_readiness
            summary['sprint_readiness'] = evaluate_sprint_readiness(
                packages=items,
                project_id=str(self.config.get("project_id", "QLDAPM")),
            )
            from .weekly_report import generate_weekly_report
            summary['weekly_report'] = generate_weekly_report(
                packages=items,
                users=user_map,
                actor_id=actor,
                actor_role=role,
                as_of_date=None,
                project_id=self.config.get("project_id", 3),
                with_ai_summary=False,
            )
            summary['control_center'] = self.control_center_state(actor, {'limit':10})
            return summary
        if action == "request_status":
            self.keys(args, {"key"}, {"key"})
            return self.store.request_status(actor, args["key"])
        if action == "reconcile_request":
            self.keys(args, {"key"}, {"key"})
            pending = self.store.pending_request(actor, args["key"])
            previous, arguments = pending["action"], pending["arguments"]
            marker = "QLDAPM-request-" + digest(f"{actor}:{args['key']}")
            found = None
            if previous == "change_gate":
                native.package(arguments["id"])
                gate = native.call(f"/api/v3/qldapm/gates/{int(arguments['id'])}")
                if any(event.get("request_id") == marker and event.get("actor_id") == actor for event in gate["gate"].get("events", [])):
                    found = gate
            elif previous == "comment":
                native.package(arguments["id"])
                activities = native.collection(f"/api/v3/work_packages/{int(arguments['id'])}/activities")
                matches = [item for item in activities if marker in item.get("comment", {}).get("raw", "") and
                           item.get("_links", {}).get("user", {}).get("href") == f"/api/v3/users/{actor}"]
                if len(matches) == 1:
                    found = matches[0]
            elif previous == 'create_work_package':
                field = self.config['source_field']
                source = arguments.get('source_id')
                matches = [item for item in native.packages() if source and item.get(field) == source]
                if len(matches) == 1:
                    item = native.package(matches[0]['id'])
                    from .business_runs import create_matches
                    if create_matches(self,actor,item,arguments):found=item
            elif previous == 'create_dependency':
                from .native_dependency import reconcile
                found = reconcile(self,who,native,arguments,args['key'])
            elif previous in {'update_dependency','delete_dependency'}:
                from .native_dependency_change import reconcile
                found = reconcile(self,who,native,arguments,args['key'])
            elif previous == 'delete_work_package':
                from .native_deletion import reconcile
                found = reconcile(self,who,native,arguments,args['key'])
            elif previous == "write_code":
                current = self.workspace.read(actor, arguments["path"])
                if current["sha256"] == digest(arguments["content"]):
                    found = current
            elif previous in {"update_work_package", "transition"}:
                if self.mode == "native":
                    if previous=='transition' and {'phase_id','phase_hash'} & arguments.keys():
                        from .native_phase_bridge import reconcile
                        found=reconcile(self,native,actor,args['key'],arguments)
                    else:
                        from .native_qa_bridge import reconcile
                        found=reconcile(native,actor,args['key'],arguments) if previous=='transition' else None
                    if found is None:raise ValueError("OUTCOME_UNKNOWN_NO_PROVEN_RECEIPT; native PATCH must not be automatically repeated")
                else:
                    native.package(arguments["id"])
                    try:
                        found = native.call(f"/api/v3/qldapm/mutation_receipts/{marker}")
                    except NativeError as error:
                        if error.status != 404:
                            raise
            elif previous in {"request_test", "propose_operation"}:
                found = self.store.job_for_request(actor, args["key"])
            if found is None:
                raise ValueError("OUTCOME_UNKNOWN_NO_PROVEN_RECEIPT; do not blindly retry")
            target = (found['id'] if previous=='create_work_package' else arguments['id']) if previous in {
                'create_work_package','update_work_package','comment','transition','change_gate'} else None
            if self.mode=='native' and previous=='transition' and (found.get('qa_native') or found.get('phase_native')) and args['key'].startswith('proposal-'):
                identifier=args['key'][9:];proposal=self.store.proposal(actor,identifier)
                token=bind_proposal(self.store,actor,self.config['project_id'],proposal)
                try:
                    return self.store.finish_reconciliation(actor,args['key'],found,self.config['project_id'],
                        knowledge_id=target,native_qa_proposal=identifier if found.get('qa_native') else None,
                        native_phase_proposal=identifier if found.get('phase_native') else None)
                finally:reset_run(token)
            if self.mode=='native' and previous in {'create_dependency','update_dependency','delete_dependency'}:
                identifier=args['key'][9:];proposal=self.store.proposal(actor,identifier)
                token=bind_proposal(self.store,actor,self.config['project_id'],proposal)
                try:
                    return self.store.finish_reconciliation(actor,args['key'],found,self.config['project_id'],
                        native_dependency_proposal=identifier,knowledge_ids=[row['id'] for row in found['readback']])
                finally:reset_run(token)
            if self.mode=='native' and previous=='delete_work_package':
                return self.store.finish_reconciliation(actor,args['key'],found,self.config['project_id'],
                    native_delete_proposal=args['key'][9:],knowledge_id=arguments['id'])
            return self.store.finish_reconciliation(actor,args['key'],found,self.config['project_id'],knowledge_id=target)
        if action == "get_job":
            self.keys(args, {"id"}, {"id"})
            return self.store.job(actor, args["id"])
        if action in {"list_code", "read_code", "write_code"}:
            self.keys(args, {"path", "content", "expected_hash", "workspace_actor"}, {"path"})
            target = int(args.get("workspace_actor", actor))
            if str(target) not in self.config["users"]:
                raise PermissionError("WORKSPACE_ACTOR_DENIED")
            if action == "list_code":
                return self.workspace.list(target, args["path"])
            if action == "read_code":
                return self.workspace.read(target, args["path"])
            if not business_manager(role) or target != actor:
                raise PermissionError("DEVELOPER_REQUIRED")
            # Serialize hash-check plus file replacement across local/UI and gateway confirmations.
            with self.store.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                return self.workspace.write(actor, args["path"], args["content"], args["expected_hash"])
        if action == "request_test":
            self.keys(args, {"suite", "workspace_actor", "work_package_id"}, {"suite"})
            if role not in {"BE", "FE", "QA", "PM", AI_SYSTEM_OWNER} or args["suite"] not in {"gate-policy", "gateway", "core-integration"}:
                raise PermissionError("TEST_SUITE_DENIED")
            target = int(args.get("workspace_actor", actor))
            if str(target) not in self.config["users"]:
                raise PermissionError("WORKSPACE_ACTOR_DENIED")
            payload = {"suite": args["suite"], "workspace_actor": target, "snapshot_hash": "AT_EXECUTION"}
            if "work_package_id" in args:
                if args["suite"] == "gateway":
                    raise ValueError("WORKSPACE_TEST_RECEIPT_REQUIRED; gateway regression tests infrastructure only")
                item = native.package(args["work_package_id"])
                gate = native.call(f"/api/v3/qldapm/gates/{item['id']}")
                payload.update(project_id=self.config["project_id"], work_package_id=item["id"], gate_revision=gate["gate"]["revision"])
            return self.store.enqueue(actor, "test", payload, request_key)
        if action == "propose_operation":
            self.keys(args, {"operation", "parameters"}, {"operation", "parameters"})
            if not business_manager(role) or args["operation"] != "delete_work_package":
                raise PermissionError("PM_AND_ALLOWED_OPERATION_REQUIRED")
            return self.store.enqueue(actor, args["operation"], args["parameters"], request_key)
        if action == "create_work_package":
            self.keys(args, {"source_id", "subject", "type_id", "parent_id", "description", "assignee_id", "assignee_role", "status_id", "source_references", "priority_id", "start_date", "due_date"},
                      {"source_id", "subject", "type_id"})
            if 'source_references' in args:
                from .native_wbs import validate_sources
                validate_sources(native,args)
            if "assignee_role" in args:
                if "assignee_id" in args:
                    raise ValueError("ONE_ASSIGNEE_SELECTOR_REQUIRED")
                args = {**args, "assignee_id": self.role_assignee(args["assignee_role"])}
            source = args["source_id"]
            if not isinstance(source, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", source):
                raise ValueError("SOURCE_ID_REQUIRED")
            field = self.config["source_field"]
            matches = [item for item in native.packages() if item.get(field) == source]
            if len(matches) > 1:
                raise ValueError("DUPLICATE_SOURCE_ID")
            if matches:
                raise NativeError(409, "SOURCE_ID_ALREADY_EXISTS; use the original request receipt, not a new create")
            if int(args["type_id"]) not in self.config["type_ids"]:
                raise ValueError("TYPE_DENIED")
            links = {"project": {"href": f"/api/v3/projects/{native.project_id}"},
                     "type": {"href": f"/api/v3/types/{int(args['type_id'])}"}}
            if "status_id" in args:
                if type(args["status_id"]) is not int or args["status_id"] not in self.config["status_ids"]:
                    raise ValueError("STATUS_DENIED")
                links["status"] = {"href": f"/api/v3/statuses/{args['status_id']}"}
            if args.get("parent_id"):
                native.package(args["parent_id"])
                links["parent"] = {"href": f"/api/v3/work_packages/{int(args['parent_id'])}"}
            if args.get("assignee_id"):
                self.assignee(args["assignee_id"])
                links["assignee"] = {"href": f"/api/v3/users/{int(args['assignee_id'])}"}
            payload = {"subject": args["subject"], field: source, "_links": links,
                       "description": {"format": "markdown", "raw": args.get("description", "")}}
            from .native_wbs import scheduling
            payload.update(scheduling(args))
            if 'priority_id' in args:links['priority']={'href':f"/api/v3/priorities/{args['priority_id']}"}
            form = native.call(f"/api/v3/projects/{native.project_id}/work_packages/form", "POST", payload)
            if errors := form.get("_embedded", {}).get("validationErrors"):
                raise NativeError(422, "OPENPROJECT_FORM_REJECTED", errors)
            scheduling(args,form)
            result = native.call("/api/v3/work_packages", "POST", payload)
            try:
                readback=native.package(result["id"])
                if 'status_id' in args and readback.get('_links',{}).get('status',{}).get('href')!=links['status']['href']:
                    raise NativeError(503,'OPENPROJECT_READBACK_OUTCOME_UNKNOWN; explicit initial status mismatched')
                if (any(readback.get(k)!=v for k,v in scheduling(args).items()) or
                        'priority_id' in args and readback.get('_links',{}).get('priority',{}).get('href')!=links['priority']['href']):
                    raise NativeError(503,'OPENPROJECT_READBACK_OUTCOME_UNKNOWN; explicit schedule/priority mismatched')
                return readback
            except (NativeError,PermissionError):
                raise NativeError(503,'OPENPROJECT_READBACK_OUTCOME_UNKNOWN; POST returned, verify original receipt') from None
        self.keys(args, {"id", "include_context"} if action == "get_work_package" else ({"id", "lock_version", "status_id", "qa_evidence_id", "qa_evidence_hash", "phase_id", "phase_hash"} if action == "transition" else {"id", "lock_version", "changes", "text", "status_id", "operation", "value"}), {"id"})
        item = native.package(args["id"])
        if action == "get_work_package":
            if args.get("include_context") is True:
                item["business_comments"] = native.collection(f"/api/v3/work_packages/{item['id']}/activities")
                relations = item.get("_embedded", {}).get("relations", {})
                rows = relations.get("_embedded", {}).get("elements", [])
                if relations.get("total") != len(rows):
                    raise NativeError(502, "OPENPROJECT_BUSINESS_RELATIONS_INCOMPLETE")
                item["business_relations"] = rows
            return item
        if action == "get_gate":
            return native.call(f"/api/v3/qldapm/gates/{item['id']}")
        if args.get("lock_version") != item["lockVersion"]:
            raise ValueError("STALE_WORK_PACKAGE")
        if action == "comment":
            self.keys(args, {"id", "lock_version", "text"}, {"id", "lock_version", "text"})
            if not args.get("text") or len(args["text"]) > 10000:
                raise ValueError("COMMENT_REQUIRED")
            created = native.call(f"/api/v3/work_packages/{item['id']}/activities", "POST",
                               {"comment": {"format": "markdown", "raw": args["text"] +
                                "\n\n<!-- QLDAPM-request-" + digest(f"{actor}:{request_key}") + " -->"}})
            matches = [row for row in native.collection(f"/api/v3/work_packages/{item['id']}/activities") if row.get("id") == created.get("id")]
            if len(matches) != 1 or matches[0].get("comment", {}).get("raw") != args["text"] + "\n\n<!-- QLDAPM-request-" + digest(f"{actor}:{request_key}") + " -->":
                raise NativeError(502, "OPENPROJECT_COMMENT_READBACK_MISSING; inspect native outcome before retry")
            return matches[0]
        if action == "transition":
            if type(args.get("status_id")) is not int or args.get("status_id") not in self.config["status_ids"]:
                raise ValueError("STATUS_DENIED")
            if self.mode == 'native':
                from .native_qa import transition_guard
                proof=transition_guard(self,who,native,item,args)
                if {'phase_id','phase_hash'} & args.keys():
                    from .native_phase_bridge import execute
                    return execute(self,actor,native,item,args,request_key)
                if proof is not None:
                    from .native_qa_bridge import execute
                    return execute(self,actor,native,item,args,request_key,proof)
            return self.mutate(native, actor, item, action, {"status_id": args["status_id"]}, request_key)
        if action == "change_gate":
            return native.call(f"/api/v3/qldapm/gates/{item['id']}", "POST",
                               {"lock_version": item["lockVersion"], "operation": args["operation"], "value": args["value"],
                                "request_id": "QLDAPM-request-" + digest(f"{actor}:{request_key}"), "request_hash": digest(canonical(args))})
        if action == "update_work_package":
            changes = args.get("changes")
            if not isinstance(changes, dict) or not changes:
                raise ValueError("CHANGES_REQUIRED")
            self.keys(changes, {"subject", "description", "assignee_id", "assignee_role", "start_date", "due_date", "priority_id"})
            if "assignee_role" in changes:
                if "assignee_id" in changes:
                    raise ValueError("ONE_ASSIGNEE_SELECTOR_REQUIRED")
                changes = dict(changes)
                changes["assignee_id"] = self.role_assignee(changes.pop("assignee_role"))
            for field in ("start_date", "due_date"):
                if field in changes and changes[field] is not None:
                    try:
                        if not isinstance(changes[field], str) or date.fromisoformat(changes[field]).isoformat() != changes[field]:
                            raise ValueError()
                    except ValueError:
                        raise ValueError(field.upper() + "_INVALID") from None
            if "start_date" in changes or "due_date" in changes:
                start, end = changes.get("start_date", item.get("startDate")), changes.get("due_date", item.get("dueDate"))
                if start and end and start > end:
                    raise ValueError("DATE_RANGE_INVALID")
            if "priority_id" in changes and (type(changes["priority_id"]) is not int or changes["priority_id"] <= 0):
                raise ValueError("PRIORITY_INVALID")
            if "assignee_id" in changes:
                self.assignee(changes["assignee_id"])
            return self.mutate(native, actor, item, action, {"changes": changes}, request_key)
        raise ValueError("UNKNOWN_ACTION")

    def assignee(self, identifier):
        if str(identifier) not in self.config["users"]:
            raise ValueError("ASSIGNEE_DENIED")

    def role_assignee(self, role):
        role = "BA" if role == "BA-PM" else role
        if not isinstance(role, str) or role not in {"BA", "PM", "BE", "FE", "QA"}:
            raise ValueError("ASSIGNEE_ROLE_DENIED")
        normalize = lambda value: "BA" if value == "BA-PM" else value
        members = [int(actor) for actor, assigned_role in self.config["users"].items() if normalize(assigned_role) == role]
        if len(members) != 1:
            raise ValueError("ASSIGNEE_ROLE_AMBIGUOUS_OR_MISSING")
        target = members[0]
        native = self.native_factory(self.config["openproject_url"], self.store.credential(target), self.config["project_id"])
        if normalize(native.identity(target)["role"]) != role:
            raise PermissionError("ASSIGNEE_ROLE_CHANGED")
        return target

    def mutate(self, native, actor, item, action, changes, request_key):
        if self.mode == "native":
            payload = {"lockVersion": item["lockVersion"]}
            links = {}
            if action == "transition":
                links["status"] = {"href": f"/api/v3/statuses/{changes['status_id']}"}
            else:
                for name, value in changes["changes"].items():
                    if name == "assignee_id":
                        links["assignee"] = {"href": f"/api/v3/users/{value}"}
                    elif name == "priority_id":
                        links["priority"] = {"href": f"/api/v3/priorities/{value}"}
                    elif name in {"start_date", "due_date"}:
                        payload[{"start_date": "startDate", "due_date": "dueDate"}[name]] = value
                    elif name == "description":
                        payload[name] = {"format": "markdown", "raw": value}
                    else:
                        payload[name] = value
            if links:
                payload["_links"] = links
            dates, adjustments = self.date_payload(native, item, changes.get("changes", {}))
            payload.update(dates)
            result = native.call(f"/api/v3/work_packages/{item['id']}", "PATCH", payload)
            readback = native.package(item["id"])
            if readback.get("lockVersion") != result.get("lockVersion"):
                raise NativeError(409, "NATIVE_READBACK_CHANGED; inspect result before retry")
            if any((readback.get(name, {}).get("raw") != value.get("raw") if name == "description" else readback.get(name) != value)
                    for name, value in payload.items() if name not in {"lockVersion", "_links"}) or any(
                    readback.get("_links", {}).get(name, {}).get("href") != value["href"] for name, value in links.items()):
                raise NativeError(502, "OPENPROJECT_WRITE_READBACK_MISMATCH; inspect native outcome before retry")
            if adjustments:
                if any(readback.get({"start_date": "startDate", "due_date": "dueDate"}[name]) != row["actual"] for name, row in adjustments.items()):
                    raise NativeError(502, "OPENPROJECT_DATE_READBACK_MISMATCH")
                readback["date_adjustments"] = adjustments
            return readback
        payload = {"action": action, "lock_version": item["lockVersion"], **changes,
                   "request_id": "QLDAPM-request-" + digest(f"{actor}:{request_key}")}
        # Only the private core bridge key can mark a receipt as an AI delegation.
        key = self.store.root / "ui.key"
        if key.is_file() and isinstance(native, Native):
            at = int(time.time())
            fingerprint = digest(canonical({"id": item["id"], **payload}))
            native.mutation_headers = {"X-Qldapm-At": str(at), "X-Qldapm-Mutation": hmac.new(key.read_bytes(),
                f"{actor}:{at}:{fingerprint}".encode(), hashlib.sha256).hexdigest()}
        return native.call("/api/v3/qldapm/mutations", "POST", {"id": item["id"], **payload})

    @staticmethod
    def date_payload(native, item, changes):
        dates = {field: changes[name] for name, field in (("start_date", "startDate"), ("due_date", "dueDate")) if name in changes}
        if not dates:
            return {}, {}
        form = native.call(f"/api/v3/work_packages/{item['id']}/form", "POST", {"lockVersion": item["lockVersion"], **dates})
        if errors := form.get("_embedded", {}).get("validationErrors"):
            raise NativeError(422, "OPENPROJECT_FORM_REJECTED", errors)
        normalized = form.get("_embedded", {}).get("payload", {})
        for field in set(dates) | ({"startDate", "dueDate"} & normalized.keys()):
            value = normalized.get(field)
            try:
                valid = field in normalized and (value is None or isinstance(value, str) and date.fromisoformat(value).isoformat() == value)
            except ValueError:
                valid = False
            if not valid:
                raise NativeError(502, "OPENPROJECT_DATE_FORM_MALFORMED")
        adjustments = {}
        for name, field in (("start_date", "startDate"), ("due_date", "dueDate")):
            requested = dates.get(field, item.get(field))
            if field in normalized and requested != normalized[field]:
                adjustments[name] = {"requested": requested, "actual": normalized[field]}
                if field not in dates:
                    adjustments[name]["automatic"] = True
        return {field: normalized[field] for field in dates}, adjustments

    @staticmethod
    def keys(args, allowed, required=set()):
        if set(args) - allowed or not required <= set(args):
            raise ValueError("INVALID_ARGUMENTS")

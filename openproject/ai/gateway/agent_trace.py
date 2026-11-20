"""Local IDs only. Trace scope comes from a claimed stored run, never model arguments."""
import re
from contextvars import ContextVar

from .agent_models import AgentRun

current_run = ContextVar("qldapm_agent_run", default=None)


def bind_run(store, actor, project, identifier):
    with store.connect() as db:
        row = db.execute("SELECT document FROM agent_runs WHERE id=?", (identifier,)).fetchone()
    if not row:
        return current_run.set(None)
    run = AgentRun.from_json(row["document"])
    if (run.actor_id, run.project_id, run.run_id) != (actor, project, identifier) or run.state != "RUNNING":
        raise PermissionError("AGENT_TRACE_SCOPE_OR_STATE_DENIED")
    return current_run.set((store, run))


def reset_run(token):
    if token is not None:
        current_run.reset(token)


def bind_proposal(store, actor, project, proposal):
    identifier=proposal['command'].get('_origin_run_id')
    if identifier is None:
        return current_run.set(None)
    run=store.agent_run(actor,project,identifier)
    result=store.run(actor,identifier).get('result') or {}
    linked=any(tool.get('result',{}).get('result',{}).get('id')==proposal['id'] for tool in result.get('tools',[]))
    if run.state!='REVIEW' or not linked:
        raise PermissionError('PROPOSAL_ORIGIN_SCOPE_OR_STATE_DENIED')
    # Trace lineage grants no authority; confirm and ingestion still perform their own fresh Native checks.
    return current_run.set((store,run))


def trace_event(layer, event):
    if layer not in {"worker", "native", "provider", "agent"} or not isinstance(event, str) or not re.fullmatch(r"[A-Za-z_]{1,40}", event):
        raise ValueError("TRACE_EVENT_CODE_ONLY")
    binding = current_run.get()
    if binding:
        store, run = binding
        store.record(run.actor_id, "trace_" + layer, event, "attempt")

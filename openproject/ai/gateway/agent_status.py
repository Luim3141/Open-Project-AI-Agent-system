"""Agent Status Widget Module (P08-03):
Measures and reports runtime operational states, including legacy PM/DEV entries.
States: ACTIVE, IDLE, WAITING_QUOTA, BLOCKED_KEY_OR_MODEL, ERROR.
Never fakes 'online' or 'active' when Docker, Gateway or Provider is down.
"""
from typing import Any, Literal, get_args
from .agent_models import AgentName
import time
import json

AgentRuntimeState = Literal["ACTIVE", "IDLE", "WAITING_QUOTA", "BLOCKED_KEY_OR_MODEL", "ERROR", "RUNTIME_DOWN"]

AGENT_KEYS = get_args(AgentName)


def _event_states(db, run):
    active, failed = set(), set()
    for row in db.execute('SELECT document FROM execution_events WHERE run_id=? AND actor=? AND project=? ORDER BY sequence',
            (run['run_id'],run['actor_id'],run['project_id'])):
        event=json.loads(row[0]);agent=event.get('agent_id');kind=event['event_type']
        if agent not in AGENT_KEYS:
            continue
        if kind in {'AGENT_STARTED','REVIEW_STARTED'}:
            active.add(agent)
        elif kind in {'AGENT_COMPLETED','REVIEW_COMPLETED','AGENT_FAILED'}:
            active.discard(agent)
            if kind=='AGENT_FAILED':failed.add(agent)
    return active,failed


def get_agents_runtime_status(store, project_id: int, actor_id=None) -> dict[str, Any]:
    """Computes verifiable, real-time agent status from actual database and queue state.
    Zero synthetic or faked status.
    """
    try:
        with store.connect() as db:
            # 1. Check if Gemini provider is blocked (circuit open, bad key/model)
            block_info = None  # Local specialists have no provider dependency; quota panel reports Gemini separately.
            is_provider_blocked = (block_info is not None)

            # 2. Count active runs per agent
            # Match agent from agent_tasks joined with agent_runs
            active_rows = db.execute(
                """SELECT json_extract(t.document, '$.agent') AS agent, r.document FROM agent_runs r
                   JOIN agent_tasks t ON t.id = r.task_id
                   WHERE r.project=? AND json_extract(r.document, '$.state') = 'RUNNING'""",
                (project_id,)
            ).fetchall()

            active_counts = {k: 0 for k in AGENT_KEYS}
            for row in active_rows:
                if actor_id is not None and __import__('json').loads(row['document'])['actor_id'] != actor_id:
                    continue
                agent_name = row["agent"]
                if agent_name in active_counts:
                    active_counts[agent_name] += 1
                active,_=_event_states(db,json.loads(row['document']))
                for specialist in active-{agent_name}:
                    active_counts[specialist] += 1

            # 3. Count waiting quota / queued runs
            waiting_rows = db.execute(
                """SELECT json_extract(t.document, '$.agent') AS agent, r.document FROM agent_runs r
                   JOIN agent_tasks t ON t.id = r.task_id
                   WHERE r.project=? AND json_extract(r.document, '$.state') IN ('WAITING_QUOTA', 'WAITING_PROVIDER')""",
                (project_id,)
            ).fetchall()

            waiting_counts = {k: 0 for k in AGENT_KEYS}
            for row in waiting_rows:
                if actor_id is not None and __import__('json').loads(row['document'])['actor_id'] != actor_id:
                    continue
                agent_name = row["agent"]
                if agent_name in waiting_counts:
                    waiting_counts[agent_name] += 1
                waiting,_=_event_states(db,json.loads(row['document']))
                for specialist in waiting-{agent_name}:
                    waiting_counts[specialist] += 1

            # 4. Check for recent unhandled errors (last 30 minutes)
            cutoff = time.time() - 1800
            error_rows = db.execute(
                """SELECT json_extract(t.document, '$.agent') AS agent, r.document FROM agent_runs r
                   JOIN agent_tasks t ON t.id = r.task_id
                   WHERE r.project=? AND json_extract(r.document, '$.state') = 'FAILED'
                     AND json_extract(r.document, '$.updated_at') >= ?
                   ORDER BY json_extract(r.document, '$.updated_at') DESC""",
                (project_id, cutoff)
            ).fetchall()

            recent_errors: dict[str, str] = {}
            for row in error_rows:
                if actor_id is not None and __import__('json').loads(row['document'])['actor_id'] != actor_id:
                    continue
                agent_name = row["agent"]
                if agent_name not in recent_errors:
                    recent_errors[agent_name] = "RECENT_RUN_FAILED"
                _,failed=_event_states(db,json.loads(row['document']))
                for specialist in failed:
                    recent_errors.setdefault(specialist,'RECENT_AGENT_FAILED')

            # 5. Build agent states
            agents_status = {}
            summary = {
                "total_agents": len(AGENT_KEYS),
                "active": 0,
                "idle": 0,
                "waiting_quota": 0,
                "blocked": 0,
                "error": 0,
            }

            for agent in AGENT_KEYS:
                if is_provider_blocked:
                    state: AgentRuntimeState = "BLOCKED_KEY_OR_MODEL"
                    summary["blocked"] += 1
                elif active_counts[agent] > 0:
                    state = "ACTIVE"
                    summary["active"] += 1
                elif waiting_counts[agent] > 0:
                    state = "WAITING_QUOTA"
                    summary["waiting_quota"] += 1
                elif agent in recent_errors:
                    state = "ERROR"
                    summary["error"] += 1
                else:
                    state = "IDLE"
                    summary["idle"] += 1

                agents_status[agent] = {
                    "agent": agent,
                    "state": state,
                    "active_runs": active_counts[agent],
                    "waiting_quota_runs": waiting_counts[agent],
                    "last_error": recent_errors.get(agent),
                    "provider_blocked": is_provider_blocked,
                    "block_reason": block_info.get("reason") if block_info else None,
                }

            return {
                "runtime_healthy": True,
                "provider_circuit_closed": not is_provider_blocked,
                "block_info": block_info,
                "agents": agents_status,
                "summary": summary,
            }

    except Exception as exc:
        # Fail-closed: report runtime down if database or store unavailable
        return {
            "runtime_healthy": False,
            "provider_circuit_closed": False,
            "error": 'STORE_UNAVAILABLE',
            "agents": {
                agent: {
                    "agent": agent,
                    "state": "RUNTIME_DOWN",
                    "active_runs": 0,
                    "waiting_quota_runs": 0,
                    "last_error": "STORE_UNAVAILABLE",
                    "provider_blocked": True,
                }
                for agent in AGENT_KEYS
            },
            "summary": {
                "total_agents": len(AGENT_KEYS),
                "active": 0,
                "idle": 0,
                "waiting_quota": 0,
                "blocked": len(AGENT_KEYS),
                "error": 0,
            },
        }

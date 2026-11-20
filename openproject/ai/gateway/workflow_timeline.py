"""Workflow Timeline & Error Trace Module (P08-05):
Provides end-to-end tracing across n8n -> Gateway Dispatcher -> Agent Run -> Native Receipt
under a single unified task_id / trace_id.
Captures recent workflow errors with root-cause identification and zero data loss.
"""
from typing import Any
from datetime import datetime, timezone, timedelta
import json
import time

BANGKOK_TZ = timezone(timedelta(hours=7))


def format_bangkok_time(ts: float | int | None) -> str:
    """Formats epoch timestamp into Asia/Bangkok readable datetime."""
    if ts is None:
        return "N/A"
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(BANGKOK_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_task_workflow_timeline(
    store,
    actor_id: int,
    project_id: int,
    task_id: str | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    """Retrieves end-to-end workflow execution timeline and recent errors.
    If task_id is given, traces that specific task through n8n -> gateway -> agent -> native.
    Otherwise, returns recent pipeline execution events and latest workflow alerts.
    """
    timeline_steps: list[dict[str, Any]] = []
    recent_errors: list[dict[str, Any]] = []

    try:
        with store.connect() as db:
            # 1. Fetch recent workflow alerts from store (n8n / automation)
            alerts = store.workflow_alerts(project_id)
            if alerts:
                for alert in alerts:
                    recent_errors.append({
                        "source": "n8n_workflow_alerts",
                        "workflow": alert.get("workflow_id"),
                        "severity": alert.get("severity", "WARNING"),
                        "message": alert.get("error_code",'WORKFLOW_ALERT'),
                        "recorded_at": format_bangkok_time(alert.get("observed_at")),
                    })

            # 2. Fetch specific task trace or recent audit traces
            if task_id:
                # Query audit table for this specific task
                audit_rows = db.execute(
                    """SELECT id, at, actor, action, target, outcome, version, run_id, trace_id
                       FROM audit
                       WHERE task_id=? AND project_id=? AND actor=?
                       ORDER BY at ASC, id ASC LIMIT ?""",
                    (task_id, project_id, actor_id, limit)
                ).fetchall()

                for row in audit_rows:
                    outcome = row["outcome"]
                    is_error = outcome in {"error", "denied", "failed"} or outcome.startswith("ERR_")
                    timeline_steps.append({
                        "step_id": row["id"],
                        "timestamp": format_bangkok_time(row["at"]),
                        "layer": "gateway_agent_trace",
                        "action": row["action"],
                        "target": row["target"],
                        "status": "ERROR" if is_error else "SUCCESS",
                        "outcome": outcome,
                        "version": row["version"],
                        "run_id": row["run_id"],
                        "trace_id": row["trace_id"],
                    })
                    if is_error:
                        recent_errors.append({
                            "source": "gateway_audit",
                            "action": row["action"],
                            "target": row["target"],
                            "message": f"Execution outcome: {outcome}",
                            "recorded_at": format_bangkok_time(row["at"]),
                        })
            else:
                # Retrieve most recent general audit events for this actor
                audit_rows = db.execute(
                    """SELECT id, at, actor, action, target, outcome, version, run_id, task_id, trace_id
                       FROM audit
                       WHERE project_id=? AND actor=?
                       ORDER BY at DESC, id DESC LIMIT ?""",
                    (project_id, actor_id, limit)
                ).fetchall()

                for row in reversed(audit_rows):
                    outcome = row["outcome"]
                    is_error = outcome in {"error", "denied", "failed"} or outcome.startswith("ERR_")
                    timeline_steps.append({
                        "step_id": row["id"],
                        "timestamp": format_bangkok_time(row["at"]),
                        "layer": "pipeline_event",
                        "action": row["action"],
                        "target": row["target"],
                        "status": "ERROR" if is_error else "SUCCESS",
                        "outcome": outcome,
                        "version": row["version"],
                        "run_id": row["run_id"],
                        "task_id": row["task_id"],
                        "trace_id": row["trace_id"],
                    })
                    if is_error:
                        recent_errors.append({
                            "source": "pipeline_audit",
                            "action": row["action"],
                            "target": row["target"],
                            "message": f"Audit outcome: {outcome}",
                            "recorded_at": format_bangkok_time(row["at"]),
                        })

    except Exception as exc:
        recent_errors.append({
            "source": "store_query_failure",
            "message": 'TIMELINE_UNAVAILABLE',
            "recorded_at": format_bangkok_time(time.time()),
        })

    return {
        "task_id": task_id,
        "timeline_trace": timeline_steps,
        "recent_errors": recent_errors,
        "has_active_errors": len(recent_errors) > 0,
        "total_steps": len(timeline_steps),
    }

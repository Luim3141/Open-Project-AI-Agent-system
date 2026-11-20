"""Development Progress Reporter Module (P08-07):
Parses docs/ai-multi-agent-upgrade/TASKS.json to generate verified implementation metrics.
Calculates overall completion %, per-phase progress (P00-P10), blocked tasks, and evidence gaps.
Strictly READ-ONLY: never writes unilaterally to OpenProject live packages.
"""
from typing import Any
from pathlib import Path
import json


def get_tasks_progress_report(tasks_file_path: Path | str | None = None) -> dict[str, Any]:
    """Reads TASKS.json and computes authoritative progress metrics without live DB mutation."""
    default_candidates = [
        Path("docs/ai-multi-agent-upgrade/TASKS.json"),
        Path(__file__).resolve().parent.parent.parent / "docs" / "ai-multi-agent-upgrade" / "TASKS.json",
        
    ]

    resolved_path = None
    if tasks_file_path:
        p = Path(tasks_file_path)
        if p.exists():
            resolved_path = p
    else:
        for candidate in default_candidates:
            if candidate.exists():
                resolved_path = candidate
                break

    if not resolved_path:
        return {
            "available": False,
            "error": "TASKS_JSON_NOT_FOUND",
            "total_tasks": 0,
            "done_tasks": 0,
            "percent_done": 0.0,
            "phases": {},
            "blocked_tasks": [],
            "missing_evidence_tasks": [],
            "read_only": True,
        }

    try:
        data = json.loads(resolved_path.read_text(encoding="utf-8"))
        tasks = data.get("tasks", [])
    except Exception as exc:
        return {
            "available": False,
            "error": "TASKS_JSON_PARSE_ERROR",
            "total_tasks": 0,
            "done_tasks": 0,
            "percent_done": 0.0,
            "phases": {},
            "blocked_tasks": [],
            "missing_evidence_tasks": [],
            "read_only": True,
        }

    total_tasks = len(tasks)
    done_tasks = 0
    blocked_tasks = []
    missing_evidence = []
    phases_map: dict[str, dict[str, Any]] = {}

    for task in tasks:
        tid = task.get("id", "UNKNOWN")
        phase = task.get("phase", tid.split("-")[0] if "-" in tid else "OTHER")
        status = task.get("status", "TODO").upper()
        evidence = task.get("evidence", [])

        if phase not in phases_map:
            phases_map[phase] = {"total": 0, "done": 0, "blocked": 0, "in_progress": 0, "todo": 0}

        phases_map[phase]["total"] += 1

        if status == "DONE":
            done_tasks += 1
            phases_map[phase]["done"] += 1
            if not evidence:
                missing_evidence.append({
                    "id": tid,
                    "title": task.get("title", ""),
                    "phase": phase,
                })
        elif status == "BLOCKED":
            blocked_tasks.append({
                "id": tid,
                "title": task.get("title", ""),
                "phase": phase,
                "notes": task.get("notes", ""),
            })
            phases_map[phase]["blocked"] += 1
        elif status == "IN_PROGRESS":
            phases_map[phase]["in_progress"] += 1
        else:
            phases_map[phase]["todo"] += 1

    percent_done = round((done_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # Format phase progress
    phases_report = {}
    for phase_name in sorted(phases_map.keys()):
        pdata = phases_map[phase_name]
        ptotal = pdata["total"]
        pdone = pdata["done"]
        p_pct = round((pdone / ptotal * 100), 1) if ptotal > 0 else 0.0

        if pdone == ptotal and ptotal > 0:
            phase_status = "DONE"
        elif pdone > 0 or pdata["in_progress"] > 0:
            phase_status = "IN_PROGRESS"
        else:
            phase_status = "TODO"

        phases_report[phase_name] = {
            "phase": phase_name,
            "total": ptotal,
            "done": pdone,
            "percent": p_pct,
            "status": phase_status,
            "blocked": pdata["blocked"],
        }

    return {
        "available": True,
        "source_file": resolved_path.name,
        "acceptance_basis": "HISTORICAL_DECLARED_CHECKLIST_NOT_RUNTIME_VERIFICATION",
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "percent_done": percent_done,
        "phases": phases_report,
        "blocked_tasks": blocked_tasks,
        "blocked_count": len(blocked_tasks),
        "missing_evidence_tasks": missing_evidence,
        "missing_evidence_count": len(missing_evidence),
        "read_only": True,
        "mutation_safety": "ZERO_LIVE_WRITE_INTO_OPENPROJECT",
    }

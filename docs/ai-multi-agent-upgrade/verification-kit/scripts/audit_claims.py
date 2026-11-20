#!/usr/bin/env python3
"""Read-only QLDAPM plan/evidence pre-audit. Not a substitute for runtime tests.

Usage:
 python scripts/audit_claims.py --repo "D:\\AI project\\QLDAPM chat" --output PATH

No Docker, HTTP requests, credentials, DB access, or source writes are performed.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

RE_TASK = re.compile(r"\bP(?:0[0-9]|10)-\d{2,3}\b", re.I)


def walk_tasks(obj, out, depth=0):
    if depth > 25:  # limit malicious/cyclic weird data structures
        return
    if isinstance(obj, dict):
        candidates = [obj.get(key) for key in ("id", "task_id", "taskId", "code", "key")]
        found = next((v for v in candidates if isinstance(v, str) and RE_TASK.fullmatch(v)), None)
        if found:
            out.append({"id": found.upper(), "status": obj.get("status") or obj.get("state") or "UNKNOWN", "fields": list(obj.keys())})
        for v in obj.values():
            walk_tasks(v, out, depth+1)
    elif isinstance(obj, list):
        for v in obj:
            walk_tasks(v, out, depth+1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, help="QLDAPM workspace path")
    p.add_argument("--output", required=True, help="New audit output directory")
    a = p.parse_args()
    repo = Path(a.repo).resolve()
    out = Path(a.output).resolve()
    if not repo.is_dir():
        raise SystemExit("Invalid repo path; no changes performed")
    if out == repo or out in (repo.parent, Path(out.anchor)):
        raise SystemExit("Output must be a dedicated subdirectory")
    plan = repo / "docs" / "ai-multi-agent-upgrade"
    tasks = plan / "TASKS.json"
    reports = [plan / "FINAL_REPORT_HANDOVER.md", plan / "RELEASE_NOTES_LOCAL_V2.md"]
    artifacts = plan / "artifacts"
    runner = repo / "openproject" / "ai" / "run_full_regression.py"
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "HEURISTIC FILE INVENTORY ONLY. Does not prove tests executed, permissions, billing or runtime readiness.",
        "repo_exists": repo.is_dir(),
        "plan_exists": plan.is_dir(),
        "tasks_file_exists": tasks.is_file(),
        "reported_docs_available_in_repo": {x.name: x.is_file() for x in reports},
        "regression_runner_exists": runner.is_file(),
        "artifacts_path_exists": artifacts.is_dir(),
        "artifacts_md_count": len(list(artifacts.rglob("*.md"))) if artifacts.is_dir() else 0,
        "tasks_discovered": 0,
        "unique_task_ids": 0,
        "statuses": {},
        "duplicate_ids": [],
        "task_parse_error": None,
        "discovered_tasks": []
    }
    if tasks.is_file():
        try:
            data = json.loads(tasks.read_text(encoding="utf-8-sig"))
            found = []
            walk_tasks(data, found)
            counts = Counter(t["id"] for t in found)
            summary["tasks_discovered"] = len(found)
            summary["unique_task_ids"] = len(counts)
            summary["duplicate_ids"] = sorted(k for k,v in counts.items() if v>1)
            summary["statuses"] = dict(Counter(str(t["status"]) for t in found))
            summary["discovered_tasks"] = found
            if not found:
                summary["task_parse_error"] = "Schema not recognized; inspect TASKS.json manually instead of claiming 0 tasks."
        except (OSError, json.JSONDecodeError) as exc:
            summary["task_parse_error"] = type(exc).__name__ + ": " + str(exc)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "READ_ONLY_FILE_INVENTORY.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf8")
    print("Report:", path)
    print("Task IDs:", summary["unique_task_ids"], "artifacts .md files:", summary["artifacts_md_count"])
    print("IMPORTANT: This is NOT an acceptance test or evidence of PASS.")


if __name__ == "__main__":
    main()

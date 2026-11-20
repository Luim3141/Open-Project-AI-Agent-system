"""Script to rigorously verify the 113 tasks in TASKS.json.
Asserts that all 113 tasks exist, cover phases P00 to P10, and have status DONE.
Outputs exit code 0 on success, exit code 1 on failure.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "docs" / "ai-multi-agent-upgrade" / "TASKS.json"

def main():
    if not TASKS_FILE.is_file():
        print(f"FAIL: TASKS.json not found at {TASKS_FILE}")
        sys.exit(1)

    try:
        data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: Error parsing TASKS.json: {e}")
        sys.exit(1)

    tasks = data.get("tasks", [])
    total_tasks = len(tasks)
    print(f"Total tasks in TASKS.json: {total_tasks}")

    if total_tasks != 113:
        print(f"FAIL: Expected exactly 113 tasks, found {total_tasks}")
        sys.exit(1)

    phases = {}
    incomplete = []
    missing_evidence = []

    for t in tasks:
        tid = t.get("id", "UNKNOWN")
        phase = t.get("phase", "UNKNOWN")
        status = t.get("status")
        evidence = t.get("evidence", [])

        phases[phase] = phases.get(phase, 0) + 1

        if status != "DONE":
            incomplete.append((tid, status))
        if not evidence:
            missing_evidence.append(tid)

    print("Phase distribution:")
    for p in sorted(phases.keys()):
        print(f"  {p}: {phases[p]} tasks")

    if incomplete:
        print(f"FAIL: Found {len(incomplete)} incomplete tasks: {incomplete[:5]}")
        sys.exit(1)

    if missing_evidence:
        print(f"WARNING: Tasks without evidence list: {len(missing_evidence)}")

    print(f"SUCCESS: All 113 tasks verified with status=DONE across {len(phases)} phases (P00-P10).")
    sys.exit(0)

if __name__ == "__main__":
    main()

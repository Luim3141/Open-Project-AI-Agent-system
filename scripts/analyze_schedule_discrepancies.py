"""Analyze discrepancies in 7-sprint schedule proposal."""
import csv
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CSV_PATH = REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/MAIN_SCRUM_329_NATIVE_FORK_PROPOSAL.csv'

def working_after(d):
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d

def main():
    rows = list(csv.DictReader(CSV_PATH.open(encoding='utf-8-sig')))
    print(f"Total rows in CSV: {len(rows)}")

    types = Counter(r['Type'] for r in rows)
    print(f"Types: {dict(types)}")

    # Anchor and Sprints in CSV
    # Sprints defined as 2-week intervals starting Monday 2026-10-05:
    anchor = date(2026, 10, 5)
    sprint_windows = {}
    for i in range(1, 8):
        s_start = anchor + timedelta(days=(i - 1) * 14)
        s_end = s_start + timedelta(days=11)  # Friday of second week
        sprint_windows[f"S{i}"] = (s_start, s_end)
        print(f"Sprint S{i} window: {s_start} (Mon) -> {s_end} (Fri) [10 working days]")

    subtasks = [r for r in rows if r['Type'] == 'Subtask']
    tasks = [r for r in rows if r['Type'] == 'Task']
    epics = [r for r in rows if r['Type'] == 'Epic']

    print(f"\nSubtasks count per sprint in CSV:")
    sprint_counts = Counter(r['Proposed Native Sprint'] for r in subtasks)
    for s in sorted(sprint_counts.keys()):
        print(f"  {s}: {sprint_counts[s]}")

    # Check 52 subtasks outside sprint window
    outside = []
    cross_sprint = []
    for r in subtasks:
        sprint = r['Proposed Native Sprint']
        if sprint in sprint_windows:
            w_start, w_end = sprint_windows[sprint]
            p_start = date.fromisoformat(r['Proposed Start Date'])
            p_due = date.fromisoformat(r['Proposed Due Date'])
            if p_start < w_start or p_due > w_end:
                outside.append({
                    'id': r['ID'],
                    'subject': r['Subject'],
                    'sprint': sprint,
                    'p_start': str(p_start),
                    'p_due': str(p_due),
                    'w_start': str(w_start),
                    'w_end': str(w_end),
                    'parent': r['Parent ID']
                })
            if (p_due - p_start).days > 0 and (p_due.day != p_start.day):
                pass

    print(f"\nSubtasks with dates outside assigned Sprint window: {len(outside)}")
    for o in outside[:10]:
        print(f"  WP #{o['id']} (Parent {o['parent']}) in {o['sprint']} has dates {o['p_start']} to {o['p_due']}, but window is {o['w_start']} to {o['w_end']}")

    # Let's check how the parent tasks are assigned
    print("\nTasks count per sprint:")
    task_counts = Counter(r['Proposed Native Sprint'] for r in tasks)
    for s in sorted(task_counts.keys()):
        print(f"  {s}: {task_counts[s]}")

if __name__ == '__main__':
    main()

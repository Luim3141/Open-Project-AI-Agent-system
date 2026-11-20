import csv
from datetime import date
from pathlib import Path

REPO = Path('.')
CSV_PATH = REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/MAIN_SCRUM_329_NATIVE_FORK_PROPOSAL.csv'

rows = {int(r['ID']): r for r in csv.DictReader(CSV_PATH.open(encoding='utf-8-sig'))}

subtasks = [r for r in rows.values() if r['Type'] == 'Subtask']
tasks = [r for r in rows.values() if r['Type'] == 'Task']
epics = [r for r in rows.values() if r['Type'] == 'Epic']

sub_violations = []
for s in subtasks:
    p_id = int(s['Parent ID'])
    p = rows[p_id]
    s_start, s_due = date.fromisoformat(s['Proposed Start Date']), date.fromisoformat(s['Proposed Due Date'])
    p_start, p_due = date.fromisoformat(p['Proposed Start Date']), date.fromisoformat(p['Proposed Due Date'])
    if s_start < p_start or s_due > p_due:
        sub_violations.append((s['ID'], p_id))

task_violations = []
for t in tasks:
    p_id = int(t['Parent ID'])
    p = rows[p_id]
    t_start, t_due = date.fromisoformat(t['Proposed Start Date']), date.fromisoformat(t['Proposed Due Date'])
    p_start, p_due = date.fromisoformat(p['Proposed Start Date']), date.fromisoformat(p['Proposed Due Date'])
    if t_start < p_start or t_due > p_due:
        task_violations.append((t['ID'], p_id))

print(f"Subtask within Task violations: {len(sub_violations)}")
print(f"Task within Epic violations: {len(task_violations)}")

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

REPO = Path('.')
BASELINE = json.loads((REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/main-schedule-baseline.json').read_text())

wps = {x['id']: x for x in BASELINE['work_packages']}
epics = {x['id']: x for x in BASELINE['work_packages'] if x['type'] == 'Epic'}
tasks = {x['id']: x for x in BASELINE['work_packages'] if x['type'] == 'Task'}
parent = {i: i if x['type'] == 'Task' else x['parent_id'] for i, x in wps.items() if x['type'] != 'Epic'}
follows = [r for r in BASELINE['relations'] if r['relation_type'] == 'follows']

task_preds = defaultdict(set)
for r in follows:
    f_task = parent[r['from_id']]
    t_task = parent[r['to_id']]
    if f_task != t_task:
        task_preds[f_task].add(t_task)

from graphlib import TopologicalSorter
ts = TopologicalSorter(task_preds)
task_order = list(ts.static_order())

earliest_week = {}
for t in task_order:
    preds = task_preds[t]
    if not preds:
        earliest_week[t] = 1
    else:
        earliest_week[t] = max(earliest_week[p] for p in preds) + 1

# Check Epic groupings
epics_tasks = defaultdict(list)
for t_id, t in tasks.items():
    epics_tasks[t['parent_id']].append(t_id)

print(f"Total Epics: {len(epics)}")
for e_id, e in sorted(epics.items()):
    t_list = epics_tasks[e_id]
    w_list = [earliest_week[t] for t in t_list]
    print(f"Epic #{e_id:2d}: {e['subject'][:35]:35s} | Tasks: {len(t_list):2d} | Weeks: {min(w_list):2d}..{max(w_list):2d}")

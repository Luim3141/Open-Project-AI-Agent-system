import json
from collections import defaultdict
from graphlib import TopologicalSorter
from pathlib import Path

REPO = Path('.')
BASELINE = json.loads((REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/main-schedule-baseline.json').read_text())

wps = {x['id']: x for x in BASELINE['work_packages']}
tasks = {x['id']: x for x in BASELINE['work_packages'] if x['type'] == 'Task'}
parent = {i: i if x['type'] == 'Task' else x['parent_id'] for i, x in wps.items() if x['type'] != 'Epic'}
follows = [r for r in BASELINE['relations'] if r['relation_type'] == 'follows']

# Task level dependencies
task_preds = defaultdict(set)
task_succs = defaultdict(set)
for r in follows:
    f_task = parent[r['from_id']]
    t_task = parent[r['to_id']]
    if f_task != t_task:
        task_preds[f_task].add(t_task)
        task_succs[t_task].add(f_task)

ts = TopologicalSorter(task_preds)
task_order = list(ts.static_order())

# Earliest week (1..14)
earliest_week = {}
for t in task_order:
    preds = task_preds[t]
    if not preds:
        earliest_week[t] = 1
    else:
        earliest_week[t] = max(earliest_week[p] for p in preds) + 1

max_earliest = max(earliest_week.values())
print(f"Max earliest week needed: {max_earliest} weeks.")

# Distribution of tasks by earliest week:
by_earliest = defaultdict(list)
for t, w in earliest_week.items():
    by_earliest[w].append(t)

for w in range(1, max_earliest + 1):
    print(f"  Week {w:2d} (Sprint {(w-1)//2 + 1}): {len(by_earliest[w])} tasks: {by_earliest[w]}")

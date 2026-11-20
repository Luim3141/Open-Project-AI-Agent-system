"""Inspect the 53 tasks and their dependency chain."""
import json
from collections import defaultdict
from graphlib import TopologicalSorter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASELINE = json.loads((REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/main-schedule-baseline.json').read_text())

def main():
    wps = {x['id']: x for x in BASELINE['work_packages']}
    tasks = {x['id']: x for x in BASELINE['work_packages'] if x['type'] == 'Task'}
    epics = {x['id']: x for x in BASELINE['work_packages'] if x['type'] == 'Epic'}
    subtasks = {x['id']: x for x in BASELINE['work_packages'] if x['type'] == 'Subtask'}
    print(f"Total WPs: {len(wps)}, Epics: {len(epics)}, Tasks: {len(tasks)}, Subtasks: {len(subtasks)}")

    parent = {i: i if x['type'] == 'Task' else x['parent_id'] for i, x in wps.items() if x['type'] != 'Epic'}
    follows = [r for r in BASELINE['relations'] if r['relation_type'] == 'follows']
    print(f"Follows relations count: {len(follows)}")

    # Build task dependency graph
    task_deps = defaultdict(set)
    for r in follows:
        s_task = parent[r['from_id']]
        p_task = parent[r['to_id']]
        if s_task != p_task:
            task_deps[s_task].add(p_task)

    # Topological order of tasks
    ts = TopologicalSorter(task_deps)
    task_order = list(ts.static_order())
    print(f"Topological order of tasks: {len(task_order)} tasks.")

    # Calculate longest path (critical path) in terms of tasks
    depth = {}
    crit_pre = {}
    for t_id in task_order:
        preds = task_deps[t_id]
        if not preds:
            depth[t_id] = 1
            crit_pre[t_id] = None
        else:
            best_p = max(preds, key=lambda p: depth[p])
            depth[t_id] = depth[best_p] + 1
            crit_pre[t_id] = best_p

    max_t = max(depth, key=lambda t: depth[t])
    print(f"Maximum dependency depth (Critical Path length): {depth[max_t]} tasks.")

    # Trace critical path
    curr = max_t
    crit_chain = []
    while curr:
        crit_chain.append(curr)
        curr = crit_pre[curr]
    crit_chain.reverse()
    print("Critical path task IDs:", crit_chain)
    print(f"Length of critical path: {len(crit_chain)} tasks.")

if __name__ == '__main__':
    main()

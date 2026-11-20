import json
from collections import defaultdict
from pathlib import Path

REPO = Path('.')
BASELINE = json.loads((REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/main-schedule-baseline.json').read_text())

wps = {x['id']: x for x in BASELINE['work_packages']}
subtasks_by_task = defaultdict(list)
for x in BASELINE['work_packages']:
    if x['type'] == 'Subtask':
        subtasks_by_task[x['parent_id']].append(x)

t49_subs = subtasks_by_task[49]
print("Task 49 subtasks:")
for s in t49_subs:
    print(f"  ID {s['id']}: {s['subject']}")

follows = [r for r in BASELINE['relations'] if r['relation_type'] == 'follows']
t49_ids = {s['id'] for s in t49_subs}
print("\nInternal follows for Task 49:")
for r in follows:
    if r['from_id'] in t49_ids and r['to_id'] in t49_ids:
        print(f"  {r['from_id']} ({wps[r['from_id']]['subject']}) follows {r['to_id']} ({wps[r['to_id']]['subject']})")

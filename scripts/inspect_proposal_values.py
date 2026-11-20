import csv
from collections import Counter
from pathlib import Path

p = Path('docs/ai-multi-agent-upgrade/codex-main-completion/MAIN_SCRUM_329_NATIVE_FORK_PROPOSAL.csv')
with p.open(encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

for t in ['Epic', 'Task', 'Subtask']:
    sample = next(r for r in rows if r['Type'] == t)
    print(f"{t}:")
    print(f"  Proposed Sprint: {sample['Proposed Native Sprint']}")
    print(f"  Proposed Version: {sample['Proposed Roadmap Version']}")
    print(f"  Proposed Dates: {sample['Proposed Start Date']} -> {sample['Proposed Due Date']}")

print("\nSprint values per Type:")
for t in ['Epic', 'Task', 'Subtask']:
    counts = Counter(r['Proposed Native Sprint'] for r in rows if r['Type'] == t)
    print(f"  {t}: {dict(counts)}")

print("\nVersion values per Type:")
for t in ['Epic', 'Task', 'Subtask']:
    counts = Counter(r['Proposed Roadmap Version'] for r in rows if r['Type'] == t)
    print(f"  {t}: {dict(counts)}")

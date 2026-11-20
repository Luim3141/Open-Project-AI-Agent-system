import csv
import json
from datetime import date
from pathlib import Path

REPO = Path('.')
CSV_PATH = REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/MAIN_SCRUM_329_NATIVE_FORK_PROPOSAL.csv'
BASELINE = json.loads((REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/main-schedule-baseline.json').read_text())

rows = {int(r['ID']): r for r in csv.DictReader(CSV_PATH.open(encoding='utf-8-sig'))}
follows = [r for r in BASELINE['relations'] if r['relation_type'] == 'follows']

violations = []
for rel in follows:
    f_id = rel['from_id']  # Follower (successor)
    t_id = rel['to_id']    # Predecessor
    rf = rows[f_id]
    rt = rows[t_id]
    sf, df = date.fromisoformat(rf['Proposed Start Date']), date.fromisoformat(rf['Proposed Due Date'])
    st, dt = date.fromisoformat(rt['Proposed Start Date']), date.fromisoformat(rt['Proposed Due Date'])
    
    # Predecessor dt must be <= follower sf
    # Or in calendar days, if dt is Friday and sf is Monday, sf >= dt
    if sf < dt:
        violations.append({
            'rel_id': rel['id'],
            'from_id': f_id,
            'from_subj': rf['Subject'],
            'from_start': str(sf),
            'to_id': t_id,
            'to_subj': rt['Subject'],
            'to_due': str(dt),
            'diff': (sf - dt).days
        })

print(f"Total follows relations checked: {len(follows)}")
print(f"Violations where follower start < predecessor due: {len(violations)}")
for v in violations[:10]:
    print(f"  Rel #{v['rel_id']}: WP #{v['from_id']} ('{v['from_subj']}') starts {v['from_start']}, but predecessor WP #{v['to_id']} ('{v['to_subj']}') ends {v['to_due']} (diff {v['diff']} days)")

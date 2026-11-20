"""Generate FINAL_7_SPRINT_NATIVE_PROPOSAL_V2.csv for final delivery."""
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE_CSV = REPO / 'docs/ai-multi-agent-upgrade/antigravity-continuation/FINAL_7_SPRINT_NATIVE_PROPOSAL.csv'
TARGET_DIR = REPO / 'docs/ai-multi-agent-upgrade/run_20261021_final_delivery'
TARGET_DIR.mkdir(parents=True, exist_ok=True)
TARGET_CSV = TARGET_DIR / 'FINAL_7_SPRINT_NATIVE_PROPOSAL_V2.csv'

def main():
    with SOURCE_CSV.open(encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames)

    print(f"Loaded {len(rows)} rows from {SOURCE_CSV.name}")

    # Verify rows integrity
    assert len(rows) == 329, f"Expected 329 rows, got {len(rows)}"

    # Update statuses to reflect Owner Approval and pending qualification
    for r in rows:
        r['Apply Status'] = 'OWNER_APPROVED_7_SPRINT_SCHEDULE'
        r['Native Dry Run'] = 'PENDING_CLONE_QUALIFICATION'

    with TARGET_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    sha256 = hashlib.sha256(TARGET_CSV.read_bytes()).hexdigest()
    print(f"Generated {TARGET_CSV.name} (Size: {TARGET_CSV.stat().st_size:,} bytes, SHA-256: {sha256})")

    # Generate metadata summary
    summary = {
        'source_csv': str(SOURCE_CSV.relative_to(REPO)),
        'target_csv': str(TARGET_CSV.relative_to(REPO)),
        'sha256': sha256,
        'total_rows': len(rows),
        'epics_count': sum(1 for r in rows if r['Type'] == 'Epic'),
        'tasks_count': sum(1 for r in rows if r['Type'] == 'Task'),
        'subtasks_count': sum(1 for r in rows if r['Type'] == 'Subtask'),
        'schedule_anchor': '2026-10-05 (Monday)',
        'schedule_finish': '2027-01-08 (Friday)',
        'working_days_total': 70,
        'sprints_count': 7
    }
    (TARGET_DIR / 'proposal_v2_manifest.json').write_text(json.dumps(summary, indent=2))
    print("Proposal V2 manifest written successfully.")

if __name__ == '__main__':
    main()

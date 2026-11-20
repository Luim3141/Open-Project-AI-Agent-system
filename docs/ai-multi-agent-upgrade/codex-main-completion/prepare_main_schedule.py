"""Main-only schedule preview from Owner-selected Staging plan; no API writes."""
import csv
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).parent
SOURCE = OUT.parent / 'final-gantt-boards-ai-fixes/SCRUM_GANTT_1WEEK_PROPOSAL.csv'


def main():
    baseline = json.loads((OUT / 'main-schedule-baseline.json').read_text())
    packages = {w['id']: w for w in baseline['work_packages']}
    assert len(packages) == 329
    records = list(csv.DictReader(SOURCE.open(encoding='utf-8-sig', newline='')))
    assert len({r['ID'] for r in records}) == len(records), 'DUPLICATE_STAGING_PROPOSAL_IDS'
    proposed = {int(r['ID']): r for r in records if int(r['ID']) in packages}
    assert set(proposed) == set(packages), 'MAIN_IDS_MISSING_FROM_PROPOSAL'
    dates = {i: (date.fromisoformat(r['Start Date']), date.fromisoformat(r['Due Date'])) for i, r in proposed.items()}
    for identifier, (start, finish) in dates.items():
        assert start <= finish and start.weekday() < 5 and finish.weekday() < 5
        assert proposed[identifier]['Subject'] == packages[identifier]['subject'], 'ID_SUBJECT_MAPPING_DRIFT'
    violations = defaultdict(list)
    for relation in baseline['relations']:
        if relation['relation_type'] != 'follows': continue
        successor, predecessor = relation['from_id'], relation['to_id']
        assert successor in packages and predecessor in packages
        # Native relation.from is successor; lag0 still requires a later start day.
        if relation['lag'] not in (None, 0):
            violations[successor].append({'relation_id': relation['id'], 'predecessor': predecessor, 'reason': 'NONZERO_LAG_REQUIRES_NATIVE_DRY_RUN'})
        elif dates[successor][0] <= dates[predecessor][1]:
            violations[successor].append({'relation_id': relation['id'], 'predecessor': predecessor, 'reason': 'START_NOT_AFTER_PREDECESSOR_FINISH'})
    occupancy = defaultdict(list)
    for identifier, (start, finish) in dates.items():
        if packages[identifier]['type'] != 'Subtask': continue
        while start <= finish:
            if start.weekday() < 5: occupancy[(packages[identifier]['assigned_to_id'], start.isoformat())].append(identifier)
            start += timedelta(days=1)
    collisions = {key: ids for key, ids in occupancy.items() if len(ids) > 1}
    row_flags = defaultdict(set)
    for (_, _), ids in collisions.items():
        for identifier in ids: row_flags[identifier].add('CONCURRENT_LEAF_WORK_EFFORT_UNKNOWN')
    fields = ['ID', 'Subject', 'Type', 'Parent ID', 'Actor ID', 'Current Status ID', 'Proposed Status ID', 'Status Rationale',
              'Original Start Date', 'Original Due Date', 'Proposed Start Date', 'Proposed Due Date', 'Proposed Sprint',
              'Schedule Manually Preserved', 'Ignore Non Working Days Preserved', 'Predecessor Conflicts', 'Flags', 'Apply Status']
    with (OUT / 'MAIN_SCRUM_329_SCHEDULE_PROPOSAL.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for identifier, w in packages.items():
            p = proposed[identifier]
            flags = set(row_flags[identifier])
            if violations[identifier]: flags.add('NATIVE_DEPENDENCY_CONFLICT')
            if date.fromisoformat(p['Due Date']) < date.today(): flags.add('PAST_PLANNED_FINISH_IS_NOT_COMPLETION_EVIDENCE')
            writer.writerow(dict(zip(fields, [identifier, w['subject'], w['type'], w['parent_id'], w['assigned_to_id'], w['status_id'], w['status_id'],
                'Preserve actual status; elapsed date is not acceptance or gate evidence', w['start_date'], w['due_date'], p['Start Date'], p['Due Date'], p['Sprint'],
                w['schedule_manually'], w['ignore_non_working_days'], ';'.join(str(v['predecessor']) for v in violations[identifier]), ';'.join(sorted(flags)), 'PREVIEW_ONLY_NATIVE_DRY_RUN_PENDING'])))
    result = {'main_rows': len(packages), 'staging_rows_excluded': sorted(int(r['ID']) for r in records if int(r['ID']) not in packages),
              'start': min(x[0] for x in dates.values()).isoformat(), 'finish': max(x[1] for x in dates.values()).isoformat(),
              'follows_relations': sum(r['relation_type'] == 'follows' for r in baseline['relations']),
              'conflicting_relations': sum(map(len, violations.values())), 'affected_successors': sum(bool(v) for v in violations.values()),
              'dependency_conflicts': {str(k): v for k, v in violations.items() if v},
              'concurrent_leaf_actor_days': len(collisions), 'peak_concurrent_leaves': max(map(len, occupancy.values())),
              'capacity_status': 'UNKNOWN_EFFORT_AND_ACTUAL_AVAILABILITY; concurrency is not an hours estimate',
              'business_writes': 0, 'status_changes': 0, 'sprint_assignments': 0, 'native_form_dry_run': 'PENDING',
              'safe_to_apply_unchanged': not any(violations.values())}
    (OUT / 'schedule-constraint-analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k != 'dependency_conflicts'}, ensure_ascii=False))


if __name__ == '__main__': main()

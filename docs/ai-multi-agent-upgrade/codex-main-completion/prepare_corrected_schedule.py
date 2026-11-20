"""Dependency-compatible Main preview, preserving all Native owners/status/modes. No writes."""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from graphlib import TopologicalSorter
from pathlib import Path
OUT = Path(__file__).parent

def working_after(day):
    day += timedelta(days=1)
    while day.weekday() >= 5: day += timedelta(days=1)
    return day

def week(start):
    days = [start]
    for _ in range(4): days.append(working_after(days[-1]))
    return days

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-fork', action='store_true')
    args = parser.parse_args()
    proposal_name = 'MAIN_SCRUM_329_NATIVE_FORK_PROPOSAL.csv' if args.native_fork else 'MAIN_SCRUM_329_DEPENDENCY_CORRECTED_PROPOSAL.csv'
    analysis_name = 'schedule-native-fork-analysis.json' if args.native_fork else 'schedule-corrected-analysis.json'
    baseline = json.loads((OUT / 'main-schedule-baseline.json').read_text())
    w = {x['id']: x for x in baseline['work_packages']}
    source = {int(r['ID']): r for r in csv.DictReader((OUT / 'MAIN_SCRUM_329_SCHEDULE_PROPOSAL.csv').open(encoding='utf-8-sig'))}
    native = {r['id']: r for r in json.loads((OUT / 'main-native-schedule-fields.json').read_text())}
    existing_sprints = json.loads((OUT / 'main-native-sprint-version-preflight.json').read_text())['sprints']
    sprint_names = {'/api/v3/sprints/' + str(s['id']): s['name'] for s in existing_sprints}
    calendar = json.loads((OUT / 'main-native-calendar.json').read_text())
    assert not calendar['weekday_exceptions'], 'RECALCULATE_FOR_NATIVE_CALENDAR_EXCEPTIONS'
    anchor = date(2026, 10, 5)
    tasks = {i: set() for i, x in w.items() if x['type'] == 'Task'}
    children = {i: sorted(k for k, x in w.items() if x['parent_id'] == i) for i in tasks}
    assert len(w) == 329 and len(tasks) == 53 and all(len(c) == 5 for c in children.values())
    parent = {i: i if x['type'] == 'Task' else x['parent_id'] for i, x in w.items() if x['type'] != 'Epic'}
    follows = [r for r in baseline['relations'] if r['relation_type'] == 'follows']
    assert len(follows) == 343 and all(r['lag'] in (None, 0) for r in follows)
    for r in follows:
        successor, predecessor = parent[r['from_id']], parent[r['to_id']]
        if successor != predecessor: tasks[successor].add(predecessor)
    order = list(TopologicalSorter(tasks).static_order()); dates = {}; local_depth = {}; critical = {}
    for identifier in order:
        start = max([date.fromisoformat(source[identifier]['Proposed Start Date'])] + [working_after(dates[p][1]) for p in tasks[identifier]])
        days = week(start); dates[identifier] = (days[0], days[-1])
        local = {c: set() for c in children[identifier]}
        for r in follows:
            if r['from_id'] in local and r['to_id'] in local: local[r['from_id']].add(r['to_id'])
        if args.native_fork:
            roots = [c for c in local if not local[c]]
            branches = [c for c in local if len(local[c]) == 1 and next(iter(local[c])) in roots]
            joins = [c for c in local if local[c] == set(branches)]
            assert len(roots) == 1 and len(branches) == 2 and len(joins) == 1, 'UNEXPECTED_LOCAL_DEPENDENCY_PATTERN'
            assert w[roots[0]]['schedule_manually'] is True
            for child in TopologicalSorter(local).static_order():
                begin = max((working_after(dates[p][1]) for p in local[child]), default=start)
                # Native automatic scheduling keeps the two branches parallel; dates are durations, not effort.
                dates[child] = (begin, working_after(begin) if child in branches else begin)
            assert min(dates[c][0] for c in local) == start and max(dates[c][1] for c in local) == days[-1]
        else:
            for index, child in enumerate(TopologicalSorter(local).static_order()): dates[child] = (days[index], days[index])
        predecessor = max(tasks[identifier], key=lambda p: local_depth[p], default=None)
        local_depth[identifier] = 1 + (local_depth[predecessor] if predecessor else 0)
        critical[identifier] = (critical[predecessor] if predecessor else []) + [identifier]
    for identifier, x in w.items():
        if x['type'] == 'Epic':
            descendants = [k for k, c in w.items() if c['parent_id'] == identifier]
            dates[identifier] = (min(dates[k][0] for k in descendants), max(dates[k][1] for k in descendants))
    violations = [r['id'] for r in follows if dates[r['from_id']][0] <= dates[r['to_id']][1]]
    assert not violations, 'CORRECTED_SCHEDULE_STILL_CONFLICTS'
    assert all(dates[i][0] >= dates[x['parent_id']][0] and dates[i][1] <= dates[x['parent_id']][1] for i, x in w.items() if x['parent_id'])
    occupancy = defaultdict(list)
    for i, x in w.items():
        if x['type'] == 'Subtask':
            day = dates[i][0]
            while day <= dates[i][1]:
                occupancy[(x['assigned_to_id'], day.isoformat())].append(i)
                day = working_after(day)
    fields = ['ID', 'Subject', 'Type', 'Parent ID', 'Actor ID Preserved', 'Status ID Preserved', 'Schedule Manually Preserved',
              'Ignore Non Working Days Preserved', 'Original Start Date', 'Original Due Date', 'Staging Baseline Start', 'Staging Baseline Due',
              'Proposed Start Date', 'Proposed Due Date', 'Original Native Sprint', 'Proposed Native Sprint', 'Original Version', 'Proposed Roadmap Version', 'Effort Hours', 'Native Dry Run', 'Apply Status']
    with (OUT / proposal_name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for i, x in w.items():
            index = (dates[i][0] - anchor).days // 14 + 1
            sprint = 'PRESERVE_UNASSIGNED_ROLLUP' if x['type'] == 'Epic' else 'S' + str(index)
            version = 'PRESERVE_UNASSIGNED_ROLLUP' if x['type'] == 'Epic' else 'Sprint ' + str(index)
            writer.writerow(dict(zip(fields, [i, x['subject'], x['type'], x['parent_id'], x['assigned_to_id'], x['status_id'], x['schedule_manually'],
                x['ignore_non_working_days'], x['start_date'], x['due_date'], source[i]['Proposed Start Date'], source[i]['Proposed Due Date'],
                dates[i][0], dates[i][1], sprint_names.get(native[i]['sprint'], 'UNASSIGNED'), sprint, native[i]['version'] or 'UNASSIGNED', version,
                'UNKNOWN_NOT_DURATION', 'PENDING', 'PREVIEW_ONLY_REQUIRES_NATIVE_QUALIFICATION_AND_OWNER_REVIEW'])))
    longest = max(critical, key=lambda i: len(critical[i])); finish = max(d[1] for d in dates.values())
    summary = {'rows': len(w), 'task_duration_workdays': 5, 'leaf_duration_days': '1; parallel branches 2' if args.native_fork else 1, 'effort_hours': 'UNKNOWN',
               'start': str(anchor), 'finish': str(finish), 'proposed_two_week_sprints': (finish - anchor).days // 14 + 1,
               'all_343_dependencies_satisfied_static': not violations, 'parent_containment': True,
               'critical_path_task_ids': critical[longest], 'critical_lower_bound_workdays': len(critical[longest]) * 5,
               'original_finish': '2026-11-27', 'concurrent_leaf_actor_days': sum(len(v) > 1 for v in occupancy.values()),
               'peak_concurrent_leaf_items': max(map(len, occupancy.values())), 'capacity_qualified': False,
               'existing_native_sprint_memberships': sum(bool(v['sprint']) for v in native.values()),
               'native_sprint_membership_changes_proposed': sum(sprint_names.get(native[i]['sprint']) != 'S' + str((dates[i][0] - anchor).days // 14 + 1) for i, x in w.items() if x['type'] != 'Epic'),
               'new_native_iterations_proposed': ['S6', 'S7'], 'new_roadmap_versions_proposed': ['Sprint 5', 'Sprint 6', 'Sprint 7'],
               'calendar_exceptions': calendar['weekday_exceptions'],
               'native_dry_run': 'PENDING', 'business_writes': 0, 'approval': 'REQUIRED_FOR_DEADLINE_AND_EXTRA_SPRINTS'}
    (OUT / analysis_name).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == '__main__': main()

"""Commit the proposed dates ONLY on the owned clone to test Native scheduling cascades."""
import argparse
import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path
from native_configure_views import Configuration, Native, OUT
from jira_sync_backup import database_state, inspect

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-native-fork', action='store_true')
    args = parser.parse_args()
    result_path = OUT / ('schedule-native-fork-clone-dryrun.json' if args.resume_native_fork else 'schedule-native-clone-dryrun.json')
    assert not result_path.exists(), 'DRYRUN_ALREADY_STARTED_RECONCILE_CHECKPOINT_BEFORE_RESUME'
    clone = json.loads((OUT / 'clone.json').read_text()); private = Path(clone['private']); db = clone['names']['db']
    assert inspect(db)['Config']['Labels'].get('qldapm.qualification') == 'codex-main-20261020'
    assert not (private / 'gateway/gemini.key').exists()
    configuration = Configuration('clone'); assert configuration.base == 'http://127.0.0.1:18088'
    native = Native(configuration.base, configuration.token, 5)
    proposal_path = OUT / ('MAIN_SCRUM_329_NATIVE_FORK_PROPOSAL.csv' if args.resume_native_fork else 'MAIN_SCRUM_329_DEPENDENCY_CORRECTED_PROPOSAL.csv')
    proposal = list(csv.DictReader(proposal_path.open(encoding='utf-8-sig')))
    targets = {int(r['ID']): r for r in proposal}; assert len(targets) == 329
    snapshot = native.packages(); assert {w['id'] for w in snapshot} == set(targets)
    before = {w['id']: w for w in snapshot}
    main_before = database_state('qldapm-openproject-db-1')
    backup = private / 'schedule-dryrun-before.dump'
    if args.resume_native_fork:
        prior = json.loads((OUT / 'schedule-native-clone-dryrun.json').read_text())
        assert prior['phase'] == 'STOPPED_REVIEW_NATIVE_CHECKPOINT' and [r['id'] for r in prior['processed']] == [102, 103]
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == prior['clone_backup_sha256'], 'ORIGINAL_CLONE_BACKUP_DRIFT'
        before = {w['id']: w for w in json.loads((private / 'schedule-dryrun-before-work-packages.json').read_text())}
        assert set(before) == set(targets)
        assert all(all(w.get(k) == before[w['id']].get(k) for k in ('subject', 'scheduleManually', 'ignoreNonWorkingDays')) and
                   all(w['_links'].get(k) == before[w['id']]['_links'].get(k) for k in ('project', 'type', 'status', 'assignee', 'parent', 'sprint', 'version')) for w in snapshot), 'PARTIAL_CLONE_NONDATE_DRIFT'
    else:
        with backup.open('xb') as stream:
            operation = subprocess.run(['docker', 'exec', db, 'pg_dump', '-U', 'postgres', '-Fc', 'openproject'], stdout=stream, stderr=subprocess.PIPE, timeout=180)
        assert operation.returncode == 0, 'CLONE_SNAPSHOT_FAILED_OUTPUT_WITHHELD'
        (private / 'schedule-dryrun-before-work-packages.json').write_text(json.dumps(snapshot), encoding='utf8')
    result = {'scope': 'OWNED_CLONE_REAL_NATIVE_DATE_COMMITS_ONLY', 'actor': configuration.actor, 'project': 5,
              'main_writes': 0, 'provider_calls': 0, 'sprint_or_version_assignments': 0, 'clone_backup': str(backup),
              'clone_backup_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(), 'phase': 'PREPARED', 'processed': [],
              'proposal': proposal_path.name, 'proposal_sha256': hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
              'reconciled_prior_partial_run': args.resume_native_fork}
    def save(): result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    save(); started = time.monotonic()
    leaves = sorted((r for r in proposal if r['Type'] == 'Subtask'), key=lambda r: (r['Proposed Start Date'], int(r['ID'])))
    assert len(leaves) == 265
    try:
        for index, row in enumerate(leaves):
            assert time.monotonic() - started < 900, 'NATIVE_DRYRUN_TIME_BUDGET_STOPPED_WITH_CHECKPOINT'
            native = Native(configuration.base, configuration.token, 5)
            identifier = int(row['ID']); current = native.package(identifier)
            dates = {'startDate': row['Proposed Start Date'], 'dueDate': row['Proposed Due Date']}
            payload = {'lockVersion': current['lockVersion'], 'scheduleManually': before[identifier]['scheduleManually'],
                       'ignoreNonWorkingDays': before[identifier]['ignoreNonWorkingDays'], **dates}
            form = native.call('/api/v3/work_packages/' + str(identifier) + '/form', 'POST', payload)['_embedded']
            errors = form['validationErrors']; assert not errors, 'NATIVE_FORM_VALIDATION_ERROR:' + ','.join(errors)
            if not all(form['payload'].get(k) == value for k, value in dates.items()):
                result['normalization'] = {'id': identifier, 'requested': dates,
                                           'draft': {k: form['payload'].get(k) for k in (*dates, 'duration', 'scheduleManually')}}
                raise AssertionError('NATIVE_FORM_DATE_NORMALIZATION_REQUIRES_REVIEW')
            assert form['payload']['scheduleManually'] == before[identifier]['scheduleManually'], 'SCHEDULING_MODE_DRIFT'
            changed = any(current.get(k) != v for k, v in dates.items())
            if changed: current = native.call('/api/v3/work_packages/' + str(identifier), 'PATCH', payload)
            assert all(current.get(k) == value for k, value in dates.items()), 'NATIVE_COMMIT_DATE_NORMALIZATION_REQUIRES_REVIEW'
            result['processed'].append({'id': identifier, 'operation': 'CLONE_NATIVE_PATCH' if changed else 'ALREADY_MATCHED', **dates})
            result['phase'] = 'APPLYING_CLONE_DATES'; save()
            if (index + 1) % 10 == 0: print(json.dumps({'processed': index + 1, 'total': len(leaves), 'scope': 'CLONE_ONLY'}), flush=True)
        actual = {w['id']: w for w in Native(configuration.base, configuration.token, 5).packages()}
        mismatches = [{'id': i, 'start': actual[i].get('startDate'), 'due': actual[i].get('dueDate')}
                      for i, row in targets.items() if actual[i].get('startDate') != row['Proposed Start Date'] or actual[i].get('dueDate') != row['Proposed Due Date']]
        result['date_mismatches'] = mismatches
        assert not mismatches, 'NATIVE_PARENT_ROLLUP_OR_CASCADE_DIFFERS_FROM_PREVIEW'
        scalar_fields = ('subject', 'scheduleManually', 'ignoreNonWorkingDays')
        link_fields = ('project', 'type', 'status', 'assignee', 'parent', 'sprint', 'version')
        assert all(all(actual[i].get(k) == before[i].get(k) for k in scalar_fields) and
                   all(actual[i]['_links'].get(k) == before[i]['_links'].get(k) for k in link_fields) for i in actual), 'NATIVE_NONDATE_BUSINESS_FIELD_CHANGED'
        relations = json.loads((OUT / 'main-schedule-baseline.json').read_text())['relations']
        assert all(actual[r['from_id']]['startDate'] > actual[r['to_id']]['dueDate'] for r in relations if r['relation_type'] == 'follows')
        main_after = database_state('qldapm-openproject-db-1')
        protected = ['work_packages', 'relations', 'members', 'member_roles', 'roles', 'role_permissions', 'sprints', 'sprint_goals']
        assert all(main_before[t] == main_after[t] for t in protected), 'MAIN_CHANGED_DURING_CLONE_DRYRUN_REVIEW'
        result.update(phase='NATIVE_DATE_CASCADE_MATCHES_329_PREVIEW', passed=True, native_follows_checked=343,
                      scheduling_modes_owners_statuses_sprints_versions_preserved=True, main_protected_tables_unchanged=protected,
                      elapsed_seconds=round(time.monotonic() - started, 2), capacity_qualified=False)
    except Exception as error:
        result.update(phase='STOPPED_REVIEW_NATIVE_CHECKPOINT', passed=False, error_type=type(error).__name__)
        if isinstance(error, AssertionError): result['error'] = str(error)
        else: result['native_error_status'] = getattr(error, 'status', None)
    save(); print(json.dumps({k: v for k, v in result.items() if k != 'processed'}, ensure_ascii=False, indent=2))
    if not result['passed']: raise SystemExit(1)

if __name__ == '__main__': main()

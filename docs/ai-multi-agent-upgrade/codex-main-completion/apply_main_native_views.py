"""Apply only Owner-approved Native view/Version configuration, with preservation read-back."""
import json
import shutil
from native_configure_views import Configuration, OUT
from jira_sync_backup import database_state

def main():
    assert not (OUT / 'main-native-views-apply-result.json').exists(), 'EXISTING_APPLY_RECONCILE'
    assert json.loads((OUT / 'main-gantt-core-deployment.json').read_text())['passed']
    assert json.loads((OUT / 'native-views-clone-qualification.json').read_text())['passed']
    assert json.loads((OUT / 'gantt-clone-qualification.json').read_text())['passed']
    backup = json.loads((OUT / 'backup-receipt.json').read_text()); restore = json.loads((OUT / 'fresh-backup-restore.json').read_text())
    assert restore['passed'] and restore['backup_directory'] == backup['directory']
    config = Configuration('main')
    board8 = config.call('/api/v3/grids/8'); query29 = config.call('/api/v3/queries/29')
    before = database_state('qldapm-openproject-db-1')
    sprints = config.collection('/api/v3/projects/5/sprints')
    before_sprints = [{'id': s['id'], 'name': s['name'], 'start': s.get('startDate'), 'finish': s.get('finishDate'), 'status': s.get('_links', {}).get('status', {}).get('title')} for s in sprints]
    result = {'phase': 'PREPARED', 'backup': backup['directory'], 'business_writes': 0,
              'existing_native_sprints_preserved': before_sprints, 'native_versions_are_separate_from_sprint_iterations': True}
    (OUT / 'main-native-views-apply-result.json').write_text(json.dumps(result, indent=2))
    config.apply()
    shutil.copy2(OUT / 'main-native-views-configuration.json', OUT / 'main-native-views-created-20261021.json')
    after = database_state('qldapm-openproject-db-1')
    tables = ['work_packages', 'relations', 'members', 'member_roles', 'roles', 'role_permissions', 'two_factor_authentication_devices']
    tables += [t for t in before if t.startswith('sprint')]
    assert all(before[t] == after[t] for t in tables), 'PROTECTED_MAIN_DATA_OR_NATIVE_SPRINTS_CHANGED'
    assert board8 == config.call('/api/v3/grids/8') and query29 == config.call('/api/v3/queries/29'), 'EXISTING_BOARD_OR_QUERY_CHANGED'
    Configuration('main').apply()
    preserved = json.loads((OUT / 'main-native-views-configuration.json').read_text(encoding='utf8'))
    assert all(e['operation'] == 'PRESERVED_EXISTING' for e in preserved['events'])
    assert all(database_state('qldapm-openproject-db-1')[t] == before[t] for t in tables)
    result.update(phase='NATIVE_CONFIGURATION_AND_IDEMPOTENCY_PASS_BROWSER_PENDING', passed=True, protected_tables_unchanged=tables,
                  board8_and_query29_preserved=True, idempotency='PASS', configuration=preserved['events'])
    (OUT / 'main-native-views-apply-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()

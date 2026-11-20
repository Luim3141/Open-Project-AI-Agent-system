"""Human-local apply and independent readback for immutable one-time sync previews."""
import getpass
import json
import sys
import time
from pathlib import Path

from jira_sync import CLOUD_ID, SITE, fingerprint, load_snapshot, private_save, read_issue_pages, read_children
from jira_sync_apply import apply_preview, verify_preview
from jira_sync_operator import configuration, script_hashes, backup_proof
from jira_sync_target import Target
from jira_sync_backup import SPECS, inspect


def load_preview(path):
    path = Path(path).resolve()
    if path.is_symlink() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('PREVIEW_PATH_OR_SIZE_DENIED')
    envelope = json.loads(path.read_text(encoding='utf-8'))
    preview = envelope['preview']
    if envelope['hash'] != fingerprint(preview) or preview.get('schema') != 1 or preview['target'] not in SPECS:
        raise ValueError('PREVIEW_HASH_OR_SCOPE_INVALID')
    required = {'configuration', 'scripts', 'core_image', 'expires_at', 'snapshot_path', 'backup', 'native_relations_hash'}
    if not required.issubset(preview):
        raise ValueError('NEW_QUALIFIED_PREVIEW_REQUIRED')
    return preview, envelope['hash']


def simulation_id(current):
    rows = [row for row in current['before']['activities'] if row['name'] == 'Simulation']
    if len(rows) != 1 or rows[0]['active'] or not any(row['project_id'] == current['before']['project_id'] and row['active'] for row in rows[0]['projects']):
        raise ValueError('SCOPED_SIMULATION_ACTIVITY_REQUIRED')
    return rows[0]['id']


def verify_source(client, snapshot):
    identity = client.call('atlassianUserInfo', {})
    resources = client.call('getAccessibleAtlassianResources', {})
    if identity.get('accountId') != '712020:0d04982c-00bf-46af-b3a7-446d0f44edfb' or not any(
            row.get('cloudId') == CLOUD_ID and row.get('url') == SITE for row in resources.get('resources', [])):
        raise ValueError('OFFICIAL_SOURCE_IDENTITY_OR_SITE_CHANGED')
    fresh = read_issue_pages(client.call)
    if fingerprint(fresh) != fingerprint(snapshot['issues']):
        raise ValueError('JIRA_CHANGED_SINCE_APPROVED_SNAPSHOT')


def apply(path):
    if not sys.stdin.isatty():
        raise PermissionError('LOCAL_INTERACTIVE_OPERATOR_REQUIRED_NO_AI_APPROVAL')
    preview, _ = load_preview(path)
    from jira_sync_backup import operator_lease
    with operator_lease(preview['target']):
        return apply_locked(path)


def apply_locked(path):
    from jira_sync_mcp import OfficialMCP
    preview, hash_value = load_preview(path)
    if preview['expires_at'] < time.time() or preview['scripts'] != script_hashes():
        raise ValueError('PREVIEW_EXPIRED_OR_OPERATOR_CODE_CHANGED')
    target = Target(preview['target'])
    info = inspect(SPECS[target.name]['web'])
    if info['Image'] != preview['core_image']:
        raise ValueError('CORE_IMAGE_CHANGED_SINCE_PREVIEW')
    if backup_proof(preview['backup']['directory'], target) != preview['backup']:
        raise ValueError('BACKUP_OR_PROOF_CHANGED_SINCE_PREVIEW')
    if not sys.stdin.isatty():
        raise PermissionError('LOCAL_INTERACTIVE_OPERATOR_REQUIRED_NO_AI_APPROVAL')
    print(json.dumps({'target': target.name, 'project_id': target.project, 'actor': target.actor,
        'summary': preview['summary'], 'configuration': preview['configuration']['desired'], 'hash': hash_value,
        'unchanged': ['Jira', 'Gemini', 'credentials', 'core live image', 'hard gate', 'original v7 source']}, ensure_ascii=False))
    if input('Type this exact hash to approve this one-time configuration/data change: ').strip() != hash_value:
        raise PermissionError('LOCAL_OPERATOR_NOT_CONFIRMED')
    directory = Path(path).resolve().with_suffix('')
    if (directory / 'local-approval.json').exists():
        raise ValueError('EXISTING_APPLY_REQUIRES_READBACK_RECONCILIATION_NO_RETRY')
    private_save(directory / 'local-approval.json', {'hash': hash_value, 'operator': getpass.getuser(),
        'source': 'interactive_local_confirmation', 'at': time.time()})
    snapshot = load_snapshot(preview['snapshot_path'])
    if fingerprint(snapshot) != preview['snapshot_hash']:
        raise ValueError('APPROVED_SNAPSHOT_HASH_CHANGED')
    with OfficialMCP() as client:
        verify_source(client, snapshot)
        for query, operation in [('list Jira issue comments', 'listJiraIssueComments'), ('list Jira issue worklogs', 'listJiraIssueWorklogs')]:
            found = client.call('discover', {'query': query})
            if not any(row['name'] == operation and row.get('executeTool') == 'executeRead' for row in found.get('results', [])):
                raise ValueError('MUTABLE_SOURCE_READ_UNAVAILABLE')
        # Check every mutable child before the first write, including empty
        # lists; a source count omission is never permission to assume zero.
        for number, row in enumerate(preview['rows'], 1):
            children = snapshot['children'][row['jira_key']]
            for name, operation in [('comments', 'listJiraIssueComments'), ('worklogs', 'listJiraIssueWorklogs')]:
                if fingerprint(read_children(client.call, operation, row['jira_key'], name)) != fingerprint(children[name]):
                    raise ValueError('JIRA_CHILD_CHANGED_SINCE_PREVIEW')
            if number % 25 == 0:
                print(json.dumps({'verified_source_children': number, 'total': len(preview['rows'])}), flush=True)
        verify_source(client, snapshot)
        from jira_sync import read_sprint_membership
        found = client.call('discover', {'query': 'list Jira sprint issues'})
        if not any(row['name'] == 'getJiraBoardSprintData' and row.get('executeTool') == 'executeRead' for row in found.get('results', [])):
            raise ValueError('SPRINT_MEMBERSHIP_READ_UNAVAILABLE')
        if read_sprint_membership(client.call, snapshot['sprints']) != snapshot['sprint_memberships']:
            raise ValueError('JIRA_SPRINT_CHANGED_SINCE_PREVIEW')
        if time.time() >= preview['expires_at'] or preview['scripts'] != script_hashes():
            raise ValueError('PREVIEW_EXPIRED_OR_OPERATOR_CODE_CHANGED')
        if fingerprint(target.collection('/api/v3/relations')) != preview['native_relations_hash']:
            raise ValueError('NATIVE_RELATIONS_CHANGED_SINCE_PREVIEW')
        current = configuration(target)
        if current['hash'] != preview['configuration']['hash']:
            raise ValueError('CONFIGURATION_CHANGED_SINCE_PREVIEW')
        target.confirmed_config_hash = current['hash']
        private_save(directory / 'configuration-pending.json', {'hash': current['hash'], 'state': 'pending', 'approval_hash': hash_value})
        changed = configuration(target, current['hash'])
        private_save(directory / 'configuration-applied.json', {'state': 'applied', 'before': current, 'after': changed, 'approval_hash': hash_value})
        results = apply_preview(preview, target, directory / 'receipts', simulation_id(changed),
            source_check=lambda: verify_source(client, snapshot),
            progress=lambda n, total: print(json.dumps({'target': target.name, 'processed': n, 'total': total}), flush=True))
        verify_source(client, snapshot)
    report = verify_preview(preview, target, simulation_id(configuration(target)))
    report['approval_hash'] = hash_value
    report['receipts'] = str(directory / 'receipts')
    private_save(directory / 'verification.json', report)
    print(json.dumps({'verification': str(directory / 'verification.json'), 'summary': report['summary'],
                      'processed_rows': len(results), 'not_status_parity': True}))


def verify(path):
    preview, hash_value = load_preview(path)
    target = Target(preview['target'])
    report = verify_preview(preview, target, simulation_id(configuration(target)))
    report['preview_hash'] = hash_value
    destination = Path(path).resolve().with_name('readback-' + __import__('uuid').uuid4().hex + '.json')
    private_save(destination, report)
    print(json.dumps({'verification': str(destination), 'summary': report['summary'], 'read_only_native': True}))

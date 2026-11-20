"""Owner-only settings migration: publish fixed error workflow, preserve existing report graphs."""
import argparse
import json
import os
from pathlib import Path
import uuid

from n8n_owner import check_primary_backup, provision
from n8n_status_workflow import (LocalWorkflow, install, matches, SOURCE, DAILY_SOURCE, ERROR_SOURCE,
                                 LEGACY_SOURCE, LEGACY_DAILY_SOURCE, ERROR_WORKFLOW_ID)


class ErrorWorkflowOwner(LocalWorkflow):
    def __init__(self, base='http://localhost:5678'):
        super().__init__(base)
        self.push_ref = str(uuid.uuid4())

    def publish_error(self):
        workflow = self.workflow()
        if workflow.get('activeVersionId') != workflow['versionId']:
            body = {'versionId': workflow['versionId'], 'expectedChecksum': workflow['checksum']}
            self._request('/rest/workflows/' + self.workflow_id + '/activate', body)
        actual = self.workflow()
        if actual.get('activeVersionId') != actual['versionId']:
            raise ValueError('ERROR_WORKFLOW_NOT_PUBLISHED')
        return actual['activeVersionId']

    def attach(self, before, after):
        actual = self.workflow()
        if matches(actual, after) and actual['settings'] == after['settings']:
            return False
        if not matches(actual, before) or actual.get('settings') != before['settings']:
            raise PermissionError('OWNER_WORKFLOW_CHANGED; preserve edits, no overwrite')
        path = '/rest/workflows/' + self.workflow_id
        if self._request(path + '/collaboration/write-lock', allow_null=True) is not None:
            raise PermissionError('OWNER_EDITOR_LOCKED; no mutation attempted')
        # Community forces save; only merge this one setting, never submit the stored graph.
        self._request(path, {'settings': {'errorWorkflow': ERROR_WORKFLOW_ID}, 'versionId': actual['versionId'],
                             'expectedChecksum': actual['checksum']}, method='PATCH')
        result = self.workflow()
        if (not matches(result, after) or result['settings'] != after['settings']
                or result['active'] != actual['active']):
            raise RuntimeError('ERROR_BINDING_READBACK_CHANGED; reconcile, no automatic retry')
        return True


def enroll(owner_root, base='http://localhost:5678'):
    error = ErrorWorkflowOwner(base)
    error.workflow_id = ERROR_WORKFLOW_ID
    created = install(owner_root, error)
    published = error.publish_error()
    changes = []
    for previous, current in ((LEGACY_SOURCE, SOURCE), (LEGACY_DAILY_SOURCE, DAILY_SOURCE)):
        before, after = (json.loads(path.read_text(encoding='utf-8')) for path in (previous, current))
        client = ErrorWorkflowOwner(base)
        client.workflow_id = after['id']
        provision(owner_root, client)
        changes.append({'workflow_id': client.workflow_id, 'binding_added_now': client.attach(before, after)})
    return {'passed': True, 'error_workflow_created_now': created, 'published_version_id': published,
            'bindings': changes, 'nodes_connections_credentials_submitted': False, 'native_writes': 0,
            'model_calls': 0, 'error_messages_forwarded': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, type=Path)
    args = parser.parse_args()
    try:
        check_primary_backup(args.backup)
        root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/n8n-owner'
        print(json.dumps(enroll(root)))
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'no_overwrite_or_automatic_retry': True}))
        raise SystemExit(1)

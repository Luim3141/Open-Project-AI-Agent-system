"""Fixed-five daily native brief: one 09:00 schedule and one current-day catch-up after startup."""
import argparse
import json
import os
from pathlib import Path

from n8n_owner import check_primary_backup
from n8n_status_workflow import DAILY_WORKFLOW_ID, LocalWorkflow, install_and_run


class LocalDailyWorkflow(LocalWorkflow):
    workflow_id = DAILY_WORKFLOW_ID

    def publish(self):
        workflow = self.workflow()
        if workflow.get('active') is True:
            return False
        body = {'versionId': workflow['versionId']}
        if isinstance(workflow.get('checksum'), str):
            body['expectedChecksum'] = workflow['checksum']
        self._request('/rest/workflows/' + self.workflow_id + '/activate', body)
        if self.workflow().get('active') is not True:
            raise ValueError('DAILY_WORKFLOW_PUBLICATION_NOT_VERIFIED')
        return True


def enroll(owner_root, client, publish=False):
    result = install_and_run(owner_root, client)
    targets = result.get('targets', 0)
    ready = result.get('ready', 0)
    if not (1 <= targets <= 20) or ready != targets or result.get('kind') != 'daily_brief':
        raise ValueError('ALL_READY_NATIVE_BRIEFS_REQUIRED; preserve native permissions, inspect owner history')
    if publish:
        result['published_now'] = client.publish()
        result['schedule'] = '09:00 Asia/Bangkok and current-day startup catch-up; one receipt/day'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    try:
        check_primary_backup(args.backup)
        root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/n8n-owner'
        print(json.dumps(enroll(root, LocalDailyWorkflow(), args.publish)))
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'no_workflow_overwrite_or_automatic_retry': True}))
        raise SystemExit(1)

"""A cloned n8n's real daily workflow, publication and accelerated schedule fixture."""
import copy
import json
import time
import uuid

from n8n_status_workflow import DAILY_SOURCE
from n8n_daily_workflow import LocalDailyWorkflow, enroll
from n8n_machine import command
from n8n_owner import provision

FIXTURE_ID = 'p04DailyScheduleFixture'


class ScheduledFixture(LocalDailyWorkflow):
    workflow_id = FIXTURE_ID

    def last_success(self):
        try:
            return self._request('/rest/workflows/' + self.workflow_id + '/executions/last-successful')
        except ValueError as error:
            if str(error) == 'N8N_RESPONSE_INVALID':  # No successful execution yet returns data:null.
                return {}
            raise


class DailyHistory(ScheduledFixture):
    workflow_id = 'qldapmDailyBrief'


def decode_data(execution):
    data = execution['data']
    if isinstance(data, dict):
        return data
    return json.loads(command('node', '-e',
        "const r=require('module').createRequire('/usr/local/lib/node_modules/n8n/package.json');process.stdout.write(JSON.stringify(r('flatted').parse(require('fs').readFileSync(0,'utf8'))))",
        payload=data.encode()))


def exercise(owner_root, base, restart_check=False):
    client = LocalDailyWorkflow(base)
    startup = False
    if restart_check:
        provision(owner_root, client)
        history = DailyHistory(base)
        history.cookie = client.cookie
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            latest = history.last_success()
            if latest.get('id') and latest.get('mode') == 'trigger':
                run_data = decode_data(latest)['resultData']['runData']
                if 'After startup' in run_data:
                    startup = run_data['After startup'][-1]['data']['main'][0][0]['json'].get('event') == 'Instance started'
                    if startup:
                        break
            time.sleep(1)
        assert startup, 'ACTUAL_STARTUP_CATCHUP_NOT_OBSERVED'
    manual = enroll(owner_root, client, publish=True)
    # Test only: same installed schedule node every five seconds; product keeps exact 09:00 rule.
    if not restart_check:
        document = copy.deepcopy(json.loads(DAILY_SOURCE.read_text(encoding='utf-8')))
        document.update(id=FIXTURE_ID, name='P04 private accelerated schedule fixture', versionId=str(uuid.uuid4()))
        next(node for node in document['nodes'] if node['name'] == 'Daily 09:00')['parameters']['rule']['interval'][0]['expression'] = '*/5 * * * * *'
        document['nodes'] = [node for node in document['nodes'] if node['name'] != 'After startup']
        document['connections'].pop('After startup')
        path = '/tmp/p04-daily-schedule-' + str(uuid.uuid4()) + '.json'
        command('node', '-e', "require('fs').writeFileSync(process.argv[1],require('fs').readFileSync(0),{flag:'wx',mode:384})", path,
                payload=json.dumps([document]).encode())
        command('n8n', 'import:workflow', '--input=' + path)
        command('node', '-e', "require('fs').unlinkSync(process.argv[1])", path)
    fixture = ScheduledFixture(base)
    fixture.cookie = client.cookie
    fixture.publish()
    deadline = time.monotonic() + 30
    execution = None
    while time.monotonic() < deadline:
        latest = fixture.last_success()
        if latest.get('id'):
            execution = fixture.execution(latest['id'])
            if execution.get('status') == 'success' and execution.get('mode') == 'trigger':
                break
        time.sleep(1)
    if not execution or execution.get('status') != 'success' or execution.get('mode') != 'trigger':
        raise AssertionError('ACTUAL_SCHEDULE_FIXTURE_NOT_EXECUTED')
    output = json.loads(command('node', '-e',
        "const r=require('module').createRequire('/usr/local/lib/node_modules/n8n/package.json');const d=r('flatted').parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(d.resultData.runData['Gateway status'].at(-1).data.main[0][0].json))",
        payload=execution['data'].encode()))
    assert output['result']['run_id'] == manual['run_id'] and output['result']['ready'] == 5
    return {'passed': True, 'manual': manual, 'actual_scheduled_execution_id': execution['id'],
            'scheduled_mode': execution['mode'], 'same_daily_receipt': True, 'product_schedule': '09:00 Asia/Bangkok',
            'test_only_accelerated_schedule_seconds': 5, 'after_restore': restart_check,
            'startup_catchup_observed': startup}

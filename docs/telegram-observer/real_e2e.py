"""Owner-approved /health regression scenario over the existing Main Gateway/worker."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

OUT = Path(__file__).resolve().parent
AI = OUT.parents[1] / 'openproject/ai'
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
FEEDBACK = '''Owner-approved Telegram/Observer E2E: bổ sung regression tests cho endpoint GET /health của mini-task-manager.
Chỉ bổ sung tests và ghi chú test cần thiết, không đổi hành vi ứng dụng hoặc thêm endpoint.
Kiểm tra status HTTP hiện hành, schema/body thực tế và việc gọi lặp không làm thay đổi dữ liệu Task.
BA phải đọc nguồn và mô tả đúng contract hiện có trước khi giao Dev. Dev viết tests trên code thật;
Reviewer độc lập review diff; QA chạy bộ tests liên quan và báo exit code/bằng chứng.
Không replay unit cũ, không merge hoặc deploy ứng dụng. Tạo đúng một unit mới cho phạm vi này.
Giữ One Task—Multiple Agent Runs, dùng runner/provider/budget/RBAC/approval hiện có.
Runtime thành công chỉ READY FOR RELEASE; Owner sẽ nghiệm thu riêng sau khi xem bằng chứng.'''


def command(action, args, key=None):
    token = (PRIVATE / 'telegram-ai/secrets/gateway.token').read_text().strip()
    body = {'action': action, 'arguments': args, 'project_id': 6}
    if key:
        body['idempotency_key'] = key
    request = urllib.request.Request('http://127.0.0.1:18089/api/v1/commands',
        data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            data = json.load(error)
            safe = {k: data[k] for k in ('code', 'error', 'message') if k in data}
        except ValueError:
            safe = {}
        raise RuntimeError('GATEWAY_HTTP_' + str(error.code) + ':' + json.dumps(safe)) from None


def source():
    process = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python',
        '-m', 'gateway.engineering_operator'], input=json.dumps({'op': 'source', 'args': {}}),
        text=True, capture_output=True, timeout=120)
    assert process.returncode == 0, 'SOURCE_READ_FAILED'
    value = json.loads(process.stdout)
    assert value['ok']
    return value['result']


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['plan', 'status', 'observe', 'resume-plan', 'run'])
    args = parser.parse_args()
    if args.action == 'plan':
        target = OUT / 'real-e2e-plan-admission.json'
        if target.exists():
            raise RuntimeError('EXISTING_PLAN_RECEIPT_PRESERVED')
        item = source()
        result = command('engineering_plan', {'native_id': 379, 'lock_version': item['lock_version'],
            'feedback': FEEDBACK}, 'telegram-health-regression-plan-20261105')
        save(target.name, result)
        print(json.dumps(result, ensure_ascii=False))
    elif args.action == 'status':
        data = command('engineering_status', {})
        state = data['result']
        summary = {'mode': state.get('mode'), 'control': state.get('control'),
            'worker': state.get('delivery_worker'),
            'latest_runs': [{**{k: r.get(k) for k in ('id', 'unit', 'queue_state', 'native_id')},
                'result': {k: (r.get('result') or {}).get(k) for k in ('status', 'stage', 'error', 'head_sha', 'pr_url')}}
                            for r in state.get('runs', [])[:2]],
            'backlog': [{k: u.get(k) for k in ('unit', 'native_id', 'state', 'eligible', 'blocked_reason')}
                        for u in state.get('backlog', []) if u.get('state') == 'PLANNED']}
        save('real-e2e-status.json', summary)
        print(json.dumps(summary, ensure_ascii=False))
    elif args.action == 'observe':
        value = command('observer_task_progress', {'task_id': 397})['result']
        summary = {k: value.get(k) for k in ('task_id', 'project_id', 'version', 'workflow_status',
            'business_status', 'acceptance_status', 'acceptance', 'current_agent', 'current_stage',
            'freshness', 'source_conflicts', 'revision', 'notification_events', 'runs')}
        summary['stages'] = [{k: s.get(k) for k in ('agent_role', 'status', 'started_at', 'updated_at',
            'completed_at', 'latest_run_id', 'attempts', 'blocker')} for s in value.get('stages', [])]
        summary['artifacts'] = [{k: a.get(k) for k in ('title', 'verification_status', 'uri', 'source_record_id')}
            for a in value.get('artifacts', [])]
        summary['events'] = value.get('events', [])
        save('real-e2e-observer-' + str(int(time.time())) + '.json', summary)
        print(json.dumps({k: summary[k] for k in ('task_id', 'workflow_status', 'acceptance_status', 'current_agent', 'stages')}, ensure_ascii=False))
    elif args.action == 'resume-plan':
        proof = json.loads((OUT / 'planning-relation-readback.json').read_text())
        assert proof['status'] == 'VERIFIED_EXISTING_RELATION' and proof['native_writes'] == 0
        state = command('engineering_status', {})['result']
        run = next(r for r in state['runs'] if r['id'] == proof['run_id'])
        checkpoint = run['checkpoint']
        assert checkpoint.get('version') and run['queue_state'] == 'finished'
        result = command('engineering_resume', {'run_id': run['id'], 'checkpoint_version': checkpoint['version']},
            'telegram-health-regression-resume-plan-20261106')
        save('real-e2e-plan-resume.json', result)
        print(json.dumps(result, ensure_ascii=False))
    else:
        target = OUT / 'real-e2e-dev-admission.json'
        if target.exists():
            raise RuntimeError('EXISTING_DEVELOPMENT_RECEIPT_PRESERVED')
        plan_id = json.loads((OUT / 'real-e2e-plan-admission.json').read_text())['result']['id']
        state = command('engineering_status', {})['result']
        plan = next(p for p in state['plans'] if p.get('id') == plan_id or p.get('run_id') == plan_id)
        assert plan['state'] == 'PUBLISHED', 'BA_PM_HANDOFF_REQUIRED'
        feedback_units = [(key, value) for key, value in plan['native_units'].items() if value['state'] != 'DELIVERED']
        assert len(feedback_units) == 1, 'EXACTLY_ONE_NEW_UNIT_REQUIRED'
        unit, native = feedback_units[0]
        assert FEEDBACK in plan.get('feedback', ''), 'EXACT_APPROVED_SCOPE_REQUIRED'
        task = next(t for t in state['tasks'] if t['id'] == native['id'])
        result = command('engineering_run_once', {'native_id': task['id'],
            'lock_version': task['lock_version'], 'unit': unit}, 'telegram-health-regression-dev-20261105')
        save(target.name, result)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

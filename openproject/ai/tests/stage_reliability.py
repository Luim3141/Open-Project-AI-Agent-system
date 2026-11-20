"""Native and real-provider acceptance; exact owned fixtures, durable checkpoint, no source writes."""
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
from gateway.native import Native
from gateway.store import canonical

runtime = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
credentials = json.loads((runtime / 'stage/test-credentials.json').read_text())
bootstrap = json.loads((runtime / 'stage/bootstrap.json').read_text())
key = (runtime / 'stage-ai/ui.key').read_bytes()
report_path = Path('artifacts/assistant-reliability-stage.json')
report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {
    'source': 'AI-RELIABILITY-' + uuid.uuid4().hex, 'created': [], 'checks': [], 'runs': []}
client = httpx.Client(base_url='http://127.0.0.1:18092', trust_env=False, timeout=70)


def save():
    report_path.write_text(canonical(report), encoding='utf-8')


def native(role='PM'):
    return Native('http://127.0.0.1:18091', credentials[role]['token'], bootstrap['project_id'])


def command(role, action, arguments=None, request=None, auto=False, operation='command', status=200):
    data = {'action': action, 'arguments': arguments or {}, 'idempotency_key': request, 'auto_execute': auto} if operation == 'command' else arguments
    body = canonical({'actor': credentials[role]['id'], 'project': bootstrap['project_id'], 'audience': 'qldapm-ai-ui',
        'at': time.time(), 'nonce': uuid.uuid4().hex, 'operation': operation, 'command': data}).encode()
    response = client.post('/internal/ui', content=body, headers={'Content-Type': 'application/json',
        'X-Qldapm-Signature': hmac.new(key, body, hashlib.sha256).hexdigest()})
    assert response.status_code == status, f'{action}: HTTP {response.status_code}: {response.json().get("error")}'
    return response.json().get('result')


def check(label):
    report['checks'].append(label)
    save()
    print(label, flush=True)


def source_snapshot():
    rows = native().packages()
    return [{**{k: r.get(k) for k in ('id', 'subject', 'description', 'startDate', 'dueDate', 'percentageDone', 'lockVersion', 'updatedAt')},
             'links': {k: r['_links'].get(k) for k in ('type', 'status', 'parent', 'assignee', 'priority')},
             'fields': {k: v for k, v in r.items() if k.startswith('customField')}}
            for r in sorted(rows, key=lambda r: r['id']) if r['id'] not in report['created']]


def create(role, label, type_name, parent=None):
    args = {'source_id': report['source'] + '-' + label, 'subject': report['source'] + ' ' + label,
            'type_id': bootstrap['types'][type_name], 'assignee_role': role}
    if parent:
        args['parent_id'] = parent
    result = command(role, 'create_work_package', args, report['source'] + '-' + label, True)
    report['created'].append(result['id'])
    save()
    assert command(role, 'create_work_package', args, report['source'] + '-' + label, True)['id'] == result['id']
    if parent:
        assert native(role).package(result['id'])['_links']['parent']['href'].endswith('/' + str(parent))
    return result['id']


def native_matrix():
    assert not report['created'], 'Do not replay a partially executed fixture matrix'
    report['baseline'] = source_snapshot()
    assert len(report['baseline']) == 329
    save()
    report['epic'] = create('PM', 'Epic', 'Epic')
    report['task'] = create('PM', 'Task', 'Task', report['epic'])
    report['children'] = {}
    priority = command('PM', 'get_project_options')['priorities'][0]['id']
    for role in credentials:
        identifier = create(role, role, 'Subtask', report['task'])
        report['children'][role] = identifier
        current = native(role).package(identifier)
        args = {'id': identifier, 'lock_version': current['lockVersion'], 'changes': {
            'subject': report['source'] + ' Updated ' + role, 'description': 'Fixture nghiệp vụ: chỉ thu hồi quyền khi có xác nhận',
            'due_date': '2026-10-20', 'priority_id': priority, 'assignee_role': role}}
        result = command(role, 'update_work_package', args, report['source'] + '-update-' + role, True)
        actual = native(role).package(identifier)
        assert actual['subject'] == args['changes']['subject'] and actual['description']['raw'] == args['changes']['description']
        assert actual['dueDate'] == '2026-10-20' and actual['_links']['assignee']['href'].endswith('/' + str(credentials[role]['id']))
        command(role, 'update_work_package', args, report['source'] + '-stale-' + role, True, status=409)
        text = 'Kiểm tra staging — ' + role
        comment_args = {'id': identifier, 'lock_version': result['lockVersion'], 'text': text}
        receipt = command(role, 'comment', comment_args, report['source'] + '-comment-' + role, True)
        assert command(role, 'comment', comment_args, report['source'] + '-comment-' + role, True)['id'] == receipt['id']
        assert sum(a.get('comment', {}).get('raw', '').startswith(text) for a in native(role).collection(f'/api/v3/work_packages/{identifier}/activities')) == 1
        current = native(role).package(identifier)
        command(role, 'transition', {'id': identifier, 'lock_version': current['lockVersion'], 'status_id': 7}, report['source'] + '-transition-' + role, True)
        assert native(role).package(identifier)['_links']['status']['href'] == '/api/v3/statuses/7'
        current = native(role).package(identifier)
        command(role, 'update_work_package', {'id': identifier, 'lock_version': current['lockVersion'], 'changes': {'due_date': None}}, report['source'] + '-clear-' + role, True)
        assert native(role).package(identifier)['dueDate'] is None
        check(role + ': create parent + update + comment + transition + clear date + replay/stale')
    check('Epic > Task > Subtask native tree; all five roles')
    assert source_snapshot() == report['baseline']


def google_run(role, label, prompt, allow=True):
    args = {'prompt': prompt, 'allow_routine_writes': allow, 'write_scope_ids': []}
    started = command(role, 'start_ai_run', args, report['source'] + '-' + label)
    assert command(role, 'start_ai_run', args, report['source'] + '-' + label)['id'] == started['id']
    report['runs'].append({'role': role, 'label': label, 'id': started['id'], 'prompt': prompt})
    save()
    deadline, last_wait = time.monotonic() + 650, None
    while True:
        result = command(role, 'get_ai_run', {'id': started['id']})
        message = (result.get('result') or {}).get('message')
        if message and message != last_wait:
            print(label + ': ' + message, flush=True)
            last_wait = message
            report['quota_wait_observed'] = True
        if result['state'] != 'running':
            break
        assert time.monotonic() < deadline, 'RUN_TIMEOUT'
        time.sleep(2)
    report['runs'][-1]['result'] = result
    for tool in (result.get('result') or {}).get('tools', []):
        item = tool.get('result', {}).get('result', {})
        if tool['action'] == 'create_work_package' and item.get('native_confirmed') and item['id'] not in report['created']:
            report['created'].append(item['id'])
    save()
    print(canonical({'label': label, 'state': result['state'], 'status': (result.get('result') or {}).get('status'), 'error': (result.get('result') or {}).get('error')}), flush=True)
    assert result['state'] == 'done', 'Provider interrupted; retained receipts, no automatic replay'
    return result['result']


def google_matrix():
    for role in credentials:
        identifier = report['children'][role]
        prompt = (f'Sửa tên và mô tả, thêm bình luận, tạo Subtask và chuyển trạng thái. Công việc {identifier}: '
            f'đổi tên chính xác thành "{report["source"]} Gemini {role}", mô tả chính xác "Đối soát nghiệp vụ qua Gemini thật", '
            f'giao cho {role}, đặt hạn hoàn thành 2026-10-22. Thêm bình luận chính xác "Đã kiểm tra bằng Gemini thật — {role}". '
            f'Tạo Subtask dưới công việc {report["task"]}, tên "{report["source"]} Gemini child {role}", giao cho {role}; chuyển Subtask vừa tạo sang IN PROGRESS. '
            'Đọc kết quả và giải thích ngắn gọn bằng tiếng Việt các việc đã làm.')
        result = google_run(role, 'google-' + role, prompt)
        for action in ('update_work_package', 'comment', 'create_work_package', 'transition'):
            assert any(o['action'] == action and o['state'] == 'succeeded' for o in result['outcomes']), action
        actual = native(role).package(identifier)
        assert actual['subject'] == report['source'] + ' Gemini ' + role and actual['description']['raw'] == 'Đối soát nghiệp vụ qua Gemini thật'
        assert actual['dueDate'] == '2026-10-22'
        child_id = next(o['work_package_id'] for o in result['outcomes'] if o['action'] == 'create_work_package' and o['state'] == 'succeeded')
        child = native(role).package(child_id)
        assert child['_links']['parent']['href'] == '/api/v3/work_packages/' + str(report['task'])
        assert child['_links']['status']['href'] == '/api/v3/statuses/7'
        comments = native(role).collection(f'/api/v3/work_packages/{identifier}/activities')
        assert sum(a.get('comment', {}).get('raw', '').startswith('Đã kiểm tra bằng Gemini thật — ' + role) for a in comments) == 1
        check(role + ': real Gemini typed create/update/comment/transition, exact native readback')
    assert source_snapshot() == report['baseline']


def proposals_and_bulk():
    args = {'source_id': report['source'] + '-PM-review', 'subject': report['source'] + ' PM review',
        'type_id': bootstrap['types']['Subtask'], 'parent_id': report['task'], 'assignee_role': 'PM'}
    review = command('BE', 'create_work_package', args, report['source'] + '-PM-review', True)
    report['created'].append(review['id'])
    save()
    actual = native().package(review['id'])
    assert actual['_links']['assignee']['href'].endswith('/' + str(credentials['PM']['id']))
    transition = {'id': review['id'], 'lock_version': actual['lockVersion'], 'status_id': 7}
    command('QA', 'transition', transition, report['source'] + '-wrong-assignee', True, status=422)
    command('PM', 'transition', transition, report['source'] + '-right-assignee', True)
    check('Original BE creates PM review with parent; QA cannot bypass assignee workflow, PM can transition')
    identifier = report['children']['BE']
    previous = native().package(identifier)['subject']
    title = report['source'] + ' Preview approved'
    result = google_run('PM', 'preview', f'Sửa tên công việc {identifier} thành "{title}". Giải thích thay đổi trước khi duyệt.', False)
    proposal = next(o for o in result['outcomes'] if o['state'] == 'proposed')
    assert native().package(identifier)['subject'] == previous
    pending = command('PM', 'get_proposal', {'id': proposal['proposal_id']})
    assert pending['command']['preview'], 'Human preview required'
    command('PM', None, {'id': pending['id'], 'hash': pending['hash']}, operation='confirm')
    assert native().package(identifier)['subject'] == title
    command('PM', None, {'id': pending['id'], 'hash': pending['hash']}, operation='confirm', status=409)
    current = native().package(identifier)
    rejected = command('PM', 'update_work_package', {'id': identifier, 'lock_version': current['lockVersion'],
        'changes': {'subject': 'Must never be written'}}, report['source'] + '-reject-preview')
    command('PM', 'reject_proposal', {'id': rejected['id'], 'hash': rejected['hash']}, report['source'] + '-reject')
    assert native().package(identifier)['subject'] == title
    command('PM', None, {'id': rejected['id'], 'hash': rejected['hash']}, operation='confirm', status=409)
    check('Real Gemini preview/approve once, reject no write, consumed proposal denied')
    texts = [f'Kiểm tra nhiều thao tác {report["source"]} — {i}' for i in range(1, 9)]
    result = google_run('PM', 'bulk-eight', f'Thêm tám bình luận riêng biệt vào công việc {identifier}. '
        'Mỗi bình luận phải là một thao tác riêng, giữ nguyên các nội dung sau, không gộp: ' + json.dumps(texts, ensure_ascii=False))
    succeeded = [o for o in result['outcomes'] if o['action'] == 'comment' and o['state'] == 'succeeded']
    assert len(succeeded) == 8
    actual = native().collection(f'/api/v3/work_packages/{identifier}/activities')
    for text in texts:
        assert sum(a.get('comment', {}).get('raw', '').split('\n\n<!--')[0] == text for a in actual) == 1
    check('Real Gemini eight writes in one request; exact eight native comments, no duplicates')
    result = google_run('PM', 'read-tools', 'Đọc danh tính tài khoản hiện tại, tìm danh sách công việc có chữ AI-RELIABILITY và phân tích số lượng/overdue của nhóm đó. Dùng cả identity, list_work_packages và analyze; không sửa gì.', False)
    assert {'identity', 'list_work_packages', 'analyze'} <= {t['action'] for t in result['tools']}
    check('Real Gemini identity + concise list + analyze; nine business tools covered')
    assert source_snapshot() == report['baseline']


def cleanup():
    # Exact created IDs plus exact fixture source or confirmed run receipt; never source work packages.
    ruby = f'''require "json"
raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
field=WorkPackageCustomField.find_by!(name:"Source ID")
User.execute_as(User.find_by!(login:"stage-owner")) do
 {list(reversed(report['created']))}.each do |id|
  item=WorkPackage.find(id)
  value=item.custom_value_for(field).value.to_s
  owned=value.start_with?("{report['source']}") || {json.dumps([r['id'] for r in report['runs']])}.any? {{ |run| value.start_with?("ai-#{{run}}-") }}
  raise "OTHER_FIXTURE" unless owned && item.project_id==3 && !item.children.exists?
  Qldapm::MutationReceipt.where(work_package_id:id).delete_all
  Thread.current[:qldapm_approved_delete]=id
  item.destroy!
 ensure
  Thread.current[:qldapm_approved_delete]=nil
 end
end
puts JSON.generate({{roles: Role.where(id:12..16).map {{ |r| {{id:r.id,permissions:r.permissions}} }},
 workflow: Workflow.where(role_id:12..16).group(:role_id,:type_variant_id,:old_status_id,:new_status_id,:author,:assignee).count.map {{ |k,v| {{key:k,count:v}} }},
 source_count: WorkPackage.where(project_id:3).count}})
'''
    result = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-stage-staging-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
        input=ruby, text=True, capture_output=True, timeout=180)
    assert result.returncode == 0, 'Cleanup failed; inspect exact fixture IDs'
    after = next(json.loads(line) for line in result.stdout.splitlines() if line.startswith('{'))
    before = json.loads(Path('artifacts/assistant-workflow-before.json').read_text(encoding='utf-8'))
    assert sorted(after['workflow'], key=canonical) == sorted(before['workflow'], key=canonical)
    for role in after['roles']:
        expected = next(r['permissions'] for r in before['roles'] if r['id'] == role['id'])
        if role['id'] in range(13, 17):
            expected = list(set(expected + ['manage_subtasks']))
        assert sorted(role['permissions']) == sorted(expected)
    report['native_configuration_after'] = after
    assert source_snapshot() == report['baseline'], 'Source records changed'
    report['cleaned'] = True
    check('All owned fixtures removed; all329 source fields/versions preserved')


if __name__ == '__main__':
    {'native': native_matrix, 'google': google_matrix, 'extra': proposals_and_bulk, 'cleanup': cleanup}[sys.argv[1]]()

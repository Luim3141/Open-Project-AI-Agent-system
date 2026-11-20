import subprocess
import json
import uuid
import time
import urllib.request

print("=================================================================")
print("RUNNING PHASE 2.7 DEFECT REMEDIATION & VERIFICATION SUITE")
print("=================================================================\n")

results = {}

# -------------------------------------------------------------
# 1. DEFECT-04: Test Owner Full Control over PM20 Runs & Isolation
# -------------------------------------------------------------
print("--- 1. Testing DEFECT-04 (Owner 18 Authority & Multi-Agent Scope) ---")

fixture_id = str(uuid.uuid4())
task_id = str(uuid.uuid4())
trace_id = str(uuid.uuid4())
conv_id = str(uuid.uuid4())

payload_str = json.dumps({
    "project_id": 6,
    "unit": "test-owner-auth-fixture",
    "engine": "openclaw",
    "native_id": 379,
    "source_version": 1,
    "spec_sha256": "0" * 64
})

insert_py = """
import sqlite3, json, sys, time

fixture_id, task_id, trace_id, conv_id, payload_str = sys.argv[1:6]
now = time.time()

with sqlite3.connect('/state/gateway.sqlite') as d:
    d.execute("INSERT INTO ai_queue (id, actor, payload, state, created) VALUES (?, 20, ?, 'queued', ?)", (fixture_id, payload_str, now))
    task_doc = json.dumps({
        'schema_version': 1,
        'task_id': task_id,
        'actor_id': 20,
        'project_id': 6,
        'agent': 'dev',
        'instruction': 'test instruction',
        'references': [],
        'run_class': 'development',
        'conversation_id': conv_id,
        'created_at': now,
        'expires_at': now + 3600
    })
    d.execute("INSERT INTO agent_tasks (id, actor, project, conversation, document, expires) VALUES (?, 20, 6, ?, ?, ?)", (task_id, conv_id, task_doc, now + 3600))
    run_doc = json.dumps({
        'schema_version': 1,
        'run_id': fixture_id,
        'task_id': task_id,
        'actor_id': 20,
        'project_id': 6,
        'trace_id': trace_id,
        'state': 'QUEUED',
        'created_at': now,
        'updated_at': now,
        'result': None
    })
    d.execute("INSERT INTO agent_runs (id, task_id, actor, project, document) VALUES (?, ?, 20, 6, ?)", (fixture_id, task_id, run_doc))
    d.execute("INSERT INTO ai_runs (id, actor, state, result, created) VALUES (?, 20, 'running', ?, ?)", (fixture_id, json.dumps({'status': 'running'}), now))
print('FIXTURE_INSERTED')
"""

r_ins = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-gateway-1", "python", "-", fixture_id, task_id, trace_id, conv_id, payload_str],
    input=insert_py,
    capture_output=True,
    text=True
)
print("Fixture insert output:", r_ins.stdout.strip(), r_ins.stderr.strip())
assert "FIXTURE_INSERTED" in r_ins.stdout

ruby_test_script = f"""
require 'json'
require 'securerandom'

res_map = {{}}
p6 = Project.find(6)
owner = User.find(18)
pm = User.find(20)

def bridge(proj, user, action, args = {{}})
  Qldapm::AiBridge.call(proj, user, 'command', {{
    action: action,
    arguments: args,
    idempotency_key: SecureRandom.uuid
  }})
end

# 1.1 Owner can read engineering_status on Project 6
begin
  st = bridge(p6, owner, 'engineering_status')
  res_map['owner_status'] = {{ pass: st['result'].is_a?(Hash) && st['result']['project_id'] == 6, mode: st['result']['mode'] }}
rescue => e
  res_map['owner_status'] = {{ pass: false, error: e.message }}
end

# 1.2 Owner cancels PM20 run (Cross-actor cancellation)
begin
  c_res = bridge(p6, owner, 'engineering_cancel', {{ run_id: '{fixture_id}' }})
  res_map['owner_cancel_pm20_run'] = {{
    pass: c_res['result']['cancelled'] == true,
    detail: c_res['result']
  }}
rescue => e
  res_map['owner_cancel_pm20_run'] = {{ pass: false, error: e.message }}
end

# 1.3 Owner can toggle control mode (OFF -> PAUSED -> OFF)
begin
  p_res = bridge(p6, owner, 'engineering_control', {{ mode: 'PAUSED' }})
  o_res = bridge(p6, owner, 'engineering_control', {{ mode: 'OFF' }})
  res_map['owner_control_toggle'] = {{
    pass: p_res['result']['mode'] == 'PAUSED' && o_res['result']['mode'] == 'OFF',
    paused: p_res['result']['mode'],
    off: o_res['result']['mode']
  }}
rescue => e
  res_map['owner_control_toggle'] = {{ pass: false, error: e.message }}
end

# 1.4 Project 5 Isolation check: Owner calling engineering action on Project 5 must be rejected
begin
  p5 = Project.find(5)
  bridge(p5, owner, 'engineering_status')
  res_map['project5_isolation'] = {{ pass: false, error: 'Expected failure on Project 5' }}
rescue => e
  res_map['project5_isolation'] = {{
    pass: e.message.include?('không khớp') || e.message.include?('ENGINEERING_PROJECT_MISMATCH') || e.message.include?('từ chối') || e.message.include?('403') || e.message.include?('OpenProject'),
    message: e.message
  }}
end

# 2. DEFECT-06: Reporting Scheduler & Notifications
# 2.1 Get schedule
begin
  sched = bridge(p6, owner, 'engineering_report_schedule_get')
  res_map['report_schedule_get'] = {{
    pass: sched['result'].is_a?(Hash) && sched['result']['daily_enabled'] == 1,
    schedule: sched['result']
  }}
rescue => e
  res_map['report_schedule_get'] = {{ pass: false, error: e.message }}
end

# 2.2 Update schedule
begin
  up_sched = bridge(p6, owner, 'engineering_report_schedule_update', {{ daily_hour: 7, daily_minute: 30 }})
  res_map['report_schedule_update'] = {{
    pass: up_sched['result']['daily_hour'] == 7 && up_sched['result']['daily_minute'] == 30,
    schedule: up_sched['result']
  }}
rescue => e
  res_map['report_schedule_update'] = {{ pass: false, error: e.message }}
end

# 2.3 Generate On-Demand Report
begin
  rep = bridge(p6, owner, 'engineering_report_generate', {{ report_type: 'ON_DEMAND', include_narrative: false }})
  rep_id = rep['result']['id']
  rep_get = bridge(p6, owner, 'engineering_report_get', {{ id: rep_id }})
  res_map['report_generation_and_get'] = {{
    pass: rep_id.present? && rep_get['result']['id'] == rep_id,
    report_id: rep_id,
    title: rep['result']['title']
  }}
rescue => e
  res_map['report_generation_and_get'] = {{ pass: false, error: e.message }}
end

puts 'REMEDIATION_EVIDENCE=' + JSON.generate(res_map)
"""

try:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
        input=ruby_test_script,
        capture_output=True,
        text=True
    )
    for line in r.stdout.splitlines():
        if line.startswith('REMEDIATION_EVIDENCE='):
            data = json.loads(line.split('=', 1)[1])
            for k, v in data.items():
                print(f"  [{'PASS' if v.get('pass') else 'FAIL'}] {k}: {v}")
                results[k] = v.get('pass', False)
finally:
    # Cleanup fixture
    cleanup_py = """
import sqlite3, sys
fixture_id, task_id = sys.argv[1:3]
with sqlite3.connect('/state/gateway.sqlite') as d:
    d.execute("DELETE FROM ai_queue WHERE id=?", (fixture_id,))
    d.execute("DELETE FROM agent_runs WHERE id=?", (fixture_id,))
    d.execute("DELETE FROM agent_tasks WHERE id=?", (task_id,))
    d.execute("DELETE FROM ai_runs WHERE id=?", (fixture_id,))
print('FIXTURE_CLEANED')
"""
    subprocess.run(["docker", "exec", "-i", "qldapm-ai-gateway-1", "python", "-", fixture_id, task_id], input=cleanup_py, capture_output=True, text=True)

# -------------------------------------------------------------
# 3. DEFECT-07: GitHub Reviews & CI Checks Transparency
# -------------------------------------------------------------
print("\n--- 2. Testing DEFECT-07 (GitHub Reviews & CI Status Transparency) ---")
try:
    check_gh_code = """
import json
from openproject.ai.gateway.engineering_github_sync import fetch_pull_requests
prs = fetch_pull_requests('Luim3141/mini-task-manager')
assert len(prs) >= 4
for p in prs:
    assert 'reviews_state' in p
    assert 'checks_state' in p
print('GITHUB_PRS_VERIFIED=' + json.dumps({
    'count': len(prs),
    'sample_reviews_state': prs[0]['reviews_state'],
    'sample_checks_state': prs[0]['checks_state']
}))
"""
    r_gh = subprocess.run(["python", "-c", check_gh_code], capture_output=True, text=True, check=True)
    for line in r_gh.stdout.splitlines():
        if line.startswith('GITHUB_PRS_VERIFIED='):
            gh_data = json.loads(line.split('=', 1)[1])
            print(f"  [PASS] GitHub PR Transparency: {gh_data}")
            results['github_prs_transparency'] = True
except Exception as e:
    print(f"  [FAIL] GitHub PR Transparency: {e}")
    results['github_prs_transparency'] = False

# -------------------------------------------------------------
# 4. Web UI Verification (HTML inspection)
# -------------------------------------------------------------
print("\n--- 3. Testing Web UI Elements in Rendered Page ---")
try:
    render_ruby = """
require 'action_controller'
user = User.find(18)
proj = Project.find(6)
bridge_res = Qldapm::AiBridge.call(proj, user, 'command', { action: 'engineering_status', arguments: {}, idempotency_key: SecureRandom.uuid })
controller = Class.new(ApplicationController) do
  def test_render(proj, user, eng_data)
    @project = proj
    @current_user = user
    @engineering = eng_data['result'] || {}
    render_to_string(template: 'qldapm_ai/engineering', layout: false)
  end
end.new
html = controller.test_render(proj, user, bridge_res)
has_local_ai = html.include?('Local AI Review:')
has_reviews_col = html.include?('Reviews & CI GitHub')
has_sched_info = html.include?('Lịch tự động:')
puts 'UI_RENDER_CHECK=' + JSON.generate({
  has_local_ai_review_label: has_local_ai,
  has_github_reviews_column: has_reviews_col,
  has_schedule_info: has_sched_info,
  pass: has_local_ai && has_reviews_col && has_sched_info
})
"""
    r_ui = subprocess.run(
        ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
        input=render_ruby,
        capture_output=True,
        text=True
    )
    for line in r_ui.stdout.splitlines():
        if line.startswith('UI_RENDER_CHECK='):
            ui_data = json.loads(line.split('=', 1)[1])
            print(f"  [{'PASS' if ui_data.get('pass') else 'FAIL'}] UI Rendering: {ui_data}")
            results['ui_rendering'] = ui_data.get('pass', False)
except Exception as e:
    print(f"  [FAIL] UI Rendering: {e}")
    results['ui_rendering'] = False

print("\n=================================================================")
all_pass = all(results.values()) and len(results) >= 8
print(f"OVERALL VERIFICATION: {'>>> ALL REMEDIATIONS PASSED <<<' if all_pass else '>>> SOME CHECKS FAILED <<<'}")
print("=================================================================")

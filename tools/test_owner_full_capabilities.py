import subprocess
import json
import uuid

# 1. Create a safe fixture run in Gateway SQLite from host
fixture_id = f"test-owner-lifecycle-{uuid.uuid4().hex[:12]}"
payload_str = json.dumps({"project_id": 6, "unit": "test-owner-auth-fixture"})

insert_sql = f"""
import sqlite3
with sqlite3.connect('/state/gateway.sqlite') as d:
    d.execute("INSERT INTO ai_queue (id, actor, payload, state, created) VALUES ('{fixture_id}', 20, '{payload_str}', 'queued', 1700000000)")
    d.execute("INSERT INTO agent_runs (id, actor, role, status, payload, result, created) VALUES ('{fixture_id}', 20, 'dev', 'queued', '{payload_str}', '{{}}', 1700000000)")
print('FIXTURE_CREATED')
"""

r_ins = subprocess.run(["docker", "exec", "qldapm-ai-gateway-1", "python", "-c", insert_sql], capture_output=True, text=True, check=True)
assert "FIXTURE_CREATED" in r_ins.stdout

ruby_script = f"""
require 'json'
require 'securerandom'

results = {{}}
p6 = Project.find(6)
owner = User.find(18)
pm = User.find(20)

def call_bridge(proj, user, action, args = {{}})
  Qldapm::AiBridge.call(proj, user, 'command', {{
    action: action,
    arguments: args,
    idempotency_key: SecureRandom.uuid
  }})
end

# 1. Test Owner can read engineering_status
begin
  res = call_bridge(p6, owner, 'engineering_status')
  results['owner_engineering_status'] = {{
    pass: res['result'].is_a?(Hash) && res['result'].key?('mode'),
    mode: res['result']['mode']
  }}
rescue => e
  results['owner_engineering_status'] = {{ pass: false, error: e.message }}
end

# 2. Test Owner can toggle control mode (OFF -> PAUSED -> OFF)
begin
  res_paused = call_bridge(p6, owner, 'engineering_control', {{ mode: 'PAUSED' }})
  res_off = call_bridge(p6, owner, 'engineering_control', {{ mode: 'OFF' }})
  results['owner_toggle_control_mode'] = {{
    pass: res_paused['result']['mode'] == 'PAUSED' && res_off['result']['mode'] == 'OFF',
    res_paused: res_paused['result']['mode'],
    res_off: res_off['result']['mode']
  }}
rescue => e
  results['owner_toggle_control_mode'] = {{ pass: false, error: e.message }}
end

# 3. Test Cross-Actor Lifecycle: PM20 run cancelled and resumed by Owner18
begin
  cancel_res = call_bridge(p6, owner, 'engineering_cancel', {{ run_id: '{fixture_id}' }})
  resume_res = call_bridge(p6, owner, 'engineering_resume', {{ run_id: '{fixture_id}' }})
  results['owner_cross_actor_cancel_resume'] = {{
    pass: cancel_res['result']['cancelled'] == true && resume_res['result']['resumed'] == true,
    cancel_result: cancel_res['result'],
    resume_result: resume_res['result']
  }}
rescue => e
  results['owner_cross_actor_cancel_resume'] = {{ pass: false, error: e.message }}
end

# 4. Test Owner can generate On-Demand report
begin
  rep = call_bridge(p6, owner, 'engineering_report_generate', {{ report_type: 'ON_DEMAND', include_narrative: false }})
  rep_id = rep['result']['id']
  rep_title = rep['result']['title']
  
  list_res = call_bridge(p6, owner, 'engineering_report_list', {{ limit: 5 }})
  found_in_list = list_res['result']['reports'].any? {{ |r| r['id'] == rep_id }}
  
  get_res = call_bridge(p6, owner, 'engineering_report_get', {{ report_id: rep_id }})
  
  results['owner_report_full_lifecycle'] = {{
    pass: rep_id.present? && found_in_list && get_res['result']['id'] == rep_id,
    report_id: rep_id,
    report_title: rep_title,
    found_in_list: found_in_list
  }}
rescue => e
  results['owner_report_full_lifecycle'] = {{ pass: false, error: e.message }}
end

# 5. Multiproject Isolation Check: Owner cannot run engineering actions on Project 5
begin
  p5 = Project.find(5)
  call_bridge(p5, owner, 'engineering_status')
  results['project5_engineering_isolation'] = {{ pass: false, error: 'Expected rejection on Project 5' }}
rescue => e
  results['project5_engineering_isolation'] = {{
    pass: e.message.include?('không khớp') || e.message.include?('ENGINEERING_PROJECT_MISMATCH') || e.message.include?('từ chối') || e.message.include?('OpenProject'),
    observed_message: e.message
  }}
end

puts 'OWNER_CAPABILITY_VERIFICATION=' + JSON.generate(results)
"""

try:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
        input=ruby_script,
        capture_output=True,
        text=True
    )
    for line in r.stdout.splitlines():
        if line.startswith('OWNER_CAPABILITY_VERIFICATION='):
            data = json.loads(line.split('=', 1)[1])
            print(json.dumps(data, indent=2))
            all_passed = all(v.get('pass') for v in data.values())
            print(f"\nOVERALL RESULT: {'ALL PASS' if all_passed else 'SOME FAILED'}")
finally:
    # Clean up fixture
    delete_sql = f"""
import sqlite3
with sqlite3.connect('/state/gateway.sqlite') as d:
    d.execute("DELETE FROM ai_queue WHERE id='{fixture_id}'")
    d.execute("DELETE FROM agent_runs WHERE id='{fixture_id}'")
print('FIXTURE_CLEANED')
"""
    subprocess.run(["docker", "exec", "qldapm-ai-gateway-1", "python", "-c", delete_sql], capture_output=True, text=True)

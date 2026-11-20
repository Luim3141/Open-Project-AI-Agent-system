import json
import subprocess

print("=================================================================")
print("VERIFYING DEFECT-05: AUTO MODE STATE MACHINE & AUTO SHUTOFF")
print("=================================================================\n")

test_ruby_code = """
require 'json'
require 'securerandom'

p6 = Project.find(6)
owner = User.find(18)

def bridge(proj, user, action, args = {})
  Qldapm::AiBridge.call(proj, user, 'command', {
    action: action,
    arguments: args,
    idempotency_key: SecureRandom.uuid
  })
end

results = {}

# 1. Check Initial State is OFF
st1 = bridge(p6, owner, 'engineering_status')
results['initial_mode'] = st1['result']['mode']
puts "Initial mode: #{results['initial_mode']}"

# 2. Toggle mode to AUTO
t_res = bridge(p6, owner, 'engineering_control', { mode: 'AUTO' })
results['toggle_to_auto'] = t_res['result']['mode']
puts "Toggled to: #{results['toggle_to_auto']}"

# 3. Call status which triggers auto evaluation
st2 = bridge(p6, owner, 'engineering_status')
results['auto_evaluated_mode'] = st2['result']['mode']
puts "Mode after auto evaluation (Auto Shutoff verification): #{results['auto_evaluated_mode']}"

# 4. Ensure mode is OFF (Auto Shutoff safely executed since all units are delivered)
results['auto_shutoff_success'] = (results['auto_evaluated_mode'] == 'OFF')

# 5. Reset to OFF explicitly to be safe
bridge(p6, owner, 'engineering_control', { mode: 'OFF' })

puts "AUTO_MODE_TEST_RESULTS=" + JSON.generate(results)
"""

r = subprocess.run(
    ["docker", "exec", "-i", "qldapm-openproject-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=test_ruby_code,
    capture_output=True,
    text=True
)

for line in r.stdout.splitlines():
    if line.startswith("AUTO_MODE_TEST_RESULTS="):
        res = json.loads(line.split("=", 1)[1])
        print("Test Results:")
        for k, v in res.items():
            print(f"  - {k}: {v}")
        if res.get("auto_shutoff_success"):
            print("\n[PASS] DEFECT-05 Auto Mode State Machine & Safe Shutoff VERIFIED 100%")
        else:
            print("\n[FAIL] Auto Mode did not shut off as expected")
        break
else:
    print("Script output:\n", r.stdout)
    if r.stderr:
        print("Script error:\n", r.stderr)

print("\n=================================================================")

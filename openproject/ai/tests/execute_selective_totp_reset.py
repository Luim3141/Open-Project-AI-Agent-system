import json
import subprocess
import sys

ruby_script = '''
require "json"

ActiveRecord::Base.transaction do
  target_ids = [5, 6, 9, 10]
  protected_ids = [7, 8]
  
  # 1. Pre-reset verification
  before_state = {}
  [4, 5, 6, 7, 8, 9, 10, 11, 12].each do |uid|
    u = User.find(uid)
    pw = UserPassword.find_by(user_id: uid)
    before_state[uid] = {
      login: u.login,
      active_devices: u.otp_devices.where(active: true).pluck(:id),
      all_devices: u.otp_devices.pluck(:id),
      password_updated_at: pw&.updated_at&.to_s
    }
  end
  puts "BEFORE_STATE=" + JSON.generate(before_state)
  
  # Guard: Protected accounts must have their exact active device IDs
  pm_active = before_state[7][:active_devices]
  be_active = before_state[8][:active_devices]
  raise "GUARD_FAILED: PM active devices #{pm_active} != [24]" unless pm_active == [24]
  raise "GUARD_FAILED: BE active devices #{be_active} != [23]" unless be_active == [23]
  
  # 2. Execute selective destroy on target accounts ONLY
  reset_log = []
  target_ids.each do |uid|
    u = User.find(uid)
    devices = u.otp_devices
    dev_count = devices.count
    devices.destroy_all
    reset_log << { id: uid, login: u.login, destroyed_count: dev_count }
  end
  puts "RESET_LOG=" + JSON.generate(reset_log)
  
  # 3. Post-reset verification
  after_state = {}
  [4, 5, 6, 7, 8, 9, 10, 11, 12].each do |uid|
    u = User.find(uid)
    pw = UserPassword.find_by(user_id: uid)
    after_state[uid] = {
      login: u.login,
      active_devices: u.otp_devices.where(active: true).pluck(:id),
      all_devices: u.otp_devices.pluck(:id),
      password_updated_at: pw&.updated_at&.to_s
    }
  end
  puts "AFTER_STATE=" + JSON.generate(after_state)
  
  # Verification assertions
  target_ids.each do |uid|
    if after_state[uid][:all_devices].any?
      raise "ASSERTION_FAILED: Target user #{uid} still has devices: #{after_state[uid][:all_devices]}"
    end
  end
  
  # Verify PM and BE are 100% UNTOUCHED
  if after_state[7][:active_devices] != [24]
    raise "ASSERTION_FAILED: PM active device modified!"
  end
  if after_state[8][:active_devices] != [23]
    raise "ASSERTION_FAILED: BE active device modified!"
  end
  if after_state[7][:password_updated_at] != before_state[7][:password_updated_at]
    raise "ASSERTION_FAILED: PM password modified!"
  end
  if after_state[8][:password_updated_at] != before_state[8][:password_updated_at]
    raise "ASSERTION_FAILED: BE password modified!"
  end
  
  puts "TRANSACTION_COMMITTED_SUCCESSFULLY"
end
'''

print("Executing Selective 2FA Reset on Staging Web...")
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=60
)
print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr, file=sys.stderr)

if res.returncode != 0 or "TRANSACTION_COMMITTED_SUCCESSFULLY" not in res.stdout:
    print("FATAL: Selective 2FA Reset failed!", file=sys.stderr)
    sys.exit(1)

print("Selective 2FA Reset completed and verified.")

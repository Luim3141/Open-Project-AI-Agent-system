import subprocess
import json

ruby_script = (
    'require "json"\n'
    'ActiveRecord::Base.transaction do\n'
    '  ActiveRecord::Base.connection.execute("SET TRANSACTION READ ONLY")\n'
    '  d = TwoFactorAuthentication::Device::Totp.find_by!(user_id: 7, active: true, default: true)\n'
    '  at = Time.now.to_i / 30 * 30\n'
    '  puts "PRIVATE_CODES=" + JSON.generate((0..60).map { |i| t = at + i * 30; [t, d.totp.at(t)] }.to_h)\n'
    'end\n'
)
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script,
    capture_output=True,
    text=True,
    timeout=60,
    check=True
)
for line in res.stdout.splitlines():
    if line.startswith("PRIVATE_CODES="):
        codes = json.loads(line.split("=", 1)[1])
        print("SUCCESS! TOTP codes generated:", len(codes))

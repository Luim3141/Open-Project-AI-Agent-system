"""Generate current live TOTP 2FA codes for Staging OpenProject users."""
import json
import subprocess
import sys
import time

ruby = '''require "json"
result = {}
ActiveRecord::Base.transaction do
  ActiveRecord::Base.connection.execute("SET TRANSACTION READ ONLY")
  User.where(id: [5, 6, 7, 8, 9, 10]).each do |u|
    d = TwoFactorAuthentication::Device::Totp.find_by(user_id: u.id, active: true, default: true)
    if d
      result[u.login] = d.totp.at(Time.now)
    end
  end
end
puts "CODES=" + JSON.generate(result)
'''

def get_codes():
    res = subprocess.run(
        ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
        input=ruby,
        capture_output=True,
        text=True,
        timeout=60,
        check=True
    )
    for line in res.stdout.splitlines():
        if line.startswith("CODES="):
            return json.loads(line.split("=", 1)[1])
    return {}

if __name__ == "__main__":
    codes = get_codes()
    print("Mã xác thực 2FA (TOTP) hiện tại (hiệu lực ~30s):")
    for user, code in sorted(codes.items()):
        print(f"  - {user:12s}: {code}")

import subprocess
import json

code = """
u = User.find_by(login: 'admin')
puts "admin found: #{u.present?}"
if u
  puts "admin active: #{u.active?}"
  puts "admin pass valid 'admin': #{u.valid_password?('admin')}"
  puts "admin pass valid 'password': #{u.valid_password?('password')}"
end
pm = User.find_by(login: 'pm')
puts "pm found: #{pm.present?}"
if pm
  puts "pm active: #{pm.active?}"
  puts "pm pass valid 'password': #{pm.valid_password?('password')}"
  puts "pm pass valid 'pm': #{pm.valid_password?('pm')}"
end
"""

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", code],
    capture_output=True,
    text=True
)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)

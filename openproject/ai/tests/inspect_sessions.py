import subprocess

ruby_code = '''
puts "=== BACKUP CODES AND SESSIONS INSPECTION ==="
[5, 6, 7, 8, 9, 10].each do |uid|
  u = User.find(uid)
  devices = u.otp_devices
  puts "User #{u.id} (#{u.login}): active_devices=#{devices.count}"
end

puts "\nAny sessions active?"
puts "Total active sessions: #{Session.count rescue 'N/A'}"
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

import subprocess

ruby_code = '''
puts "=== 2FA PLUGIN INSPECTION ==="
puts "TwoFactorAuthentication setting: " + Setting.plugin_openproject_two_factor_authentication.to_json

puts "\nDevices table classes:"
puts TwoFactorAuthentication::Device.descendants.map(&:name).join(", ")

puts "\nDevices currently registered:"
TwoFactorAuthentication::Device.all.each do |d|
  puts "ID: #{d.id} | User: #{d.user_id} (#{d.user.login rescue 'N/A'}) | Type: #{d.type} | Active: #{d.active} | Default: #{d.default} | Identifier: #{d.identifier} | Created: #{d.created_at}"
end
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

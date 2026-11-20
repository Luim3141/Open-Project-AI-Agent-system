import subprocess

ruby_code = '''
puts "=== USERS TWO FACTOR DEVICES CONTROLLER ==="
path = Rails.root.join("modules/two_factor_authentication/app/controllers/two_factor_authentication/users/two_factor_devices_controller.rb")
if File.exist?(path)
  puts File.read(path)
else
  puts "File not found at #{path}"
end
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

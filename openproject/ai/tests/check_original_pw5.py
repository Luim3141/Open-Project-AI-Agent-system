import subprocess

ruby_code = '''
require "bcrypt"
p = "PUBLICATION_REDACTED"
h = "PUBLICATION_REDACTED"
puts "Does accounts.json pass match original hash? " + BCrypt::Password.new(h).is_password?(p).to_s
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

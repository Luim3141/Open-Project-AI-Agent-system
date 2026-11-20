import subprocess

ruby_code = '''
u = User.find(5)
pw = UserPassword.find_by(user_id: 5)
puts "User 5: #{u.login} | status: #{u.status} | failed_login_count: #{u.failed_login_count}"
puts "Password in accounts.json: PUBLICATION_REDACTED"
puts "Check pw: #{u.check_password?('PUBLICATION_REDACTED')}"
puts "Hashed password in DB: #{pw&.hashed_password}"
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

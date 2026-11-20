import subprocess

ruby_script = """
users = [
  [19, 'ba-pm', 'PUBLICATION_REDACTED'],
  [20, 'pm', 'PUBLICATION_REDACTED'],
  [21, 'be', 'PUBLICATION_REDACTED'],
  [22, 'fe', 'PUBLICATION_REDACTED'],
  [23, 'qa', 'PUBLICATION_REDACTED']
]
users.each do |uid, login, pwd|
  u = User.find(uid)
  puts "#{login} (#{uid}): #{u.check_password?(pwd)}"
end
"""

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-openproject-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=60
)
print(res.stdout)

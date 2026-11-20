import subprocess

code = """
u = User.find(18)
puts "USER: " + u.login
puts "ROLE: " + Qldapm::Rbac.role(Project.find(6), u, fresh: true).to_s
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code,
    text=True,
    capture_output=True
)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr)

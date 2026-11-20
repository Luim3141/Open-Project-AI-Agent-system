import subprocess

code = '''
p = Project.find(5)
u = User.find(19)
result = Qldapm::AiBridge.call(p, u, "command", {action: "identity"})
puts "BRIDGE_RESULT:" + result.to_json
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code,
    capture_output=True,
    text=True
)
print("Returncode:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)

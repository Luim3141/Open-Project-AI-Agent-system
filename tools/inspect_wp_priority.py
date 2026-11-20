import subprocess

code = """
p = WorkPackage.find(379)
puts 'Priority: ' + p.priority.inspect
puts 'Priority ID: ' + p.priority_id.inspect
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code,
    text=True,
    capture_output=True
)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr)

import subprocess
import json

code = """
p = Project.find(6)
wps = WorkPackage.where(project_id: 6).order(:id)
puts wps.map { |w| {id: w.id, subject: w.subject, status_id: w.status_id, status: w.status.name, parent_id: w.parent_id, lock_version: w.lock_version} }.to_json
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code,
    text=True,
    capture_output=True
)
print("PROJECT 6 WORK PACKAGES:")
for item in json.loads(r.stdout.strip()):
    print(item)

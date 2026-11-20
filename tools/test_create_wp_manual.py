import subprocess

code = """
p6 = Project.find(6)
parent = WorkPackage.find(379)
u_owner = User.find(18)

wp = WorkPackage.find_by(project_id: 6, subject: '[AI backlog] Them route GET /healthz va unit test status ok')
if !wp
  wp = WorkPackage.new(
    project: p6,
    parent: parent,
    author: u_owner,
    assigned_to: User.find_by(login: 'ba-pm') || u_owner,
    type: parent.type,
    priority: parent.priority,
    status: Status.find_by(name: 'In progress') || Status.find(7),
    subject: '[AI backlog] Them route GET /healthz va unit test status ok',
    description: "Bo sung route GET /healthz tra ve JSON {status: 'ok', app: 'mini-task-manager', version: '1.0.0'} va unit test trong test_crud_web.py."
  )
  wp.save!
  puts JSON.generate({created: true, id: wp.id, lock_version: wp.lock_version})
else
  puts JSON.generate({created: false, id: wp.id, lock_version: wp.lock_version})
end
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code,
    text=True,
    capture_output=True
)
print("STDOUT:", repr(r.stdout))
print("STDERR:", repr(r.stderr))

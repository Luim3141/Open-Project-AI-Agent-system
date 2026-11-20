import subprocess

code = '''
pm = User.find_by!(login: 'ba-pm')
User.current = pm
controller = QldapmAIController.new
controller.request = ActionDispatch::TestRequest.create
controller.response = ActionDispatch::TestResponse.create
controller.params = ActionController::Parameters.new(project_id: 'qldapm-local')

puts "Step 0 performed: #{controller.performed?}"

project = Project.visible(User.current).find_by!(identifier: 'qldapm-local')
puts "Step 1 project visible performed: #{controller.performed?}"

item = WorkPackage.visible(User.current).where(project: project).first
puts "Step 2 item visible performed: #{controller.performed?}"

actor_info = item.qldapm_actor(User.current)
puts "Step 3 qldapm_actor performed: #{controller.performed?}"

role = Qldapm::Rbac.role(project, User.current)
puts "Step 4 Rbac.role performed: #{controller.performed?}"
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code.encode(),
    capture_output=True
)
print("STDOUT:")
print(res.stdout.decode())
if res.stderr:
    print("STDERR:")
    print(res.stderr.decode()[:500])

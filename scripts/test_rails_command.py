import subprocess

code = '''
pm = User.find_by!(login: 'ba-pm')
User.current = pm
controller = QldapmAIController.new
controller.request = ActionDispatch::TestRequest.create
controller.response = ActionDispatch::Response.new
puts "Performed before load_project: #{controller.performed?}"
controller.params = ActionController::Parameters.new(
  project_id: 'qldapm-local',
  engine: 'supervisor',
  prompt: 'BA và QA phân tích Work Package #49, tạo bản đề xuất test cases, không thay đổi dữ liệu.',
  allow_routine_writes: '0',
  write_scope_ids: ''
)

begin
  controller.send(:load_project)
  puts "Project loaded, role: " + controller.instance_variable_get(:@role).to_s
  puts "Response status after load_project: " + controller.response.status.to_s
  puts "Performed after load_project: " + controller.performed?.to_s
  controller.send(:command)
  puts "Command response status: " + controller.response.status.to_s
rescue => e
  puts "Exception: " + e.class.name + " - " + e.message
  puts e.backtrace.slice(0, 10).join("\n")
end
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

import subprocess

code = '''
pm = User.find_by!(login: 'ba-pm')
User.current = pm

env = Rack::MockRequest.env_for(
  "/projects/qldapm-local/qldapm-ai/commands",
  method: "POST",
  params: {
    engine: "supervisor",
    prompt: "BA và QA phân tích Work Package #49, tạo bản đề xuất test cases, không thay đổi dữ liệu.",
    allow_routine_writes: "0",
    write_scope_ids: ""
  }
)
env["action_dispatch.request.path_parameters"] = { project_id: "qldapm-local" }
env["action_dispatch.show_exceptions"] = false

begin
  status, headers, body = QldapmAIController.action(:command).call(env)
  puts "Action returned HTTP status: #{status}"
  puts "Location: #{headers['Location']}"
  body_text = ""
  body.each { |part| body_text << part }
  puts "Body snippet: #{body_text.slice(0, 300)}"
rescue => e
  puts "Direct Exception: #{e.class.name} - #{e.message}"
  puts e.backtrace.join("\n")
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

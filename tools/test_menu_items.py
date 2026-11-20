import subprocess

ruby_code = """
project = Project.find_by(identifier: 'ai-dev-demo')
user = User.find(18)
User.current = user

puts 'PROJECT: ' + project.identifier
root_node = Redmine::MenuManager.items(:project_menu, project)
children = root_node.respond_to?(:children) ? root_node.children : []
children.each do |it|
  cond = it.condition ? it.condition.call(project) : true
  puts "- #{it.name}: #{it.caption(project)} (condition: #{cond})"
end
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=ruby_code,
    capture_output=True,
    text=True
)
print('STDOUT:\n', r.stdout)
if r.stderr:
    print('STDERR:\n', r.stderr)

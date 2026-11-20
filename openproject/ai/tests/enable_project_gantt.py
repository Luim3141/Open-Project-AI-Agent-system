import subprocess

ruby_code = '''
p = Project.find_by!(identifier: "qldapm-local")
puts "Before enabled modules: " + p.enabled_module_names.sort.join(", ")

unless p.module_enabled?(:gantt)
  p.enabled_modules.create!(name: "gantt")
  p.reload
end

puts "After enabled modules: " + p.enabled_module_names.sort.join(", ")
puts "Is :gantt enabled? " + p.module_enabled?(:gantt).to_s

# Verify PM (id 7) can view Gantt
u_pm = User.find(7)
can_view = u_pm.allowed_in_project?(:view_work_packages, p)
puts "PM can view work packages & gantt in qldapm-local: " + can_view.to_s
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

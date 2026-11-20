import subprocess

ruby_code = '''
puts "=== ROLE PERMISSIONS INSPECTION ==="
r_pm = Role.find_by(name: "QLDAPM PM")
if r_pm
  puts "Role: #{r_pm.name} (id: #{r_pm.id})"
  puts "Permissions count: #{r_pm.permissions.count}"
  puts "Has :select_project_modules?: #{r_pm.has_permission?(:select_project_modules)}"
  puts "Has :edit_project?: #{r_pm.has_permission?(:edit_project)}"
  puts "Has :view_gantt?: #{r_pm.has_permission?(:view_gantt)}"
  puts "Has :view_work_packages?: #{r_pm.has_permission?(:view_work_packages)}"
  puts "\nAll permissions for QLDAPM PM:"
  puts r_pm.permissions.sort.join(", ")
else
  puts "Role QLDAPM PM not found"
end

puts "\n=== AVAILABLE PROJECT MODULES IN OPENPROJECT ==="
puts OpenProject::AccessControl.available_project_modules.join(", ")

puts "\n=== GANTT PERMISSIONS IN ACCESS CONTROL ==="
gantt_perms = OpenProject::AccessControl.permissions.select { |p| p.name.to_s.include?("gantt") || p.project_module.to_s.include?("gantt") }
gantt_perms.each do |p|
  puts "Permission: #{p.name} | Module: #{p.project_module} | Public: #{p.public?}"
end
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

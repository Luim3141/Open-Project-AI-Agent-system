import subprocess

ruby_code = '''
puts "=== MENU ITEMS FOR PROJECT ==="
menu = Redmine::MenuManager.items(:project_menu)
gantt_item = menu.find { |i| i.name == :gantt }
if gantt_item
  puts "Gantt item found in project_menu:"
  puts "  name: #{gantt_item.name}"
  puts "  url: #{gantt_item.url}"
  puts "  condition: #{gantt_item.condition.inspect}"
else
  puts "Gantt item NOT found in project_menu. All item names:"
  puts menu.map(&:name).join(", ")
end

wp_item = menu.find { |i| i.name == :work_packages }
if wp_item
  puts "\nWork packages item in project_menu:"
  puts "  name: #{wp_item.name}"
  puts "  url: #{wp_item.url}"
  puts "  children: #{wp_item.children.map(&:name).join(', ')}"
end
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

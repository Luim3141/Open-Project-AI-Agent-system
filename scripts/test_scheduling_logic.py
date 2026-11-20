import subprocess

code = '''
wp_sub = WorkPackage.where(type_id: 10, project_id: 5).first
parent = wp_sub.parent
puts "Subtask #{wp_sub.id}, parent #{parent.id} (#{parent.type.name})"
puts "Parent dates before: #{parent.start_date} -> #{parent.due_date}"

pm = User.find_by(login: 'ba-pm') || User.find(19)
User.current = pm
puts "Current user: #{User.current.login} (ID: #{User.current.id})"

wp_sub.start_date = Date.new(2026, 10, 5)
wp_sub.due_date = Date.new(2026, 10, 6)
if !wp_sub.save
  puts "Validation errors: #{wp_sub.errors.full_messages}"
  puts "Details: #{wp_sub.errors.details}"
else
t49 = WorkPackage.find(49)
t50 = WorkPackage.find(50)
puts "Task 49: #{t49.subject}, dates: #{t49.start_date} -> #{t49.due_date}"
puts "Task 50: #{t50.subject}, dates: #{t50.start_date} -> #{t50.due_date}"

# Case 1: Valid schedule (t50 starts Monday 2026-10-12 after t49 finishes Friday 2026-10-09)
t50.start_date = Date.new(2026, 10, 12)
t50.due_date = Date.new(2026, 10, 16)
if !t50.save
  puts "Valid case failed: #{t50.errors.full_messages}"
else
  puts "Valid case succeeded: #{t50.start_date} -> #{t50.due_date}"
end

# Case 2: Invalid schedule (t50 starts 2026-10-07 while t49 finishes 2026-10-09)
t50.start_date = Date.new(2026, 10, 7)
t50.due_date = Date.new(2026, 10, 11)
if !t50.save
  puts "Invalid case rejected as expected: #{t50.errors.full_messages}"
else
  puts "Invalid case unexpectedly allowed: #{t50.start_date} -> #{t50.due_date}"
end
end
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-rd-core-20261021', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code.encode(),
    capture_output=True
)
print("STDOUT:")
print(res.stdout.decode())
if res.stderr:
    print("STDERR:")
    print(res.stderr.decode()[:500])

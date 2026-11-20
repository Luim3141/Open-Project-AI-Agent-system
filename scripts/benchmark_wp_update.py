import subprocess
import time

test_code = '''
t0 = Time.now
User.current = User.find(19)
wps = WorkPackage.where(project_id: 5).limit(10)
wps.each do |wp|
  wp.start_date = Date.new(2026, 10, 5)
  wp.due_date = Date.new(2026, 10, 6)
  wp.save!
end
t1 = Time.now
puts "Updated 10 WPs with save! in #{t1 - t0} seconds"
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-rd-core-20261021', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=test_code.encode(),
    capture_output=True
)
print(res.stdout.decode())
if res.stderr:
    print("STDERR:", res.stderr.decode()[:500])

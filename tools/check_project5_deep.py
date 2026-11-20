import subprocess
import json

ruby_script = """
require 'json'

p5 = Project.find(5)
wps = p5.work_packages.unscope(:order)
wp_ids = wps.order(:id).pluck(:id)
statuses = wps.group(:status_id).count
types = wps.group(:type_id).count
max_lock = wps.maximum(:lock_version)
min_lock = wps.minimum(:lock_version)
last_updated_at = wps.maximum(:updated_at)

members = p5.members.includes(:principal, :roles).map do |m|
  {
    user_id: m.user_id,
    login: (m.principal.login rescue 'unknown'),
    roles: m.roles.map(&:name)
  }
end

result = {
  project_id: p5.id,
  identifier: p5.identifier,
  name: p5.name,
  wp_count: wps.count,
  wp_id_min: wp_ids.min,
  wp_id_max: wp_ids.max,
  wp_ids_checksum: Digest::SHA256.hexdigest(wp_ids.join(',')),
  status_breakdown: statuses,
  type_breakdown: types,
  min_lock_version: min_lock,
  max_lock_version: max_lock,
  last_wp_updated_at: last_updated_at&.iso8601,
  members: members
}

puts 'PROJECT5_INVARIANTS=' + JSON.generate(result)
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=ruby_script,
    capture_output=True,
    text=True
)

found = False
for line in r.stdout.splitlines():
    if line.startswith('PROJECT5_INVARIANTS='):
        data = json.loads(line.split('=', 1)[1])
        print(json.dumps(data, indent=2))
        found = True

if not found:
    print("STDOUT:", r.stdout)
    print("STDERR:", r.stderr)

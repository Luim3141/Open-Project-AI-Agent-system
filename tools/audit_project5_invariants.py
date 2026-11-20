import subprocess
import json

ruby_script = """
p5 = Project.find(5)
wps = WorkPackage.where(project_id: 5)
count = wps.count
ids = wps.order(:id).pluck(:id)
status_counts = wps.unscope(:order).group(:status_id).count
max_lock_version = wps.maximum(:lock_version)
latest_updated = wps.maximum(:updated_at)

members = Member.where(project_id: 5).map { |m| { user_id: m.user_id, roles: m.roles.map(&:name) } }

puts "P5_INVARIANTS=" + JSON.generate({
  project_id: 5,
  identifier: p5.identifier,
  name: p5.name,
  work_package_count: count,
  min_id: ids.first,
  max_id: ids.last,
  status_distribution: status_counts,
  max_lock_version: max_lock_version,
  latest_updated_at: latest_updated.iso8601,
  members_count: members.count,
  members: members
})
"""

r = subprocess.run(
    ["docker", "exec", "-i", "qldapm-openproject-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script,
    capture_output=True,
    text=True
)

for line in r.stdout.splitlines():
    if line.startswith("P5_INVARIANTS="):
        data = json.loads(line.split("=", 1)[1])
        print("Project 5 Invariants:")
        print(f"  Count: {data['work_package_count']}")
        print(f"  ID range: {data['min_id']} -> {data['max_id']}")
        print(f"  Status distribution: {data['status_distribution']}")
        print(f"  Max lock_version: {data['max_lock_version']}")
        print(f"  Latest updated_at: {data['latest_updated_at']}")
        print(f"  Members: {len(data['members'])} users")
        with open("docs/ai/engineering/project5_invariants_baseline.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Saved docs/ai/engineering/project5_invariants_baseline.json")
        break
else:
    print("Script output:\n", r.stdout)
    if r.stderr:
        print("Script error:\n", r.stderr)

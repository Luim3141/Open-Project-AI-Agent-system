import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-access-gantt-boards"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ruby_script = '''require "json"

begin
  versions_map = Version.where(project_id: 3).index_by(&:id)
  wps = WorkPackage.where(project_id: 3).order(:id)

  data = wps.map do |wp|
    {
      id: wp.id,
      subject: wp.subject,
      type_id: wp.type_id,
      type_name: wp.type&.name,
      status_id: wp.status_id,
      status_name: wp.status&.name,
      parent_id: wp.parent_id,
      parent_subject: wp.parent&.subject,
      version_id: wp.version_id,
      version_name: versions_map[wp.version_id]&.name,
      assignee: wp.assigned_to&.name,
      start_date: wp.start_date&.to_s,
      due_date: wp.due_date&.to_s,
      schedule_manually: wp.schedule_manually,
      estimated_hours: wp.estimated_hours,
      children_count: wp.children.count
    }
  end

  versions = versions_map.values.map do |v|
    {
      id: v.id,
      name: v.name,
      start_date: v.try(:start_date)&.to_s,
      effective_date: v.try(:effective_date)&.to_s,
      status: v.status
    }
  end

  puts "###RESULT_START###"
  puts JSON.generate({ work_packages: data, versions: versions })
  puts "###RESULT_END###"
rescue => e
  puts "ERROR: " + e.message
  puts e.backtrace.first(10)
  exit 1
end
'''

print("Executing Rails query to audit work packages...")
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=120
)

if res.returncode != 0:
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    raise RuntimeError(f"Rails runner failed with code {res.returncode}")


stdout = res.stdout
start_idx = stdout.find("###RESULT_START###") + len("###RESULT_START###")
end_idx = stdout.find("###RESULT_END###")
json_str = stdout[start_idx:end_idx].strip()

data = json.loads(json_str)
work_packages = data["work_packages"]
versions = data["versions"]

print(f"Total Work Packages retrieved: {len(work_packages)}")
print(f"Total Versions retrieved: {len(versions)}")

# Save raw json for processing
(OUTPUT_DIR / "wp_audit_raw.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved wp_audit_raw.json")

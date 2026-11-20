import json
import subprocess
from pathlib import Path

ruby_script = '''require "json"

begin
  ActiveRecord::Base.transaction do
    ActiveRecord::Base.connection.execute("SET TRANSACTION READ ONLY")
    
    total_wps = WorkPackage.count
    p3_wps = WorkPackage.where(project_id: 3).count
    
    p3 = Project.find_by(id: 3)
    p3_info = {
      id: p3&.id,
      identifier: p3&.identifier,
      name: p3&.name,
      modules: p3&.enabled_modules&.pluck(:name),
      members: p3&.members&.map { |m| { user_id: m.user_id, login: m.principal&.login, roles: m.roles.map(&:name) } }
    }
    
    users = User.where(id: [5, 6, 7, 8, 9, 10]).map do |u|
      {
        id: u.id,
        login: u.login,
        admin: u.admin?,
        status: u.status,
        totp_devices: TwoFactorAuthentication::Device::Totp.where(user_id: u.id).map { |d| { id: d.id, active: d.active, default: d.default } }
      }
    end

    queries = Query.where(project_id: 3).map do |q|
      {
        id: q.id,
        name: q.name,
        public: q.public?,
        filters: q.filters.map { |f| { field: f.field, operator: f.operator, values: f.values } },
        column_names: q.column_names,
        sort_criteria: q.sort_criteria,
        show_hierarchies: q.show_hierarchies
      }
    end

    boards = Boards::Grid.where(project_id: 3).map do |b|
      {
        id: b.id,
        name: b.name,
        options: b.options,
        widgets_count: b.widgets.count
      }
    end

    puts "###START###"
    puts JSON.generate({
      total_wps: total_wps,
      p3_wps: p3_wps,
      p3_info: p3_info,
      users: users,
      queries: queries,
      boards: boards
    })
    puts "###END###"
  end
rescue => e
  puts "ERROR: #{e.message}"
  puts e.backtrace.first(10)
  exit 1
end
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=120
)
if res.returncode != 0:
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    raise RuntimeError(f"Rails runner failed with code {res.returncode}")


start = res.stdout.find("###START###") + len("###START###")
end = res.stdout.find("###END###")
data = json.loads(res.stdout[start:end].strip())
print(json.dumps(data, indent=2, ensure_ascii=False))

out_path = Path("docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/baseline_data.json")
out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved baseline_data.json successfully")

import json
import subprocess
from pathlib import Path

ruby_script = '''require "json"

grids = Boards::Grid.where(project_id: 3).order(:id)
grids_data = grids.map do |g|
  widgets = g.widgets.map do |w|
    {
      id: w.id,
      identifier: w.identifier,
      options: w.options
    }
  end
  {
    id: g.id,
    name: g.name,
    options: g.options,
    widgets: widgets
  }
end

registrations = OpenProject::Boards::GridRegistration.all rescue []
reg_names = registrations.map(&:type) rescue []

puts "###DATA###" + JSON.generate({
  grids: grids_data,
  registrations: reg_names
})
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=120
)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
for line in res.stdout.splitlines():
    if line.startswith("###DATA###"):
        data = json.loads(line.replace("###DATA###", ""))
        print(json.dumps(data, indent=2, ensure_ascii=False))

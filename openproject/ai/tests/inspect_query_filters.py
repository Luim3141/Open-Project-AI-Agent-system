import json
import subprocess

ruby_script = '''require "json"

q35 = Query.find(35)
q36 = Query.find(36)

puts "###DATA###" + JSON.generate({
  q35: {
    id: q35.id,
    name: q35.name,
    filters: q35.filters.map { |f| { class: f.class.name, field: f.field, operator: f.operator, values: f.values } },
    column_names: q35.column_names,
    sort_criteria: q35.sort_criteria
  },
  q36: {
    id: q36.id,
    name: q36.name,
    filters: q36.filters.map { |f| { class: f.class.name, field: f.field, operator: f.operator, values: f.values } }
  }
})
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=120
)
for line in res.stdout.splitlines():
    if line.startswith("###DATA###"):
        data = json.loads(line.replace("###DATA###", ""))
        print(json.dumps(data, indent=2, ensure_ascii=False))

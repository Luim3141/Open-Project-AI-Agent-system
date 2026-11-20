import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-access-gantt-boards"

ruby_script = '''require "json"

boards = Board.where(project_id: 3).order(:id)

boards_data = boards.map do |b|
  queries = b.queries.map do |q|
    {
      id: q.id,
      name: q.name,
      filters: q.filters.map { |f| { field: f.field, operator: f.operator, values: f.values } }
    }
  end

  {
    id: b.id,
    name: b.name,
    type: b.type,
    options: b.options,
    queries_count: b.queries.count,
    queries: queries
  }
end

# Check available Board types in OpenProject codebase
board_classes = Board.descendants.map(&:name) rescue []

puts "###RESULT_START###"
puts JSON.generate({
  project_id: 3,
  boards: boards_data,
  board_classes: board_classes
})
puts "###RESULT_END###"
'''

print("Querying Rails for existing boards in Project 3...")
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=120
)

if res.returncode != 0:
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    raise RuntimeError("Rails runner failed")

stdout = res.stdout
start_idx = stdout.find("###RESULT_START###") + len("###RESULT_START###")
end_idx = stdout.find("###RESULT_END###")
data = json.loads(stdout[start_idx:end_idx].strip())

print(f"Total boards found in Project 3: {len(data['boards'])}")
for b in data["boards"]:
    print(f"Board #{b['id']}: '{b['name']}' (Type: {b['type']}, Queries/Cols: {b['queries_count']})")

(OUTPUT_DIR / "boards_audit_raw.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved boards_audit_raw.json successfully.")

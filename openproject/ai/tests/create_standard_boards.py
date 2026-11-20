import json
import subprocess
from pathlib import Path

ruby_script = '''require "json"

project = Project.find(3)
user = User.find(7) # PM
User.current = user

created_boards = []

ActiveRecord::Base.transaction do
  # -------------------------------------------------------------
  # BOARD 1: QLDAPM — Main Scrum Kanban Board (7 statuses)
  # -------------------------------------------------------------
  b1 = Boards::Grid.find_or_initialize_by(project: project, name: "QLDAPM — Main Scrum Kanban Board")
  b1.options = { "type" => "action", "attribute" => "status" }
  b1.column_count = 7
  b1.row_count = 1
  b1.widgets.destroy_all if b1.persisted?
  b1.save!

  statuses = [
    { id: 1, name: "NEW" },
    { id: 7, name: "IN PROGRESS" },
    { id: 21, name: "CODE REVIEW" },
    { id: 22, name: "READY FOR TEST" },
    { id: 9, name: "IN TESTING" },
    { id: 23, name: "READY FOR RELEASE" },
    { id: 17, name: "DONE" }
  ]

  statuses.each_with_index do |st, idx|
    q = Query.find_or_initialize_by(project: project, name: "#{b1.name} — #{st[:name]}")
    q.user = user
    q.public = true
    q.include_subprojects = true
    q.filters = [Queries::WorkPackages::Filter::StatusFilter.create!(operator: "=", values: [st[:id].to_s])]
    q.sort_criteria = [["manual_sorting", "asc"], ["id", "asc"]]
    q.save!

    b1.widgets.create!(
      identifier: "work_package_query",
      start_row: 1,
      end_row: 2,
      start_column: idx + 1,
      end_column: idx + 2,
      options: {
        "queryId" => q.id,
        "filters" => [{ "status_id" => { "operator" => "=", "values" => [st[:id].to_s] } }]
      }
    )
  end
  created_boards << { id: b1.id, name: b1.name, columns: b1.widgets.count }

  # -------------------------------------------------------------
  # BOARD 2: QLDAPM — Team Workload & Assignee Board (6 columns)
  # -------------------------------------------------------------
  b2 = Boards::Grid.find_or_initialize_by(project: project, name: "QLDAPM — Team Workload & Assignee Board")
  b2.options = { "type" => "action", "attribute" => "assignee" }
  b2.column_count = 6
  b2.row_count = 1
  b2.widgets.destroy_all if b2.persisted?
  b2.save!

  assignees = [
    { id: "6", name: "BA-PM", op: "=", vals: ["6"] },
    { id: "7", name: "PM", op: "=", vals: ["7"] },
    { id: "8", name: "BE", op: "=", vals: ["8"] },
    { id: "9", name: "FE", op: "=", vals: ["9"] },
    { id: "10", name: "QA", op: "=", vals: ["10"] },
    { id: "none", name: "Chưa phân công", op: "!*", vals: [] }
  ]

  assignees.each_with_index do |asg, idx|
    q = Query.find_or_initialize_by(project: project, name: "#{b2.name} — #{asg[:name]}")
    q.user = user
    q.public = true
    q.include_subprojects = true
    q.filters = [Queries::WorkPackages::Filter::AssignedToFilter.create!(operator: asg[:op], values: asg[:vals])]
    q.sort_criteria = [["manual_sorting", "asc"], ["id", "asc"]]
    q.save!

    b2.widgets.create!(
      identifier: "work_package_query",
      start_row: 1,
      end_row: 2,
      start_column: idx + 1,
      end_column: idx + 2,
      options: {
        "queryId" => q.id,
        "filters" => [{ "assigned_to_id" => { "operator" => asg[:op], "values" => asg[:vals] } }]
      }
    )
  end
  created_boards << { id: b2.id, name: b2.name, columns: b2.widgets.count }

  # -------------------------------------------------------------
  # BOARD 3: QLDAPM — Epic Breakdown & Subtasks Board (5 columns)
  # -------------------------------------------------------------
  b3 = Boards::Grid.find_or_initialize_by(project: project, name: "QLDAPM — Epic Breakdown & Subtasks Board")
  b3.options = { "type" => "action", "attribute" => "subtasks" }
  b3.column_count = 5
  b3.row_count = 1
  b3.widgets.destroy_all if b3.persisted?
  b3.save!

  epics = [
    { id: "38", name: "Tài khoản & Role" },
    { id: "39", name: "Quản lý Project" },
    { id: "40", name: "Backlog" },
    { id: "41", name: "Sprint" },
    { id: "42", name: "Task / User Story" }
  ]

  epics.each_with_index do |ep, idx|
    q = Query.find_or_initialize_by(project: project, name: "#{b3.name} — #{ep[:name]}")
    q.user = user
    q.public = true
    q.include_subprojects = true
    q.filters = [Queries::WorkPackages::Filter::ParentFilter.create!(operator: "=", values: [ep[:id]])]
    q.sort_criteria = [["manual_sorting", "asc"], ["id", "asc"]]
    q.save!

    b3.widgets.create!(
      identifier: "work_package_query",
      start_row: 1,
      end_row: 2,
      start_column: idx + 1,
      end_column: idx + 2,
      options: {
        "queryId" => q.id,
        "filters" => [{ "parent" => { "operator" => "=", "values" => [ep[:id]] } }]
      }
    )
  end
  created_boards << { id: b3.id, name: b3.name, columns: b3.widgets.count }

  # -------------------------------------------------------------
  # BOARD 4: QLDAPM — Roadmap & Milestone Board (4 Sprints Preview)
  # -------------------------------------------------------------
  b4 = Boards::Grid.find_or_initialize_by(project: project, name: "QLDAPM — Roadmap & Milestone Board")
  b4.options = { "type" => "free" }
  b4.column_count = 4
  b4.row_count = 1
  b4.widgets.destroy_all if b4.persisted?
  b4.save!

  sprints = [
    { name: "Sprint 1: Nền tảng (W1-2)" },
    { name: "Sprint 2: Backlog & Stories (W3-4)" },
    { name: "Sprint 3: Boards & Timeline (W5-6)" },
    { name: "Sprint 4: Dashboard & Alerts (W7-8)" }
  ]

  sprints.each_with_index do |sp, idx|
    q = Query.find_or_initialize_by(project: project, name: "#{b4.name} — #{sp[:name]}")
    q.user = user
    q.public = true
    q.include_subprojects = true
    q.sort_criteria = [["manual_sorting", "asc"], ["id", "asc"]]
    q.save!

    b4.widgets.create!(
      identifier: "work_package_query",
      start_row: 1,
      end_row: 2,
      start_column: idx + 1,
      end_column: idx + 2,
      options: {
        "queryId" => q.id,
        "filters" => [{ "manualSort" => { "operator" => "ow", "values" => [] } }]
      }
    )
  end
  created_boards << { id: b4.id, name: b4.name, columns: b4.widgets.count }
end

puts "###RESULT###" + JSON.generate(created_boards)
'''

print("Instantiating 4 standard agile boards via Rails...")
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_script, capture_output=True, text=True, timeout=120
)

print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
for line in res.stdout.splitlines():
    if line.startswith("###RESULT###"):
        data = json.loads(line.replace("###RESULT###", ""))
        print("Created boards successfully:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

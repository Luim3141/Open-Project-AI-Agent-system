require "json"
require "csv"
marker = "/private/board-initialized.json"
if File.exist?(marker)
  puts "Initial board layout retained."
  exit
end
config = JSON.parse(File.read("/private/bootstrap.json"))
mapping = JSON.parse(File.read("/private/source-mapping.json"))
project = Project.find(config.fetch("project_id"))
board = Boards::Grid.find(config.fetch("board_id"))
query = board.contained_queries.first!
task_sources = CSV.read("/private/wbs-snapshot.csv", headers: true, encoding: "bom|utf-8")
                  .select { |r| r["Issue Type"] == "Task" }.map { |r| r["Source ID"] }
raise "Wrong Task total" unless task_sources.size == 53
ActiveRecord::Base.transaction do
  task_sources.each_with_index do |source, index|
    query.ordered_work_packages.find_or_create_by!(work_package_id: mapping.fetch(source)) { |wp| wp.position = index + 1 }
  end
  project.project_types.where.not(type_id: config.fetch("types").values).destroy_all
  role = ProjectRole.find_by!(name: "QLDAPM PM")
  role.permissions = (role.permissions + %i[manage_work_package_relations]).uniq
  role.save!
end
File.write(marker, JSON.generate({ "board_id" => board.id, "initial_task_cards" => query.ordered_work_packages.count }))
puts "Basic board populated with 53 Task cards; project limited to Epic/Task/Subtask."

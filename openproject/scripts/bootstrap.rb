# Configure only the isolated OpenProject database; no Jira integration.
require "json"
private_dir = ENV.fetch("PRIVATE_DIR", "/private")
accounts = JSON.parse(File.read("#{private_dir}/accounts.json"))
export_path = "#{private_dir}/bootstrap.json"
export = File.exist?(export_path) ? JSON.parse(File.read(export_path)) : {}
ActiveRecord::Base.transaction do
  Setting.login_required = true
  Setting.self_registration = 0
  Setting.password_min_length = 14
  Setting.autologin = 0
  Setting.session_ttl_enabled = true
  Setting.session_ttl = 60
  Setting.plugin_openproject_two_factor_authentication = {
    "active_strategies" => ["totp"], "enforced" => true, "allow_remember_for_days" => 0
  }
  admin = User.find_or_initialize_by(login: accounts.fetch("admin").fetch("login"))
  if admin.new_record?
    admin.assign_attributes(firstname: "System", lastname: "Owner", mail: "owner@qldapm.local",
                            admin: true, status: :active,
                            password: accounts["admin"]["password"], password_confirmation: accounts["admin"]["password"],
                            force_password_change: true)
    admin.save!
  end
  User.current = admin
  User.where(login: "admin").where.not(id: admin.id).each { |user| user.update!(status: :locked) }
  Project.where.not(identifier: "qldapm-local").find_each { |project| project.update!(public: false) }
  project = Project.find_or_initialize_by(identifier: "qldapm-local")
  project.assign_attributes(name: "QLDAPM — Local Community", public: false, workspace_type: "project")
  project.save!
  project.enabled_module_names = %w[work_package_tracking backlogs board_view activity]

  common = %i[view_project view_project_attributes view_members view_work_packages add_work_packages
              edit_work_packages add_work_package_comments edit_own_work_package_comments save_queries
              view_work_package_watchers show_board_views view_sprints view_project_activity work_package_assigned]
  roles = (accounts.fetch("users").map { |account| account.fetch("role") } + %w[PM BE FE QA]).uniq.to_h do |name|
    role = ProjectRole.find_or_initialize_by(name: "QLDAPM #{name}")
    role.permissions = common + (name == "PM" ? %i[manage_members manage_versions manage_public_queries
      manage_board_views create_sprints start_complete_sprint manage_sprint_items select_backlog_types_and_statuses manage_work_package_relations] : [])
    role.save!
    [name, role]
  end
  [ProjectRole.anonymous, ProjectRole.non_member].compact.each { |role| role.update!(permissions: []) }
  users = accounts.fetch("users").to_h do |account|
    user = User.find_or_initialize_by(login: account.fetch("login"))
    if user.new_record?
      user.assign_attributes(firstname: "QLDAPM", lastname: account.fetch("role"), mail: account.fetch("email"),
        status: :active, admin: false, password: account.fetch("password"),
        password_confirmation: account.fetch("password"), force_password_change: true)
      user.save!
    end
    member = Member.find_or_initialize_by(project: project, principal: user)
    member.roles = [roles.fetch(account.fetch("role"))]
    member.save!
    [account.fetch("email").downcase, user.id]
  end
  color = Color.first!
  status_names = ["NEW", "READY", "IN PROGRESS", "REVIEW", "DONE", "CANCELLED", "IN ANALYSIS",
                 "READY FOR DEV", "CODE REVIEW", "READY FOR TEST", "IN TESTING", "READY FOR RELEASE"]
  statuses = status_names.to_h do |name|
    status = Status.where("LOWER(name) = ?", name.downcase).first || Status.new(name: name)
    status.assign_attributes(name: name, color: status.color || color,
                             is_closed: %w[DONE CANCELLED].include?(name), default_done_ratio: name == "DONE" ? 100 : 0)
    status.is_default = true if name == "NEW"
    status.save!
    [name, status]
  end
  types = %w[Epic Task Subtask].to_h do |name|
    type = Type.where("LOWER(name) = ?", name.downcase).first || Type.new(name: name)
    type.assign_attributes(name: name, color: type.color || color)
    type.save!
    ProjectType.find_or_create_by!(project: project, type: type)
    [name, type]
  end
  fields = {
    "Source ID" => "string", "Triage" => "list", "Proposed Sprint" => "string",
    "Simulation Hours" => "float", "Simulation Points" => "float"
  }.to_h do |name, format|
    field = WorkPackageCustomField.find_or_initialize_by(name: name)
    field.field_format = format if field.new_record?
    raise "Custom field format mismatch" unless field.field_format == format
    field.assign_attributes(is_filter: true, is_for_all: false)
    field.possible_values = %w[needs-triage needs-info ready-for-agent ready-for-human wontfix] if name == "Triage" && field.new_record?
    field.save!
    field.projects = (field.projects.to_a + [project]).uniq
    field.type_variants = types.values.map(&:default_variant)
    [name, field.attribute_name(:camel_case)]
  end
  # Explicit edges, not all-to-all: reviewers are designated through role assignment.
  edges = {
    "Epic" => [["NEW", "READY", %w[PM]], ["READY", "NEW", %w[PM]],
      ["READY", "IN PROGRESS", %w[PM]], ["IN PROGRESS", "REVIEW", %w[PM]],
      ["REVIEW", "DONE", %w[PM]], ["REVIEW", "IN PROGRESS", %w[PM]],
      ["DONE", "IN PROGRESS", %w[PM]], ["CANCELLED", "NEW", %w[PM]]] +
      %w[NEW READY].concat(["IN PROGRESS", "REVIEW"]).map { |s| [s, "CANCELLED", %w[PM]] },
    "Task" => [["NEW", "IN ANALYSIS", %w[BA-PM PM]], ["IN ANALYSIS", "READY FOR DEV", %w[BA-PM PM]],
      ["READY FOR DEV", "IN PROGRESS", %w[BE FE PM]], ["IN PROGRESS", "CODE REVIEW", %w[BE FE PM]],
      ["CODE REVIEW", "IN PROGRESS", %w[PM]], ["CODE REVIEW", "READY FOR TEST", %w[PM]],
      ["READY FOR TEST", "IN TESTING", %w[QA PM]], ["IN TESTING", "IN PROGRESS", %w[QA PM]],
      ["IN TESTING", "REVIEW", %w[QA PM]], ["REVIEW", "IN PROGRESS", %w[BA-PM PM]],
      ["REVIEW", "IN TESTING", %w[QA PM]], ["REVIEW", "READY FOR RELEASE", %w[PM]],
      ["READY FOR RELEASE", "DONE", %w[PM]], ["DONE", "IN PROGRESS", %w[PM]]],
    "Subtask" => [["NEW", "IN PROGRESS", roles.keys], ["IN PROGRESS", "REVIEW", roles.keys],
      ["REVIEW", "DONE", %w[PM]], ["REVIEW", "IN PROGRESS", %w[PM]], ["DONE", "IN PROGRESS", %w[PM]]]
  }
  types.each do |name, type|
    Workflow.where(type_variant_id: type.default_variant.id).delete_all
    edges.fetch(name).each do |from, to, names|
      names.each do |role_name|
        Workflow.create!(type_variant: type.default_variant, role: roles.fetch(role_name == "BA-PM" && roles.key?("BA") ? "BA" : role_name),
          old_status: statuses.fetch(from), new_status: statuses.fetch(to), author: false,
          assignee: name == "Subtask" && role_name != "PM" && ["NEW", "IN PROGRESS"].include?(from))
      end
    end
  end
  sprints = (1..5).to_h do |i|
    sprint = Sprint.find_or_create_by!(project: project, name: "S#{i}")
    raise "Sprint unexpectedly started" unless sprint.in_planning?
    ["S#{i}", sprint.id]
  end
  Setting.work_package_done_ratio = "status" if Setting.respond_to?(:work_package_done_ratio=)
  board = Boards::Grid.find_or_initialize_by(project: project, name: "QLDAPM Basic — manual status")
  if board.new_record?
    board.assign_attributes(row_count: 1, column_count: 1, options: { "type" => "free" })
    query = Query.new_default(name: "QLDAPM — Imported backlog", project: project, user: admin, public: true)
    query.sort_criteria = [[:manual_sorting, "asc"]]
    query.add_filter(:manual_sort, "ow", [])
    query.save!
    board.widgets.build(identifier: "work_package_query", start_row: 1, end_row: 2,
                        start_column: 1, end_column: 2, options: { "queryId" => query.id,
                          "filters" => [{ "manualSort" => { "operator" => "ow", "values" => [] } }] })
    board.save!
  end
  export.merge!("project_id" => project.id, "users" => users, "types" => types.transform_values(&:id),
                "statuses" => statuses.transform_values(&:id), "fields" => fields, "sprints" => sprints,
                "board_id" => board.id)
  export["api_token"] ||= Token::API.create_and_return_value(admin)
end
File.write(export_path, JSON.pretty_generate(export))
puts "QLDAPM bootstrap configured: private project, 5 members, role workflows, TOTP enforced."

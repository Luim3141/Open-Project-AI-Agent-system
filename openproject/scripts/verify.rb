require "json"
require "csv"
config = JSON.parse(File.read("/private/bootstrap.json"))
rows = CSV.read("/private/wbs-snapshot.csv", headers: true, encoding: "bom|utf-8")
project = Project.find(config.fetch("project_id"))
source_field = WorkPackageCustomField.find_by!(name: "Source ID")
packages = project.work_packages.to_a
raise "Wrong total" unless packages.size == 329
index = packages.to_h { |wp| [wp.custom_values.find { |v| v.custom_field_id == source_field.id }&.value, wp] }
raise "Duplicate/missing source" unless index.size == 329 && !index.key?(nil)
ids = rows.to_h { |row| [row["Issue ID"], row["Source ID"]] }
rows.each do |row|
  wp = index.fetch(row["Source ID"])
  raise "Wrong subject" unless wp.subject == row["Summary"]
  raise "Wrong status" unless wp.status.name == "NEW"
  raise "Wrong assignee" unless wp.assigned_to_id == config["users"].fetch(row["Proposed Assignee Email"].downcase)
  parent = row["Parent"].to_s.empty? ? nil : index.fetch(ids.fetch(row["Parent"])).id
  raise "Wrong hierarchy" unless wp.parent_id == parent
  raise "AC missing" unless wp.description.include?(row["Acceptance Criteria"].to_s)
end
raise "Wrong members" unless project.members.count == 5
raise "Public project" if project.public?
raise "Login required disabled" unless Setting.login_required?
raise "Registration enabled" unless Setting.self_registration == 0
raise "TOTP not enforced" unless OpenProject::TwoFactorAuthentication::TokenStrategyManager.enforced?
raise "Wrong OTP strategies" unless OpenProject::TwoFactorAuthentication::TokenStrategyManager.configuration["active_strategies"] == ["totp"]
raise "Default admin still enabled" unless User.find_by(login: "admin").locked?
raise "Temporary password not forced" unless User.where(login: %w[op-owner pm ba-pm be fe qa]).all?(&:force_password_change)
raise "Started or dated Sprint" unless Sprint.where(project:).count == 5 && Sprint.where(project:).all? { |s| s.in_planning? && s.start_date.nil? && s.finish_date.nil? }
raise "Missing basic board" unless Boards::Grid.where(project:).any? { |b| b.board_type == :free }
board = Boards::Grid.find(config.fetch("board_id"))
raise "Wrong initial board cards" unless board.contained_queries.first!.ordered_work_packages.count == 53
raise "Unexpected enabled types" unless project.project_types.pluck(:type_id).sort == config.fetch("types").values.sort
JSON.parse(File.read("/private/accounts.json")).fetch("users").map { |account| account.fetch("role") }.uniq.each do |name|
  role = ProjectRole.find_by!(name: "QLDAPM #{name}")
  variant = Type.find_by!(name: "Epic").default_variant
  has_epic_acceptance = Workflow.exists?(role:, type_variant: variant, new_status: Status.find_by!(name: "DONE"))
  raise "Unauthorized role can accept Epic" unless has_epic_acceptance == (name == "PM")
end
puts JSON.generate({ result: "PASS", packages: packages.size, counts: packages.group_by { |w| w.type.name }.transform_values(&:size),
  private_project: true, members: 5, default_admin_locked: true, totp_enforced: true, sprints_in_planning: 5,
  workflows_role_scoped: true, parent_assignee_ac_verified: true })

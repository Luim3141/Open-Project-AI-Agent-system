require "json"
require "digest"
require "securerandom"

request = JSON.parse(File.read(ENV.fetch("QLDAPM_REQUEST")))
project = Project.find_by!(identifier: "qldapm-local")
member_ids = project.memberships.where(entity_id: nil).pluck(:user_id)
raise "Project members required" if member_ids.empty?
actor = User.find(request.fetch("actor"))
raise "PM_REQUIRED" unless Qldapm::Rbac.pm?(project, actor, fresh: true)
owner = User.where(admin: true, status: User.statuses[:active]).where.not(id: member_ids).first!
User.current = owner
parameters = request.fetch("parameters")
action = request.fetch("action")
exact = ->(keys) { raise "INVALID_PARAMETERS" unless parameters.keys.sort == keys.sort }
roles = ProjectRole.where(name: %w[PM BA BA-PM BE FE QA].map { |name| "QLDAPM #{name}" })
fingerprint = nil
ActiveRecord::Base.transaction do
WorkPackage.connection.execute("SELECT pg_advisory_xact_lock(817609, #{project.id})")
User.where(id: member_ids).order(:id).lock.load
roles.order(:id).lock.load
Setting.order(:id).lock.load
snapshot = {
  "users" => User.where(id: member_ids).order(:id).pluck(:id, :login, :status, :force_password_change),
  "roles" => roles.order(:id).map { |role| [role.id, role.name, role.permissions.map(&:to_s).sort] },
  "types" => project.project_types.order(:type_id).pluck(:type_id, :variant_id),
  "workflows" => Workflow.where(type_variant_id: project.project_types.pluck(:variant_id)).order(:id).pluck(
    :id, :role_id, :old_status_id, :new_status_id, :type_variant_id, :author, :assignee),
  "fields" => project.work_package_custom_fields.order(:id).pluck(:id, :name, :field_format, :is_required),
  "settings" => {"login_required" => Setting.login_required, "self_registration" => Setting.self_registration,
                 "session_ttl" => Setting.session_ttl, "password_min_length" => Setting.password_min_length,
                 "totp" => Setting.plugin_openproject_two_factor_authentication}
}
fingerprint = Digest::SHA256.hexdigest(JSON.generate(snapshot))
if action == "inspect"
  raise "CONFIGURATION_CHANGED" if ENV["QLDAPM_EXPECTED_CONFIGURATION"] && ENV["QLDAPM_EXPECTED_CONFIGURATION"] != fingerprint
  puts JSON.generate({"configuration" => snapshot, "hash" => fingerprint})
  exit
end
raise "CONFIGURATION_CHANGED" unless request.fetch("before_hash") == fingerprint
  case action
  when "user"
    exact.call(%w[user_id operation])
    raise "USER_OUTSIDE_PROJECT" unless member_ids.include?(Integer(parameters["user_id"]))
    user = User.find(parameters["user_id"])
    case parameters["operation"]
    when "lock" then user.update!(status: :locked)
    when "unlock" then user.update!(status: :active)
    when "reset_password"
      password = "Aa1!" + SecureRandom.urlsafe_base64(32)
      user.update!(password:, password_confirmation: password, force_password_change: true)
      Token::API.where(user:).destroy_all
      File.write("/operator/reset-user-#{user.id}.json", JSON.generate({"user_id" => user.id, "temporary_password" => password}))
    else raise "USER_OPERATION_DENIED"
    end
  when "role"
    exact.call(%w[role_id permissions])
    role = roles.find(parameters["role_id"])
    raise "SHARED_ROLE_DENIED" if MemberRole.where(role:).joins(:member).where.not(members: {project_id: project.id}).exists?
    permissions = parameters.fetch("permissions").map(&:to_sym)
    known = Redmine::AccessControl.permissions.map(&:name)
    raise "UNKNOWN_PERMISSION" unless (permissions - known).empty?
    role.update!(permissions:)
  when "workflow"
    exact.call(%w[type_id edges])
    variant = project.project_types.find_by!(type_id: parameters["type_id"]).variant
    raise "PROJECT_OWNED_VARIANT_REQUIRED" unless variant.project_id == project.id
    require_relative "overlay/app/models/qldapm/gate_policy"
    edges = parameters.fetch("edges")
    policy = Qldapm::GatePolicy.new
    snapshot_item = {"type" => variant.type.name, "data" => {"stream" => "development"}}
    allowed = policy.edges(snapshot_item)
    allowed = allowed.merge(Qldapm::GatePolicy::BUSINESS) { |_, a, b| (a + b).uniq } if variant.type.name == "Subtask"
    edges.each do |edge|
      raise "INVALID_EDGE" unless edge.keys.sort == %w[from role to]
      policy_role = edge["role"] == "BA" ? "BA-PM" : edge["role"]
      raise "EDGE_OUTSIDE_HARD_POLICY" unless allowed.fetch([edge["from"], edge["to"]], []).include?(policy_role)
    end
    Workflow.where(type_variant_id: variant.id).delete_all
    edges.each do |edge|
      Workflow.create!(type_variant: variant, role: roles.find_by!(name: "QLDAPM #{edge['role']}"),
        old_status: Status.find_by!(name: edge["from"]), new_status: Status.find_by!(name: edge["to"]), author: false, assignee: false)
    end
  when "field"
    exact.call(%w[name format required])
    raise "FIELD_NAME_DENIED" unless parameters["name"].match?(/\AQLDAPM [\p{L}\p{N} _-]{1,70}\z/)
    raise "FIELD_FORMAT_DENIED" unless %w[string text bool int float date].include?(parameters["format"])
    field = WorkPackageCustomField.find_or_initialize_by(name: parameters["name"])
    raise "SHARED_FIELD_DENIED" if field.persisted? && field.projects.where.not(id: project.id).exists?
    field.assign_attributes(field_format: parameters["format"], is_required: parameters["required"], is_for_all: false)
    field.save!
    field.projects = [project]
    field.type_variants = project.project_types.map(&:variant)
  when "type"
    exact.call(%w[name])
    raise "TYPE_NAME_DENIED" unless parameters["name"].match?(/\AQLDAPM [\p{L}\p{N} _-]{1,70}\z/)
    type = Type.find_or_create_by!(name: parameters["name"]) { |t| t.color = Color.first! }
    raise "SHARED_TYPE_DENIED" if type.projects.where.not(id: project.id).exists?
    ProjectType.find_or_create_by!(project:, type:)
  when "status"
    exact.call(%w[name closed])
    raise "STATUS_NAME_DENIED" unless parameters["name"].match?(/\AQLDAPM [\p{L}\p{N} _-]{1,70}\z/)
    status = Status.find_or_initialize_by(name: parameters["name"])
    raise "SHARED_STATUS_DENIED" if status.persisted? && WorkPackage.where(status:).where.not(project:).exists?
    status.assign_attributes(color: status.color || Color.first!, is_closed: parameters["closed"], default_done_ratio: 0)
    status.save!
  when "settings"
    exact.call(%w[session_ttl password_min_length])
    ttl, length = Integer(parameters["session_ttl"]), Integer(parameters["password_min_length"])
    raise "SECURITY_DOWNGRADE_DENIED" unless (5..60).cover?(ttl) && (14..128).cover?(length)
    Setting.session_ttl = ttl
    Setting.password_min_length = length
    Setting.login_required = true
    Setting.self_registration = 0
    Setting.plugin_openproject_two_factor_authentication = {"active_strategies" => ["totp"], "enforced" => true, "allow_remember_for_days" => 0}
  when "delete_work_package"
    exact.call(%w[id lock_version])
    work_package = project.work_packages.find(parameters["id"])
    raise "STALE_WORK_PACKAGE" unless work_package.lock_version == parameters["lock_version"]
    raise "DELETE_CHILDREN_FIRST" if work_package.children.exists?
    Thread.current[:qldapm_approved_delete] = work_package.id
    begin
      User.execute_as(actor) { work_package.destroy! }
    ensure
      Thread.current[:qldapm_approved_delete] = nil
    end
  else
    raise "ADMIN_ACTION_DENIED"
  end
end
puts JSON.generate({"operation" => action, "result" => "applied", "requested_by" => actor.id, "before_hash" => fingerprint})

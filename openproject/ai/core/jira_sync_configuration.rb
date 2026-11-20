# Fixed configuration operation for the one-time Jira import.
# No runner/endpoint commits this operation. Caller must supply a transaction
# and separately qualify backup/rehearsal and human-local approval before use.
require "json"
require "digest"

module JiraSyncConfiguration
  class Conflict < StandardError; end

  def self.target(expected)
    raise Conflict, "TARGET_PROJECT_MISMATCH" unless [3, 5].include?(expected)
    project = Project.find_by!(identifier: "qldapm-local")
    raise Conflict, "TARGET_PROJECT_MISMATCH" unless project.id == expected
    roles = ProjectRole.where(name: "QLDAPM PM").to_a
    raise Conflict, "PM_ROLE_AMBIGUOUS" unless roles.size == 1
    role = roles.first
    projects = Member.joins(:roles).where(roles: {id: role.id}).distinct.pluck(:project_id).sort
    raise Conflict, "PM_ROLE_NOT_PROJECT_SCOPED" unless projects == [expected]
    [project, role]
  end

  def self.preview(expected)
    project, role = target(expected)
    activities = TimeEntryActivity.order(:id).map do |row|
      {id: row.id, name: row.name, active: row.active?,
       projects: row.time_entry_activities_projects.order(:project_id, :id).map do |entry|
         {project_id: entry.project_id, active: entry.active?}
       end}
    end
    simulation = activities.select { |row| row[:name] == "Simulation" }
    raise Conflict, "SIMULATION_ACTIVITY_AMBIGUOUS" if simulation.size > 1
    if simulation.any?
      row = simulation.first
      raise Conflict, "SIMULATION_ACTIVITY_NOT_SCOPED" if row[:active] || row[:projects].any? { |p| p[:active] && p[:project_id] != expected }
    end
    before = {project_id: project.id, modules: project.enabled_module_names.sort,
              pm_role_id: role.id, permissions: role.permissions.map(&:to_s).sort,
              activities: activities}
    desired = {modules: (before[:modules] + ["costs"]).uniq.sort,
               permissions: (before[:permissions] + %w[view_time_entries log_time]).uniq.sort,
               activity: {name: "Simulation", active: false, active_only_project_id: expected}}
    result = {operation: "jira_sync_simulation_time_tracking", before: before, desired: desired,
              unchanged: %w[users_password_totp_tokens other_roles workflows gates Jira Gemini],
              human_local_approval_required: true, mutation_performed: false}
    result.merge(hash: Digest::SHA256.hexdigest(JSON.generate(result)))
  end

  def self.apply_in_transaction!(expected, approved_hash)
    raise Conflict, "TRANSACTION_REQUIRED" unless Project.connection.transaction_open?
    project, role = target(expected)
    project.lock!
    role.lock!
    TimeEntryActivity.order(:id).lock.load
    TimeEntryActivitiesProject.order(:id).lock.load
    current = preview(expected)
    raise Conflict, "CONFIGURATION_CONFLICT" unless approved_hash == current[:hash]
    desired = current[:desired]
    unless project.enabled_module_names.sort == desired[:modules]
      project.enabled_module_names = desired[:modules]
      project.save!
    end
    unless role.permissions.map(&:to_s).sort == desired[:permissions]
      role.permissions = desired[:permissions]
      role.save!
    end
    activity = TimeEntryActivity.find_by(name: "Simulation") || TimeEntryActivity.create!(name: "Simulation", active: false)
    setting = TimeEntryActivitiesProject.find_or_initialize_by(project_id: expected, activity_id: activity.id)
    setting.active = true
    setting.save! if setting.new_record? || setting.changed?
    after = preview(expected)
    raise Conflict, "CONFIGURATION_READBACK_FAILED" unless after[:before][:modules] == desired[:modules] && after[:before][:permissions] == desired[:permissions] && activity.reload.active_in_project?(project.reload)
    after
  end
end

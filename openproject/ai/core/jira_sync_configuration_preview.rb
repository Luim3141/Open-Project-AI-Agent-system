# Fixed read-only configuration preview; no approval or mutation here.
require "json"
require "digest"
project = Project.find_by!(identifier: "qldapm-local")
expected = Integer(ENV.fetch("QLDAPM_SYNC_PROJECT_ID"))
raise "TARGET_PROJECT_MISMATCH" unless [3, 5].include?(expected) && project.id == expected
role = ProjectRole.find_by!(name: "QLDAPM PM")
role_projects = Member.joins(:roles).where(roles: {id: role.id}).distinct.pluck(:project_id).sort
raise "PM_ROLE_NOT_PROJECT_SCOPED" unless role_projects == [project.id]
before = {project_id: project.id, modules: project.enabled_module_names.sort,
          pm_role_id: role.id, permissions: role.permissions.map(&:to_s).sort,
          activities: TimeEntryActivity.order(:id).map { |row| {id: row.id, name: row.name, active: row.active?} }}
desired = {modules: (before[:modules] + ["costs"]).uniq.sort,
           permissions: (before[:permissions] + %w[view_time_entries log_time]).uniq.sort,
           activity: {name: "Simulation", active: false, active_only_project_id: project.id}}
preview = {operation: "jira_sync_simulation_time_tracking", before:, desired:,
           unchanged: %w[users_password_totp_tokens_roles_except_PM_worklog_permissions workflows gates Jira Gemini],
           human_local_approval_required: true, mutation_performed: false}
puts JSON.generate(preview.merge(hash: Digest::SHA256.hexdigest(JSON.generate(preview))))

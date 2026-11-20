# Fixed synthetic staging regression; no committed configuration changes.
require "json"
require "digest"
expected = Integer(ENV.fetch("QLDAPM_SYNC_PROJECT_ID", "3"))
raise "SCOPED_REHEARSAL_ONLY" unless [3, 5].include?(expected) && Project.find_by(identifier: "qldapm-local")&.id == expected &&
  (expected == 3 || ENV["QLDAPM_TEST_ONLY"] == "true")
load File.join(__dir__, "jira_sync_configuration.rb")
project = Project.find(expected)
before = JiraSyncConfiguration.preview(expected)
source_before = Digest::SHA256.hexdigest(JSON.generate(project.work_packages.order(:id).map(&:attributes)))
users_before = Digest::SHA256.hexdigest(JSON.generate(User.order(:id).map(&:attributes)))
other_roles = ProjectRole.where.not(id: before[:before][:pm_role_id]).order(:id).map(&:attributes)
user = User.find(expected == 3 ? 7 : 19)
raise "NON_ADMIN_PM_REQUIRED" if user.admin?
User.current = user
begin
  JiraSyncConfiguration.apply_in_transaction!(expected, before[:hash])
  raise "UNSCOPED_TRANSACTION_ACCEPTED"
rescue JiraSyncConfiguration::Conflict => error
  raise unless error.message == "TRANSACTION_REQUIRED"
end
begin
  Project.transaction do
    begin
      JiraSyncConfiguration.apply_in_transaction!(expected, "0" * 64)
      raise "STALE_HASH_ACCEPTED"
    rescue JiraSyncConfiguration::Conflict
      # A stale approval must never cause even a partial configuration write.
    end
    raise "STALE_HASH_MUTATED" unless JiraSyncConfiguration.preview(expected) == before
    JiraSyncConfiguration.apply_in_transaction!(expected, before[:hash])
    after = JiraSyncConfiguration.preview(expected)
    raise "MODULE_MISSING" unless project.reload.enabled_module_names.include?("costs")
    added = after[:before][:permissions] - before[:before][:permissions]
    raise "EXCESS_PERMISSION" unless added.sort == %w[log_time view_time_entries]
    activity = TimeEntryActivity.find_by!(name: "Simulation")
    raise "GLOBAL_ACTIVITY_ENABLED" if activity.active?
    raise "PROJECT_ACTIVITY_DISABLED" unless activity.active_in_project?(project)
    raise "OTHER_PROJECT_ACTIVITY_ENABLED" if Project.where.not(id: expected).any? { |p| activity.active_in_project?(p) }
    user = User.find(user.id) # Fresh permission cache after the temporary grant.
    item = project.work_packages.first!
    entry = TimeEntry.new(project: project.reload, entity: item, user: user, activity: activity,
                          hours: 0.25, spent_on: Date.current,
                          comments: "SIMULATION fixture; Jira source author/date are documentary, not real labor.")
    contract = TimeEntries::CreateContract.new(entry, user)
    raise "NATIVE_TIME_ENTRY_CONTRACT_DENIED:#{contract.errors.full_messages.join(';')}" unless contract.validate
    raise "TIME_ENTRY_DELETE_PERMISSION_GRANTED" if user.allowed_in_project?(:edit_time_entries, project)
    JiraSyncConfiguration.apply_in_transaction!(expected, after[:hash])
    raise "REPLAY_MUTATED" unless JiraSyncConfiguration.preview(expected) == after
    Project.transaction(requires_new: true) do
      activity.update!(active: true)
      begin
        JiraSyncConfiguration.preview(expected)
        raise "GLOBAL_SIMULATION_ACCEPTED"
      rescue JiraSyncConfiguration::Conflict => error
        raise unless error.message == "SIMULATION_ACTIVITY_NOT_SCOPED"
      end
      raise ActiveRecord::Rollback
    end
    raise "OTHER_ROLE_MUTATED" unless ProjectRole.where.not(id: before[:before][:pm_role_id]).order(:id).map(&:attributes) == other_roles
    raise ActiveRecord::Rollback
  end
ensure
  raise "ROLLBACK_FAILED" unless JiraSyncConfiguration.preview(expected) == before
  raise "SOURCE_MUTATED" unless Digest::SHA256.hexdigest(JSON.generate(project.work_packages.order(:id).map(&:attributes))) == source_before
  raise "USER_MUTATED" unless Digest::SHA256.hexdigest(JSON.generate(User.order(:id).map(&:attributes))) == users_before
end
puts "Jira sync configuration PASS: stale/replay/permissions/project isolation/rollback; no persistent mutation."

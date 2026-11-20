# Run only on synthetic staging; all changes are rolled back.
require "json"
load "/qldapm-core/overlay/app/services/qldapm/insights.rb" if ENV["QLDAPM_SYNC_SOURCE_TEST"] == "true"
raise "STAGING_ONLY" unless Project.find_by(identifier: "qldapm-local")&.id == 3
project = Project.find(3)
user = User.find_by!(login: "pm")
User.current = user
WorkPackage.transaction do
  item = project.work_packages.joins(:type).where(types: {name: "Subtask"}).first!
  result = WorkPackages::UpdateService.new(user:, model: item).call(
    description: "> JIRA IMPORT — SIMULATION ONLY. Synthetic fixture.\n\n#{item.description}")
  raise result.errors.full_messages.join(";") unless result.success?
  report = Qldapm::Insights.new(project, user).report(user.id, 90)
  raise "SIMULATED_IMPORT_INCLUDED_IN_PERFORMANCE" if report.fetch("events").any? { |row| row["work_package_id"] == item.id }
  raise ActiveRecord::Rollback
end
puts "Jira sync Insights simulation exclusion PASS; transaction rolled back."

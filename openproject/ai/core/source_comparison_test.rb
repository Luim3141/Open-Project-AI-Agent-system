raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
item = project.work_packages.first!
original = item.attributes
ENV.delete("QLDAPM_COMPARE_SOURCE")
ENV.delete("VERIFY_BACKUP")
load "/qldapm/backup_state.rb"
ENV["QLDAPM_COMPARE_SOURCE"] = "true"
ActiveRecord::Base.transaction do
  WorkPackage.connection.execute("SELECT pg_advisory_xact_lock(817609, #{project.id})")
  item.update_columns(qldapm_gate: item.qldapm_gate.merge("synthetic_migration_probe" => true))
  ENV["VERIFY_BACKUP"] = "true"
  load "/qldapm/backup_state.rb"
  item.update_columns(subject: "Synthetic source change must be detected")
  begin
    load "/qldapm/backup_state.rb"
    raise "SOURCE_CHANGE_UNDETECTED"
  rescue RuntimeError => error
    raise unless error.message.include?("Restored database differs: work_packages")
  end
  raise ActiveRecord::Rollback
end
raise "SOURCE_TEST_MUTATED_STAGE" unless item.reload.attributes == original && project.work_packages.count == 329
puts "Source comparison PASS: gate-only migration allowed, source mutation detected, transaction rolled back."

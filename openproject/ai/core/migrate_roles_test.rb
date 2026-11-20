require "digest"
raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
role = project.members.includes(:roles).flat_map(&:roles).uniq.find { |item| item.name == "QLDAPM BA-PM" }
raise "LEGACY_STAGING_ROLE_REQUIRED" unless role
before = Digest::SHA256.hexdigest(WorkPackage.where(project:).order(:id).map(&:attributes).to_json)
original_name = role.name
ActiveRecord::Base.transaction do
  role.update!(name: "QLDAPM BA")
  load File.join(__dir__, "migrate_snapshot.rb")
  foreign = ProjectRole.create!(name: "QLDAPM BA-PM", permissions: role.permissions)
  variants = project.project_types.filter_map { |item| item.variant if item.variant&.variant_name == "QLDAPM gated" }
  raise "SCOPED_VARIANTS_REQUIRED" unless variants.size == 3 && variants.all? { |item| item.project_id == project.id }
  Workflow.where(type_variant_id: variants.map(&:id)).delete_all
  load File.join(__dir__, "migrate_snapshot.rb")
  raise "RENAMED_BA_WORKFLOW_MISSING" unless Workflow.where(type_variant_id: variants.map(&:id), role_id: role.id).exists?
  raise "FOREIGN_ROLE_USED" if Workflow.where(type_variant_id: variants.map(&:id), role_id: foreign.id).exists?
  member = project.members.includes(:roles).find { |item| item.roles.any? { |assigned| assigned.name == "QLDAPM BE" } }
  member.roles = member.roles.to_a + [foreign]
  begin
    load File.join(__dir__, "migrate_snapshot.rb")
    raise "AMBIGUOUS_BA_ROLES_ACCEPTED"
  rescue RuntimeError => error
    raise unless error.message == "MIGRATION_ROLE_MISSING_OR_AMBIGUOUS: BA-PM"
  end
  raise "MIGRATION_CHANGED_SOURCE" unless before == Digest::SHA256.hexdigest(WorkPackage.where(project:).order(:id).map(&:attributes).to_json)
  raise ActiveRecord::Rollback
end
raise "ROLE_RENAME_NOT_ROLLED_BACK" unless role.reload.name == original_name
raise "SOURCE_ROLLBACK_CHANGED" unless before == Digest::SHA256.hexdigest(WorkPackage.where(project:).order(:id).map(&:attributes).to_json)
puts "Renamed BA migration, foreign-role isolation and ambiguous-alias denial PASS; all changes rolled back."

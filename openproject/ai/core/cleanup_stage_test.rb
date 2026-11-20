raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
field = WorkPackageCustomField.find_by!(name: "Source ID")
items = project.work_packages.joins(:custom_values).where(custom_values: {custom_field_id: field.id})
  .where("custom_values.value LIKE ?", "AI-TEST-%")
User.execute_as(User.find_by!(login: "stage-owner")) do
  items.find_each do |item|
    raise "FIXTURE_HAS_CHILDREN" if item.children.exists?
    Qldapm::MutationReceipt.where(work_package_id: item.id).delete_all if defined?(Qldapm::MutationReceipt)
    Thread.current[:qldapm_approved_delete] = item.id
    item.destroy!
  ensure
    Thread.current[:qldapm_approved_delete] = nil
  end
end
raise "COUNT_MISMATCH" unless project.work_packages.count == 329
puts "Synthetic fixtures removed; 329 source work packages retained."

require "digest"
raise "UUID_FIXTURE_REQUIRED" unless ENV.fetch("QLDAPM_PAIR_PROJECT", "").match?(/\Aqldapm-pair-test-[a-f0-9-]{36}\z/)
raise "SYNTHETIC_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
raise "SOURCE329_REQUIRED" unless project.work_packages.count == 329 && project.members.count == 5
before = Digest::SHA256.hexdigest(project.work_packages.order(:id).map(&:attributes).to_json)
ActiveRecord::Base.transaction do
  roles = project.members.includes(:roles).flat_map(&:roles).uniq.select { |role| ["QLDAPM BA", "QLDAPM BA-PM"].include?(role.name) }
  raise "ONE_BA_ROLE_REQUIRED" unless roles.one?
  roles.first.update!(name: "QLDAPM BA")
  project.project_types.each do |entry|
    next unless %w[Epic Task Subtask].include?(entry.type.name)
    variant = entry.variant
    raise "SCOPED_VARIANT_REQUIRED" unless variant.project_id == project.id && variant.variant_name == "QLDAPM gated"
    entry.update!(variant: entry.type.default_variant)
    Workflow.where(type_variant_id: variant.id).delete_all
  end
  raise "SOURCE_CHANGED" unless before == Digest::SHA256.hexdigest(project.work_packages.order(:id).map(&:attributes).to_json)
end
puts "UUID-only official-origin fixture: BA role and legacy default workflows prepared; source329 unchanged."

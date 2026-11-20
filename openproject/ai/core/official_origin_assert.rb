require "csv"
raise "UUID_FIXTURE_REQUIRED" unless ENV.fetch("QLDAPM_PAIR_PROJECT", "").match?(/\Aqldapm-pair-test-[a-f0-9-]{36}\z/)
raise "SYNTHETIC_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
connection = ActiveRecord::Base.connection
raise "CANDIDATE_SCHEMA_PRESENT" if WorkPackage.column_names.include?("qldapm_gate") ||
  %w[qldapm_insight_snapshots qldapm_insight_responses qldapm_mutation_receipts].any? { |table| connection.data_source_exists?(table) }
raise "CANDIDATE_MODELS_PRESENT" if defined?(QldapmGateWrite)
field = WorkPackageCustomField.find_by!(name: "Source ID")
rows = CSV.read("/private/wbs-snapshot.csv", headers: true, encoding: "bom|utf-8")
items = project.work_packages.includes(:custom_values).to_a
ids = items.map { |item| item.custom_values.find { |value| value.custom_field_id == field.id }&.value }
raise "SOURCE_IDS_CHANGED" unless items.size == 329 && ids.uniq.size == 329 && ids.sort == rows.map { |row| row["Source ID"] }.sort
raise "BA_ROLE_REQUIRED" unless project.members.includes(:roles).flat_map(&:roles).any? { |role| role.name == "QLDAPM BA" }
subtask = project.enabled_types.find_by!(name: "Subtask")
raise "LEGACY_VARIANT_REQUIRED" unless project.project_types.find_by!(type: subtask).variant_id == subtask.default_variant.id
statuses = Workflow.where(type_variant_id: subtask.default_variant.id).includes(:old_status, :new_status).flat_map { |edge| [edge.old_status.name, edge.new_status.name] }.uniq.sort
raise "LEGACY_FOUR_STATUS_REQUIRED" unless statuses == ["DONE", "IN PROGRESS", "NEW", "REVIEW"]
puts "Official image/schema PASS: source329, BA role, legacy4states, no candidate models/gate/AI tables."

# Compare the backup's actual state, not the initial NEW-only WBS after the team starts work.
require "json"
require "digest"
models = [Project, User, UserPassword, Token::API, Member, MemberRole, ProjectRole, RolePermission, WorkPackage, CustomField,
          CustomOption, CustomValue, Type, TypeVariant, ProjectType, Workflow, Status,
          EnabledModule, Sprint, Query, OrderedWorkPackage, Boards::Grid, Grids::Widget,
          Attachment, Setting, TwoFactorAuthentication::Device]
connection = ActiveRecord::Base.connection
tables = models.map(&:table_name) + %w[custom_fields_projects custom_fields_types]
tables += %w[journals work_package_journals]
ai_tables = %w[qldapm_insight_snapshots qldapm_insight_responses qldapm_mutation_receipts]
tables += ai_tables.select { |name| connection.data_source_exists?(name) }
state = tables.uniq.sort.to_h do |table|
  columns = connection.columns(table).map(&:name)
  order = columns.include?("id") ? "id" : columns.map { |c| connection.quote_column_name(c) }.join(",")
  rows = connection.select_all("SELECT * FROM #{connection.quote_table_name(table)} ORDER BY #{order}").to_a
  fingerprint = { "rows" => rows.size, "sha256" => Digest::SHA256.hexdigest(JSON.generate(rows)) }
  if table == WorkPackage.table_name
    fingerprint["source_sha256"] = Digest::SHA256.hexdigest(JSON.generate(rows.map { |row| row.except("qldapm_gate") }))
  end
  [table, fingerprint]
end
path = "/backup/database-state.json"
if ENV["VERIFY_BACKUP"] == "true"
  expected = JSON.parse(File.read(path))
  differences = (expected.keys | state.keys).reject do |key|
    before, after = expected[key], state[key]
    if ENV["QLDAPM_COMPARE_SOURCE"] == "true" && key == WorkPackage.table_name && before && after
      before["rows"] == after["rows"] && (before["source_sha256"] || before["sha256"]) == after["source_sha256"]
    elsif ENV["QLDAPM_COMPARE_SOURCE"] == "true" && ai_tables.include?(key) && !before
      after && after["rows"].zero?
    else
      before && after && before.slice("rows", "sha256") == after.slice("rows", "sha256")
    end
  end
  differences -= [TypeVariant.table_name, ProjectType.table_name, Workflow.table_name] if ENV["QLDAPM_COMPARE_SOURCE"] == "true"
  raise "Restored database differs: #{differences.join(', ')}" if differences.any?
  puts "Restored database snapshot PASS: #{state.size} tables, including passwords/TOTP, hierarchy, workflow and board."
else
  File.write(path, JSON.pretty_generate(state))
  puts "Database verification fingerprint captured for #{state.size} tables."
end

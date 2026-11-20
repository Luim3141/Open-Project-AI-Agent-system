require "csv"
require "digest"
require "json"
project = Project.find_by!(identifier: "qldapm-local")
source_field = WorkPackageCustomField.find_by!(name: "Source ID")
rows = CSV.read("/private/wbs-snapshot.csv", headers: true, encoding: "bom|utf-8")
raise "Snapshot count mismatch" unless rows.length == 329
WorkPackage.transaction do
  WorkPackage.connection.execute("SELECT pg_advisory_xact_lock(817609, #{project.id})")
  packages = WorkPackage.where(project:).includes(:status, :type).to_a
  source_map = packages.to_h { |wp| [wp.custom_values.detect { |value| value.custom_field_id == source_field.id }&.value, wp] }
  raise "Duplicate/missing work packages" unless packages.length == 329 && source_map.length == 329
  project_roles = project.members.includes(:roles).flat_map(&:roles).uniq.select { |role| role.name.start_with?("QLDAPM ") }
  roles = %w[PM BA-PM BE FE QA].to_h do |name|
    candidates = project_roles.select { |role| Qldapm::GatePolicy.actor_role([role.name.delete_prefix("QLDAPM ")]) == name }
    raise "MIGRATION_ROLE_MISSING_OR_AMBIGUOUS: #{name}" unless candidates.one?
    [name, candidates.first]
  end
  original = packages.to_h { |wp| [wp.id, wp.attributes.except("qldapm_gate")] }
  rows.each do |row|
    wp = source_map.fetch(row["Source ID"])
    next if wp.qldapm_gate["source_id"] == row["Source ID"]
    role = wp.assigned_to.is_a?(User) ? wp.qldapm_actor(wp.assigned_to)["role"] : nil
    checklist = wp.qldapm_gate.fetch("checklist", [])
    checklist = row["Checklist"].to_s.lines.map(&:strip).reject(&:empty?).each_with_index.map { |text, index|
      {"id" => Digest::SHA256.hexdigest("#{row['Source ID']}:#{index}")[0, 16], "text" => text, "done" => false}
    } if checklist.empty?
    data = wp.qldapm_gate.merge({"revision" => 0, "source_id" => row["Source ID"], "acceptance_criteria" => row["Acceptance Criteria"].to_s,
      "checklist" => checklist,
      "evidence" => {}, "approvals" => {}, "contributors" => [], "stream" => %w[BE FE].include?(role) ? "development" : "business",
      "kind" => role == "QA" ? "qa" : "work"})
    # Trusted migration only: preserve status, hierarchy, assignee, timestamps and lock versions byte-for-byte.
    WorkPackage.where(id: wp.id).update_all(qldapm_gate: data, lock_version: wp.lock_version)
  end
  types = %w[Epic Task Subtask].to_h { |name| [name, project.enabled_types.find_by!(name:)] }
  edges = {"Epic" => Qldapm::GatePolicy::EPIC, "Task" => Qldapm::GatePolicy::TASK,
           "Subtask" => Qldapm::GatePolicy::BUSINESS.merge(Qldapm::GatePolicy::DEVELOPMENT) { |_, a, b| (a + b).uniq }}
  types.each do |name, type|
    variant = TypeVariant.find_or_initialize_by(type:, project:, variant_name: "QLDAPM gated")
    if variant.new_record?
      variant.assign_attributes(is_default_variant: false, enabled_in_new_projects: false)
      (TypeVariant::ASPECTS - ["workflows"]).each { |aspect| variant.public_send("#{aspect}_source_id=", type.default_variant.id) }
      variant.save!
      variant.custom_fields = type.default_variant.custom_fields
    end
    project.project_types.find_by!(type:).update!(variant:)
    next if Workflow.where(type_variant_id: variant.id).exists?
    Workflow.where(type_variant_id: variant.id).delete_all
    edges.fetch(name).each do |(from, to), names|
      names.each do |role|
        Workflow.create!(type_variant: variant, role: roles.fetch(role),
          old_status: Status.find_by!(name: from), new_status: Status.find_by!(name: to), author: false, assignee: false)
      end
    end
  end
  packages.each do |wp|
    wp.reload
    changed = wp.attributes.except("qldapm_gate").keys.select { |key| wp[key] != original.fetch(wp.id)[key] }
    raise "Migration altered work package #{wp.id} columns: #{changed.join(',')}" if changed.any?
  end
end
puts "gate migration: 329 work packages unchanged; structured checklist unchecked; Subtask 7 states"

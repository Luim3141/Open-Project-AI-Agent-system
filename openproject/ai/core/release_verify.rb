require "csv"
project = Project.find_by!(identifier: "qldapm-local")
rows = CSV.read("/private/wbs-snapshot.csv", headers: true, encoding: "bom|utf-8")
items = project.work_packages.includes(:type).to_a
raise "SOURCE_COUNT_CHANGED" unless items.size == rows.size && items.size == 329
mapping = items.to_h { |item| [item.qldapm_gate["source_id"], item] }
raise "SOURCE_IDS_CHANGED" unless mapping.size == 329 && mapping.keys.sort == rows.map { |row| row["Source ID"] }.sort
count = rows.sum do |row|
  item = mapping.fetch(row["Source ID"])
  raise "MIGRATED_AC_CHANGED" unless item.qldapm_gate["acceptance_criteria"] == row["Acceptance Criteria"].to_s
  raise "GATE_NOT_INSTALLED" unless item.class.included_modules.include?(QldapmGateWrite)
  row["Issue Type"] == "Task" ? item.qldapm_gate["acceptance_criteria"].lines.count { |line| !line.strip.empty? } : 0
end
raise "AC_COUNT_CHANGED" unless count == 106
puts "Release migration PASS: 329 Source IDs, 106 AC, native guard installed."

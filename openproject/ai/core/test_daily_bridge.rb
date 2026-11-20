# Actual staged Rails signing/HTTP bridge; no browser login or native business mutation.
project = Project.find_by!(identifier: "qldapm-local")
roles = {6 => "BA-PM", 7 => "PM", 8 => "BE", 9 => "FE", 10 => "QA"}
records = roles.map do |id, role|
  actor = User.find(id)
  summary = Qldapm::AiBridge.call(project, actor, "command", {action: "analyze", arguments: {}}).fetch("result")
  brief = summary.fetch("daily_brief")
  raise "OWN_DAILY_NOT_READY" unless brief["state"] == "READY" && brief.dig("snapshot", "count") == summary["count"]
  raise "DAILY_PERSONNEL_EXPOSED" if brief.fetch("snapshot").key?("by_assignee")
  permissions = Qldapm::AiBridge.call(project, actor, "command", {action: "get_permissions", arguments: {}}).fetch("result")
  write = permissions.fetch("tools").find { |tool| tool["name"] == "update_work_package" }.fetch("allowed")
  raise "PM_ONLY_WRITE_CHANGED" unless write == (role == "PM")
  {actor: id, role:, own_daily_ready: true, count: summary["count"], pm_only_write_preserved: true}
end
puts "P04_DAILY_BRIDGE=" + JSON.generate({passed: true, roles: records, actual_rails_signing_http: true,
  native_business_mutations: 0, browser_login_claimed: false})

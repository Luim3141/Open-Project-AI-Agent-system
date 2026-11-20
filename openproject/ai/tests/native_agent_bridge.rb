# Staging read-only probe through the actual Rails signing/HTTP bridge, not a simulated browser login.
project = Project.find_by!(identifier: "qldapm-local")
roles = {6 => "BA-PM", 7 => "PM", 8 => "BE", 9 => "FE", 10 => "QA"}
records = roles.map do |actor_id, expected_role|
  actor = User.find(actor_id)
  identity = Qldapm::AiBridge.call(project, actor, "command", {action: "identity", arguments: {}}).fetch("result")
  raise "IDENTITY_OR_ROLE_CHANGED" unless identity.values_at("user_id", "project_id", "role") == [actor_id, project.id, expected_role]
  page = Qldapm::AiBridge.call(project, actor, "command", {action: "list_agent_runs", arguments: {limit: 1}}).fetch("result")
  raise "UNEXPECTED_PRIMARY_AGENT_TASKS" unless page.fetch("total") == 0
  permissions = Qldapm::AiBridge.call(project, actor, "command", {action: "get_permissions", arguments: {}}).fetch("result")
  update = permissions.fetch("tools").find { |tool| tool.fetch("name") == "update_work_package" }.fetch("allowed")
  raise "PM_ONLY_WRITE_CEILING_CHANGED" unless update == (expected_role == "PM")
  %w[list_agent_runs get_agent_run get_agent_trace].each do |name|
    raise "READ_TOOL_NOT_AVAILABLE" unless permissions.fetch("tools").any? { |tool| tool["name"] == name && tool["allowed"] }
  end
  {actor: actor_id, role: expected_role, native_signed_bridge_read: true, own_empty_task_page: true, pm_only_write_preserved: true}
end
puts "P03_NATIVE_BRIDGE_READ=" + JSON.generate({passed: true, users: records,
  actual_core_signing_and_http: true, synthetic_browser_login_claimed: false,
  commands: %w[identity list_agent_runs get_permissions], native_business_mutations: 0})

require ENV.fetch("QLDAPM_POLICY", File.expand_path("overlay/app/models/qldapm/gate_policy", __dir__))
def assert(value, message)
  raise message unless value
end
policy = Qldapm::GatePolicy.new
assert(Qldapm::GatePolicy.actor_role(["BA"]) == "BA-PM", "BA must use only the historical BA policy")
assert(Qldapm::GatePolicy.actor_role(["BA", "PM"]) == "PM", "effective project PM role must be recognized")
assert(Qldapm::GatePolicy.actor_role(["BA", "BA-PM"]) == "BA-PM", "BA aliases must not elevate")
actor = {"id" => 1, "role" => "PM"}
epic = {"type" => "Epic", "assignee" => 2, "data" => {}, "children" => []}
errors = policy.errors(epic, actor, "IN PROGRESS", "REVIEW")
assert(errors.include?("CHILDREN_REQUIRED"), "empty Epic must not enter REVIEW")
puts "gate-policy: empty Epic rejected"
dev = {"type" => "Subtask", "assignee" => 2, "children" => [], "data" => {
  "stream" => "development", "revision" => 0, "reviewer_id" => 1, "contributors" => [2]}}
assert(policy.errors(dev, {"id" => 2, "role" => "BE"}, "IN PROGRESS", "REVIEW").include?("TRANSITION_DENIED"),
       "development cannot bypass review and test")
assert(!policy.can_approve?(dev, {"id" => 2, "role" => "BE"}, "code"), "assignee cannot approve own work")
assert(policy.can_approve?(dev, actor, "code"), "independent designated PM can review")
assert(policy.errors(dev, {"id" => 3, "role" => "PM"}, "CODE REVIEW", "IN PROGRESS").include?("REVIEWER_ONLY"),
       "another developer cannot reject without reviewer assignment")
puts "gate-policy: branch, self-approval and reviewer rules enforced"

task = {"type" => "Task", "assignee" => 2, "data" => {"revision" => 0,
  "evidence" => {"story" => [{"actor_id" => 2, "revision" => 0, "reference" => "story:synthetic"}]}}, "children" => []}
analysis = policy.errors(task, actor, "NEW", "IN ANALYSIS")
assert(analysis.include?("AC_REQUIRED") && analysis.include?("APPROVAL_SCOPE_REQUIRED"),
       "analysis requires AC and approved scope, not only a story reference")
submitted = {"type" => "Subtask", "assignee" => 2, "data" => {"stream" => "development", "revision" => 0,
  "checklist" => [{"done" => true, "reference" => "test:valid", "revision" => 0}],
  "evidence" => {"implementation" => [{"actor_id" => 2, "revision" => 0, "reference" => "commit:valid"}]}}, "children" => []}
assert(policy.errors(submitted, {"id" => 2, "role" => "PM"}, "IN PROGRESS", "CODE REVIEW").include?("REVIEWER_REQUIRED"),
       "cannot submit development work without an independent reviewer")
reopen = {"type" => "Epic", "assignee" => 2, "data" => {"revision" => 0, "transition_reason" => {
  "from" => "DONE", "to" => "IN PROGRESS", "text" => "Needs further changes", "actor_id" => 1, "revision" => 0}}, "children" => []}
assert(policy.errors(reopen, actor, "DONE", "IN PROGRESS").include?("CHANGE_EVIDENCE_REQUIRED"),
       "reopen requires evidence as well as a reason")
failed_test = {"revision" => 0, "evidence" => {"test" => [
  {"actor_id" => 3, "revision" => 0, "reference" => "test:old-passed", "result" => "passed"},
  {"actor_id" => 3, "revision" => 0, "reference" => "test:latest-failed", "result" => "failed"}]}}
assert(!policy.evidence?(failed_test, "test"), "a newer failed test cannot be hidden by an older passing result")

total = 0
[["Epic", nil], ["Task", nil], ["Subtask", "development"], ["Subtask", "business"]].each do |type, stream|
  data = {"stream" => stream, "kind" => "work", "revision" => 0, "acceptance_criteria" => "Synthetic AC",
    "reviewer_id" => 1, "contributors" => [2], "checklist" => [{"done" => true, "reference" => "test:valid", "revision" => 0}],
    "evidence" => {}, "approvals" => {}}
  %w[story scope analysis implementation test_cases test_build test retest retest_not_needed completion bug integration handover deployment smoke].each do |key|
    data["evidence"][key] = [{"actor_id" => 1, "revision" => 0, "reference" => "test:valid", "result" => "passed", "environment" => "Test"}]
  end
  policy.class::APPROVERS.each_key { |key| data["approvals"][key] = {"actor_id" => 1, "revision" => 0, "reference" => "test:valid"} }
  item = {"type" => type, "assignee" => 2, "data" => data,
    "children" => [{"type" => type == "Epic" ? "Task" : "Subtask", "status" => "DONE", "stream" => "development", "kind" => "qa"}], "blocking_bugs" => []}
  policy.edges(item).each do |(from, to), roles|
    selected = {"id" => 1, "role" => roles.include?("PM") ? "PM" : roles.first}
    data["transition_reason"] = {"from" => from, "to" => to, "text" => "test:reason", "reference" => "test:evidence", "actor_id" => 1, "revision" => 0}
    item["blocking_bugs"] = from == "IN TESTING" && to == "IN PROGRESS" ? [{"status" => "IN PROGRESS"}] : []
    failures = policy.errors(item, selected, from, to)
    assert(failures.empty?, "valid #{type}/#{stream} #{from}->#{to}: #{failures}")
    assert(policy.errors(item, {"id" => 3, "role" => "outsider"}, from, to) == ["TRANSITION_DENIED"], "wrong role must fail")
    %w[BA-PM BE FE QA].each { |role| assert(policy.errors(item, {"id" => 3, "role" => role}, from, to) == ["TRANSITION_DENIED"], "non-PM must fail every edge") }
    total += 1
  end
end
puts "gate-policy: #{total} valid edges and #{total} wrong-role edges passed"

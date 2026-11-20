require "json"
require "digest"

raise "STAGING_ONLY" unless ENV["QLDAPM_TEST_ONLY"] == "true" && User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
users = project.members.includes(:roles).to_h { |member| [member.roles.first.name.delete_prefix("QLDAPM "), member.principal] }
raise "MEMBERS_MISMATCH" unless users.keys.sort == %w[BA-PM BE FE PM QA].sort
checks = []
assert = ->(condition, label) { raise "FAILED: #{label}" unless condition; checks << label }
baseline = WorkPackage.where(project:).order(:id).pluck(:id, :subject, :description, :parent_id, :assigned_to_id, :status_id, :lock_version, :qldapm_gate)
WorkPackage.transaction do
  item = project.work_packages.joins(:type).find_by!(types: {name: "Subtask"}, assigned_to_id: users.fetch("BE").id)
  pm, be = users.values_at("PM", "BE")
  assert.call(item.qldapm_gate["stream"] == "development", "migration uses stable development branch")
  item.define_singleton_method(:qldapm_validate_write) do
    locked = WorkPackage.connection.select_value("SELECT COUNT(*) FROM pg_locks WHERE locktype='advisory' AND pid=pg_backend_pid() AND classid=817609 AND objid=#{project_id}")
    assert.call(locked.to_i > 0, "project lock held before gate validation")
    super()
  end
  User.execute_as(be) do
    result = WorkPackages::UpdateService.new(user: be, model: item).call(status_id: Status.find_by!(name: "DONE").id)
    assert.call(!result.success? && item.reload.status.name == "NEW", "native update service rejects shortcut before commit")
    item.status = Status.find_by!(name: "DONE")
    assert.call(!item.save(validate: false) && item.reload.status.name == "NEW", "dependent save(validate:false) cannot bypass gate")
    items = project.work_packages.joins(:type).where(types: {name: "Subtask"}, assigned_to_id: be.id).limit(2).to_a
    bulk = WorkPackages::Bulk::UpdateService.new(user: be, work_packages: items).call(status_id: Status.find_by!(name: "DONE").id)
    assert.call(!bulk.success? && items.all? { |child| child.reload.status.name == "NEW" }, "native bulk update cannot bypass gate")
  end
  actions = ->(user, operation, value) { Qldapm::GateActions.new(item.reload, user).call(operation, value, item.lock_version) }
  reviewer = users.fetch("FE")
  actions.call(pm, "reviewer", {"user_id" => reviewer.id})
  actions.call(be, "evidence", {"key" => "implementation", "reference" => "commit:synthetic-test-only"})
  begin
    actions.call(be, "approve", {"key" => "code", "reference" => "review:my-own-work"})
    raise "SELF_APPROVAL_ACCEPTED"
  rescue ArgumentError => error
    assert.call(error.message.include?("SELF_APPROVAL"), "self approval denied")
  end
  actions.call(reviewer, "approve", {"key" => "code", "reference" => "review:synthetic-only"})
  assert.call(item.reload.qldapm_gate.dig("approvals", "code", "actor_id") == reviewer.id, "independent designated reviewer approves")
  actions.call(be, "evidence", {"key" => "implementation", "reference" => "commit:changed-synthetic-only"})
  assert.call(item.reload.qldapm_gate["approvals"].empty?, "implementation revision invalidates approval")
  operation = Qldapm::GateActions.new(item.reload, be)
  value = {"key" => "implementation", "reference" => "commit:replay-test-only"}
  version = item.lock_version
  request_id, request_hash = "QLDAPM-request-" + "a" * 64, "b" * 64
  operation.call("evidence", value, version, request_id:, request_hash:)
  revision, count = item.reload.qldapm_gate.values_at("revision", "events")
  operation.call("evidence", value, version, request_id:, request_hash:)
  assert.call(item.reload.qldapm_gate["revision"] == revision && item.qldapm_gate["events"].size == count.size,
              "native gate receipt prevents duplicate revision/evidence after timeout")
  User.execute_as(reviewer) do
    result = WorkPackages::UpdateService.new(user: reviewer, model: item.reload).call(subject: "Reviewer authored synthetic content")
    assert.call(result.success?, "reviewer may contribute before approval")
  end
  actions.call(be, "evidence", {"key" => "implementation", "reference" => "commit:content-author-test"})
  begin
    actions.call(reviewer, "approve", {"key" => "code", "reference" => "review:authored-by-reviewer"})
    raise "CONTENT_AUTHOR_SELF_APPROVAL_ACCEPTED"
  rescue ArgumentError => error
    assert.call(error.message.include?("SELF_APPROVAL"), "content author cannot approve as designated reviewer")
  end
  analyst = users.fetch("BA-PM")
  actions.call(pm, "reviewer", {"user_id" => analyst.id})
  actions.call(analyst, "acceptance_criteria", {"text" => "Synthetic changed acceptance criteria"})
  actions.call(be, "evidence", {"key" => "analysis", "reference" => "analysis:synthetic-content"})
  begin
    actions.call(analyst, "approve", {"key" => "analysis", "reference" => "analysis:self-authored"})
    raise "AC_AUTHOR_SELF_APPROVAL_ACCEPTED"
  rescue ArgumentError => error
    assert.call(error.message.include?("SELF_APPROVAL"), "acceptance-criteria author cannot self-approve analysis")
  end
  begin
    Qldapm::GateActions.new(item, pm).call("reviewer", {"user_id" => reviewer.id}, item.lock_version - 1)
    raise "STALE_GATE_ACCEPTED"
  rescue ArgumentError => error
    assert.call(error.message == "STALE_WORK_PACKAGE", "stale gate update rejected")
  end
  stream = item.qldapm_gate["stream"]
  User.execute_as(pm) { item.update!(assigned_to: users.fetch("QA")) }
  assert.call(item.reload.qldapm_gate["stream"] == stream, "assignee change does not change branch")
  parent = item.parent
  WorkPackage.where(id: parent.id).update_all(status_id: Status.find_by!(name: "REVIEW").id)
  User.execute_as(be) do
    item.subject = "Should never commit"
    assert.call(!item.save(validate: false) && item.reload.subject != "Should never commit", "closed parent blocks child content changes")
  end
  User.execute_as(pm) do
    item.parent = project.work_packages.joins(:type).where(types: {name: "Task"}).where.not(id: parent.id).first!
    assert.call(!item.save(validate: false) && item.reload.parent_id == parent.id, "hierarchy move cannot escape a closed parent")
  end
  begin
    actions.call(pm, "reviewer", {"user_id" => pm.id})
    raise "CLOSED_PARENT_GATE_ACCEPTED"
  rescue ActiveRecord::RecordInvalid => error
    assert.call(error.message.include?("PARENT_CLOSED"), "closed parent blocks gate writes")
  end
  User.execute_as(pm) do
    item.destroy
    assert.call(item.persisted? && item.errors.full_messages.join.include?("LOCAL_APPROVAL"), "delete requires local operator approval")
    begin
      Thread.current[:qldapm_approved_delete] = item.id
      item.destroy
      assert.call(item.persisted? && item.errors.full_messages.join.include?("PARENT_CLOSED"),
                  "approved delete still requires reopening the closed parent")
    ensure
      Thread.current[:qldapm_approved_delete] = nil
    end
  end
  raise ActiveRecord::Rollback
end
assert.call(WorkPackage.where(project:).order(:id).pluck(:id, :subject, :description, :parent_id, :assigned_to_id, :status_id, :lock_version, :qldapm_gate) == baseline,
            "integration transaction leaves all 329 records unchanged")
assert.call(project.work_packages.count == 329, "329 source records retained")
puts JSON.generate({"passed" => true, "checks" => checks})

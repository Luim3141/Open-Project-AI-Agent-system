raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
checks = []
assert = ->(value, label) { raise label unless value; checks << label }
ActiveRecord::Base.transaction do
  item = project.work_packages.order(:id).first!
  %w[pm ba-pm be fe qa].each do |login|
    actor = User.find_by!(login:)
    pm = login == "pm"
    assert.call(actor.allowed_in_project?(:edit_work_packages, project) == pm, "#{login}: native edit ceiling")
    assert.call(actor.allowed_in_project?(:manage_board_views, project) == pm, "#{login}: board ceiling")
    assert.call(actor.allowed_in_project?(:add_work_package_comments, project), "#{login}: native comments")
    assert.call(!actor.allowed_in_project?(:manage_members, project), "#{login}: no membership escalation")
    next if pm
    User.execute_as(actor) do
      copy = WorkPackage.find(item.id)
      copy.subject = "MUST NOT PERSIST"
      assert.call(!copy.save(validate: false) && copy.errors.full_messages.join.include?("PM_REQUIRED"), "#{login}: model rejects direct save")
      copy = WorkPackage.find(item.id)
      field = WorkPackageCustomField.find_by!(name: "Source ID")
      copy.custom_field_values = {field.id => "RBAC-MUST-NOT-WRITE"}
      assert.call(!copy.save(validate: false) && copy.errors.full_messages.join.include?("PM_REQUIRED"), "#{login}: model rejects custom field autosave")
      begin
        Qldapm::GateActions.new(item, actor).call("approve", {"key" => "pm", "reference" => "test:spoof"}, item.lock_version)
        raise "GATE_ESCAPED"
      rescue ArgumentError => error
        assert.call(error.message == "PM_REQUIRED", "#{login}: gate approval denied")
      end
    end
  end
  be = User.find_by!(login: "be")
  # Add a permissive secondary native role and a work-package share: the ceiling must still deny edits.
  member = Member.find_by!(project:, user_id: be.id, entity_id: nil)
  extra = ProjectRole.create!(name: "RBAC fixture extra", permissions: %i[edit_work_packages manage_board_views])
  member.roles << extra
  be.reload
  assert.call(!be.allowed_in_work_package?(:edit_work_packages, item), "additional role cannot grant BE edit")
  editor = WorkPackageRole.find_by!(builtin: Role::BUILTIN_WORK_PACKAGE_EDITOR)
  Member.create!(project:, principal: be, entity: item, roles: [editor])
  be.reload
  assert.call(!be.allowed_in_work_package?(:edit_work_packages, item), "work-package editor share cannot grant BE edit")
  board = Boards::Grid.new(project:, name: "RBAC transaction fixture", row_count: 1, column_count: 4, options: {"type" => "free"})
  assert.call(!OpenProject::Boards::GridRegistration.writable?(board, be), "board SQL role grants cannot bypass PM ceiling")
  User.execute_as(be) { assert.call(!board.save(validate: false), "board model rejects direct background save") }
  User.execute_as(User.find_by!(login: "pm")) { assert.call(board.save!, "PM board model save allowed") }
  other = Project.create!(identifier: "rbac-other-project", name: "RBAC other", workspace_type: "project")
  assert.call(Qldapm::Rbac.role(other, User.find_by!(login: "pm")).nil?, "PM does not inherit PM outside project")
  assert.call(!User.find_by!(login: "pm").allowed_in_project?(:edit_work_packages, other), "native cross-project write denied")
  assert.call(Qldapm::GatePolicy.actor_role(%w[BA PM]) == "PM", "multiple project roles aggregate to PM")
  assert.call(Qldapm::GatePolicy.actor_role(%w[BA BA-PM]) == "BA-PM", "BA aliases do not elevate")
  actor = User.find_by!(login: "pm")
  original_login = actor.login
  actor.login = "rbac-renamed-pm"
  assert.call(Qldapm::Rbac.pm?(project, actor), "identity is membership-based, not login whitelist")
  actor.login = original_login
  snapshot = {"assignee" => actor.id, "data" => {"reviewer_id" => actor.id, "contributors" => [actor.id]}}
  assert.call(!Qldapm::GatePolicy.new.can_approve?(snapshot, {"id" => actor.id, "role" => "PM"}, "pm"), "PM self-approval still denied")
  actor.update!(admin: true)
  actor.reload
  assert.call(Qldapm::Rbac.pm?(project, actor, fresh: true), "administrator with PM membership retains business role")
  assert.call(actor.allowed_in_project?(:manage_members, project), "administrator retains native project administration")
  assert.call(!Qldapm::GatePolicy.new.can_approve?(snapshot, {"id" => actor.id, "role" => "PM"}, "pm"), "administrator cannot self-approve")
  Member.where(project:, user_id: actor.id, entity_id: nil).destroy_all
  assert.call(!Qldapm::Rbac.pm?(project, actor, fresh: true), "administrator requires PM membership for managed business writes")
  raise ActiveRecord::Rollback
end
puts JSON.generate({passed: true, checks:, rollback: true})

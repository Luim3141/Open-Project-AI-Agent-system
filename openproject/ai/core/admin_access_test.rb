require "json"
require "digest"
raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
user = User.find_by!(login: "system-admin")
raise "ACTIVE_ADMIN_REQUIRED" unless user.admin? && user.active? && user.force_password_change
fingerprint = -> { Digest::SHA256.hexdigest(JSON.generate(WorkPackage.order(:id).map(&:attributes))) }
before = fingerprint.call
checks = []
assert = ->(value, label) { raise label unless value; checks << label }
Project.order(:id).each do |project|
  assert.call(user.allowed_in_project?(:manage_members, project), "project #{project.id}: manage members")
  assert.call(user.allowed_in_project?(:edit_work_packages, project), "project #{project.id}: edit work packages")
end
project = Project.find_by!(identifier: "qldapm-local")
pm = User.find_by!(login: "pm")
id = project.work_packages.joins(:status).where(assigned_to_id: pm.id, statuses: {name: "NEW"}).first!.id
ActiveRecord::Base.transaction do
  User.execute_as(user) do
    item = WorkPackage.find(id)
    independent = {"assignee" => pm.id, "data" => {"contributors" => [pm.id], "reviewer_id" => user.id}}
    assert.call(Qldapm::GatePolicy.new.can_approve?(independent, item.qldapm_actor(user), "pm"), "independent administrator may review original PM work")
    item.subject = "Administrator access regression fixture"
    assert.call(item.save!, "administrator edits task assigned to original PM")
    item.assigned_to = user
    assert.call(item.save!, "administrator reassigns original PM task")
    assert.call(!Qldapm::GatePolicy.new.can_approve?(item.qldapm_snapshot, item.qldapm_actor(user), "pm"), "administrator cannot approve own assigned/contributed work")
  end
  raise ActiveRecord::Rollback
end
assert.call(fingerprint.call == before, "all work package attributes unchanged after rollback")
puts JSON.generate({passed: true, checks:, tested_work_package: id, work_packages: WorkPackage.count, rollback: true})

# Fixed operator operation; never expose through REST/MCP or accept arbitrary roles.
require "json"
require "digest"
mode = ENV.fetch("QLDAPM_ROLE_MODE", "preview")
raise "MODE_DENIED" unless %w[preview apply test].include?(mode)
stage = mode == "test"
raise "STAGING_ONLY" if stage && (!User.exists?(login: "stage-owner") || User.exists?(login: "op-owner"))
project = Project.find_by!(identifier: "qldapm-local")
targets = stage ? [User.find_by!(login: "ba-pm"), User.find_by!(login: "pm")] :
  [User.find_by!(mail: "hiepk40c@gmail.com"), User.find_by!(mail: "2101minhkhai@gmail.com")]
raise "WRONG_IDENTITIES" unless targets.map(&:login) == %w[ba-pm pm] && targets.none?(&:admin?) && targets.all?(&:active?)
pm = ProjectRole.where(name: "QLDAPM PM").distinct.sole
ba = ProjectRole.where(name: ["QLDAPM BA-PM", "QLDAPM BA"]).distinct.sole
raise "SHARED_ROLE_DENIED" if MemberRole.where(role: ba).joins(:member).where.not(members: {project_id: project.id}).exists?
members = targets.map { |u| Member.find_by!(project: project, principal: u, entity_id: nil) }
snapshot = -> {
  {"project_id" => project.id, "users" => targets.map { |u| {"id" => u.id, "login" => u.login, "email" => u.mail,
    "roles" => Member.find(members[targets.index(u)].id).roles.distinct.pluck(:id).sort} },
   "ba_role" => {"id" => ba.id, "name" => ba.reload.name, "permissions" => ba.permissions.map(&:to_s).sort},
   "pm_role" => {"id" => pm.id, "permissions" => pm.permissions.map(&:to_s).sort},
   "workflows_hash" => Digest::SHA256.hexdigest(Workflow.where(role_id: [ba.id, pm.id]).order(:id).map(&:attributes).to_json),
   "work_packages_hash" => Digest::SHA256.hexdigest(project.work_packages.order(:id).map(&:attributes).to_json),
   "user_security_hash" => Digest::SHA256.hexdigest(User.where(id: targets.map(&:id)).order(:id).map(&:attributes).to_json),
   "api_tokens_hash" => Digest::SHA256.hexdigest(Token::API.order(:id).map(&:attributes).to_json)}
}
before = snapshot.call
hash = Digest::SHA256.hexdigest(JSON.generate(before))
if mode == "preview"
  puts JSON.generate({"before" => before, "before_hash" => hash, "desired" => {targets[0].id => "PM", targets[1].id => "BA"}})
else
  ActiveRecord::Base.transaction do
    WorkPackage.connection.execute("SELECT pg_advisory_xact_lock(817609, #{Integer(project.id)})")
    User.where(id: targets.map(&:id)).order(:id).lock.load
    Member.where(id: members.map(&:id)).order(:id).lock.load
    ProjectRole.unscoped.where(id: [pm.id, ba.id]).order(:id).lock.load
    raise "CONFIGURATION_CHANGED" unless Digest::SHA256.hexdigest(JSON.generate(snapshot.call)) == (stage ? hash : ENV.fetch("QLDAPM_ROLE_BEFORE_HASH"))
    raise "BA_HAS_MANAGEMENT_PERMISSIONS" unless (ba.permissions - pm.permissions).empty? &&
      (ba.permissions.map(&:to_s) & %w[manage_members manage_versions manage_board_views create_sprints start_complete_sprint manage_sprint_items]).empty?
    User.current = User.find_by!(login: stage ? "stage-owner" : "op-owner")
    raise "OWNER_REQUIRED" unless User.current.admin? && User.current.active?
    ba.update!(name: "QLDAPM BA")
    members.zip([pm, ba]).each { |member, role| member.roles = [role]; member.save! }
    after = snapshot.call
    %w[workflows_hash work_packages_hash user_security_hash api_tokens_hash].each do |key|
      raise "UNEXPECTED_CHANGE_#{key}" unless before[key] == after[key]
    end
    raise "ROLE_ASSIGNMENT_FAILED" unless after["users"].map { |u| u["roles"] } == [[pm.id], [ba.id]]
    puts JSON.generate({"result" => stage ? "test_rolled_back" : "applied", "before" => before, "after" => after})
    raise ActiveRecord::Rollback if stage
  end
  raise "TEST_DID_NOT_ROLL_BACK" if stage && snapshot.call != before
end

require "json"
raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
roles = Member.where(project:, entity_id: nil).includes(:roles).flat_map(&:roles).uniq
raise "SHARED_ROLE_REQUIRES_SEPARATE_PLAN" unless roles.all? { |r| r.members.where(entity_id: nil).distinct.pluck(:project_id) == [project.id] }
before = roles.to_h { |r| [r.id, {name: r.name, permissions: r.permissions.map(&:to_s).sort}] }
backup = "/private/rbac-roles-before.json"
raise "BACKUP_ALREADY_EXISTS" if File.exist?(backup)
File.write(backup, JSON.pretty_generate(before), mode: "wx", perm: 0600)
Role.transaction do
  roles.each do |role|
    name = Qldapm::GatePolicy.actor_role([role.name.delete_prefix("QLDAPM ")])
    raise "UNKNOWN_ROLE" unless name
    permissions = name == "PM" ? Qldapm::Rbac::PM_PERMISSIONS : Qldapm::Rbac::READ_COMMENT
    role.permissions = permissions
    role.save!
  end
end
puts JSON.generate({passed: true, backup:, roles: roles.map { |r| {id: r.id, name: r.name, permissions: r.reload.permissions.sort} }})

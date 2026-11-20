require "json"
project = Project.find_by!(identifier: "qldapm-local")
roles = Member.where(project:, entity_id: nil).includes(:roles).flat_map(&:roles).uniq
puts JSON.generate({project_id: project.id, roles: roles.map { |r| {id: r.id, name: r.name, permissions: r.permissions.sort,
  projects: r.members.where(entity_id: nil).distinct.pluck(:project_id)} },
  members: Member.where(project:, entity_id: nil).includes(:roles, :principal).map { |m|
    {id: m.user_id, active: m.principal.active?, admin: m.principal.try(:admin?), roles: m.roles.map(&:name)} },
  modules: project.enabled_modules.pluck(:name), work_packages: project.work_packages.count,
  permissions: OpenProject::AccessControl.permissions.select { |p| p.project? || p.work_package? }.map(&:name).sort})

module Qldapm
  module Rbac
    READ_COMMENT = %i[view_project view_work_packages export_work_packages add_work_package_comments
      show_board_views view_sprints view_members view_changesets view_wiki_pages view_cost_entries
      view_time_entries view_own_time_entries view_work_package_watchers view_project_activity view_project_attributes
      search_project work_package_assigned].freeze
    PM_PERMISSIONS = (READ_COMMENT + %i[add_work_packages edit_work_packages change_work_package_status
      delete_work_packages copy_work_packages move_work_packages manage_subtasks manage_work_package_relations
      manage_board_views manage_public_queries save_queries create_sprints start_complete_sprint manage_sprint_items
      select_backlog_types_and_statuses manage_versions assign_versions share_sprint]).freeze

    def self.managed?(project)
      project&.identifier == "qldapm-local"
    end

    def self.roles(project, user, fresh: false)
      return [] unless user.is_a?(User) && user.active?
      return [] if fresh && !User.active.where(id: user.id).exists?
      load_roles = -> { Member.where(project_id: project.id, user_id: user.id, entity_id: nil).includes(:roles)
        .flat_map(&:roles).map { |role| role.name.delete_prefix("QLDAPM ") }.uniq
      }
      return load_roles.call if fresh || !RequestStore.active?
      # One native HTTP request may render hundreds of permission links; never cache across requests.
      cache = RequestStore.store[:qldapm_project_roles] ||= {}
      cache.fetch([project.id, user.id]) { cache[[project.id, user.id]] = load_roles.call }
    end

    def self.role(project, user, fresh: false)
      GatePolicy.actor_role(roles(project, user, fresh:))
    end

    def self.pm?(project, user, fresh: false)
      role(project, user, fresh:) == "PM"
    end

    def self.filter(permissions, project, user)
      return permissions unless managed?(project)
      return permissions if user.is_a?(User) && user.active? && user.admin?
      role = role(project, user)
      return [] unless role
      ceiling = role == "PM" ? PM_PERMISSIONS : READ_COMMENT
      permissions.select { |permission| ceiling.include?(permission.name.to_sym) }
    end
  end

end

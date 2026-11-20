module Qldapm
  # Cap native authorization as well as role configuration, including work-package shares.
  module PermissionCeiling
    private

    def allowed_in_single_project?(permissions, project)
      filtered = Rbac.filter(permissions, project, user)
      filtered.any? && super(filtered, project)
    end

    def allowed_in_single_project_scoped_entity?(permissions, entity)
      filtered = Rbac.filter(permissions, entity&.project, user)
      filtered.any? && super(filtered, entity)
    end

    def allowed_in_any_project_scoped_entity?(permissions, entity_class, in_project:)
      filtered = Rbac.filter(permissions, in_project, user)
      filtered.any? && super(filtered, entity_class, in_project:)
    end
  end
end

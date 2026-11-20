module Qldapm
  # Minimal metadata from current Native visibility; never serialize full representers.
  class ObserverPackages
    def self.project_for(user, project_id)
      project = Project.visible(user).find(project_id)
      raise ArgumentError, 'OBSERVER_PROJECT_DENIED' unless {5 => 'qldapm-local', 6 => 'ai-dev-demo'}[project.id] == project.identifier
      raise ArgumentError, 'OBSERVER_NATIVE_READ_DENIED' unless user.allowed_in_project?(:view_work_packages, project) && Rbac.role(project, user, fresh: true)
      project
    end

    def self.render_items(user, project, items)
      items.filter_map do |item|
        next unless user.allowed_in_work_package?(:view_work_packages, item)
        {id: item.id, subject: item.subject, lockVersion: item.lock_version,
         '_links' => {project: {href: "/api/v3/projects/#{project.id}"},
                     status: {href: "/api/v3/statuses/#{item.status_id}", title: item.status.name},
                     type: {title: item.type.name},
                     parent: item.parent_id ? {href: "/api/v3/work_packages/#{item.parent_id}"} : nil}}
      end
    end

    def self.call(user, project_id, identifiers)
      raise ArgumentError, 'OBSERVER_PACKAGE_IDS_INVALID' unless identifiers.is_a?(Array) && identifiers.size.between?(1, 100) && identifiers.all? { |id| id.is_a?(Integer) && id.positive? }
      project = project_for(user, project_id)
      items = WorkPackage.visible(user).where(project_id: project.id, id: identifiers.uniq).includes(:status, :type).to_a
      {project_id: project.id, items: render_items(user, project, items)}
    end

    def self.list(user, project_id, query, limit)
      raise ArgumentError, 'OBSERVER_LIST_INVALID' unless query.is_a?(String) && query.length <= 160 && limit.between?(1, 200)
      project = project_for(user, project_id)
      scope = WorkPackage.visible(user).where(project_id: project.id)
      if query.match?(/\A#?[1-9][0-9]*\z/)
        scope = scope.where(id: query.delete_prefix('#').to_i)
      elsif query.present?
        scope = scope.where('work_packages.subject ILIKE ?', "%#{ActiveRecord::Base.sanitize_sql_like(query)}%")
      end
      items = scope.includes(:status, :type).order(updated_at: :desc, id: :desc).limit(limit + 1).to_a
      {project_id: project.id, items: render_items(user, project, items.first(limit)), truncated: items.length > limit}
    end
  end
end

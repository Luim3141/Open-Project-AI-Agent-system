Rails.application.config.to_prepare do
  Authorization::UserPermissibleService.prepend(Qldapm::PermissionCeiling) unless Authorization::UserPermissibleService < Qldapm::PermissionCeiling
  OpenProject::Boards::GridRegistration.singleton_class.prepend(Qldapm::BoardPermissions) unless OpenProject::Boards::GridRegistration.singleton_class < Qldapm::BoardPermissions
  [Boards::Grid, Grids::Widget].each { |model| model.include(QldapmBoardWrite) unless model < QldapmBoardWrite }
  WorkPackage.include(QldapmGateWrite) unless WorkPackage < QldapmGateWrite
  Relation.include(QldapmRelationWrite) unless Relation < QldapmRelationWrite
  WorkPackagesController.prepend(QldapmWorkPackageTree) unless WorkPackagesController < QldapmWorkPackageTree
  QldapmWorkPackageTreeHook.instance
end

Rails.application.config.after_initialize do
  # Menu checks controller/action permissions, unlike the controller's explicit permission authorization.
  OpenProject::AccessControl.permission(:view_work_packages).controller_actions.concat(
    %w[qldapm_ai/show qldapm_ai/insights qldapm_ai/permissions qldapm_ai/executions qldapm_ai/execution qldapm_ai/observer qldapm_gates/index]
  )
  OpenProject::AccessControl.clear_caches
  Redmine::MenuManager.map(:project_menu) do |menu|
    menu.push :qldapm_ai, {controller: "/qldapm_ai", action: "show"},
              caption: ->(project) { project&.identifier == "ai-dev-demo" ? "AI Command Center" : "AI Assistant" },
              param: :project_id,
              icon: "comment-discussion",
              html: {data: {turbo: false}},
              after: :work_packages,
              if: ->(project) {
                return false unless project
                if project.identifier == "ai-dev-demo"
                  User.current.admin? || %w[PM AI_SYSTEM_OWNER].include?(Qldapm::Rbac.role(project, User.current, fresh: true))
                elsif project.identifier == "qldapm-local"
                  true
                else
                  false
                end
              }
    menu.push :qldapm_insights, {controller: "/qldapm_ai", action: "insights"}, caption: "Insights", param: :project_id,
              icon: "graph", after: :qldapm_ai,
              if: ->(project) { project&.identifier == "qldapm-local" }
    menu.push :qldapm_gates, {controller: "/qldapm_gates", action: "index"},
              caption: "Workflow gates", param: :project_id, icon: "checklist",
              if: ->(project) { project&.identifier == "qldapm-local" }
  end
  Rails.application.config.good_job.cron.merge!(qldapm_insights: {cron: "55 23 * * * Asia/Bangkok", class: "Qldapm::InsightSnapshotJob"})
end

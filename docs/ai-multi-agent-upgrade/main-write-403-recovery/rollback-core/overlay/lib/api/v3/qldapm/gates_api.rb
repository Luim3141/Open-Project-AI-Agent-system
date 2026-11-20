module API
  module V3
    module Qldapm
      class GatesAPI < ::API::OpenProjectAPI
        resources :qldapm do
          resource :daily_summary do
            get do
              error!({error: "SUMMARY_SELECTORS_DENIED"}, 422) unless request.GET.empty?
              project = Project.visible(current_user).find_by!(identifier: "qldapm-local")
              error!({error: "ACTIVE_MEMBER_REQUIRED"}, 403) unless ::Qldapm::Rbac.role(project, current_user, fresh: true)
              error!({error: "VIEW_WORK_PACKAGES_REQUIRED"}, 403) unless current_user.allowed_in_project?(:view_work_packages, project)
              # Model progress includes status-based defaults; raw SQL done_ratio would change overdue semantics.
              items = WorkPackage.visible(current_user).where(project:).includes(:status, :type).order(:id).to_a
              today = Time.current.in_time_zone("Asia/Bangkok").to_date
              statuses = items.each_with_object(Hash.new(0)) { |item, counts| counts[item.status.name] += 1 }
              overdue = items.filter_map do |item|
                item.id if !item.milestone? && item.due_date && item.due_date < today && item.done_ratio != 100 &&
                  !%w[DONE CLOSED].include?(item.status.name.upcase)
              end
              {actor: current_user.id, project_id: project.id, count: items.length, by_status: statuses, overdue_ids: overdue}
            end
          end
          resource :permissions do
            get do
              project = Project.visible(current_user).find_by!(identifier: "qldapm-local")
              role = ::Qldapm::Rbac.role(project, current_user)
              error!({error: "ACTIVE_MEMBER_REQUIRED"}, 403) unless role
              definitions = OpenProject::AccessControl.permissions.select { |p| p.project? || p.work_package? }
              {project_id: project.id, actor: current_user.id, role:, roles: ::Qldapm::Rbac.roles(project, current_user),
               effective: definitions.to_h { |p| [p.name, current_user.allowed_in_project?(p.name, project)] },
               matrix: role == "PM" ? {PM: ::Qldapm::Rbac::PM_PERMISSIONS, BA: ::Qldapm::Rbac::READ_COMMENT,
                 BE: ::Qldapm::Rbac::READ_COMMENT, FE: ::Qldapm::Rbac::READ_COMMENT, QA: ::Qldapm::Rbac::READ_COMMENT} : nil,
               notice: "PM-only business writes; native permissions, workflow, evidence and independent approvals still apply."}
            end
          end
          resource :mutations do
            params do
              requires :id, type: Integer
              requires :action, type: String
              requires :lock_version, type: Integer
              requires :request_id, type: String
              optional :status_id, type: Integer
              optional :changes, type: Hash
            end
            post do
              item = WorkPackage.visible(current_user).find(params[:id])
              authorize_in_work_package(:edit_work_packages, work_package: item)
              begin
                payload = declared(params, include_missing: false).to_h.deep_stringify_keys
                payload.delete("id")
                ::Qldapm::Mutations.call(item, current_user, payload, headers)
              rescue ArgumentError => error
                error!({error: error.message}, error.message.include?("STALE") ? 409 : 422)
              end
            end
          end
          resources :mutation_receipts do
            route_param :request_id, type: String do
              get do
                receipt = ::Qldapm::MutationReceipt.where(user_id: current_user.id, request_id: params[:request_id]).first!
                item = WorkPackage.visible(current_user).find(receipt.work_package_id)
                authorize_in_work_package(:view_work_packages, work_package: item)
                raise ::API::Errors::NotFound.new(model: :work_package) unless item.qldapm_managed? && item.qldapm_actor(current_user)["role"]
                receipt.result
              end
            end
          end
          resource :insights do
            params do
              optional :user_id, type: Integer
              optional :days, type: Integer, default: 30
            end
            get do
              item = WorkPackage.visible(current_user).joins(:project).where(projects: {identifier: "qldapm-local"}).first!
              authorize_in_work_package(:view_work_packages, work_package: item)
              begin
                ::Qldapm::Insights.new(item.project, current_user).report(params[:user_id] || current_user.id, params[:days])
              rescue ArgumentError => error
                error!({error: error.message}, 403)
              end
            end
          end
          resource :capabilities do
            get do
              item = WorkPackage.visible(current_user).joins(:project).where(projects: {identifier: "qldapm-local"}).first!
              authorize_in_work_package(:view_work_packages, work_package: item)
              error!({error: "ACTIVE_MEMBER_REQUIRED"}, 403) unless item.qldapm_actor(current_user)["role"]
              {project_id: item.project_id, gate_schema: 2, enforced: item.class.included_modules.include?(::QldapmGateWrite)}
            end
          end
          resource :configuration do
            get do
              item = WorkPackage.visible(current_user).joins(:project).where(projects: {identifier: "qldapm-local"}).first!
              authorize_in_work_package(:view_work_packages, work_package: item)
              error!({error: "PM_REQUIRED"}, 403) unless item.qldapm_actor(current_user)["role"] == "PM"
              project = item.project
              variants = project.project_types.includes(:type, :variant)
              {project_id: project.id, types: variants.map { |row| {id: row.type_id, name: row.type.name, variant_id: row.variant_id} },
               workflow: Workflow.where(type_variant_id: variants.map(&:variant_id)).order(:id).pluck(
                 :role_id, :old_status_id, :new_status_id, :type_variant_id),
               fields: project.work_package_custom_fields.order(:id).pluck(:id, :name, :field_format, :is_required),
               settings: {login_required: Setting.login_required, self_registration: Setting.self_registration,
                          session_ttl: Setting.session_ttl, password_min_length: Setting.password_min_length,
                          totp: Setting.plugin_openproject_two_factor_authentication}}
            end
          end
          resources :gates do
            route_param :id, type: Integer do
              helpers do
                def gated_work_package
                  item = WorkPackage.visible(current_user).find(params[:id])
                  authorize_in_work_package(:view_work_packages, work_package: item)
                  raise ::API::Errors::NotFound.new(model: :work_package) unless item.qldapm_managed?
                  item
                end
              end
              get do
                item = gated_work_package
                snapshot = item.qldapm_snapshot
                policy = ::Qldapm::GatePolicy.new
                {id: item.id, lockVersion: item.lock_version, gate: item.qldapm_gate,
                 ui: "/qldapm/gates/#{item.id}", transitions: policy.edges(snapshot).keys.filter_map { |from, to|
                   {to:, errors: policy.errors(snapshot, item.qldapm_actor(current_user), from, to)} if from == item.status.name
                 }}
              end
              params do
                requires :lock_version, type: Integer
                requires :operation, type: String
                requires :value, type: Hash
                optional :request_id, type: String
                optional :request_hash, type: String
              end
              post do
                item = gated_work_package
                begin
                  ::Qldapm::GateActions.new(item, current_user).call(params[:operation], params[:value].to_h.deep_stringify_keys,
                                                                    params[:lock_version], request_id: params[:request_id], request_hash: params[:request_hash])
                rescue ArgumentError, ActiveRecord::RecordInvalid, KeyError => error
                  error!({error: error.message}, error.message.include?("STALE") ? 409 : 422)
                end
              end
            end
          end
        end
      end
    end
  end
end

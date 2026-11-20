require_relative 'dependency_mutation'

module Qldapm
  class HierarchyReadback
    def self.call(user,identifier)
      item=WorkPackage.visible(user).find(identifier)
      raise ArgumentError, 'NATIVE_HIERARCHY_MANAGER_REQUIRED' unless item.project_id==5 && item.qldapm_managed? && Rbac.pm?(item.project,user,fresh:true) && user.allowed_in_work_package?(:edit_work_packages,item)
      snapshot=JSON.parse(JSON.generate(DependencyMutation.state(item)))
      duration=if item.start_date && item.due_date
                 item.ignore_non_working_days ? (item.due_date-item.start_date).to_i+1 : WorkPackages::Shared::WorkingDays.new.duration(item.start_date,item.due_date)
               end
      {'id'=>item.id,'project_id'=>5,'actor_id'=>user.id,'lock_version'=>item.lock_version,
       'snapshot'=>snapshot,'snapshot_sha256'=>DependencyMutation.fingerprint(snapshot),'working_duration'=>duration}
    end
  end
end

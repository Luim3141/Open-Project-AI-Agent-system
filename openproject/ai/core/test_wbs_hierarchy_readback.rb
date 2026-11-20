require 'ostruct'
require 'date'
require_relative 'overlay/app/services/qldapm/hierarchy_readback'

module Qldapm::Rbac
  def self.pm?(project,user,fresh:)
    raise 'FRESH_ROLE_LOOKUP_REQUIRED' unless fresh
    [18,19].include?(user.id) && project.id==5
  end
end

class WorkPackage
  class << self
    attr_accessor :item,:observed_user
    def visible(user)
      self.observed_user=user
      self
    end
    def find(id)
      raise 'NATIVE_IDENTIFIER_CHANGED' unless id==376
      item
    end
  end
end

project=OpenStruct.new(id:5)
item=OpenStruct.new(id:376,project_id:5,project:project,lock_version:1,parent_id:nil)
item.define_singleton_method(:qldapm_managed?) { true }
item.define_singleton_method(:attributes) { {'id'=>id,'project_id'=>project_id,'lock_version'=>lock_version,'subject'=>'Private fixture','updated_at'=>Time.utc(2026,10,26,8,0,0)} }
WorkPackage.item=item
([18,19,20,21,22,23,99]).each do |identifier|
  user=OpenStruct.new(id:identifier)
  user.define_singleton_method(:allowed_in_work_package?) do |permission,target|
    raise 'NATIVE_PERMISSION_SCOPE_CHANGED' unless permission==:edit_work_packages && target.equal?(item)
    [18,19].include?(id)
  end
  if [18,19].include?(identifier)
    result=Qldapm::HierarchyReadback.call(user,376)
    raise 'AUTHENTICATED_ACTOR_OR_STATE_CHANGED' unless result['actor_id']==identifier && result['snapshot']['attributes'].except('updated_at')==item.attributes.except('updated_at') && WorkPackage.observed_user.equal?(user)
    raise 'SNAPSHOT_MUST_HAVE_TRANSPORT_STABLE_TIMESTAMPS' unless result['snapshot']['attributes']['updated_at'].is_a?(String)
    raise 'SOURCE_HASH_MISMATCH' unless result['snapshot_sha256']==Qldapm::DependencyMutation.fingerprint(result['snapshot'])
  else
    begin
      Qldapm::HierarchyReadback.call(user,376)
      raise 'NON_MANAGER_READ_MODEL_LEAK'
    rescue ArgumentError
    end
  end
end
owner=OpenStruct.new(id:18)
owner.define_singleton_method(:allowed_in_work_package?) { |*_| true }
module WorkPackages
  module Shared
    class WorkingDays
      def duration(first,last)
        raise 'NATIVE_CALENDAR_RANGE_CHANGED' unless first==Date.new(2026,10,23) && last==Date.new(2026,10,26)
        2
      end
    end
  end
end
item.start_date=Date.new(2026,10,23);item.due_date=Date.new(2026,10,26)
item.ignore_non_working_days=false
raise 'NATIVE_WORKING_DAY_PROOF_MISSING' unless Qldapm::HierarchyReadback.call(owner,376)['working_duration']==2
item.ignore_non_working_days=true
raise 'NATIVE_ALL_DAY_PROOF_MISSING' unless Qldapm::HierarchyReadback.call(owner,376)['working_duration']==4
owner.define_singleton_method(:allowed_in_work_package?) { |*_| false }
begin
  Qldapm::HierarchyReadback.call(owner,376)
  raise 'NATIVE_PERMISSION_BYPASSED'
rescue ArgumentError
end
item.project_id=3
begin
  Qldapm::HierarchyReadback.call(owner,376)
  raise 'OTHER_PROJECT_ALLOWED'
rescue ArgumentError
end
puts 'WBS hierarchy: fresh manager + own Native permission + visible Main model hash PASS'

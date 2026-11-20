# The upstream derivation must leave invalid status references for native contract validation.
module WorkPackages
  class SetAttributesService
    class DeriveProgressValuesBase; end
  end
end
require '/app/app/services/work_packages/set_attributes_service/derive_progress_values_status_based'
probe=WorkPackages::SetAttributesService::DeriveProgressValuesStatusBased.allocate
probe.define_singleton_method(:work_invalid?){false}
probe.define_singleton_method(:work_package){Struct.new(:status).new(nil)}
raise 'NULL_STATUS_NOT_REJECTED' unless probe.send(:invalid_progress_values?)
probe.define_singleton_method(:work_package){Struct.new(:status).new(Object.new)}
raise 'VALID_STATUS_REJECTED' if probe.send(:invalid_progress_values?)
probe.define_singleton_method(:work_invalid?){true}
raise 'INVALID_WORK_BYPASSED' unless probe.send(:invalid_progress_values?)
puts 'NULL_VALID_STATUS_AND_INVALID_WORK_PASS'

require 'digest'

module Qldapm
  module ApplicationQaSources
    PATHS = %w[
      app/models/concerns/qldapm_gate_write.rb
      app/models/qldapm/gate_policy.rb
      app/services/qldapm/hierarchy_readback.rb
      app/services/work_packages/create_service.rb
      app/services/work_packages/set_attributes_service/derive_progress_values_status_based.rb
    ].freeze

    def self.read(root)
      PATHS.to_h { |path| [path, Digest::SHA256.file(File.join(root.to_s, path)).hexdigest] }
    end
  end
end

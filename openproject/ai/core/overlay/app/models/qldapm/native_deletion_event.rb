module Qldapm
  class NativeDeletionEvent < ApplicationRecord
    self.table_name = 'qldapm_native_deletion_events'
    belongs_to :project
    belongs_to :user
  end
end

module Qldapm
  class InsightSnapshot < ApplicationRecord
    self.table_name = "qldapm_insight_snapshots"
    belongs_to :project
    belongs_to :user
    has_many :responses, class_name: "Qldapm::InsightResponse", foreign_key: :qldapm_insight_snapshot_id
  end
end

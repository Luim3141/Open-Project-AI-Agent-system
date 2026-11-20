module Qldapm
  class InsightResponse < ApplicationRecord
    self.table_name = "qldapm_insight_responses"
    belongs_to :user
    belongs_to :insight_snapshot, class_name: "Qldapm::InsightSnapshot", foreign_key: :qldapm_insight_snapshot_id
    validates :body, length: {in: 5..4000}
  end
end

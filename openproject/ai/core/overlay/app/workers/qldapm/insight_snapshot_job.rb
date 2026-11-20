module Qldapm
  class InsightSnapshotJob < ApplicationJob
    def perform
      Insights.daily
    end
  end
end

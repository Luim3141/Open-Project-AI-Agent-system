module Qldapm
  class MutationReceipt < ApplicationRecord
    self.table_name = "qldapm_mutation_receipts"
    belongs_to :project
    belongs_to :user
    belongs_to :work_package
  end
end

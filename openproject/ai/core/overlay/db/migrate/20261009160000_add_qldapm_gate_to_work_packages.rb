class AddQldapmGateToWorkPackages < ActiveRecord::Migration[8.0]
  def change
    add_column :work_packages, :qldapm_gate, :jsonb, null: false, default: {}
  end
end

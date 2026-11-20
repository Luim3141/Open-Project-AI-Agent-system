class CreateQldapmMutationReceipts < ActiveRecord::Migration[8.0]
  def change
    create_table :qldapm_mutation_receipts do |t|
      t.references :project, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.references :work_package, null: false, foreign_key: true
      t.bigint :journal_id
      t.string :request_id, null: false
      t.string :request_hash, null: false
      t.string :provenance, null: false
      t.jsonb :result, null: false, default: {}
      t.timestamps
    end
    add_index :qldapm_mutation_receipts, [:project_id, :user_id, :request_id], unique: true, name: "qldapm_mutation_replay"
  end
end

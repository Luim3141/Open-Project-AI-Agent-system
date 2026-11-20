class CreateQldapmInsightSnapshots < ActiveRecord::Migration[8.0]
  def change
    create_table :qldapm_insight_snapshots do |t|
      t.references :project, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.integer :days, null: false
      t.string :input_hash, null: false
      t.jsonb :report, null: false, default: {}
      t.timestamps
    end
    add_index :qldapm_insight_snapshots, [:project_id, :user_id, :days, :input_hash], unique: true, name: "qldapm_insight_version"
    create_table :qldapm_insight_responses do |t|
      t.references :qldapm_insight_snapshot, null: false, foreign_key: true, index: {name: "qldapm_response_snapshot"}
      t.references :user, null: false, foreign_key: true
      t.text :body, null: false
      t.timestamps
    end
  end
end

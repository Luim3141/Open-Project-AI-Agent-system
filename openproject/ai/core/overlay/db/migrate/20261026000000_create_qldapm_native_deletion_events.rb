class CreateQldapmNativeDeletionEvents < ActiveRecord::Migration[8.0]
  def up
    create_table :qldapm_native_deletion_events do |t|
      t.references :project, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      # No WorkPackage FK: the signed event must survive its source's deletion.
      t.bigint :native_id, null: false
      t.integer :source_version, null: false
      t.string :event_id, null: false
      t.string :request_id, null: false
      t.string :request_hash, null: false
      t.jsonb :result, null: false
      t.timestamps
    end
    add_index :qldapm_native_deletion_events, :event_id, unique: true
    add_index :qldapm_native_deletion_events, [:project_id, :user_id, :request_id], unique: true, name: 'qldapm_native_delete_replay'
  end

  def down
    # App rollback retains evidence; only an unused schema may be removed.
    execute 'LOCK TABLE qldapm_native_deletion_events IN ACCESS EXCLUSIVE MODE'
    raise ActiveRecord::IrreversibleMigration, 'NATIVE_DELETE_HISTORY_MUST_BE_RETAINED' if select_value('SELECT count(*) FROM qldapm_native_deletion_events').to_i.positive?
    drop_table :qldapm_native_deletion_events
  end
end

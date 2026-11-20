require "json"
require "timeout"
raise "STAGING_ONLY" unless ENV["QLDAPM_TEST_ONLY"] == "true" && User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
raise "CLEAN_STAGING_REQUIRED_RUN_AFTER_FIXTURE_CLEANUP" unless project.work_packages.count == 329
actor = User.find_by!(login: "be")
item = project.work_packages.joins(:type).where.not(parent_id: nil).order(:id).find_by!(types: {name: "Subtask"}, assigned_to_id: actor.id)
parent = item.parent
baseline = project.work_packages.order(:id).pluck(:id, :subject, :status_id, :lock_version, :qldapm_gate)
original_status, original_version = parent.status_id, parent.lock_version
locked, release, attempting, finished = Queue.new, Queue.new, Queue.new, Queue.new
threads = []
begin
  threads << Thread.new do
    ActiveRecord::Base.connection_pool.with_connection do
      WorkPackage.transaction do
        parent.qldapm_lock_projects
        # A trusted fixture commits REVIEW while a competing writer waits on the same project lock.
        WorkPackage.where(id: parent.id).update_all(status_id: Status.find_by!(name: "REVIEW").id, lock_version: original_version)
        locked << true
        Timeout.timeout(15) { release.pop }
      end
    end
  end
  Timeout.timeout(15) { locked.pop }
  threads << Thread.new do
    ActiveRecord::Base.connection_pool.with_connection do
      child = WorkPackage.find(item.id)
      child.define_singleton_method(:qldapm_serialized_save) do |&block|
        attempting << true
        super(&block)
      end
      User.execute_as(actor) do
        child.subject = "Concurrent change must never commit"
        finished << {saved: child.save(validate: false), errors: child.errors.full_messages}
      end
    end
  end
  Timeout.timeout(15) { attempting.pop }
  sleep 0.1
  raise "CHILD_DID_NOT_WAIT_FOR_LOCK" unless finished.empty?
  release << true
  result = Timeout.timeout(15) { finished.pop }
  threads.each(&:value)
  raise "CONCURRENT_WRITE_BYPASS" if result[:saved] || result[:errors].none? { |error| error.include?("PARENT_CLOSED") }
ensure
  release << true
  threads.each { |thread| thread.join(15) }
  WorkPackage.where(id: parent.id).update_all(status_id: original_status, lock_version: original_version)
end
raise "SOURCE_DATA_CHANGED" unless project.work_packages.order(:id).pluck(:id, :subject, :status_id, :lock_version, :qldapm_gate) == baseline
puts JSON.generate({passed: true, checks: ["child waits while project lock is held", "committed parent REVIEW rejects waiting child before save", "all 329 source records unchanged"]})

require "json"
raise "STAGING_ONLY" unless ENV["QLDAPM_TEST_ONLY"] == "true" && User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
request = JSON.parse(File.read("/receipts/receipt.json"))
item = WorkPackage.find(request.fetch("id"))
user = User.find(request.fetch("actor"))
raise "QA_REQUIRED" unless item.qldapm_actor(user)["role"] == "QA"
baseline = WorkPackage.where(project_id: item.project_id).order(:id).pluck(:id, :subject, :status_id, :lock_version, :qldapm_gate)
WorkPackage.transaction do
  Qldapm::GateActions.new(item, user).call("evidence", request.fetch("value"), item.lock_version)
  evidence = item.reload.qldapm_gate.fetch("evidence").fetch("test").last
  raise "AUTOMATIC_RECEIPT_NOT_RECORDED" unless evidence["verification"] == "automatic" && evidence["snapshot_hash"] == request.dig("value", "snapshot_hash")
  raise ActiveRecord::Rollback
end
raise "SOURCE_DATA_CHANGED" unless WorkPackage.where(project_id: item.project_id).order(:id).pluck(:id, :subject, :status_id, :lock_version, :qldapm_gate) == baseline
puts "Signed sandbox receipt native gate PASS; transaction rolled back, source unchanged."

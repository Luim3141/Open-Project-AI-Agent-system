require "json"
require "tmpdir"
require "active_support/security_utils"
require_relative "overlay/app/services/qldapm/mutations"
require_relative "overlay/app/services/qldapm/test_receipt"

Dir.mktmpdir do |folder|
  key_file = File.join(folder, "synthetic.key")
  File.write(key_file, "synthetic-only-key")
  item = Struct.new(:id, :project_id).new(329, 5)
  proof = {"job_id" => "synthetic-job", "actor_id" => 23, "project_id" => 5, "work_package_id" => 329,
    "gate_revision" => 7, "suite" => "core-integration", "workspace_actor" => 21, "snapshot_hash" => "a" * 64,
    "output_hash" => "b" * 64, "passed" => true, "finished_at" => Time.now.to_i}
  signature = OpenSSL::HMAC.hexdigest("SHA256", File.binread(key_file), JSON.generate(Qldapm::Mutations.canonical(proof)))
  value = {"job_receipt" => {"proof" => proof, "signature" => signature}, "snapshot_hash" => "a" * 64, "result" => "passed"}
  raise "VALID_RECEIPT_REJECTED" unless Qldapm::TestReceipt.verify(value, item, 7, key_file:)["verification"] == "automatic"
  gateway_proof = proof.merge("suite" => "gateway")
  gateway_signature = OpenSSL::HMAC.hexdigest("SHA256", File.binread(key_file), JSON.generate(Qldapm::Mutations.canonical(gateway_proof)))
  begin
    Qldapm::TestReceipt.verify(value.merge("job_receipt" => {"proof" => gateway_proof, "signature" => gateway_signature}), item, 7, key_file:)
    raise "GATEWAY_REGRESSION_IS_NOT_WORKSPACE_TEST_EVIDENCE"
  rescue ArgumentError
  end
  [[item, 8, value], [Struct.new(:id, :project_id).new(328, 5), 7, value],
   [item, 7, value.merge("snapshot_hash" => "c" * 64)], [item, 7, value.merge("result" => "failed")],
   [item, 7, value.merge("job_receipt" => {"proof" => proof, "signature" => "0" * 64})]].each do |target, revision, input|
    begin
      Qldapm::TestReceipt.verify(input, target, revision, key_file:)
    rescue ArgumentError
      next
    end
    raise "FORGED_OR_STALE_RECEIPT_ACCEPTED"
  end
end
puts "Test receipts PASS: signed scope/revision/snapshot/result, forged and stale denied."

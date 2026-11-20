require "openssl"
require "digest"

module Qldapm
  class TestReceipt
    def self.verify(value, item, revision, key_file: ENV.fetch("QLDAPM_TEST_RECEIPT_KEY_FILE", "/qldapm-ui/test-receipt.key"))
      receipt = value.fetch("job_receipt")
      raise ArgumentError, "TEST_RECEIPT_MALFORMED" unless receipt.is_a?(Hash) && receipt["proof"].is_a?(Hash)
      proof = receipt.fetch("proof")
      fields = %w[job_id actor_id project_id work_package_id gate_revision suite workspace_actor snapshot_hash output_hash passed finished_at]
      raise ArgumentError, "TEST_RECEIPT_FIELDS" unless proof.keys.sort == fields.sort && File.file?(key_file)
      expected = OpenSSL::HMAC.hexdigest("SHA256", File.binread(key_file), JSON.generate(Mutations.canonical(proof)))
      signature = receipt.fetch("signature").to_s
      raise ArgumentError, "TEST_RECEIPT_SIGNATURE" unless signature.length == 64 && ActiveSupport::SecurityUtils.secure_compare(signature, expected)
      raise ArgumentError, "TEST_RECEIPT_SCOPE_OR_REVISION" unless proof["project_id"] == item.project_id &&
        proof["work_package_id"] == item.id && proof["gate_revision"] == revision
      raise ArgumentError, "TEST_RECEIPT_SNAPSHOT" unless proof["snapshot_hash"].to_s.match?(/\A[a-f0-9]{64}\z/) && value["snapshot_hash"] == proof["snapshot_hash"]
      raise ArgumentError, "TEST_RECEIPT_FAILED_OR_INVALID" unless proof["passed"] == true && value["result"] == "passed" &&
        %w[gate-policy core-integration].include?(proof["suite"]) && proof["finished_at"].is_a?(Integer) && proof["finished_at"] <= Time.now.to_i + 30
      {"verification" => "automatic", "job_receipt" => receipt, "snapshot_hash" => proof["snapshot_hash"]}
    rescue KeyError, TypeError
      raise ArgumentError, "TEST_RECEIPT_MALFORMED"
    end
  end
end

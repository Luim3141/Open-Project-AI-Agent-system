require "json"
require "tempfile"
require "stringio"
raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
original = User.find_by!(login: "be").status
actor = User.find_by!(login: "pm")
request = Tempfile.new(["admin-stage", ".json"])
ENV["QLDAPM_REQUEST"] = request.path
capture = StringIO.new
output = $stdout
begin
  $stdout = capture
  request.write(JSON.generate({"action" => "inspect", "parameters" => {}, "actor" => actor.id}))
  request.flush
  begin
    load "/qldapm-core/admin_operation.rb"
  rescue SystemExit => error
    raise unless error.success?
  end
  before = JSON.parse(capture.string.lines.last).fetch("hash")
  ActiveRecord::Base.transaction do
    request.rewind
    request.truncate(0)
    request.write(JSON.generate({"action" => "user", "parameters" => {"user_id" => User.find_by!(login: "be").id, "operation" => "lock"},
                                 "actor" => actor.id, "before_hash" => before}))
    request.flush
    load "/qldapm-core/admin_operation.rb"
    raise "LOCK_FAILED" unless User.find_by!(login: "be").locked?
    raise ActiveRecord::Rollback
  end
ensure
  $stdout = output
  request.close!
end
raise "TEST_MUTATED_STAGE" unless User.find_by!(login: "be").status == original
puts JSON.generate({"passed" => true, "checks" => ["admin preview fingerprint", "exact before-hash approved mutation", "test rollback retains account status"]})

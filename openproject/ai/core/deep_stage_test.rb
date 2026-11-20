raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
load File.join(__dir__, "ui_routes_test.rb")
load File.join(__dir__, "ui_commands_test.rb")
load File.join(__dir__, "jira_sync_insights_test.rb")
require "json"
require "fugit"
project = Project.find_by!(identifier: "qldapm-local")
item = project.work_packages.first!
members = User.active.where(id: Member.where(project_id: project.id, entity_id: nil).select(:user_id))
pm = members.find { |user| item.qldapm_actor(user)["role"] == "PM" }
be = members.find { |user| item.qldapm_actor(user)["role"] == "BE" }
qa = members.find { |user| item.qldapm_actor(user)["role"] == "QA" }
engine = Qldapm::Insights.new(project, pm)
report = engine.report(be.id, 30)
raise "COUNT_OR_REPORT" unless project.work_packages.count == 329 && report["subject_id"] == be.id && !report.key?("score")
begin
  Qldapm::Insights.new(project, be).report(qa.id, 7)
  raise "PRIVACY_BYPASS"
rescue ArgumentError => error
  raise unless error.message == "PM_OR_SELF_REQUIRED"
end
cutoff = Time.current.beginning_of_day
snapshot = engine.snapshot(be.id, 30, now: cutoff)
original_report = snapshot.report.deep_dup
raise "SNAPSHOT_REPLAY_DUPLICATE" unless engine.snapshot(be.id, 30, now: cutoff).id == snapshot.id
snapshot.responses.create!(user: be, body: "Synthetic employee correction; keep original evidence.")
raise "ORIGINAL_OVERWRITTEN" unless snapshot.reload.report == original_report
raise "CRON_TIMEZONE_INVALID" unless Fugit::Cron.parse("55 23 * * * Asia/Bangkok")
User.execute_as(be) do
  response = Qldapm::AiBridge.call(project, be, "command", {action: "identity", arguments: {}, idempotency_key: nil})
  raise "BRIDGE_IDENTITY" unless response.dig("result", "user_id") == be.id
end
WorkPackage.transaction do
  target = project.work_packages.find_by!(assigned_to_id: be.id)
  payload = {"action" => "update_work_package", "changes" => {"subject" => "Synthetic unicode kiểm thử"},
             "lock_version" => target.lock_version, "request_id" => "QLDAPM-request-#{'f' * 64}"}
  at = Time.now.to_i
  fingerprint = Digest::SHA256.hexdigest(JSON.generate(Qldapm::Mutations.canonical(payload.merge("id" => target.id))))
  signature = OpenSSL::HMAC.hexdigest("SHA256", File.binread("/qldapm-ui/ui.key"), "#{be.id}:#{at}:#{fingerprint}")
  headers = {"X-Qldapm-At" => at.to_s, "X-Qldapm-Mutation" => signature}
  User.execute_as(be) do
    first = Qldapm::Mutations.call(target, be, payload, headers)
    second = Qldapm::Mutations.call(target, be, payload, headers)
    raise "ATOMIC_RECEIPT_REPLAY" unless first == second && first["provenance"] == "ai_gateway"
    raise "UNICODE_WRITE" unless target.reload.subject == "Synthetic unicode kiểm thử"
    analysis = Qldapm::Insights.new(project, pm).report(be.id, 7)
    observed = analysis["events"].find { |row| row["kind"] == "scope_change" && row["work_package_id"] == target.id }
    raise "JOURNAL_AI_ATTRIBUTION_LOST" unless observed && observed["provenance"] == "ai_gateway"
  end
  raise ActiveRecord::Rollback
end
WorkPackage.transaction do
  target = project.work_packages.find_by!(assigned_to_id: be.id)
  proof = {"job_id" => "synthetic-not-a-real-run", "actor_id" => qa.id, "project_id" => project.id,
    "work_package_id" => target.id, "gate_revision" => target.qldapm_gate["revision"], "suite" => "core-integration",
    "workspace_actor" => be.id, "snapshot_hash" => "a" * 64, "output_hash" => "b" * 64, "passed" => true, "finished_at" => Time.now.to_i}
  signature = OpenSSL::HMAC.hexdigest("SHA256", File.binread("/qldapm-ui/test-receipt.key"), JSON.generate(Qldapm::Mutations.canonical(proof)))
  value = {"key" => "test", "reference" => "fixture:synthetic-proof-only", "verification" => "automatic", "result" => "passed",
    "snapshot_hash" => "a" * 64, "job_receipt" => {"proof" => proof, "signature" => signature}}
  User.execute_as(qa) do
    result = Qldapm::GateActions.new(target, qa).call("evidence", value, target.lock_version)
    raise "AUTOMATIC_EVIDENCE_UNBOUND" unless result.dig("gate", "evidence", "test").last["verification"] == "automatic"
    begin
      Qldapm::GateActions.new(target, qa).call("evidence", value.deep_merge("job_receipt" => {"signature" => "0" * 64}), target.lock_version)
      raise "FORGED_TEST_RECEIPT_ACCEPTED"
    rescue ArgumentError => error
      raise unless error.message == "TEST_RECEIPT_SIGNATURE"
    end
  end
  raise ActiveRecord::Rollback
end
puts "Automatic/manual evidence receipt contract PASS with synthetic proof; transaction rolled back."
puts "Atomic mutation receipt/provenance/replay PASS; transaction rolled back."
raise "AI_RUNNER_CANNOT_SIGN_OPERATOR_APPROVAL" if File.exist?("/qldapm-ui/approval.key")
puts "Deep staging PASS: source329, PM/self privacy, immutable snapshot replay, employee response, cron timezone, signed core-to-gateway identity."
%w[qldapm_ai/show qldapm_ai/insights].each do |template|
  html = ApplicationController.renderer.render(template:, layout: false, assigns: {project:, report:, subject: be.id, days: 30, snapshots: [snapshot]})
  raise "UI_RENDER_FAILED" unless html.include?("<form") && !html.include?("synthetic-ui-secret")
end
puts "Native ERB screens render PASS; actual login/TOTP/visual browser acceptance remains separate."

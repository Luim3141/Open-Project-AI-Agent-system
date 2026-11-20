module Qldapm
  class GateActions
    EVIDENCE = %w[story scope analysis implementation test_cases test_build test retest retest_not_needed completion
                  bug integration handover deployment smoke].freeze
    def initialize(work_package, user)
      @work_package, @user, @policy = work_package, user, GatePolicy.new
    end

    def call(operation, value, lock_version, request_id: nil, request_hash: nil)
      wp = @work_package
      raise ArgumentError, "GATE_PROJECT_DENIED" unless wp.qldapm_managed?
      raise ArgumentError, "PM_REQUIRED" unless Qldapm::Rbac.pm?(wp.project, @user, fresh: true)
      raise ArgumentError, "GATE_EDIT_DENIED" unless @user.allowed_in_work_package?(:edit_work_packages, wp)
      wp.class.transaction do
        wp.qldapm_lock_projects
        wp.reload
        raise ArgumentError, "ACTIVE_MEMBER_REQUIRED" unless wp.qldapm_actor(@user)["role"]
        if request_id
          raise ArgumentError, "REQUEST_ID_DENIED" unless request_id.match?(/\AQLDAPM-request-[a-f0-9]{64}\z/) && request_hash.to_s.match?(/\A[a-f0-9]{64}\z/)
          existing = wp.qldapm_gate.fetch("events", []).find { |entry| entry["request_id"] == request_id && entry["actor_id"] == @user.id }
          if existing
            raise ArgumentError, "IDEMPOTENCY_KEY_REUSED" unless existing["request_hash"] == request_hash
            return {"id" => wp.id, "lockVersion" => wp.lock_version, "gate" => wp.qldapm_gate}
          end
        end
        raise ArgumentError, "STALE_WORK_PACKAGE" unless wp.lock_version == Integer(lock_version)
        actor, data = wp.qldapm_actor(@user), wp.qldapm_gate.deep_dup
        reference = value["reference"].to_s.strip
        case operation
        when "acceptance_criteria"
          raise ArgumentError, "BA_OR_PM_REQUIRED" unless %w[BA-PM PM].include?(actor["role"])
          text = value.fetch("text").to_s.strip
          raise ArgumentError, "AC_REQUIRED" unless (5..10000).cover?(text.length)
          data["acceptance_criteria"] = text
          data["revision"] = data.fetch("revision", 0) + 1
          data["approvals"] = {}
          data["contributors"] = (data.fetch("contributors", []) + [actor["id"]]).uniq
        when "evidence"
          key = value.fetch("key")
          raise ArgumentError, "EVIDENCE_KEY_DENIED" unless EVIDENCE.include?(key)
          validate_reference(reference)
          raise ArgumentError, "TEST_RESULT_REQUIRED" if %w[test retest smoke].include?(key) && !%w[passed failed].include?(value["result"])
          verification = {}
          if %w[test retest smoke].include?(key)
            mode = value.fetch("verification", "manual")
            raise ArgumentError, "TEST_VERIFICATION_DENIED" unless %w[manual automatic].include?(mode)
            raise ArgumentError, "AUTOMATIC_SMOKE_SUITE_NOT_IMPLEMENTED" if mode == "automatic" && key == "smoke"
            verification = mode == "automatic" ? TestReceipt.verify(value, wp, data.fetch("revision", 0)) : {"verification" => "manual"}
          end
          raise ArgumentError, "DEPLOYMENT_ENVIRONMENT_REQUIRED" if key == "deployment" && !%w[Test Staging Production].include?(value["environment"])
          if key == "implementation"
            data["revision"] = data.fetch("revision", 0) + 1
            data["approvals"] = {}
            data["contributors"] = (data.fetch("contributors", []) + [actor["id"]]).uniq
          end
          data["evidence"] ||= {}
          data["evidence"][key] ||= []
          invalidated = {"implementation" => %w[code completion], "scope" => GatePolicy::APPROVERS.keys,
            "analysis" => GatePolicy::APPROVERS.keys, "test_cases" => %w[test retest ba pm completion],
            "test_build" => %w[code test retest ba pm completion], "test" => %w[test retest ba pm completion],
            "retest" => %w[retest ba pm completion], "retest_not_needed" => %w[retest ba pm],
            "deployment" => %w[pm], "smoke" => %w[pm completion], "completion" => %w[completion], "handover" => %w[handover]}.fetch(key, [])
          invalidated.each { |approval| data.fetch("approvals", {}).delete(approval) }
          data["evidence"][key] << receipt(actor, data, reference).merge(value.slice("result", "environment")).merge(verification)
        when "checklist_add"
          raise ArgumentError, "ASSIGNEE_OR_PM_REQUIRED" unless wp.assigned_to_id == actor["id"] || actor["role"] == "PM"
          text = value.fetch("text").to_s.strip
          raise ArgumentError, "CHECKLIST_TEXT_REQUIRED" unless (5..2000).cover?(text.length)
          data["checklist"] ||= []
          identifier = Digest::SHA256.hexdigest("#{wp.id}:#{text}")[0, 16]
          raise ArgumentError, "DUPLICATE_CHECKLIST_ITEM" if data["checklist"].any? { |entry| entry["id"] == identifier }
          data["checklist"] << {"id" => identifier, "text" => text, "done" => false}
          data["approvals"] = {}
        when "checklist"
          raise ArgumentError, "ASSIGNEE_OR_PM_REQUIRED" unless wp.assigned_to_id == actor["id"] || actor["role"] == "PM"
          entry = data.fetch("checklist").find { |item| item["id"] == value["id"] }
          raise ArgumentError, "CHECKLIST_ITEM_NOT_FOUND" unless entry
          validate_reference(reference) if value["done"]
          raise ArgumentError, "BOOLEAN_REQUIRED" unless [true, false].include?(value["done"])
          entry.merge!(receipt(actor, data, reference)).merge!("done" => value["done"])
          data["approvals"] = {}
        when "approve"
          key = value.fetch("key")
          wp.qldapm_gate = data
          raise ArgumentError, "APPROVER_DENIED_OR_SELF_APPROVAL" unless @policy.can_approve?(wp.qldapm_snapshot, actor, key)
          validate_reference(reference)
          evidence_key = key == "code" ? "implementation" : key == "pm" || key == "ba" ? "test" : key
          evidence_key = "retest_not_needed" if key == "retest" && @policy.evidence?(data, "retest_not_needed")
          raise ArgumentError, "CURRENT_EVIDENCE_REQUIRED" unless @policy.evidence?(data, evidence_key)
          data["approvals"] ||= {}
          data["approvals"][key] = receipt(actor, data, reference)
        when "reviewer"
          raise ArgumentError, "PM_REQUIRED" unless actor["role"] == "PM"
          reviewer_id = Integer(value.fetch("user_id"))
          reviewer = User.active.find(reviewer_id)
          role = wp.qldapm_actor(reviewer)["role"]
          raise ArgumentError, "MEMBER_REVIEWER_REQUIRED" unless role == "PM" && reviewer_id != wp.assigned_to_id &&
            !data.fetch("contributors", []).include?(reviewer_id)
          data["reviewer_id"] = reviewer_id
          data["approvals"] = {}
        when "classification"
          raise ArgumentError, "PM_AND_OPEN_WORK_REQUIRED" unless actor["role"] == "PM" && ["NEW", "IN PROGRESS"].include?(wp.status.name)
          validate_reference(reference)
          raise ArgumentError, "CLASSIFICATION_DENIED" unless %w[development business].include?(value["stream"]) &&
            %w[work qa fix_bug].include?(value["kind"])
          data.merge!(value.slice("stream", "kind"))
          data["revision"] = data.fetch("revision", 0) + 1
          data["approvals"] = {}
        when "reason"
          validate_reference(value["text"].to_s)
          validate_reference(reference)
          data["transition_reason"] = {"from" => wp.status.name, "to" => value.fetch("to"),
            "text" => value["text"], "reference" => reference, "actor_id" => actor["id"], "revision" => data.fetch("revision", 0)}
        else
          raise ArgumentError, "GATE_OPERATION_DENIED"
        end
        data["events"] ||= []
        data["events"] << receipt(actor, data, reference).merge("operation" => operation, "lock_version" => wp.lock_version,
          "request_id" => request_id, "request_hash" => request_hash, "value_hash" => Digest::SHA256.hexdigest(JSON.generate(value)))
        wp.qldapm_gate = data
        User.execute_as(@user) { raise ActiveRecord::RecordInvalid, wp unless wp.save }
        # Native work-package journaling stores the actor; the receipt is retained in the structured gate.
        {"id" => wp.id, "lockVersion" => wp.lock_version, "gate" => wp.qldapm_gate}
      end
    end

    private

    def validate_reference(reference)
      raise ArgumentError, "EVIDENCE_REFERENCE_REQUIRED" if reference.length < 5 || reference.length > 2000
      raise ArgumentError, "REFERENCE_SCHEME_DENIED" if reference.match?(/\A(?:javascript|data|file):/i)
    end

    def receipt(actor, data, reference)
      {"actor_id" => actor["id"], "role" => actor["role"], "revision" => data.fetch("revision", 0),
       "reference" => reference, "at" => Time.now.utc.iso8601}
    end
  end
end

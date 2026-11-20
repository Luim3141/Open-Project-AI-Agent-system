module Qldapm
  # This policy is shared by preview and the database write guard; no AI-specific bypass.
  class GatePolicy
    def self.actor_role(roles)
      recognized = roles.map { |role| role == "BA" ? "BA-PM" : role } & %w[PM BA-PM BE FE QA]
      return "PM" if recognized.include?("PM")
      # BA-PM is the historical BA policy key, not a union with PM permissions.
      recognized.first
    end

    EPIC = {
      ["NEW", "READY"] => %w[PM], ["READY", "NEW"] => %w[PM],
      ["READY", "IN PROGRESS"] => %w[PM], ["IN PROGRESS", "REVIEW"] => %w[PM],
      ["REVIEW", "DONE"] => %w[PM], ["REVIEW", "IN PROGRESS"] => %w[PM],
      ["DONE", "IN PROGRESS"] => %w[PM], ["CANCELLED", "NEW"] => %w[PM]
    }.merge(%w[NEW READY].concat(["IN PROGRESS", "REVIEW"]).to_h { |s| [[s, "CANCELLED"], %w[PM]] }).freeze
    TASK = {
      ["NEW", "IN ANALYSIS"] => %w[BA-PM PM], ["IN ANALYSIS", "READY FOR DEV"] => %w[BA-PM PM],
      ["READY FOR DEV", "IN PROGRESS"] => %w[BE FE PM], ["IN PROGRESS", "CODE REVIEW"] => %w[BE FE PM],
      ["CODE REVIEW", "IN PROGRESS"] => %w[BE FE PM], ["CODE REVIEW", "READY FOR TEST"] => %w[BE FE PM],
      ["READY FOR TEST", "IN TESTING"] => %w[QA PM], ["IN TESTING", "IN PROGRESS"] => %w[QA PM],
      ["IN TESTING", "REVIEW"] => %w[QA PM], ["REVIEW", "IN PROGRESS"] => %w[BE FE BA-PM PM],
      ["REVIEW", "IN TESTING"] => %w[QA PM], ["REVIEW", "READY FOR RELEASE"] => %w[PM],
      ["READY FOR RELEASE", "DONE"] => %w[PM], ["DONE", "IN PROGRESS"] => %w[PM]
    }.freeze
    BUSINESS = { ["NEW", "IN PROGRESS"] => %w[PM BA-PM BE FE QA],
      ["IN PROGRESS", "REVIEW"] => %w[PM BA-PM BE FE QA], ["REVIEW", "DONE"] => %w[PM BA-PM BE FE QA],
      ["REVIEW", "IN PROGRESS"] => %w[PM BA-PM BE FE QA], ["DONE", "IN PROGRESS"] => %w[PM BA-PM BE FE QA] }.freeze
    DEVELOPMENT = { ["NEW", "IN PROGRESS"] => %w[PM BE FE], ["IN PROGRESS", "CODE REVIEW"] => %w[PM BE FE],
      ["CODE REVIEW", "IN PROGRESS"] => %w[PM BE FE], ["CODE REVIEW", "READY FOR TEST"] => %w[PM BE FE],
      ["READY FOR TEST", "IN TESTING"] => %w[PM QA], ["IN TESTING", "IN PROGRESS"] => %w[PM QA],
      ["IN TESTING", "REVIEW"] => %w[PM QA], ["REVIEW", "IN TESTING"] => %w[PM QA],
      ["REVIEW", "IN PROGRESS"] => %w[PM BE FE], ["REVIEW", "DONE"] => %w[PM BE FE],
      ["DONE", "IN PROGRESS"] => %w[PM BE FE] }.freeze
    APPROVERS = {"scope" => %w[PM], "analysis" => %w[BA-PM PM], "code" => %w[PM BE FE],
      "test" => %w[QA PM], "retest" => %w[QA PM], "ba" => %w[BA-PM], "pm" => %w[PM],
      "completion" => %w[PM BA-PM BE FE QA], "handover" => %w[PM]}.freeze
    REVERSE = [["READY", "NEW"], ["CODE REVIEW", "IN PROGRESS"], ["IN TESTING", "IN PROGRESS"],
      ["REVIEW", "IN PROGRESS"], ["REVIEW", "IN TESTING"], ["DONE", "IN PROGRESS"], ["CANCELLED", "NEW"]].freeze

    def edges(item)
      case item["type"]
      when "Epic" then EPIC
      when "Task" then TASK
      when "Subtask" then item.dig("data", "stream") == "development" ? DEVELOPMENT : BUSINESS
      else {}
      end
    end

    def can_approve?(item, actor, key)
      allowed = APPROVERS.key?(key) && actor["role"] == "PM" && item.dig("data", "reviewer_id") &&
        item.dig("data", "reviewer_id") != item["assignee"] &&
        !item.dig("data", "contributors").to_a.include?(item.dig("data", "reviewer_id"))
      independent = actor["id"] != item["assignee"] && !item.dig("data", "contributors").to_a.include?(actor["id"])
      if %w[code completion].include?(key)
        allowed && independent && actor["id"] == item.dig("data", "reviewer_id")
      elsif %w[test retest pm handover].include?(key)
        allowed && independent
      else
        allowed && independent
      end
    end

    def errors(item, actor, from, to)
      data, children = item.fetch("data"), item.fetch("children", [])
      errors = []
      return ["TRANSITION_DENIED"] unless actor["role"] == "PM" && edges(item).key?([from, to])
      if item["type"] == "Subtask"
        errors << "STREAM_REQUIRED" unless %w[development business].include?(data["stream"])
        if from == "NEW" || from == "IN PROGRESS"
          errors << "ASSIGNEE_ONLY" unless actor["id"] == item["assignee"] || actor["role"] == "PM"
        end
      end
      if from == "CODE REVIEW"
        errors << "REVIEWER_ONLY" unless can_approve?(item, actor, "code")
      end
      if to == "CODE REVIEW" && (!data["reviewer_id"] || data["reviewer_id"] == item["assignee"] ||
          data.fetch("contributors", []).include?(data["reviewer_id"]))
        errors << "REVIEWER_REQUIRED"
      end
      if item["type"] == "Subtask" && %w[REVIEW DONE].include?(from) && to == "IN PROGRESS"
        errors << "REVIEWER_ONLY" unless actor["role"] == "PM" || can_approve?(item, actor, "completion")
      end
      if REVERSE.include?([from, to]) || to == "CANCELLED"
        reason = data["transition_reason"] || {}
        errors << "CHANGE_REASON_REQUIRED" unless reason["from"] == from && reason["to"] == to &&
          reason["text"].to_s.strip.length >= 5 && reason["actor_id"] == actor["id"] && reason["revision"] == data["revision"]
        errors << "CHANGE_EVIDENCE_REQUIRED" unless reason["reference"].to_s.strip.length >= 5
      end
      require_evidence = ->(key) { errors << "EVIDENCE_#{key.upcase}_REQUIRED" unless evidence?(data, key) }
      require_approval = ->(key) { errors << "APPROVAL_#{key.upcase}_REQUIRED" unless approved?(data, key) }
      checklist = -> { errors << "CHECKLIST_INCOMPLETE" if data.fetch("checklist", []).empty? ||
        data["checklist"].any? { |entry| !entry["done"] || entry["reference"].to_s.empty? || entry["revision"] != data["revision"] } }
      completed_children = -> {
        errors << "CHILDREN_REQUIRED" if children.empty?
        errors << "CHILDREN_NOT_DONE" unless children.all? { |child| child["status"] == "DONE" }
      }
      clear_bugs = -> { errors << "BLOCKING_BUGS" if item.fetch("blocking_bugs", []).any? { |bug| bug["status"] != "DONE" } }
      case item["type"]
      when "Epic"
        if to == "READY"
          errors << "OWNER_REQUIRED" unless item["assignee"]
          errors << "AC_REQUIRED" if data["acceptance_criteria"].to_s.strip.empty?
          errors << "TASK_REQUIRED" unless children.any? { |child| child["type"] == "Task" }
          require_evidence.call("scope")
          require_approval.call("scope")
        elsif to == "IN PROGRESS" && from == "READY"
          errors << "CHILD_NOT_STARTED" unless children.any? { |c| c["status"] != "NEW" }
        elsif %w[REVIEW DONE].include?(to)
          completed_children.call
          if to == "DONE"
            checklist.call
            require_evidence.call("integration")
            require_evidence.call("handover")
            require_approval.call("handover")
            clear_bugs.call
          end
        end
      when "Task"
        case to
        when "IN ANALYSIS"
          require_evidence.call("story")
          errors << "AC_REQUIRED" if data["acceptance_criteria"].to_s.strip.empty?
          require_evidence.call("scope"); require_approval.call("scope")
        when "READY FOR DEV"
          errors << "AC_REQUIRED" if data["acceptance_criteria"].to_s.strip.empty?
          require_evidence.call("analysis"); require_approval.call("analysis"); require_approval.call("scope")
        when "IN PROGRESS"
          errors << "DEVELOPMENT_CHILD_REQUIRED" if from == "READY FOR DEV" && children.none? { |c| c["type"] == "Subtask" && c["stream"] == "development" }
          if from == "IN TESTING"
            require_evidence.call("bug")
            errors << "FIX_BUG_REQUIRED" if item.fetch("blocking_bugs", []).empty?
          end
        when "CODE REVIEW" then checklist.call; require_evidence.call("implementation")
        when "READY FOR TEST"
          require_approval.call("code"); require_evidence.call("test_build"); require_evidence.call("test_cases")
          errors << "REVIEWER_ONLY" unless actor["id"] == data["reviewer_id"] && can_approve?(item, actor, "code")
        when "IN TESTING" then require_evidence.call("test_cases")
        when "REVIEW"
          require_evidence.call("test"); require_approval.call("test"); clear_bugs.call
          errors << "QA_CHILD_NOT_DONE" if children.any? { |c| c["kind"] == "qa" && c["status"] != "DONE" }
        when "READY FOR RELEASE"
          %w[code ba pm].each { |key| require_approval.call(key) }
          if evidence?(data, "retest_not_needed")
            require_approval.call("retest")
          else
            require_evidence.call("retest"); require_approval.call("retest")
          end
          clear_bugs.call
        when "DONE"
          completed_children.call; checklist.call; clear_bugs.call
          %w[code ba pm retest].each { |key| require_approval.call(key) }
          require_evidence.call("deployment"); require_evidence.call("smoke")
        end
      when "Subtask"
        if to == "CODE REVIEW"
          checklist.call; require_evidence.call("implementation")
        elsif to == "READY FOR TEST"
          require_approval.call("code"); require_evidence.call("test_cases"); require_evidence.call("test_build")
          errors << "REVIEWER_ONLY" unless actor["id"] == data["reviewer_id"] && can_approve?(item, actor, "code")
        elsif to == "IN TESTING"
          require_evidence.call("test_cases")
        elsif to == "IN PROGRESS" && from == "IN TESTING"
          require_evidence.call("bug")
        elsif to == "REVIEW"
          checklist.call
          require_evidence.call(data["stream"] == "development" ? "test" : "completion")
          require_approval.call("test") if data["stream"] == "development"
          clear_bugs.call if data["kind"] == "qa" || data["stream"] == "development"
        elsif to == "DONE"
          checklist.call; require_approval.call("completion")
          errors << "REVIEWER_ONLY" unless can_approve?(item, actor, "completion")
          clear_bugs.call if data["kind"] == "qa" || data["kind"] == "fix_bug"
        end
      end
      errors.uniq
    end

    def evidence?(data, key)
      record = data.fetch("evidence", {}).fetch(key, []).last
      record && record["revision"] == data["revision"] && record["reference"].to_s.strip.length >= 5 && record["actor_id"] &&
        (!%w[test retest smoke].include?(key) || record["result"] == "passed") &&
        (key != "deployment" || record["environment"] == "Test")
    end

    def approved?(data, key)
      approval = data.fetch("approvals", {})[key]
      approval && approval["revision"] == data["revision"] && approval["actor_id"] && approval["reference"].to_s.length >= 5
    end
  end
end

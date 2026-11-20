require "digest"

module Qldapm
  class Insights
    def initialize(project, user)
      @project, @user = project, user
      raise ArgumentError, "PROJECT_DENIED" unless project.identifier == "qldapm-local"
      @item = WorkPackage.visible(user).where(project:).first!
      @role = @item.qldapm_actor(user)["role"]
      raise ArgumentError, "ACTIVE_MEMBER_REQUIRED" unless @role
    end

    def report(target, days, now: Time.current)
      target, days = Integer(target), Integer(days)
      raise ArgumentError, "PM_OR_SELF_REQUIRED" unless target == @user.id || @role == "PM"
      raise ArgumentError, "WINDOW_DENIED" unless [7, 30, 90].include?(days)
      subject = User.active.find(target)
      raise ArgumentError, "SUBJECT_MEMBER_REQUIRED" unless @item.qldapm_actor(subject)["role"]
      events = collect
      data = InsightMetrics.calculate(events, target, now - days.days, now)
      previous = InsightMetrics.calculate(events, target, now - (days * 2).days, now - days.days)
      data["previous_window"] = previous.except("events")
      data["trend"] = {"coverage" => data["coverage"] == "insufficient" || previous["coverage"] == "insufficient" ? "insufficient" : "partial",
        "task_completion_action_delta" => data.dig("metrics", "task_completion_actions", "numerator") - previous.dig("metrics", "task_completion_actions", "numerator"),
        "notice" => "Process action delta, not employee improvement/decline or a ranking."}
      data["subject"] = subject.name
      data["role_current_only"] = Member.find_by!(project_id: @project.id, user_id: subject.id, entity_id: nil).roles
        .map { |role| role.name.delete_prefix("QLDAPM ") }.find { |role| %w[PM BA BA-PM BE FE QA].include?(role) }
      data["role_context"] = {"PM" => "Planning, blockers, independent acceptance and release evidence",
        "BA" => "AC/scope clarity and business acceptance", "BA-PM" => "AC/scope clarity and business acceptance", "BE" => "Implementation/review/test evidence",
        "FE" => "Implementation/review/test evidence", "QA" => "Test cases, failures, retest and verification"}.fetch(data["role_current_only"])
      sprints = Sprint.where(project: @project)
      current = sprints.active.where.not(start_date: nil, finish_date: nil).order(:start_date).last
      recent = sprints.completed.where.not(start_date: nil, finish_date: nil).order(finish_date: :desc).limit(3)
      data["sprints"] = ([current].compact + recent).map do |sprint|
        start = sprint.start_date.in_time_zone("Asia/Bangkok").beginning_of_day
        finish = [sprint.finish_date.in_time_zone("Asia/Bangkok").end_of_day, now].min
        {"id" => sprint.id, "name" => sprint.name, "start" => start.iso8601, "finish" => finish.iso8601,
         "report" => InsightMetrics.calculate(events, target, start, finish), "commitment_coverage" => "insufficient"}
      end
      data["sprint_notice"] = "Planning/undated sprints are not started or inferred; no retrospective commitment baseline."
      data
    end

    def snapshot(target, days, now: Time.current)
      data = report(target, days, now:)
      fingerprint = Digest::SHA256.hexdigest(JSON.generate(data))
      InsightSnapshot.create_or_find_by!(project: @project, user_id: target, days:, input_hash: fingerprint) { |row| row.report = data }
    end

    def self.daily
      Project.where(identifier: "qldapm-local").each do |project|
        item = project.work_packages.first
        next unless item
        members = User.active.where(id: Member.where(project_id: project.id, entity_id: nil).select(:user_id)).select { |user| item.qldapm_actor(user)["role"] }
        pm = members.find { |user| item.qldapm_actor(user)["role"] == "PM" }
        next unless pm
        engine = new(project, pm)
        # Daily boundaries are deterministic; re-running the same day does not add duplicate reports.
        cutoff = Time.current.in_time_zone("Asia/Bangkok").change(hour: 23, min: 55).utc
        cutoff -= 1.day if cutoff > Time.current
        members.each { |user| [7, 30, 90].each { |days| engine.snapshot(user.id, days, now: cutoff) } }
      end
    end

    private

    def collect
      items = WorkPackage.visible(@user).where(project: @project).includes(:type).to_a
      journals = Journal.where(journable_type: "WorkPackage", journable_id: items.map(&:id)).includes(:data)
        .order(:version).group_by(&:journable_id)
      statuses = Status.pluck(:id, :name).to_h
      provenance = MutationReceipt.where(project: @project).where.not(journal_id: nil).pluck(:journal_id, :provenance).to_h
      events = []
      items.each do |item|
        # Imported simulation is source context, not observed human effort or quality.
        next if item.description.to_s.start_with?("> JIRA IMPORT — SIMULATION ONLY.")
        previous = nil
        journals.fetch(item.id, []).each do |journal|
          current = journal.data
          if previous && journal.user_id && !%w[import system_update].include?(journal.cause_type)
            base = {"actor_id" => journal.user_id, "assignee_id" => current.assigned_to_id, "work_package_id" => item.id,
                    "type" => item.type.name, "at" => journal.created_at, "source" => "journal:#{journal.id}", "provenance" => provenance.fetch(journal.id, "unknown")}
            if previous.assigned_to_id != current.assigned_to_id
              events << base.merge("kind" => "assignment", "previous_assignee_id" => previous.assigned_to_id)
            end
            if previous.subject != current.subject || previous.description != current.description
              events << base.merge("kind" => "scope_change")
            end
            old_status, new_status = previous.status_id, current.status_id
            if old_status != new_status
              events << {"kind" => "status", "actor_id" => journal.user_id, "assignee_id" => current.assigned_to_id,
                "from" => statuses[old_status], "to" => statuses[new_status], "work_package_id" => item.id,
                "type" => item.type.name, "at" => journal.created_at, "source" => "journal:#{journal.id}", "provenance" => provenance.fetch(journal.id, "unknown")}
            end
          end
          previous = current
        end
        gate = item.qldapm_gate
        gate.fetch("evidence", {}).each do |key, rows|
          rows.each do |row|
            events << row.slice("actor_id", "revision", "result", "role", "reference", "verification", "snapshot_hash").merge(
              "kind" => "evidence", "key" => key, "work_package_id" => item.id, "at" => Time.iso8601(row.fetch("at")),
              "source" => "gate:#{item.id}:#{key}:#{row['at']}", "provenance" => row["verification"] == "automatic" ? "broker_test_receipt" : "manual_or_legacy_assertion")
          end
        end
        gate.fetch("events", []).select { |row| row["operation"] == "approve" }.each do |row|
          events << row.slice("actor_id", "revision", "role", "reference").merge("kind" => "approval", "work_package_id" => item.id,
            "at" => Time.iso8601(row.fetch("at")), "source" => "gate:#{item.id}:approve:#{row['at']}", "provenance" => "unknown_assertion")
        end
      end
      events.sort_by { |event| [event["at"], event["source"]] }
    end
  end
end

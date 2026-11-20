require "time"

module Qldapm
  class InsightMetrics
    VERSION = 1
    def self.calculate(events, actor, from, to)
      selected = events.select { |event| event["actor_id"] == actor && event["at"] >= from && event["at"] < to }
      delivery = selected.select { |event| event["kind"] == "status" && event["type"] == "Task" }
      completions = delivery.select { |event| event["to"] == "DONE" && event["from"] != "DONE" }
      reopens = delivery.select { |event| event["from"] == "DONE" && event["to"] != "DONE" }
      evidence = events.select { |event| event["actor_id"] == actor && event["at"] < to && event["kind"] == "evidence" && %w[test retest smoke].include?(event["key"]) }
      tests = evidence.group_by { |event| [event["work_package_id"], event["key"], event["revision"]] }.values
        .map { |rows| rows.min_by { |row| row["at"] } }.select { |row| row["at"] >= from }
      passing = tests.count { |event| event["result"] == "passed" }
      cycles, waits = [], []
      events.select { |event| event["type"] == "Task" }.group_by { |event| event["work_package_id"] }.each_value do |rows|
        started, waiting = nil, nil
        rows.sort_by { |row| [row["at"], row["source"]] }.each do |row|
          next if row["at"] >= to
          started = nil if started && row["assignee_id"] != actor
          waiting = nil if waiting && row["assignee_id"] != actor
          next unless row["kind"] == "status"
          if row["to"] == "IN PROGRESS" && row["from"] == "READY FOR DEV" && row["assignee_id"] == actor
            started = row
          elsif row["to"] == "DONE" && started
            cycles << {"seconds" => row["at"] - started["at"], "sources" => [started["source"], row["source"]]} if row["at"] >= from
            started = nil
          end
          if waiting && row["from"] == waiting["to"]
            waits << {"status" => waiting["to"], "seconds" => row["at"] - waiting["at"], "sources" => [waiting["source"], row["source"]]} if row["at"] >= from
            waiting = nil
          end
          waiting = row if %w[CODE\ REVIEW READY\ FOR\ TEST REVIEW].include?(row["to"]) && row["assignee_id"] == actor
        end
      end
      {"version" => VERSION, "from" => from.utc.iso8601, "to" => to.utc.iso8601, "timezone" => "Asia/Bangkok",
       "subject_id" => actor, "coverage" => selected.empty? ? "insufficient" : "partial",
       "metrics" => {"task_completion_actions" => {"numerator" => completions.size, "denominator" => delivery.size,
           "sources" => completions.map { |event| event["source"] }, "meaning" => "Status actions by actor, not personal productivity"},
         "task_reopen_actions" => {"count" => reopens.size, "denominator" => delivery.size, "sources" => reopens.map { |event| event["source"] }},
         "first_recorded_test_pass" => {"numerator" => passing, "denominator" => tests.size,
           "ratio" => tests.empty? ? nil : passing.to_f / tests.size, "sources" => tests.map { |event| event["source"] },
           "meaning" => "Actor's first recorded assertion per revision, not independently proven test quality"},
         "review_actions" => {"count" => selected.count { |event| event["kind"] == "approval" },
           "sources" => selected.select { |event| event["kind"] == "approval" }.map { |event| event["source"] }},
         "cycle_time" => {"samples" => cycles, "mean_seconds" => cycles.empty? ? nil : cycles.sum { |row| row["seconds"] } / cycles.size,
           "sample_count" => cycles.size, "coverage" => cycles.empty? ? "insufficient" : "partial", "meaning" => "Task READY FOR DEV→IN PROGRESS→DONE with unchanged recorded assignee; not effort hours"},
         "handoff_wait" => {"samples" => waits, "sample_count" => waits.size, "coverage" => waits.empty? ? "insufficient" : "partial",
           "meaning" => "Observed review/test queue intervals, not blame or idle time"},
         "scope_changes" => {"count" => selected.count { |event| event["kind"] == "scope_change" },
           "sources" => selected.select { |event| event["kind"] == "scope_change" }.map { |event| event["source"] }},
         "blocked_time" => {"value" => nil, "coverage" => "insufficient", "reason" => "Needs explicit blocker start/end evidence"},
         "commitment_carryover" => {"value" => nil, "coverage" => "insufficient", "reason" => "No verified pre-sprint commitment snapshot"}},
       "events" => selected.map { |event| event.merge("at" => event["at"].utc.iso8601) },
       "provenance" => selected.group_by { |event| event["provenance"] || "unknown" }.transform_values(&:size),
       "limitations" => ["No score, ranking or automatic HR decision", "Task/Subtask/Epic are not summed as throughput",
         "Creation/import and simulated estimates are excluded", "Unknown provenance is not attributed as human effort",
         "Current role is not applied retrospectively", "Missing data is not zero performance"]}
    end
  end
end

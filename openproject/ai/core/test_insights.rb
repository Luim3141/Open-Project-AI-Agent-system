require "time"
require_relative "overlay/app/services/qldapm/insight_metrics"
from, to = Time.utc(2026, 10, 1), Time.utc(2026, 10, 8)
events = [
  {"kind" => "status", "actor_id" => 21, "type" => "Task", "from" => "IN PROGRESS", "to" => "DONE", "at" => from, "source" => "journal:1"},
  {"kind" => "status", "actor_id" => 21, "type" => "Subtask", "from" => "IN PROGRESS", "to" => "DONE", "at" => from, "source" => "journal:2"},
  {"kind" => "status", "actor_id" => 22, "type" => "Task", "from" => "IN PROGRESS", "to" => "DONE", "at" => from, "source" => "journal:3"},
  {"kind" => "status", "actor_id" => 21, "type" => "Task", "from" => "IN PROGRESS", "to" => "DONE", "at" => to, "source" => "journal:4"},
  {"kind" => "evidence", "actor_id" => 21, "key" => "test", "result" => "failed", "revision" => 1, "work_package_id" => 5, "at" => from, "source" => "gate:5:a"},
  {"kind" => "evidence", "actor_id" => 21, "key" => "test", "result" => "passed", "revision" => 1, "work_package_id" => 5, "at" => from + 1, "source" => "gate:5:b"}
]
result = Qldapm::InsightMetrics.calculate(events, 21, from, to)
raise "DOUBLE_COUNT_OR_WINDOW" unless result["metrics"]["task_completion_actions"]["numerator"] == 1
raise "FIRST_PASS_INVENTED" unless result["metrics"]["first_recorded_test_pass"]["ratio"] == 0.0
before_window_failure = events.map { |row| row["source"] == "gate:5:a" ? row.merge("at" => from - 1) : row }
raise "PRIOR_FAILURE_HIDDEN_BY_WINDOW" unless Qldapm::InsightMetrics.calculate(before_window_failure, 21, from, to).dig("metrics", "first_recorded_test_pass", "denominator") == 0
empty = Qldapm::InsightMetrics.calculate(events, 19, from, to)
raise "MISSING_IS_NOT_ZERO_PERFORMANCE" unless empty["coverage"] == "insufficient" && empty["metrics"]["first_recorded_test_pass"]["ratio"].nil?
raise "RANKING" if result.key?("score") || result.key?("rank")
def status(at, from, to, source, owner = 21)
  {"kind" => "status", "actor_id" => 22, "assignee_id" => owner, "type" => "Task", "work_package_id" => 6,
   "from" => from, "to" => to, "at" => at, "source" => source}
end
timeline = [status(from - 60, "READY FOR DEV", "IN PROGRESS", "journal:10"),
  status(from, "IN PROGRESS", "CODE REVIEW", "journal:11"), status(from + 30, "CODE REVIEW", "READY FOR TEST", "journal:12"),
  status(from + 60, "READY FOR TEST", "DONE", "journal:13")]
intervals = Qldapm::InsightMetrics.calculate(timeline, 21, from, to)
raise "CYCLE_BEFORE_WINDOW_LOST" unless intervals.dig("metrics", "cycle_time", "samples").first.fetch("seconds") == 120
raise "HANDOFF_INTERVALS" unless intervals.dig("metrics", "handoff_wait", "samples").map { |row| row["seconds"] } == [30, 30]
timeline.insert(1, {"kind" => "assignment", "actor_id" => 19, "assignee_id" => 23, "type" => "Task", "work_package_id" => 6,
                    "at" => from - 30, "source" => "journal:14"})
raise "REASSIGNED_CYCLE_ATTRIBUTED" unless Qldapm::InsightMetrics.calculate(timeline, 21, from, to).dig("metrics", "cycle_time", "samples").empty?
puts "Insights fixtures PASS: windows, actor attribution, parent/child counts, first failure, missing data, no ranking."

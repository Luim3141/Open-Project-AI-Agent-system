require 'action_view'
require 'json'

def render_brief(report, alerts = [])
  view = ActionView::Base.with_empty_template_cache.with_view_paths(['/views'])
  view.assign(dashboard: {'daily_brief' => report, 'workflow_alerts' => alerts})
  view.render(partial: 'qldapm_ai/daily_brief')
end

ready = {'state' => 'READY', 'observed_at' => 1792160000, 'trace_id' => 'synthetic-trace',
         'snapshot' => {'count' => 2, 'by_status' => {'<script>alert(1)</script>' => 1, 'DONE' => 1}, 'overdue_ids' => [1]}}
html = render_brief(ready)
raise 'XSS_NOT_ESCAPED' if html.include?('<script>') || !html.include?('&lt;script&gt;')
raise 'READY_CONTENT_OR_LINK_MISSING' unless html.include?('/work_packages/1') && html.include?('synthetic-trace') && html.include?('UTC+7')
raise 'ACCESSIBLE_HEADING_MISSING' unless html.include?('aria-labelledby="daily-brief-heading"')
%w[STALE DENIED OFFLINE MISSING].each do |state|
  hidden = render_brief(ready.merge('state' => state, 'snapshot' => {'count' => 987654, 'by_status' => {'PRIVATE_SHOULD_STAY_HIDDEN' => 1}, 'overdue_ids' => [987654]}))
  raise "HIDDEN_DATA_LEAK:#{state}" if hidden.include?('987654') || hidden.include?('PRIVATE_SHOULD_STAY_HIDDEN') || hidden.include?('/work_packages/')
end
raise 'EMPTY_STATE_MISSING' unless render_brief(nil).include?('Chưa có tóm tắt')
alert_html = render_brief(nil, [{'workflow_id' => 'qldapmDailyBrief', 'day' => '2026-10-17',
                               'trace_id' => '<script>unsafe</script>', 'observed_at' => 1792160000,
                               'error_message' => 'PRIVATE_RAW_ERROR_SHOULD_NOT_RENDER'}])
raise 'ERROR_ALERT_PRIVACY_OR_XSS' if alert_html.include?('<script>') || alert_html.include?('PRIVATE_RAW_ERROR_SHOULD_NOT_RENDER')
raise 'ERROR_ALERT_EMPTY_DAILY_OR_HEADING' unless alert_html.include?('workflow-alert-heading') && alert_html.include?('Tổng hợp hằng ngày') && alert_html.include?('&lt;script&gt;')
puts JSON.generate({passed: true, actual_action_view: true, ready_and_four_empty_states: true,
                    xss_escaped: true, native_links_scoped: true, workflow_alert_without_daily_snapshot: true,
                    workflow_alert_raw_error_hidden: true, database_or_network_used: false})

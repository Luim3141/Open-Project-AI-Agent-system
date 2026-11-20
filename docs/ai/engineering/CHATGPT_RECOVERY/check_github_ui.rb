# Run against supplied host source; no browser, Rails requests or business writes.
require 'json'
require 'erb'
require 'active_support/all'

source = JSON.parse(STDIN.read)
view = source.fetch('view')
controller = source.fetch('controller')
initial = view.split('<%', 3).last.split('%>', 2).first

@engineering = {'github' => {'status' => 'OFFLINE', 'prs' => []}}
context = binding
eval(initial, context)
raise 'API failure fabricated PR rows' unless context.local_variable_get(:github_prs).empty?
raise 'Empty backlog fabricated count' unless context.local_variable_get(:total_backlog) == 0
@engineering_wp = {'id' => 379, 'lockVersion' => 0}
eval(initial, context)
raise 'Native zero lock version lost' unless context.local_variable_get(:parent_lock) == 0
@engineering_wp = {}
eval(initial, context)
raise 'Missing Native lock fabricated' unless context.local_variable_get(:parent_lock).nil?
@engineering = {'github' => {'status' => 'ONLINE', 'prs' => [
  {'number' => 7, 'wp_id' => 387}, {'number' => 8}
]}}
eval(initial, context)
rows = context.local_variable_get(:github_prs)
raise 'New PR mapping lost' unless rows[0]['wp_id'] == 387
raise 'Unknown PR falsely mapped to parent' unless rows[1]['wp_id'].nil?

branch = controller.split("when 'engineering_github_sync'", 2).last.split("when 'engineering_report_generate'", 2).first
@result = {'status' => 'SUCCESS', 'total_prs_synced' => 0}
eval(branch, binding)
raise 'Empty sync fabricated PR count' unless @result['message'].include?('0')
raise 'Empty sync claimed five PRs' if @result['message'].include?('5 Pull Requests')

%w[SYNC_FAILED PARTIAL].each do |status|
  @error = nil
  @result = {'status' => status, 'total_prs_synced' => 1, 'error' => 'OPENPROJECT_403'}
  eval(branch, binding)
  raise "#{status} reported success" unless @error&.include?('OPENPROJECT_403')
end
raise 'Offline state still renders success toast' unless view.include?('if @result.present? && @error.blank?')
raise 'GitHub badge hardcoded ONLINE' if view.include?('GITHUB REST API: ONLINE')
puts 'PASS: empty/offline projection, actual zero count, failure/partial error, toast and status badge contracts'

"""Actual Rails AiBridge signed HTTP read-back; output is allowlisted, never raw telemetry."""
import datetime
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).parent
ruby=r"""
require 'json'
owner=User.find(18);project=Project.find(6)
raise 'OWNER_SCOPE_INVALID' unless project.identifier=='ai-dev-demo' && Qldapm::Rbac.ai_system_owner?(project,owner,fresh:true)
def call(project,owner,action,args={})
 Qldapm::AiBridge.call(project,owner,'command',{action:action,arguments:args,idempotency_key:SecureRandom.uuid})['result']
end
started=Process.clock_gettime(Process::CLOCK_MONOTONIC)
status=call(project,owner,'engineering_status')
run_id='b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
summary=call(project,owner,'get_execution_monitor',{id:run_id})['execution_summary']
raise 'WRONG_RUN' unless summary['id']==run_id && summary['native_id']==391
raise 'RAW_FAILURE_MISCLASSIFIED' unless summary.dig('failure','category')=='PROVIDER_QUOTA_EXHAUSTED'
raise 'BUDGET_MISMATCH' unless summary.dig('budget','calls_used')==12 && summary.dig('budget','provider_response_count')==11 && summary.dig('budget','cumulative_calls')==36
raise 'UNSAFE_PROVIDER_RETRY' unless summary.dig('resume','eligible')==false
raise 'FALSE_RUNNING' unless status['profiles'].all?{|p|p['current_state']!='RUNNING'} && status.dig('queue','active')==0
raise 'MAIN_MODE_CHANGED' unless status['mode']=='OFF'
child=Array(status['backlog']).find{|u|u['native_id']==391}
raise 'CHILD_NOT_IN_BACKLOG' unless child && child.dig('failure','category')=='PROVIDER_QUOTA_EXHAUSTED'
dev=Array(status['profiles']).find{|p|p['agent']=='dev'}
raise 'LAST_DEV_MISSING' unless dev.dig('last_activity','native_id')==391 && dev.dig('last_activity','result')=='blocked'
notes=status['notifications'].is_a?(Hash) ? Array(status['notifications']['notifications']) : Array(status['notifications'])
raise 'CHILD_NOTIFICATION_MISSING' unless notes.any?{|n|n['native_id']==391 && n['run_id']==run_id && n['reason_code']=='PROVIDER_QUOTA_EXHAUSTED'}
again=call(project,owner,'engineering_status')
next_notes=again['notifications'].is_a?(Hash) ? Array(again['notifications']['notifications']) : Array(again['notifications'])
note_ids=next_notes.map{|n|n['id']}
raise 'DUPLICATE_NOTIFICATIONS' unless note_ids.uniq==note_ids && status['notification_unread_count']==again['notification_unread_count']
report=Array(status['recent_reports']).first
if report
 report=call(project,owner,'engineering_report_get',{id:report['id']})
end
User.current=owner
html=QldapmAIController.renderer.render(partial:'qldapm_ai/engineering_command_center',assigns:{project:project,engineering:status,engineering_wp:Array(status['tasks']).find{|t|t['id']==379},reports:status['recent_reports'],schedule:status['reporting_schedule'],notifications:status['notifications'],ui_mode:'modern'})
dom=Nokogiri::HTML.fragment(html)
raise 'MAIN_ERB_IDENTITY_OR_BUDGET_MISSING' unless dom.at_css('#tab-backlog').text.include?('WP #391') && dom.at_css('#tab-mission').text.include?('PROVIDER_QUOTA_EXHAUSTED') && dom.at_css('#tab-workforce').text.include?('Lượt thực thi gần nhất: WP #391')
raise 'MAIN_READER_NOT_WIRED' unless dom.at_css('#qcc-report-raw') && dom.at_css('#qcc-report-toc')
puts({status:'PASS',utc:Time.now.utc.iso8601,route:'Actual Rails AiBridge HMAC HTTP + Native authorization; no GUI',elapsed_seconds:(Process.clock_gettime(Process::CLOCK_MONOTONIC)-started).round(3),
 mode:status['mode'],queue:status['queue'],worker:status['delivery_worker'].slice('state','seen','run_id'),
 wp391:summary.slice('id','native_id','title','task_status','native_status','stage','failure','budget','resume'),
 dev:dev.slice('agent','current_state','current_run','last_activity').tap{|d|d['last_activity']=d['last_activity'].slice('native_id','run_id','result','error','budget')},
 notification_unread_count:status['notification_unread_count'],child_notifications:notes.select{|n|n['native_id']==391}.map{|n|n.slice('id','run_id','reason_code','level','link')},
 notification_repoll_dedup:true,integration_health:status['integration_health'],report_readback:report && report.slice('id','report_type','source_state','source_status','ai_narrative_status'),
 main_erb:'PASS; real signed status rendered with production Rails view, not browser/session UAT',native_379_representations:{native_record_count:Array(status['tasks']).count{|t|t['id']==379},engineering_units:Array(status['backlog']).select{|u|u['native_id']==379}.map{|u|u['unit']}},
 provider_inference_calls:0,owner_uat:'PENDING OWNER'} .to_json)
"""
p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner','-'],input=ruby.encode(),capture_output=True,timeout=150)
if p.returncode:
    # No command payload is printed; Rails errors are retained in a private operator log.
    import os
    private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase3_1-readback-failure.log'
    private.write_bytes(p.stdout+p.stderr)
    raise RuntimeError('SIGNED_READBACK_FAILED_PRIVATE_LOG '+str(private))
result=json.loads(p.stdout.decode().splitlines()[-1])
(OUT/'main-readback.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))

"""Fresh signed Rails read-back and actual template render, no GUI/model calls."""
import json,subprocess,sys
from pathlib import Path

out=Path(__file__).parent;label=sys.argv[1]
assert label in {'before391','final'}
ruby=r'''
require 'json';require 'nokogiri'
owner=User.find(18);project=Project.find(6);User.current=owner
raise 'OWNER_PROJECT_INVALID' unless project.identifier=='ai-dev-demo' && Qldapm::Rbac.ai_system_owner?(project,owner,fresh:true)
def command(project,owner,action,args={})
 Qldapm::AiBridge.call(project,owner,'command',{action:action,arguments:args,idempotency_key:SecureRandom.uuid})['result']
end
status=command(project,owner,'engineering_status')
summary=command(project,owner,'get_execution_monitor',{id:'b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'})['execution_summary']
raise 'WRONG_RUN' unless summary['native_id']==391
raise 'CONTROL_ACTIVE' unless status['mode']=='OFF' && status.dig('queue','active')==0
raise 'WORKER_NOT_ALIVE' unless status.dig('delivery_worker','state')=='ALIVE'
raise 'FALSE_RUNNING' if status['profiles'].any?{|p|p['current_state']=='RUNNING'}
health=Array(status['integration_health']).index_by{|h|h['key']}
raise 'OPENCLAW_NOT_READY' unless health.dig('openclaw','health')=='READY'
raise 'DEMO_NOT_UP' unless health.dig('demo','health')=='UP'
html=QldapmAIController.renderer.render(partial:'qldapm_ai/engineering_command_center',assigns:{project:project,engineering:status,engineering_wp:Array(status['tasks']).find{|t|t['id']==379},reports:status['recent_reports'],schedule:status['reporting_schedule'],notifications:status['notifications'],ui_mode:'modern'})
dom=Nokogiri::HTML.fragment(html)
raise 'CHILD_NOT_RENDERED' unless dom.at_css('#tab-backlog').text.include?('WP #391')
integration=dom.at_css('#tab-integrations').text
raise 'NEW_STATUS_CARDS_MISSING' unless ['n8n lifecycle executions','RAG indexing observations','Demo backup / restore','Gemini Provider','READY'].all?{|text|integration.include?(text)}
notes=status['notifications'].is_a?(Hash) ? Array(status['notifications']['notifications']) : Array(status['notifications'])
again=command(project,owner,'engineering_status')
other=again['notifications'].is_a?(Hash) ? Array(again['notifications']['notifications']) : Array(again['notifications'])
raise 'DUPLICATE_NOTES' unless other.map{|n|n['id']}.uniq.size==other.size && notes.map{|n|n['id']}.sort==other.map{|n|n['id']}.sort
puts({status:'PASS',utc:Time.now.utc.iso8601,route:'Actual Rails AiBridge signed HTTP + template render',mode:status['mode'],queue:status['queue'],
 worker:status['delivery_worker'].slice('state','seen','run_id'),wp391:summary.slice('id','native_id','title','task_status','native_status','stage','failure','budget','resume','pr_url','result'),
 integration_health:status['integration_health'],provider_health:status['provider_health'],demo_observability:status['demo_observability'],
 github:status['github'],notes_dedup:true,new_cards_rendered:true,owner_uat:'PENDING OWNER',provider_calls:0}.to_json)
'''
p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner','-'],input=ruby.encode(),capture_output=True,timeout=150)
if p.returncode:
 import os
 private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('demo-readback-'+label+'-failure.log')
 private.write_bytes(p.stdout+p.stderr)
 raise RuntimeError('SIGNED_READBACK_FAILED_PRIVATE_LOG '+str(private))
result=json.loads(p.stdout.decode().splitlines()[-1]);(out/('readback-'+label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))

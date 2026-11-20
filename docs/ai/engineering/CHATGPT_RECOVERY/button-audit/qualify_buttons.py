"""Reuse the existing isolated Native/Rails qualification against this exact pair."""
from pathlib import Path
import sys
import release_buttons
OUT=Path(__file__).parent
legacy=OUT.parent/'cc-stabilization'
source=(legacy/'qualify_cc.py').read_text()
source=source.replace("importlib.import_module('release_caption' if caption else 'release_reports' if reports else 'release_polish' if polish else 'release_cc')","importlib.import_module('release_buttons')")
source=source.replace("OUT/'status-sync-policy-draft.json'","OUT.parent/'cc-stabilization/status-sync-policy-draft.json'")
source=source.replace('clone-qualification-v9.json','core-reuse-proof.json')
source=source.replace('timeout=240','timeout=480')
source=source.replace("before_web=before_web) as clone:","before_web=before_web,web_start_timeout=360) as clone:")
marker="    (private/'credentials.json').write_bytes"
source=source.replace(marker,"    (OUT/'core-http-proof.json').write_text(json.dumps({'status':'CORE_HTTP_PASS_NATIVE_PHASE_PENDING','core':proof['core'],'images':images,'source_hashes':manifest['source_hashes']},indent=2)+'\\n')\n"+marker)
marker="proof={}"
insertion='''
ruby=ruby.replace("'reporting_schedule'=>{'daily_enabled'","'reporting_schedule'=>{'updated'=>123.5,'daily_enabled'")
ruby=ruby.replace("raise 'CSRF_TOKEN_MISSING' unless csrf","raise 'CSRF_TOKEN_MISSING' unless csrf\\nraise 'INITIAL_SCHEDULE_VERSION_MISSING' unless html.at_css('#schedule-config-modal')['data-schedule-version']=='123.5'")
ruby=ruby.replace("raise 'CSRF_TOKEN_MISSING' unless csrf","raise 'CSRF_TOKEN_MISSING' unless csrf\\nraise 'EMPTY_ID_COPY_ENABLED' if html.css('button[data-qcc-copy]').any?{|b|b['data-qcc-copy'].blank? && !b.key?('disabled')}")
marker="before_calls=Qldapm::AiBridge.observed.size"
ruby=ruby.replace(marker,"http.post('/projects/ai-dev-demo/qldapm-ai/commands',params:{tool:'engineering_github_sync',arguments:'{}',request_id:SecureRandom.uuid,authenticity_token:csrf})\\nraise 'HTML_COMMAND_NOT_PRG' unless http.response.status==303 && URI(http.response.location).path=='/projects/ai-dev-demo/qldapm-ai'\\n"+marker)
'''
source=source.replace(marker,insertion+'\n'+marker)
extra="""
from gateway.engineering_reporting import get_schedule,update_schedule
original=get_schedule(service,18)
command={'action':'engineering_report_schedule_update','arguments':{'daily_hour':10,'timezone':original['timezone'],'expected_updated':original['updated']},'idempotency_key':'clone-schedule-first'}
saved=service.execute_actor(18,command)['result']
assert saved['daily_hour']==10 and saved['weekly_hour']==original['weekly_hour']
assert service.execute_actor(18,command)['result']==saved
try:service.execute_actor(18,{**command,'idempotency_key':'clone-schedule-stale','arguments':{'weekly_hour':11,'expected_updated':original['updated']}})
except ValueError as error:assert str(error)=='ENGINEERING_REPORT_SCHEDULE_CONFLICT'
else:raise AssertionError('STALE_SCHEDULE_ACCEPTED')
restore={k:original[k] for k in ['daily_enabled','daily_hour','daily_minute','weekly_enabled','weekly_day','weekly_hour','weekly_minute','timezone']}
service.execute_actor(18,{'action':'engineering_report_schedule_update','arguments':{**restore,'expected_updated':saved['updated']},'idempotency_key':'clone-schedule-restore'})
assert all(get_schedule(service,18)[k]==v for k,v in restore.items())
"""
source=source.replace("commands=[]\ntry:",extra+"\ncommands=[]\ntry:")
sys.argv=[__file__,'--caption','--reuse-core']
exec(compile(source,str(legacy/'qualify_cc.py'),'exec'))

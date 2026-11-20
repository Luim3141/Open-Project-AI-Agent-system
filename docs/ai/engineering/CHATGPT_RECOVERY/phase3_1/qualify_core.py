"""Candidate Core full Rails/API/controller/render contract on private restored Native clone."""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[5];sys.path.insert(0,str(root/'openproject/ai'))
from automation.main_native_clone import main_native_clone
out=Path(__file__).parent
image=json.loads(subprocess.check_output(['docker','image','inspect','qldapm-core:phase3_1']))[0]['Id']
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('phase3_1-core-clone-'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'))
private.mkdir(parents=True,exist_ok=False)
ruby=r"""
require 'net/http';require 'json';require 'nokogiri'
raise 'CLONE_ONLY' unless ENV['QLDAPM_TEST_ONLY']=='true' && ENV.fetch('DATABASE_URL').include?('@qa-db/')
owner=User.find(18);raise 'OWNER_BINDING_FAILED' unless owner.login=='op-owner' && owner.admin? && Qldapm::Rbac.ai_system_owner?(Project.find(6),owner,fresh:true)
# Actual Native HTTP on clone; never create an API token on MAIN.
token=Token::API.create_and_return_value(owner)
uri=URI('http://localhost:8080/api/v3/users/me');req=Net::HTTP::Get.new(uri);req.basic_auth('apikey',token);req['Host']='localhost:8088'
response=Net::HTTP.start(uri.host,uri.port,read_timeout:30){|h|h.request(req)}
raise 'NATIVE_IDENTITY_FAILED' unless response.code=='200' && JSON.parse(response.body)['id']==18
# Exact Rails routing/login filter is exercised anonymously, then authenticated HTTP in this isolated clone.
http=ActionDispatch::Integration::Session.new(Rails.application);http.host!('localhost:8088')
http.get('/projects/ai-dev-demo/qldapm-ai',headers:{'Accept'=>'application/json'})
raise 'ANONYMOUS_NOT_DENIED' unless [302,401,403].include?(http.response.status)
fixture={
 'project_id'=>6,'mode'=>'OFF','tasks'=>[{'id'=>379,'lock_version'=>4,'subject'=>'Parent','status'=>'In Progress'},{'id'=>390,'lock_version'=>2,'subject'=>'Title <script>bad</script>'}],
 'delivery_worker'=>{'state'=>'ALIVE','seen'=>Time.now.to_f},'backlog'=>[],'runs'=>[],
 'control'=>{'desired_mode'=>'OFF','effective_state'=>'OFF','state_revision'=>7,'blocked_reason'=>'NO_ELIGIBLE_WORK'},
 'queue'=>{'state'=>'EMPTY','ready'=>0,'active'=>0,'blocked'=>0,'reason_code'=>'NO_ELIGIBLE_WORK'},
 'github'=>{'status'=>'ONLINE','prs'=>[{'number'=>9,'state'=>'open','title'=>'Remote changed','base_ref'=>'codex/feature','head_sha'=>'4a794e2b','url'=>'https://github.com/Luim3141/mini-task-manager/pull/9'}],'sync_meta'=>{'last_success_at'=>Time.now.to_f}},
 'telemetry'=>{'cursor'=>1,'runs'=>[{'id'=>'run-390','native_id'=>390,'queue_state'=>'finished','status'=>'succeeded','created_at'=>Time.now.to_f,'updated_at'=>Time.now.to_f,'pipeline'=>[{'agent'=>'dev','status'=>'PASS','evidence_id'=>'hash'}]}],'events'=>[{'event_id'=>'event-1','run_id'=>'run-390','event_type'=>'AGENT_STARTED','agent_id'=>'dev','timestamp'=>Time.now.to_f,'trace_id'=>'trace-1'}]},
 'recent_reports'=>[{'id'=>'report-1','report_type'=>'DAILY','narrative'=>'Report <script>bad</script>','source_state'=>'CURRENT','metrics'=>{'runs'=>{'succeeded'=>1,'usage_complete'=>false},'work_packages'=>{'total_items'=>1},'github'=>{'prs'=>[]}}}],
 'notifications'=>{'notifications'=>[{'id'=>'note-1','message'=>'Fresh notification'}]},
 'reporting_schedule'=>{'daily_enabled'=>0,'daily_hour'=>8,'daily_minute'=>0,'weekly_enabled'=>1,'weekly_day'=>1,'weekly_hour'=>9,'weekly_minute'=>0}}
summary={'id'=>'run-391','native_id'=>391,'title'=>'CSV export tiếng Việt '+('x'*2000),'task_status'=>'BLOCKED','native_status'=>'BLOCKED','queue_state'=>'finished','agent'=>'dev','last_agent'=>'dev','stage'=>'dev-0','created_at'=>1793617800,'updated_at'=>1793622294,
 'failure'=>{'category'=>'PROVIDER_QUOTA_EXHAUSTED','message'=>'Provider HTTP 429; lượt đầu đã hết budget 12/12.'},
 'budget'=>{'calls_used'=>12,'call_cap'=>12,'provider_response_count'=>11,'cumulative_calls'=>36},
 'resume'=>{'eligible'=>false,'reason'=>'PROVIDER_RECOVERY_REQUIRED','remaining_continuations'=>3},'checkpoint'=>{'resumable'=>true,'version'=>16}}
fixture['telemetry']['runs'] << summary
fixture['tasks'] << {'id'=>391,'subject'=>'CSV export','status'=>'BLOCKED','created_at'=>'2026-11-02T11:00:00Z','updated_at'=>'2026-11-02T12:00:00Z'}
fixture['backlog']=(1..31).map{|i|summary.except('id').merge('unit'=>"fixture-#{i}",'run_id'=>'run-391','state'=>'BLOCKED','title'=>summary['title'],'dependency_ready'=>true)}
fixture['profiles']=[{'agent'=>'dev','status'=>'STANDBY','current_state'=>'STANDBY','last_activity'=>summary.except('id').merge('run_id'=>'run-391','result'=>'blocked')},
 {'agent'=>'reviewer','status'=>'STANDBY','current_state'=>'STANDBY'}]
fixture['plans']=(1..2).map{|i|{'id'=>"plan-#{i}",'native_id'=>391,'title'=>'CSV planning','state'=>'PUBLISHED','created_at'=>1793617800+i,'ba'=>{'summary'=>'Tiếng Việt <script>bad</script>'},'pm'=>{'next_action'=>'Xem dependency'},'native_units'=>{'fixture'=>{'id'=>391,'state'=>'BLOCKED'}}}}
fixture['integration_health']=[{'name'=>'Unavailable fixture','health'=>'UNKNOWN','check_type'=>'NOT CHECKED'},{'name'=>'Down fixture','health'=>'DOWN','checked_at'=>1793622294,'last_error'=>'HTTP_503'}]
Qldapm::AiBridge.singleton_class.class_eval { attr_accessor :fixture,:observed }
Qldapm::AiBridge.fixture=fixture;Qldapm::AiBridge.observed=[]
Qldapm::AiBridge.define_singleton_method(:call) do |project,actor,operation,command|
 raise 'PROJECT_OR_ACTOR_SCOPE' unless project.id==6 && [18,20].include?(actor.id)
 Qldapm::AiBridge.observed << {'actor'=>actor.id,'action'=>command[:action],'key'=>command[:idempotency_key],'arguments'=>command[:arguments]}
 result=case command[:action]
 when 'engineering_status' then Qldapm::AiBridge.fixture
 when 'engineering_github_sync' then {'status'=>'SUCCESS','command_id'=>'command-1','request_id'=>command[:idempotency_key],'accepted'=>true,'message'=>'Sync completed'}
 when 'engineering_control'
   mode=command[:arguments]['mode'];Qldapm::AiBridge.fixture['mode']=mode
   {'accepted'=>true,'command_id'=>'command-2','mode'=>mode,'message'=>'Control accepted'}
 when 'knowledge_search' then {'items'=>[{'native_id'=>390,'title'=>'Title','snippet'=>'Exact source','citation'=>'/work_packages/390','match_type'=>'EXACT','lock_version'=>2}]}
 when 'engineering_report_get' then {'id'=>'report-1','report_type'=>'DAILY','source_state'=>'CURRENT','narrative'=>"# Báo cáo\n\n## Kết quả\n\n**Đã lưu**\n\n| WP | State |\n| --- | --- |\n| 391 | BLOCKED |\n\n<script>bad</script>\n[bad](javascript:alert(1))"}
 else raise 'UNEXPECTED_ACTION'
 end
 {'result'=>result,'correlation_id'=>'trace-command'}
end
# Validate authenticated browser HTTP/session/CSRF on clone only. Password and TOTP devices are clone-only fixtures.
password=SecureRandom.hex(24)+'aA1!';owner.password=password;owner.password_confirmation=password;owner.save!
TwoFactorAuthentication::Device.where(user_id:18).delete_all if defined?(TwoFactorAuthentication::Device)
Setting.plugin_openproject_two_factor_authentication={'enforced'=>false,'disabled'=>true,'active_strategies'=>[]}
http.get('/login');page=Nokogiri::HTML(http.response.body);csrf=page.at_css('input[name="authenticity_token"]')&.[]('value') || page.at_css('meta[name="csrf-token"]')&.[]('content')
http.post('/login',params:{username:owner.login,password:password,authenticity_token:csrf})
login={'status'=>http.response.status,'location'=>http.response.location}
http.get('/projects/ai-dev-demo/qldapm-ai?format=json',headers:{'Accept'=>'application/json'})
raise 'AUTHENTICATED_ROUTE_FAILED_'+http.response.status.to_s unless http.response.status==200 && JSON.parse(http.response.body)['engineering']
d=JSON.parse(http.response.body);raise 'JSON_PROJECTION_MISSING' unless d['engineering']['control']['state_revision']==7
expected=%w[qcc-live-controls tab-mission tab-pipeline tab-workforce tab-backlog tab-execution tab-github tab-reports tab-integrations qcc-live-notifications]
raise 'LIVE_REGIONS_INCOMPLETE' unless expected.all?{|id|d['fragments'].key?(id)}
raise 'PR_OR_EVENT_NOT_RENDERED' unless d['fragments']['tab-github'].include?('Remote changed') && d['fragments']['tab-mission'].include?('event-1') && d['fragments']['tab-reports'].include?('report-1')
raise 'UNESCAPED_TELEMETRY' if d['fragments'].values.join.include?('<script>bad</script>')
raise 'CACHE_HEADERS_MISSING' unless http.response.headers.any?{|key,value|key.to_s.downcase=='cache-control' && value.to_s.include?('no-store')}
raise 'BLOCKED_OWNER_PROJECTION_MISSING' unless d['fragments']['tab-backlog'].include?('WP #391') && d['fragments']['tab-workforce'].include?('Lượt thực thi gần nhất: WP #391') && d['fragments']['tab-mission'].include?('KHÔNG CÓ AGENT ĐANG THỰC THI')
raise 'BACKLOG_LONG_FIXTURE_DROPPED' unless Nokogiri::HTML.fragment(d['fragments']['tab-backlog']).css('[data-work-row]').size==31
raise 'INTEGRATION_UNKNOWN_MISSING' unless d['fragments']['tab-integrations'].include?('UNKNOWN') && d['fragments']['tab-integrations'].include?('DOWN')
http.get('/projects/ai-dev-demo/qldapm-ai/reports/report-1',headers:{'Accept'=>'application/json'})
raise 'REPORT_ROUTE_FAILED' unless http.response.status==200
report=JSON.parse(http.response.body);rendered=Nokogiri::HTML.fragment(report.dig('reader','rendered_html').to_s)
raise 'MARKDOWN_NOT_STRUCTURED' unless rendered.at_css('h1') && rendered.at_css('h2') && rendered.at_css('strong') && rendered.at_css('table')
raise 'REPORT_UNSANITIZED' if rendered.at_css('script,[href^="javascript:"]')
fixture['profiles'][1].merge!('current_state'=>'RUNNING','current_run'=>{'id'=>'fixture-active','native_id'=>391,'stage'=>'REVIEWING'})
http.get('/projects/ai-dev-demo/qldapm-ai?format=json',headers:{'Accept'=>'application/json'})
raise 'ACTIVE_ROLE_RENDER_FAILED' unless http.response.status==200 && JSON.parse(http.response.body)['fragments']['tab-workforce'].include?('Đang thực thi WP #391')
http.get('/projects/ai-dev-demo/qldapm-ai');html=Nokogiri::HTML(http.response.body);csrf=html.at_css('meta[name="csrf-token"]')&.[]('content')
raise 'CSRF_TOKEN_MISSING' unless csrf
request_id=SecureRandom.uuid
http.post('/projects/ai-dev-demo/qldapm-ai/commands',params:{tool:'engineering_github_sync',arguments:'{}',request_id:request_id},headers:{'Accept'=>'application/json','X-CSRF-Token'=>csrf})
raise 'SYNC_JSON_COMMAND_FAILED_'+http.response.status.to_s unless http.response.status==200
command=JSON.parse(http.response.body);raise 'SYNC_FRESH_FRAGMENTS_FAILED' unless command['result']['request_id']==request_id && command['correlation_id']=='trace-command' && command['fragments']['tab-github'].include?('Remote changed')
http.post('/projects/ai-dev-demo/qldapm-ai/commands',params:{tool:'engineering_control',arguments:'{"mode":"OFF"}',request_id:SecureRandom.uuid,expected_revision:'7'},headers:{'Accept'=>'application/json','X-CSRF-Token'=>csrf})
raise 'CONTROL_JSON_FAILED' unless http.response.status==200
last=Qldapm::AiBridge.observed.reverse.find{|x|x['action']=='engineering_control'};raise 'REVISION_MISSING' unless last['arguments']['expected_revision']==7
http.post('/projects/ai-dev-demo/qldapm-ai/commands',params:{tool:'knowledge_search',knowledge_query:'title',native_ids:[390],request_id:SecureRandom.uuid},headers:{'Accept'=>'application/json','X-CSRF-Token'=>csrf})
raise 'KNOWLEDGE_JSON_CARD_VERSION_FAILED' unless http.response.status==200 && JSON.parse(http.response.body)['knowledge_html'].include?('Native version 2')
before_calls=Qldapm::AiBridge.observed.size
http.post('/projects/ai-dev-demo/qldapm-ai/commands',params:{tool:'engineering_control',arguments:'{\"mode\":\"OFF\"}',request_id:SecureRandom.uuid},headers:{'Accept'=>'application/json','X-CSRF-Token'=>'invalid-fixture-token'})
raise 'INVALID_CSRF_ACCEPTED' unless [401,403,422].include?(http.response.status) && Qldapm::AiBridge.observed.size==before_calls
puts({status:'PASS',identity:18,project:6,native_http:'PASS',anonymous_denied:true,owner_login_json_csrf_command:'PASS',invalid_csrf_rejected_before_gateway:true,full_template:'PASS',live_regions:expected,ui_auth_fixture:'clone-only password and disabled clone TOTP; production MFA unchanged',gateway_transport:'fixture at actual Rails bridge boundary; Gateway integration verified separately'}.to_json)
"""
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with main_native_clone(private/'clone',candidate_web_image=image) as clone:
 p=subprocess.run(['docker','exec','-i',clone['web'],'bundle','exec','rails','runner','-'],input=ruby.encode(),capture_output=True,timeout=180)
 if p.returncode:
  (private/'failure.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('CORE_CLONE_FAILED_PRIVATE_LOG '+str(private))
 result=json.loads(p.stdout.decode().splitlines()[-1]);result.update({'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image':image,'command':['python',str(Path(__file__).relative_to(root))],'environment':'isolated Native clone + actual Rails routing/session/CSRF + synthetic Gateway boundary'})
 (out/'core-clone-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


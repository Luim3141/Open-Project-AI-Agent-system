require 'bigdecimal'
require 'action_view'
require 'json'
require 'ostruct'

class User
  class << self; attr_accessor :current; end
end
view_class=ActionView::Base.with_empty_template_cache
view_class.class_eval do
  def project_qldapm_ai_path(*) = '/projects/qldapm-local/qldapm-ai'
  def project_qldapm_ai_qa_evidence_path(*) = '/projects/qldapm-local/qldapm-ai/qa-evidence'
  def project_qldapm_ai_qa_decision_path(*) = '/projects/qldapm-local/qldapm-ai/qa-evidence/decision'
  def project_qldapm_ai_qa_test_decision_path(*) = '/projects/qldapm-local/qldapm-ai/qa-evidence/qa-decision'
  def project_qldapm_ai_executions_path(*) = '/projects/qldapm-local/qldapm-ai/executions'
  def project_qldapm_ai_phases_path(*) = '/projects/qldapm-local/qldapm-ai/phases'
  def project_qldapm_ai_command_path(*) = '/projects/qldapm-local/qldapm-ai/commands'
  def params = {}
  def protect_against_forgery? = true
  def form_authenticity_token(*) = 'isolated-csrf-token'
  def request_forgery_protection_token = :authenticity_token
end
def render_qa(view_class,evidence=nil,role='AI_SYSTEM_OWNER',error=nil)
  User.current=OpenStruct.new(id:role=='QA' ? 23 : role=='PM' ? 19 : 18)
  view=view_class.with_view_paths(['/views'])
  view.assign(project:OpenStruct.new(identifier:'qldapm-local'),role:role,qa_evidence:evidence,error:error)
  view.render(template:'qldapm_ai/qa_evidence')
end
e={'id'=>'42424242-4242-4242-8242-424242424242','hash'=>'a'*64,'actor'=>23,'reviewer'=>nil,
   'state'=>'pending','source_current'=>true,'ready'=>false,'verification_kind'=>'MANUAL_ATTESTATION',
   'binding'=>{'native_id'=>371,'version'=>1,'activity_id'=>4242,'activity_created_at'=>'2026-10-25T00:00:00Z',
     'artifact_sha256'=>'b'*64,'assignee'=>'/api/v3/users/21'},
   'manifest'=>{'attachment_id'=>99,'criteria'=>{'AC1'=>'<script>unsafe criterion</script>'},
     'tests'=>[{'criterion_id'=>'AC1','reference'=>'TC1','expected'=>'HTTP401','actual'=>'<img src=x onerror=alert(1)>','outcome'=>'FAILED'}]}}
html=render_qa(view_class,e)
raise 'QA_VIEW_XSS' if html.include?('<script>') || html.include?('<img src=x')
raise 'QA_EVIDENCE_MISSING' unless ['MANUAL_ATTESTATION','HTTP401','FAILED','&lt;script&gt;','&lt;img','a'*64,'/work_packages/371'].all? { |text| html.include?(text) }
raise 'QA_CSRF_OR_CONSENT_MISSING' unless html.include?('authenticity_token') && html.include?('isolated-csrf-token') && html.include?('name="acknowledge"') && html.include?('required="required"')
raise 'QA_EXACT_DECISION_FORM_MISSING' unless html.include?('name="hash"') && html.include?('value="accept"') && html.include?('value="reject"')
raise 'QA_REVIEW_READINESS_FALSE_CLAIM' unless html.include?('Chưa đủ')
['QA','BA','BE','FE'].each do |role|
  raise "QA_ROLE_REVIEW_FORM_#{role}" if render_qa(view_class,e,role).include?('name="decision"')
end
[e.merge('state'=>'accepted'),e.merge('actor'=>18),e.merge('binding'=>e['binding'].merge('assignee'=>'/api/v3/users/18'))].each do |hidden|
  raise 'QA_CONSUMED_OR_SELF_REVIEW_FORM' if render_qa(view_class,hidden).include?('name="decision"')
end
stale=render_qa(view_class,e.merge('source_current'=>false))
raise 'QA_STALE_ACCEPT_ENABLED' unless stale.match?(/value="accept"[^>]*disabled="disabled"/)
empty=render_qa(view_class)
raise 'QA_EMPTY_PAGE_FAKE_PASS' if empty.include?('name="decision"') || !empty.include?('ID bằng chứng QA')
raise 'QA_READONLY_RUN_FORM_MISSING' unless empty.include?('value="qa_test_run"') && empty.include?('name="native_id"')
unsupported_view=view_class.with_view_paths(['/views'])
unsupported_view.assign(project:OpenStruct.new(identifier:'qldapm-local'),role:'AI_SYSTEM_OWNER',
  qa_run:{'compatibility'=>'UNSUPPORTED_RUN_KIND'})
unsupported_html=unsupported_view.render(template:'qldapm_ai/qa_evidence')
raise 'UNKNOWN_RUN_CAN_PROMOTE_EVIDENCE' unless unsupported_html.include?('Run chưa được phiên bản này hỗ trợ') &&
  !unsupported_html.include?('value="qa_evidence_from_run"')
error=render_qa(view_class,nil,'AI_SYSTEM_OWNER','<script>stale</script>')
raise 'QA_ERROR_NOT_ACCESSIBLE_OR_ESCAPED' unless error.include?('role="alert"') && error.include?('&lt;script&gt;') && !error.include?('<script>')
automated=e.merge('actor'=>19,'verification_kind'=>'AUTOMATED_NATIVE_READBACK','state'=>'pending_qa',
  'run_id'=>'34343434-3434-4434-8434-343434343434','producer'=>{'id'=>'qldapm-native-readback-v1','code_sha256'=>'c'*64},
  'automated_verdict'=>'FAILED','artifact'=>'<script>untrusted log</script>','reviews'=>[])
qa=render_qa(view_class,automated,'QA')
raise 'AUTOMATED_QA_REVIEW_FORM_MISSING' unless qa.include?('/qa-evidence/qa-decision') && qa.include?('name="decision"')
raise 'AUTOMATED_EVIDENCE_MISLABELLED_MANUAL' if qa.include?('Đây là lời xác nhận kiểm thử thủ công')
raise 'AUTOMATED_ARTIFACT_NOT_ESCAPED' unless qa.include?('&lt;script&gt;untrusted log&lt;/script&gt;') && !qa.include?('<script>')
raise 'MANAGER_CAN_SKIP_QA_REVIEW' if render_qa(view_class,automated).include?('name="decision"')
reviewed=automated.merge('state'=>'qa_accepted','reviews'=>[{'stage'=>'qa','actor'=>23,'decision'=>'accept'}])
raise 'MANAGER_STAGE_MISSING' unless render_qa(view_class,reviewed).include?('/qa-evidence/decision')
raise 'QA_CAN_REPLAY_REVIEW_STAGE' if render_qa(view_class,reviewed,'QA').include?('name="decision"')
unknown=e.merge('verification_kind'=>'FUTURE_QA_PROOF','compatibility'=>'UNSUPPORTED_EVIDENCE_KIND',
  'manifest'=>{},'source_current'=>false,'ready'=>false)
unknown_html=render_qa(view_class,unknown)
raise 'UNSUPPORTED_QA_KIND_MISLEADING' unless unknown_html.include?('Loại bằng chứng chưa được phiên bản này hỗ trợ') &&
  !unknown_html.include?('Test cases do QA xác nhận') && !unknown_html.include?('lời xác nhận kiểm thử thủ công') &&
  !unknown_html.include?('name="decision"')
application=automated.merge('actor'=>18,'verification_kind'=>'AUTOMATED_APPLICATION_WBS',
  'producer'=>{'id'=>'qldapm-wbs-application-v1','code_sha256'=>'d'*64},'native_transition_supported'=>false)
application_html=render_qa(view_class,application,'QA')
raise 'APPLICATION_QA_REVIEW_OR_SCOPE_MISSING' unless application_html.include?('/qa-evidence/qa-decision') &&
  application_html.include?('application WBS') && application_html.include?('Native transition chưa được hỗ trợ')
raise 'APPLICATION_QA_MISLABELLED' if application_html.include?('lời xác nhận kiểm thử thủ công') || application_html.include?('readback Native tự động')
supported_html=render_qa(view_class,application.merge('native_transition_supported'=>true),'QA')
raise 'APPLICATION_NATIVE_CAPABILITY_OR_APPROVAL_MISLEADING' unless supported_html.include?('Bridge Native hỗ trợ loại proof này') &&
  supported_html.include?('Native form/gate và approval riêng') && !supported_html.include?('Native transition chưa được hỗ trợ')
application_reviewed=application.merge('state'=>'qa_accepted','reviews'=>[{'stage'=>'qa','actor'=>23,'decision'=>'accept'}])
raise 'APPLICATION_PM_REVIEW_MISSING' unless render_qa(view_class,application_reviewed,'PM').include?('/qa-evidence/decision')
raise 'APPLICATION_OWNER_SELF_REVIEW_VISIBLE' if render_qa(view_class,application_reviewed).include?('name="decision"')
raise 'OWNER_PROOF_FORM_MISSING' unless render_qa(view_class).include?('name="proof_id"') && render_qa(view_class).include?('value="qa_application_proof_admit"')
raise 'QA_CAN_ADMIT_APPLICATION_PROOF' if render_qa(view_class,nil,'QA').include?('name="proof_id"')
%w[AI_SYSTEM_OWNER PM QA BA BE FE].each do |role|
  view=view_class.with_view_paths(['/views']);view.assign(project:OpenStruct.new(identifier:'qldapm-local'),role:role,control_center:nil)
  navigation=view.render(partial:'qldapm_ai/control_center')
  visible=navigation.include?('Bằng chứng QA / Kiểm duyệt') && navigation.include?('/qldapm-ai/qa-evidence')
  raise "QA_CONTROL_CENTER_NAVIGATION_#{role}" unless visible==%w[AI_SYSTEM_OWNER PM QA].include?(role)
end
puts JSON.generate({qa_review_view:'PASS',actual_action_view:true,xss:true,csrf:true,exact_hash:true,role_and_self_review_hiding:true,stale_accept_disabled:true,empty_state:true})
view=view_class.with_view_paths(['/views'])
view.assign(project:OpenStruct.new(identifier:'qldapm-local'),role:'QA',qa_inbox:{'items'=>[{'id'=>e['id'],'native_id'=>371,'version'=>1,'state'=>'pending_qa','verification_kind'=>'AUTOMATED_NATIVE_READBACK','actor'=>19,'source_current'=>true,'ready'=>false}]})
inbox=view.render(template:'qldapm_ai/qa_evidence')
raise 'QA_INBOX_OR_HANDOFF_LINK_MISSING' unless inbox.include?('Hộp thư bằng chứng') && inbox.include?('pending_qa') && inbox.include?(e['id'])
view.assign(control_center:{'local_delivery'=>{'scope'=>'OWN_COUNTS_ONLY','counts'=>{'delivered'=>3,'dlq'=>1},'external_delivery'=>'BLOCKED_CONFIGURATION'}})
delivery=view.render(partial:'qldapm_ai/control_center')
raise 'LOCAL_DELIVERY_STATUS_MISSING' unless ['Báo cáo lưu local','delivered: 3','dlq: 1','OWN_COUNTS_ONLY','BLOCKED_CONFIGURATION'].all? { |value| delivery.include?(value) }

revoked=render_qa(view_class,reviewed.merge('reviewers_current'=>false))
raise 'REVOKED_QA_REVIEWER_ACCEPT_ENABLED' unless revoked.match?(/value="accept"[^>]*disabled="disabled"/)
raise 'REVOKED_REVIEWER_STATE_NOT_VISIBLE' unless revoked.include?('Quyền reviewer đã thay đổi')
raise 'REJECTION_AFTER_REVOCATION_BLOCKED' if revoked.match?(/value="reject"[^>]*disabled="disabled"/)

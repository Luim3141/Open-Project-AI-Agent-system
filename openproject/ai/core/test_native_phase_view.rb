require 'bigdecimal'
require 'action_view'
require 'json'
require 'ostruct'
require 'securerandom'

view_class=ActionView::Base.with_empty_template_cache
view_class.class_eval do
  def project_qldapm_ai_path(*) = '/projects/qldapm-local/qldapm-ai'
  def project_qldapm_ai_phases_path(*) = '/projects/qldapm-local/qldapm-ai/phases'
  def project_qldapm_ai_phase_decision_path(*) = '/projects/qldapm-local/qldapm-ai/phases/decision'
  def project_qldapm_ai_command_path(*) = '/projects/qldapm-local/qldapm-ai/commands'
  def project_qldapm_ai_executions_path(*) = '/projects/qldapm-local/qldapm-ai/executions'
  def project_qldapm_ai_qa_evidence_path(*) = '/projects/qldapm-local/qldapm-ai/qa-evidence'
  def params = {}
  def protect_against_forgery? = true
  def form_authenticity_token(*) = 'isolated-phase-csrf'
  def request_forgery_protection_token = :authenticity_token
end
render_phase=->(document,role='AI_SYSTEM_OWNER') {
  view=view_class.with_view_paths(['/views'])
  view.assign(project:OpenStruct.new(identifier:'qldapm-local'),role:role,phase:document)
  view.render(template:'qldapm_ai/phases')
}
document={'id'=>'42424242-4242-4242-8242-424242424242','hash'=>'a'*64,'actor'=>20,'kind'=>'scope',
  'state'=>'pending','source_current'=>true,'can_review'=>true,
  'source'=>{'id'=>376,'version'=>0,'description'=>"Story: <script>unsafe</script>\nAC1: Keep unknown vectors."}}
html=render_phase.call(document)
raise 'PHASE_SOURCE_XSS' if html.include?('<script>')
raise 'PHASE_SOURCE_OR_HASH_MISSING' unless html.include?('&lt;script&gt;') && html.include?('a'*64) && html.include?('Keep unknown vectors')
raise 'PHASE_CONSENT_CSRF_HASH_MISSING' unless ['isolated-phase-csrf','name="acknowledge"','name="hash"','value="accept"'].all? { |value| html.include?(value) }
raise 'PHASE_STALE_ACCEPT_ENABLED' unless render_phase.call(document.merge('source_current'=>false)).match?(/value="accept"[^>]*disabled="disabled"/)
raise 'PHASE_SELF_OR_CONSUMED_REVIEW_VISIBLE' if render_phase.call(document.merge('can_review'=>false)).include?('name="decision"')
%w[BA BA-PM BE FE QA].each do |role|
  raise 'PHASE_LOW_ROLE_REVIEW_VISIBLE' if render_phase.call(document,role).include?('name="decision"')
end
accepted=document.merge('state'=>'accepted','can_review'=>false,'reviewer_current'=>true,'status_options'=>[{'id'=>37,'name'=>'IN ANALYSIS'}])
raise 'PHASE_PROPOSAL_FORM_MISSING' unless render_phase.call(accepted).include?('value="phase_transition_prepare"')
raise 'PHASE_REVOKED_REVIEWER_PROPOSAL_VISIBLE' if render_phase.call(accepted.merge('reviewer_current'=>false)).include?('value="phase_transition_prepare"')
raise 'PHASE_EMPTY_FAKE_REVIEW' if render_phase.call(nil).include?('name="decision"')
%w[AI_SYSTEM_OWNER PM BA BA-PM BE FE QA].each do |role|
  view=view_class.with_view_paths(['/views']);view.assign(project:OpenStruct.new(identifier:'qldapm-local'),role:role,control_center:nil)
  html=view.render(partial:'qldapm_ai/control_center')
  raise "PHASE_NAVIGATION_ROLE_#{role}" unless html.include?('Scope / Analysis — Review nguồn')==%w[AI_SYSTEM_OWNER PM BA BA-PM].include?(role)
end
puts 'Native phase actual ActionView: source escape, exact hash/consent/CSRF, stale/revoked/self/role hiding and navigation PASS'

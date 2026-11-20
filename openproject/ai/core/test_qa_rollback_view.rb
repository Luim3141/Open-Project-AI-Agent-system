require 'bigdecimal'
require 'action_view'
require 'ostruct'
require 'securerandom'
class User
  def self.current = OpenStruct.new(id:18)
end
view_class=ActionView::Base.with_empty_template_cache
view_class.class_eval do
  def project_qldapm_ai_path(*) = '/ai'
  def project_qldapm_ai_command_path(*) = '/commands'
  def project_qldapm_ai_qa_evidence_path(*) = '/qa'
  def params = {}
  def protect_against_forgery? = false
end
view=view_class.with_view_paths(['/views'])
view.assign(project:OpenStruct.new(identifier:'qldapm-local'),role:'AI_SYSTEM_OWNER',
  qa_run:{'compatibility'=>'UNSUPPORTED_RUN_KIND'})
html=view.render(template:'qldapm_ai/qa_evidence')
raise 'ROLLBACK_RUN_PROMOTION_VISIBLE' unless html.include?('Run chưa được phiên bản này hỗ trợ') && !html.include?('value="qa_evidence_from_run"')
view.assign(qa_run:nil,qa_evidence:{'verification_kind'=>'AUTOMATED_APPLICATION_WBS',
  'compatibility'=>'UNSUPPORTED_EVIDENCE_KIND'})
html=view.render(template:'qldapm_ai/qa_evidence')
raise 'ROLLBACK_EVIDENCE_REVIEW_VISIBLE' unless html.include?('Loại bằng chứng chưa được phiên bản này hỗ trợ') &&
  !html.include?('name="decision"') && !html.include?('lời xác nhận kiểm thử thủ công')
puts 'ROLLBACK_QA_VIEW_UNSUPPORTED_READ_ONLY_PASS'

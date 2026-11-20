# Actual controller methods with isolated framework/transport fixtures; no Rails DB/session spoofing.
require 'json'
require 'securerandom'
require 'ostruct'
require 'active_support'
require 'active_support/core_ext/object/blank'
require_relative 'test_ai_system_owner'

class User
  class << self
    attr_accessor :current
  end
  def allowed_in_project?(permission,project)
    raise 'UNEXPECTED_NATIVE_PERMISSION_UI_CHECK' unless permission==:delete_work_packages && project.id==5
    id==18
  end
end
class ApplicationController
  def self.before_action(name) = ((@filters ||= []) << name)
  def self.authorize_with_permission(*) = nil
  def self.filters = @filters
  attr_accessor :params
  attr_reader :head_status, :rendered_status
  def head(value) = (@head_status=value)
end
module Qldapm::AiBridge
  class RequestError < ArgumentError
    attr_reader :status
  end
  def self.calls = (@calls ||= [])
  def self.call(project,user,route,body)
    calls << [project.id,user.id,route,body]
    {'result'=>{'action'=>body[:action]}}
  end
end
require_relative 'overlay/app/controllers/qldapm_ai_controller'
class RouteFixture < QldapmAIController
  def render_assistant(status: :ok) = (@rendered_status=status)
end
def submit_fixture(actor,action,args={})
  User.current=actor
  controller=RouteFixture.new
  controller.instance_variable_set(:@project,OpenStruct.new(id:5,identifier:'qldapm-local'))
  controller.params={tool:action,arguments:JSON.generate(args)}
  controller.command
  controller
end
check(QldapmAIController.filters.include?(:require_login),'UI_LOGIN_FILTER_REMOVED')
User.registry[18]=User.new(18,'op-owner',true)
owner=User.registry[18]
%w[delete_work_package update_dependency delete_dependency create_dependency knowledge_file_ingest knowledge_file_search knowledge_file_read knowledge_incremental_sync knowledge_incremental_status knowledge_feedback_submit knowledge_feedback_get knowledge_feedback_apply bug_triage bug_propose wbs_draft wbs_get wbs_adopt wbs_next wbs_from_ba qa_evidence_get qa_transition_prepare].each do |action|
  controller=submit_fixture(owner,action,{'source_key'=>'main-workflow-contract'})
  check(controller.rendered_status==:ok,"OWNER_SUPPORTED_TOOL_DENIED_#{action}")
  _,actor,route,body=Qldapm::AiBridge.calls.last
  check(actor==18 && route=='command' && body[:action]==action && body[:auto_execute]==false,'UI_ACTOR_OR_CONSENT_CHANGED')
  check(body[:idempotency_key].match?(/\A[0-9a-f-]{36}\z/),'UI_REQUEST_ID_INVALID')
end
before=Qldapm::AiBridge.calls.size
%w[qa_application_proof_verify qa_application_proof_admit].each do |action|
  supported=submit_fixture(owner,action,{'id'=>'42424242-4242-4242-8242-424242424242'})
  check(supported.rendered_status==:ok,"OWNER_APPLICATION_PROOF_TOOL_DENIED_#{action}")
  before=Qldapm::AiBridge.calls.size
  denied=submit_fixture(User.new(19,'ba-pm',false),action,{'id'=>'42424242-4242-4242-8242-424242424242'})
  check(denied.head_status==:forbidden && Qldapm::AiBridge.calls.size==before,"APPLICATION_PROOF_PM_ESCALATION_#{action}")
end
before=Qldapm::AiBridge.calls.size
blocked=submit_fixture(User.new(99,'other-admin',true),'knowledge_file_ingest')
check(blocked.head_status==:forbidden && Qldapm::AiBridge.calls.size==before,'OTHER_ADMIN_UI_ESCALATED')
legacy=submit_fixture(User.new(19,'ba-pm',false),'identity')
check(legacy.rendered_status==:ok && Qldapm::AiBridge.calls.last[1]==19,'PM_LEGACY_UI_REGRESSION')
%w[qa_evidence_review qa_review qa_pass].each do |action|
  count=Qldapm::AiBridge.calls.size
  rejected=submit_fixture(owner,action)
  check(rejected.rendered_status==:unprocessable_entity && Qldapm::AiBridge.calls.size==count,'MODEL_REVIEW_UI_COMMAND_EXPOSED')
end
module RequestStore
  def self.active? = false
end
class Member
  class Scope < Array
    def includes(*) = self
  end
  def self.where(project_id:, user_id:, entity_id:)
    role={19=>'PM',20=>'BA',21=>'BE',22=>'FE',23=>'QA'}[user_id]
    Scope.new(role ? [OpenStruct.new(roles:[OpenStruct.new(name:'QLDAPM '+role)])] : [])
  end
end
class Project
  def self.visible(*) = self
  def self.find_by!(identifier:) = OpenStruct.new(id:5,identifier:identifier)
end
class WorkPackage
  def self.visible(*) = self
  def self.where(project:) = self
  def self.first = self
  def self.qldapm_actor(*) = {'role'=>'authenticated fixture'}
end
{18=>owner,19=>User.new(19,'ba-pm'),20=>User.new(20,'pm'),21=>User.new(21,'be'),22=>User.new(22,'fe'),23=>User.new(23,'qa')}.each do |id,actor|
  User.current=actor
  controller=RouteFixture.new;controller.params={project_id:'qldapm-local'}
  controller.send(:load_project)
  tools=controller.instance_variable_get(:@tools)
  check(tools.include?('wbs_from_ba'),"BA_CONVERSION_SELECTOR_MISSING_#{id}")
  check(tools.include?('qa_transition_prepare')==[18,19].include?(id),"QA_TRANSITION_SELECTOR_ESCALATION_#{id}")
  check(tools.include?('create_dependency')==[18,19].include?(id),"DEPENDENCY_SELECTOR_ESCALATION_#{id}")
  check(tools.include?('delete_work_package')==(id==18),"DELETE_SELECTOR_IGNORES_NATIVE_PERMISSION_#{id}")
  %w[update_dependency delete_dependency].each do |action|
    check(tools.include?(action)==[18,19].include?(id),"DEPENDENCY_CHANGE_SELECTOR_ESCALATION_#{id}_#{action}")
  end
  check(tools.include?('qa_evidence_get')==[18,19,23].include?(id),"QA_READ_SELECTOR_ESCALATION_#{id}")
  check(tools.include?('qa_evidence_capture')==(id==23),"QA_CAPTURE_SELECTOR_ESCALATION_#{id}")
  %w[qa_application_proof_verify qa_application_proof_admit].each do |action|
    check(tools.include?(action)==(id==18),"APPLICATION_PROOF_SELECTOR_ESCALATION_#{id}_#{action}")
  end
  %w[qa_test_run qa_test_get qa_evidence_from_run].each do |action|
    check(tools.include?(action)==[18,19,23].include?(id),"AUTOMATED_QA_SELECTOR_#{id}_#{action}")
  end
  check((tools & %w[qa_review qa_evidence_review qa_pass]).empty?,"QA_REVIEW_COMMAND_EXPOSED_#{id}")
end
puts 'Owner file/sync/feedback controller routes, own actor binding, consent, other-admin isolation and legacy PM route PASS (isolated fixtures)'

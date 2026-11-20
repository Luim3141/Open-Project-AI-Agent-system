require_relative 'test_owner_ui_tool_routes'

class User
  def self.active = self
  def self.where(id:) = OpenStruct.new(exists?: registry[id]&.active?)
end
class RouteFixture
  def response = (@response ||= OpenStruct.new(headers: {}))
  def render(template, status: :ok, **) = (@rendered_status=status; @template=template)
  def project_qldapm_ai_qa_evidence_path(project, **target) = target.merge(project:project)
  def redirect_to(target) = (@redirected=target)
  def redirected = @redirected
end
module Qldapm::AiBridge
  class << self
    alias_method :tool_call, :call
    attr_accessor :review_error
    attr_accessor :native_run_result
    def call(project,user,route,body)
      raise review_error if review_error
      result=tool_call(project,user,route,body)
      result['result']={'id'=>'34343434-3434-4434-8434-343434343434'} if native_run_result && route=='command' && %w[qa_test_run qa_evidence_from_run].include?(body[:action])
      result['result']={'id'=>'42424242-4242-4242-8242-424242424242','state'=>'accepted','reviewer'=>user.id} if route=='qa_review'
      result
    end
  end
end

project=OpenStruct.new(id:5,identifier:'qldapm-local')
def review_controller(project,actor,params)
  User.current=actor
  controller=RouteFixture.new;controller.instance_variable_set(:@project,project);controller.params=params
  controller
end
actors={18=>User.new(18,'op-owner',true),19=>User.new(19,'ba-pm'),20=>User.new(20,'pm'),21=>User.new(21,'be'),22=>User.new(22,'fe'),23=>User.new(23,'qa'),99=>User.new(99,'other-admin',true)}
actors.each { |id,user| User.registry[id]=user }
params={id:'42424242-4242-4242-8242-424242424242',hash:'a'*64,decision:'accept',acknowledge:'1'}
actors.each do |id,actor|
  before=Qldapm::AiBridge.calls.size
  controller=review_controller(project,actor,params);controller.qa_decision
  if [18,19].include?(id)
    check(controller.rendered_status==:ok,"MANAGER_REVIEW_DENIED_#{id}")
    _,bound_actor,operation,body=Qldapm::AiBridge.calls.last
    check(bound_actor==id && operation=='qa_review' && body==params.slice(:id,:hash,:decision),'REVIEW_ACTOR_HASH_OR_OPERATION_CHANGED')
    check(controller.response.headers['Cache-Control']=='no-store','QA_REVIEW_CACHED')
  else
    check(controller.head_status==:forbidden && Qldapm::AiBridge.calls.size==before,"REVIEW_ESCALATION_#{id}")
  end
end
before=Qldapm::AiBridge.calls.size
other_admin=review_controller(project,User.new(19,'ba-pm',true),params);other_admin.qa_decision
check(other_admin.head_status==:forbidden && Qldapm::AiBridge.calls.size==before,'ADMIN_WITH_PM_MEMBERSHIP_REVIEW_ALLOWED')
missing=review_controller(project,actors[18],params.reject { |k,_| k==:acknowledge });missing.qa_decision
check(missing.rendered_status==:unprocessable_entity && Qldapm::AiBridge.calls.size==before,'UNACKNOWLEDGED_REVIEW_SENT')
actors[18].enabled=false
revoked=review_controller(project,actors[18],params);revoked.qa_decision
check(revoked.head_status==:forbidden && Qldapm::AiBridge.calls.size==before,'INACTIVE_OWNER_REVIEW_ALLOWED')
actors[18].enabled=true
error=Qldapm::AiBridge::RequestError.new('Consumed or stale evidence')
error.instance_variable_set(:@status,409);Qldapm::AiBridge.review_error=error
stale=review_controller(project,actors[18],params);stale.qa_decision
check(stale.rendered_status==409,'REVIEW_CONFLICT_HTTP_CHANGED')
Qldapm::AiBridge.review_error=nil
actors.each do |id,actor|
  controller=review_controller(project,actor,{});controller.qa_evidence
  check([18,19,23].include?(id) ? controller.rendered_status==:ok : controller.head_status==:forbidden,"QA_READ_UI_ROLE_#{id}")
  if [18,19,23].include?(id)
    _,bound_actor,operation,body=Qldapm::AiBridge.calls.last
    check(bound_actor==id && operation=='command' && body[:action]=='qa_evidence_list' && body[:arguments]=={},'QA_INBOX_NOT_BOUND_TO_CURRENT_ACTOR')
  end
end
actors.each do |id,actor|
  before=Qldapm::AiBridge.calls.size
  controller=review_controller(project,actor,params);controller.qa_test_decision
  if id==23
    _,bound_actor,operation,body=Qldapm::AiBridge.calls.last
    check(controller.rendered_status==:ok && bound_actor==23 && operation=='qa_review','QA_AUTOMATED_REVIEW_ACTOR_OR_ROUTE')
    check(body==params.slice(:id,:hash,:decision),'QA_AUTOMATED_REVIEW_HASH_CHANGED')
  else
    check(controller.head_status==:forbidden && Qldapm::AiBridge.calls.size==before,"QA_STAGE_IMPERSONATION_#{id}")
  end
end
puts 'QA human UI: six-role review/read, exact hash, own actor, separate operation, revoked Owner, no consent and conflict409 PASS'
Qldapm::AiBridge.native_run_result=true
controller=review_controller(project,actors[19],{tool:'qa_test_run',arguments:'{}',native_id:'371',actor:18,approved:true})
controller.command
_,actor,operation,body=Qldapm::AiBridge.calls.last
check(actor==19 && operation=='command' && body[:arguments]=={'native_id'=>371} && body[:auto_execute]==false,'QA_RUN_FORGED_ACTOR_OR_ARGS')
check(controller.redirected=={project:'qldapm-local',run_id:'34343434-3434-4434-8434-343434343434'},'QA_RUN_RESULT_REDIRECT')
controller=review_controller(project,actors[19],{tool:'qa_evidence_from_run',arguments:'{"run_id":"34343434-3434-4434-8434-343434343434"}'})
controller.command
check(controller.redirected=={project:'qldapm-local',id:'34343434-3434-4434-8434-343434343434'},'QA_EVIDENCE_RESULT_REDIRECT')
puts 'Automated QA UI commands: own authenticated actor/native ID, no auto-execute, run/evidence redirects PASS'

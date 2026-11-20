require_relative 'test_qa_review_ui'

actors=User.registry
project=OpenStruct.new(id:5,identifier:'qldapm-local')
params={id:'42424242-4242-4242-8242-424242424242',hash:'a'*64,decision:'accept',acknowledge:'1'}
actors.each do |id,actor|
  before=Qldapm::AiBridge.calls.size
  controller=review_controller(project,actor,params);controller.phase_decision
  if [18,19].include?(id)
    _,bound_actor,operation,body=Qldapm::AiBridge.calls.last
    check(bound_actor==id && operation=='phase_review' && body==params.slice(:id,:hash,:decision),'PHASE_REVIEW_ACTOR_OR_HASH')
    check(controller.rendered_status==:ok,'PHASE_REVIEW_UI_DENIED')
  else
    check(controller.head_status==:forbidden && Qldapm::AiBridge.calls.size==before,"PHASE_REVIEW_ESCALATION_#{id}")
  end
end
before=Qldapm::AiBridge.calls.size
missing=review_controller(project,actors[18],params.except(:acknowledge));missing.phase_decision
check(missing.rendered_status==:unprocessable_entity && Qldapm::AiBridge.calls.size==before,'PHASE_REVIEW_NO_ACK')
actors.each do |id,actor|
  controller=review_controller(project,actor,{});controller.phases
  check([18,19,20].include?(id) ? controller.rendered_status==:ok : controller.head_status==:forbidden,"PHASE_READ_UI_ROLE_#{id}")
end
actors[18].enabled=false
revoked=review_controller(project,actors[18],params);revoked.phase_decision
check(revoked.head_status==:forbidden,'PHASE_REVOKED_OWNER_ALLOWED');actors[18].enabled=true
puts 'Native phase UI: fresh own identity, Manager-only exact review, BA read/draft, revocation and no-consent denial PASS'

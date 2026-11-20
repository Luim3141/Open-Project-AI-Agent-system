require_relative 'test_policy'

policy = Qldapm::GatePolicy.new
manager = {'id'=>18, 'role'=>'AI_SYSTEM_OWNER'}
data = {'stream'=>'development','kind'=>'work','revision'=>3,'reviewer_id'=>18,'contributors'=>[21],
  'checklist'=>[{'done'=>true,'reference'=>'fixture:application-check','revision'=>3}], 'evidence'=>{}, 'approvals'=>{}}
%w[implementation test_cases test_build test].each do |key|
  data['evidence'][key]=[{'actor_id'=>key=='test' ? 23 : 21,'revision'=>3,'reference'=>'fixture:'+key,'result'=>'passed'}]
end
%w[code test completion].each do |key|
  data['approvals'][key]={'actor_id'=>18,'revision'=>3,'reference'=>'fixture:review-'+key}
end
item={'type'=>'Subtask','native_subtask'=>true,'assignee'=>21,'children'=>[],'blocking_bugs'=>[],'data'=>data}
expected=[['NEW','IN PROGRESS'],['IN PROGRESS','REVIEW'],['REVIEW','DONE'],['REVIEW','IN PROGRESS'],['DONE','IN PROGRESS']]
assert(policy.edges(item).keys.sort==expected.sort,'Native development Subtask must use actual four-state schema')
[['IN PROGRESS','REVIEW'],['REVIEW','DONE']].each do |from,to|
  assert(policy.errors(item,manager,from,to).empty?,"complete Native development evidence rejected #{from}->#{to}")
  %w[implementation test_cases test_build test].each do |key|
    missing=Marshal.load(Marshal.dump(item));missing['data']['evidence'].delete(key)
    assert(policy.errors(missing,manager,from,to).include?('EVIDENCE_'+key.upcase+'_REQUIRED'),"missing #{key} accepted #{to}")
  end
  %w[code test].each do |key|
    stale=Marshal.load(Marshal.dump(item));stale['data']['approvals'][key]['revision']=2
    assert(policy.errors(stale,manager,from,to).include?('APPROVAL_'+key.upcase+'_REQUIRED'),"stale #{key} accepted #{to}")
  end
  failed=Marshal.load(Marshal.dump(item));failed['data']['evidence']['test'][-1]['result']='failed'
  assert(policy.errors(failed,manager,from,to).include?('EVIDENCE_TEST_REQUIRED'),'failed QA accepted')
  blocked=Marshal.load(Marshal.dump(item));blocked['blocking_bugs']=[{'status'=>'NEW'}]
  assert(policy.errors(blocked,manager,from,to).include?('BLOCKING_BUGS'),"open defect accepted #{to}")
  unchecked=Marshal.load(Marshal.dump(item));unchecked['data']['checklist'][0]['done']=false
  assert(policy.errors(unchecked,manager,from,to).include?('CHECKLIST_INCOMPLETE'),'unchecked implementation accepted')
  self_review=Marshal.load(Marshal.dump(item));self_review['data']['reviewer_id']=21
  assert(policy.errors(self_review,manager,from,to).include?('REVIEWER_REQUIRED'),'self reviewer accepted')
  %w[BA-PM BE FE QA outsider].each do |role|
    assert(policy.errors(item,{'id'=>21,'role'=>role},from,to)==['TRANSITION_DENIED'],'Native non-manager permission widened')
  end
end
legacy=Marshal.load(Marshal.dump(item));legacy.delete('native_subtask')
assert(policy.edges(legacy).key?(['IN PROGRESS','CODE REVIEW']),'legacy logical development policy changed')
forged=Marshal.load(Marshal.dump(legacy));forged['data']['native_subtask']=true
assert(policy.edges(forged)==policy.edges(legacy),'caller gate-data marker granted Native policy')
puts 'NATIVE_SUBTASK_FOUR_STATE_STRICT_EVIDENCE_POLICY_PASS'

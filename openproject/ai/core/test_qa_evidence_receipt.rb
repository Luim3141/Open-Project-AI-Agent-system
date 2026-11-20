require 'tmpdir'
require 'openssl'
require_relative 'test_owner_gate_actions'
require_relative 'overlay/app/services/qldapm/qa_evidence_receipt'

class QaReceiptItem
  attr_accessor :id,:project,:project_id,:subject,:description,:lock_version,:start_date,:due_date,:type,:status,:priority,:assigned_to_id,:parent_id,:qldapm_gate
  def initialize
    @id=379;@project_id=5;@project=OpenStruct.new(id:5,identifier:'qldapm-local');@lock_version=7;@subject='Kiểm thử Native Unicode'
    @description='AC1: native.startDate == "2026-10-26"';@start_date=Date.new(2026,10,26);@due_date=Date.new(2026,10,27)
    @type=OpenStruct.new(id:1,name:'Task');@status=OpenStruct.new(id:7,name:'IN TESTING');@priority=OpenStruct.new(id:8,name:'Normal');@assigned_to_id=21
    @qldapm_gate={'revision'=>3,'reviewer_id'=>18,'contributors'=>[19],'evidence'=>{},'approvals'=>{}}
  end
  def qldapm_managed? = true
  def qldapm_actor(user) = {'id'=>user.id,'role'=>Qldapm::Rbac.role(project,user,fresh:true)}
  def type_id = type.id
  def status_id = status.id
  def priority_id = priority.id
  def qldapm_snapshot = {'id'=>id,'type'=>type.name,'status'=>status.name,'assignee'=>assigned_to_id,'data'=>qldapm_gate,'children'=>[]}
end
def canonical_qa(value) = JSON.generate(Qldapm::Mutations.canonical(value))
def sha_qa(value) = Digest::SHA256.hexdigest(value)
def sign_qa(value,key,domain)
  document=canonical_qa(value)
  {'document'=>document,'signature'=>OpenSSL::HMAC.hexdigest('SHA256',key,domain+document)}
end
require_relative 'overlay/app/services/qldapm/mutations'
item=QaReceiptItem.new;key='isolated-native-qa-proof-key';at=Time.now.to_i
snapshot={'id'=>379,'version'=>7,'description'=>item.description,'project'=>'/api/v3/projects/5','fields'=>{
  'subject'=>item.subject,'startDate'=>'2026-10-26','dueDate'=>'2026-10-27','type_id'=>1,'status_id'=>7,'assignee_id'=>21,'priority_id'=>8,'priority_name'=>'Normal','parent_id'=>nil}}
binding={'native_id'=>379,'version'=>7,'snapshot_sha256'=>sha_qa(canonical_qa(snapshot)),'criteria_sha256'=>sha_qa(item.description),'assignee'=>'/api/v3/users/21'}
producer={'id'=>'qldapm-native-readback-v1','code_sha256'=>'a'*64};tests=[{'criterion_id'=>'AC1','reference'=>'Native:AC1:startDate','expected'=>'"2026-10-26"','actual'=>'"2026-10-26"','outcome'=>'PASSED','observed_at'=>at}]
artifact=canonical_qa({'suite'=>producer['id'],'project_id'=>5,'binding'=>binding,'producer'=>producer,'started_at'=>at-1,'finished_at'=>at,'tests'=>tests,'verdict'=>'PASSED'})
run={'id'=>'11111111-1111-4111-8111-111111111111','actor'=>19,'project_id'=>5,'binding'=>binding,'producer'=>producer,'criteria'=>{'AC1'=>'native.startDate == "2026-10-26"'},'tests'=>tests,'started_at'=>at-1,'finished_at'=>at,'verdict'=>'PASSED','artifact'=>artifact,'artifact_sha256'=>sha_qa(artifact),'verification_kind'=>'AUTOMATED_NATIVE_READBACK'}
manifest={'schema'=>'QLDAPM_AUTOMATED_NATIVE_QA_V1','work_package_id'=>379,'source_version'=>7,'criteria'=>run['criteria'],'tests'=>tests,'artifact_sha256'=>run['artifact_sha256'],'started_at'=>at-1,'finished_at'=>at}
evidence={'id'=>'22222222-2222-4222-8222-222222222222','actor'=>19,'role'=>'AUTOMATED_PRODUCER','project_id'=>5,'captured_at'=>at,'verification_kind'=>run['verification_kind'],'producer'=>producer,'run_id'=>run['id'],'binding'=>binding.merge('artifact_sha256'=>run['artifact_sha256']),'manifest'=>manifest}
hash=sha_qa(canonical_qa(evidence));reviews=[{'evidence_id'=>evidence['id'],'hash'=>hash,'stage'=>'qa','actor'=>23,'role'=>'QA','decision'=>'accept','at'=>at},{'evidence_id'=>evidence['id'],'hash'=>hash,'stage'=>'manager','actor'=>18,'role'=>'AI_SYSTEM_OWNER','decision'=>'accept','at'=>at}]
packet={'version'=>1,'run'=>sign_qa(run,key,"qldapm.native-qa-run.v1\0"),'evidence_document'=>canonical_qa(evidence),'reviews'=>reviews.map { |r| sign_qa(r,key,"qldapm.native-qa-review.v1\0") }}
Dir.mktmpdir do |directory|
  path=File.join(directory,'ui.key');File.binwrite(path,key);original=item.qldapm_gate.deep_dup
  result=Qldapm::QaEvidenceReceipt.verify(packet,item,User.registry[19],'REVIEW',key_file:path)
  check(result['data']['approvals']['test']['actor_id']==18,'WRONG_INDEPENDENT_MANAGER')
  check(result['data']['evidence']['test'].last['actor_id']==23,'WRONG_QA_REVIEW_SOURCE')
  check(result['data']['qa_bridge']['artifact_sha256']==run['artifact_sha256'],'ARTIFACT_PROVENANCE_LOST')
  check(item.qldapm_gate==original && item.lock_version==7,'READONLY_QA_PREFLIGHT_MUTATED_MODEL')
  preflight=Qldapm::QaEvidenceReceipt.preflight(packet,item,User.registry[19],'REVIEW',key_file:path)
  check(preflight['valid'] && preflight['errors'].empty? && preflight['lockVersion']==7,'SIGNED_QA_READONLY_PREFLIGHT_FAILED')
  cases=[->(p) { p['run']['signature']='0'*64 },->(p) { p['reviews'].pop },->(p) { p['reviews'][0]['signature']='0'*64 },
    ->(p) { p['approved']=true },->(p) { p['evidence_document']='{}' }]
  cases.each do |mutate|
    altered=Marshal.load(Marshal.dump(packet));mutate.call(altered)
    begin
      Qldapm::QaEvidenceReceipt.verify(altered,item,User.registry[19],'REVIEW',key_file:path)
      raise 'FORGED_QA_PACKET_ACCEPTED'
    rescue ArgumentError
    end
  end
  [20,21,22,23,99].each do |actor|
    begin
      Qldapm::QaEvidenceReceipt.verify(packet,item,User.registry[actor],'REVIEW',key_file:path)
      raise 'LOW_ROLE_QA_BRIDGE_ACCEPTED'
    rescue ArgumentError
    end
  end
  [-> {item.lock_version=8},-> {item.description+=' changed'},-> {item.project_id=6},-> {item.qldapm_gate['contributors']=[18,19]}].each do |change|
    original_item=Marshal.load(Marshal.dump(item));change.call
    begin
      Qldapm::QaEvidenceReceipt.verify(packet,item,User.registry[19],'REVIEW',key_file:path)
      raise 'STALE_OR_NONINDEPENDENT_QA_PROOF_ACCEPTED'
    rescue ArgumentError
    ensure
      item=original_item
    end
  end
  [18,23].each do |actor|
    User.registry[actor].enabled=false
    begin
      Qldapm::QaEvidenceReceipt.verify(packet,item,User.registry[19],'REVIEW',key_file:path)
      raise 'REVOKED_REVIEWER_STILL_AUTHORIZED'
    rescue ArgumentError
    ensure
      User.registry[actor].enabled=true
    end
  end
end
puts 'Native QA receipt: signed run/artifact/two independent reviews, source/role/lock/readonly and forged/stale denial PASS (isolated fixtures)'

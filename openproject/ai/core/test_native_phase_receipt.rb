require 'tmpdir'
require 'ostruct'
require 'active_support/all'
require_relative 'overlay/app/models/qldapm/gate_policy'
require_relative 'overlay/app/services/qldapm/native_phase_receipt'

module Qldapm::Rbac
  def self.role(_project,user,fresh: false)
    raise 'PHASE_REQUIRES_FRESH_ROLE' unless fresh
    {18=>'AI_SYSTEM_OWNER',19=>'PM',20=>'BA-PM',21=>'BE',22=>'FE',23=>'QA'}[user.id]
  end
  def self.pm?(project,user,fresh: false) = %w[PM AI_SYSTEM_OWNER].include?(role(project,user,fresh:))
end
class User
  def self.active = self
  def self.denied = (@denied ||= [])
  def self.find_by(id:)
    actor=OpenStruct.new(id:id)
    actor.define_singleton_method(:allowed_in_work_package?) { |permission,_item| permission==:view_work_packages && !User.denied.include?(id) }
    actor
  end
end

Dir.mktmpdir do |directory|
  key='isolated-native-phase-fixture';file=File.join(directory,'key');File.binwrite(file,key)
  project=OpenStruct.new(id:5)
  item=OpenStruct.new(id:376,project_id:5,project:project,lock_version:0,assigned_to_id:21,
    description:"Story: Preserve unknown vectors during ingestion.\nAC1: Registered cleanup preserves quarantined points.\nScope: Exact source identity and payload only.\nAnalysis: Use registered point proofs and durable retry.\n",
    status:OpenStruct.new(name:'NEW'),type:OpenStruct.new(name:'Task'),priority:OpenStruct.new(name:'Normal'),
    type_id:1,status_id:1,priority_id:8,parent_id:nil,start_date:nil,due_date:nil)
  item.define_singleton_method(:qldapm_managed?) { true }
  item.define_singleton_method(:qldapm_gate) { {'revision'=>1,'evidence'=>{},'approvals'=>{},'contributors'=>[18]} }
  item.define_singleton_method(:qldapm_snapshot) { {'type'=>type.name,'status'=>status.name,'assignee'=>assigned_to_id,'data'=>qldapm_gate,'children'=>[]} }
  item.define_singleton_method(:qldapm_actor) { |user| {'id'=>user.id,'role'=>Qldapm::Rbac.role(project,user,fresh:true)} }
  manager=OpenStruct.new(id:19)
  manager.define_singleton_method(:allowed_in_work_package?) { |permission,target| permission==:edit_work_packages && target.equal?(item) }
  sign=->(value,domain) { body=Qldapm::NativePhaseReceipt.canonical(value);{'document'=>body,'signature'=>OpenSSL::HMAC.hexdigest('SHA256',key,domain+body)} }
  source=Qldapm::QaEvidenceReceipt.native_snapshot(item)
  document={'version'=>1,'id'=>'11111111-1111-4111-8111-111111111111','actor'=>18,'project_id'=>5,'kind'=>'scope',
    'source'=>source,'gate_revision'=>1,'created_at'=>Time.now.to_f}
  hash=Digest::SHA256.hexdigest(Qldapm::NativePhaseReceipt.canonical(document))
  review={'artifact_id'=>document['id'],'hash'=>hash,'actor'=>19,'role'=>'PM','decision'=>'accept','kind'=>'scope','approvals'=>['scope'],'at'=>Time.now.to_f}
  packet=->(d=document,r=review) { {'version'=>1,'artifact'=>sign.call(d,Qldapm::NativePhaseReceipt::DOMAIN),'review'=>sign.call(r,Qldapm::NativePhaseReceipt::REVIEW_DOMAIN)} }
  reject=->(proof,destination='IN ANALYSIS') do
    begin
      Qldapm::NativePhaseReceipt.preflight(proof,item,manager,destination,key_file:file)
      raise 'INVALID_NATIVE_PHASE_ACCEPTED'
    rescue ArgumentError
    end
  end
  rejected=review.merge('decision'=>'reject');reject.call(packet.call(document,rejected))
  reject.call(packet.call(document,review.merge('actor'=>18,'role'=>'AI_SYSTEM_OWNER')))
  reject.call(packet.call(document,review.merge('actor'=>21,'role'=>'BE')))
  reject.call(packet.call(document,review.merge('hash'=>'0'*64)))
  reject.call(packet.call(document,review.merge('approvals'=>[])))
  reject.call(packet.call(document.merge('source'=>source.merge('id'=>999))))
  reject.call(packet.call(document.merge('source'=>source.merge('version'=>1))))
  reject.call(packet.call(document.merge('approved'=>true)))
  broken=packet.call;broken['artifact']['signature']='0'*64;reject.call(broken)
  User.denied << 19;reject.call(packet.call);User.denied.clear
  User.denied << 18;reject.call(packet.call);User.denied.clear
  reject.call(packet.call,'REVIEW')
  original=item.description
  item.description=original.gsub(/^AC1:.*\n/,'')
  missing=document.merge('source'=>Qldapm::QaEvidenceReceipt.native_snapshot(item))
  missing_review=review.merge('hash'=>Digest::SHA256.hexdigest(Qldapm::NativePhaseReceipt.canonical(missing)))
  reject.call(packet.call(missing,missing_review))
  item.description=original;item.status.name='IN PROGRESS';reject.call(packet.call)
  item.status.name='NEW'
  result=Qldapm::NativePhaseReceipt.preflight(packet.call,item,manager,'IN ANALYSIS',key_file:file)
  raise 'VALID_NATIVE_SOURCE_PHASE_BLOCKED' unless result['valid'] && result['source_version']==0 && result['hash']==hash
  raise 'PHASE_PREFLIGHT_PERSISTED_DATA' unless item.qldapm_gate['evidence'].empty?
  raise 'PHASE_SCOPE_APPROVAL_MISSING' unless result['data']['approvals']['scope']['actor_id']==19
  raise 'PHASE_MODEL_APPROVAL_OR_REVISION_CHANGED' unless result['data']['revision']==2 && result['data']['acceptance_criteria'].include?('AC1:')
  item.description=original.gsub("\n","\r\n")
  crlf=document.merge('source'=>Qldapm::QaEvidenceReceipt.native_snapshot(item))
  crlf_review=review.merge('hash'=>Digest::SHA256.hexdigest(Qldapm::NativePhaseReceipt.canonical(crlf)))
  raise 'NATIVE_CRLF_SOURCE_REJECTED' unless Qldapm::NativePhaseReceipt.preflight(packet.call(crlf,crlf_review),item,manager,'IN ANALYSIS',key_file:file)['valid']
  item.description=original.gsub(/^AC1:.*$/, 'AC1:    ')
  blank=document.merge('source'=>Qldapm::QaEvidenceReceipt.native_snapshot(item))
  blank_review=review.merge('hash'=>Digest::SHA256.hexdigest(Qldapm::NativePhaseReceipt.canonical(blank)))
  reject.call(packet.call(blank,blank_review))
end
puts 'Native source phase: exact signed source/review, fresh Native policy, stale/role/hash/unsupported transition denial PASS'

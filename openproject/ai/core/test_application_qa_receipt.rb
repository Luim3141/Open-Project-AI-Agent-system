require 'fileutils'
require_relative 'test_qa_evidence_receipt'
require_relative 'overlay/app/services/qldapm/application_qa_sources'
require_relative 'overlay/app/services/qldapm/application_qa_receipt'

item=QaReceiptItem.new;item.id=371;item.subject='[Bug] [CODEX TEST] WBS application qualification'
criteria=JSON.parse(File.read(File.join(__dir__,'../tests/fixtures/wbs_bug371_criteria.json')))
item.description=criteria.map { |id,text| "#{id}: #{text}" }.join("\n")
item.qldapm_gate={'revision'=>3,'reviewer_id'=>19,'contributors'=>[],'evidence'=>{},'approvals'=>{}}
key='isolated-application-qa-key';at=Time.now.to_i
Dir.mktmpdir do |root|
  Qldapm::ApplicationQaSources::PATHS.each do |path|
    target=File.join(root,path);FileUtils.mkdir_p(File.dirname(target));File.write(target,"fixture #{path}")
  end
  Object.const_set(:Rails,Module.new) unless defined?(Rails)
  Rails.define_singleton_method(:root) { root }
  source=Qldapm::QaEvidenceReceipt.native_snapshot(item)
  binding={'native_id'=>371,'version'=>item.lock_version,'snapshot_sha256'=>sha_qa(canonical_qa(source)),
    'criteria_sha256'=>sha_qa(item.description),'assignee'=>'/api/v3/users/21'}
  producer={'id'=>'qldapm-wbs-application-v1','code_sha256'=>'fec0d913e57172c422f749a3d9e068a5cd33aa6ff35b4cfee43f0fa0aed05f77'}
  tests=criteria.keys.map { |id| {'criterion_id'=>id,'reference'=>"wbs-application:#{id}",'expected'=>'Pinned assertion passes',
    'actual'=>'Isolated application qualification completed','outcome'=>'PASSED','proof_sha256'=>'5'*64} }
  proof={'version'=>1,'id'=>'33333333-3333-4333-8333-333333333333','actor'=>18,'project_id'=>5,
    'producer'=>producer['id'],'producer_sha256'=>producer['code_sha256'],'source'=>source,'criteria'=>criteria,
    'sources'=>{'core'=>Qldapm::ApplicationQaSources.read(root),'gateway'=>%w[native_wbs.py native_wbs_hierarchy.py native_wbs_relations.py wbs_analysis.py].to_h { |path| [path,'1'*64] }},
    'build'=>{'core'=>'sha256:'+'2'*64,'gateway'=>'sha256:'+'3'*64},'started_at'=>at-1,'finished_at'=>at,
    'tests'=>tests,'verdict'=>'PASSED','qualification'=>'ISOLATED_APPLICATION_AND_NATIVE; synthetic embeddings and isolated decisions; not human QA approval'}
  artifact=canonical_qa(proof)
  run={'id'=>'11111111-1111-4111-8111-111111111111','actor'=>18,'project_id'=>5,'verification_kind'=>'AUTOMATED_APPLICATION_WBS',
    'binding'=>binding,'producer'=>producer,'criteria'=>criteria,'tests'=>tests,'started_at'=>at-1,'finished_at'=>at,'verdict'=>'PASSED',
    'artifact'=>artifact,'artifact_sha256'=>sha_qa(artifact),'application_signature'=>OpenSSL::HMAC.hexdigest('SHA256',key,"qldapm.wbs-application-proof.v1\0"+artifact)}
  evidence={'id'=>'22222222-2222-4222-8222-222222222222','actor'=>18,'role'=>'AUTOMATED_PRODUCER','project_id'=>5,
    'verification_kind'=>run['verification_kind'],'producer'=>producer,'run_id'=>run['id'],
    'binding'=>binding.merge('artifact_sha256'=>run['artifact_sha256']),
    'manifest'=>{'schema'=>'QLDAPM_AUTOMATED_APPLICATION_QA_V1','work_package_id'=>371,'source_version'=>item.lock_version,
      'criteria'=>criteria,'tests'=>tests,'artifact_sha256'=>run['artifact_sha256'],'started_at'=>at-1,'finished_at'=>at}}
  fingerprint=sha_qa(canonical_qa(evidence))
  reviews=[{'stage'=>'qa','actor'=>23,'role'=>'QA'},{'stage'=>'manager','actor'=>19,'role'=>'PM'}].map { |r|
    r.merge('evidence_id'=>evidence['id'],'hash'=>fingerprint,'decision'=>'accept','at'=>at) }
  packet={'version'=>1,'run'=>sign_qa(run,key,Qldapm::QaEvidenceReceipt::RUN_DOMAIN),'evidence_document'=>canonical_qa(evidence),
    'reviews'=>reviews.map { |r| sign_qa(r,key,Qldapm::QaEvidenceReceipt::REVIEW_DOMAIN) }}
  path=File.join(root,'ui.key');File.binwrite(path,key)
  accepted=Qldapm::QaEvidenceReceipt.preflight(packet,item,User.registry[18],'REVIEW',key_file:path)
  check(accepted['valid'],'APPLICATION_QA_EXISTING_NATIVE_GATE_DENIED')
  result=Qldapm::QaEvidenceReceipt.verify(packet,item,User.registry[18],'REVIEW',key_file:path)
  check(result['data']['evidence']['test'].last['verification']=='automated_application_wbs','APPLICATION_PROVENANCE_MISLABELLED')
  check(item.qldapm_gate['evidence'].empty? && item.lock_version==7,'APPLICATION_PREFLIGHT_WROTE_NATIVE')
  item.status=OpenStruct.new(id:2,name:'IN ANALYSIS')
  begin
    Qldapm::QaEvidenceReceipt.preflight(packet,item,User.registry[18],'REVIEW',key_file:path)
    raise 'APPLICATION_PROOF_BYPASSED_NATIVE_PHASE'
  rescue ArgumentError
  ensure
    item.status=OpenStruct.new(id:7,name:'IN TESTING')
  end
  original=run.deep_dup
  [->(r) {r['application_signature']='0'*64},->(r) {r['producer']['code_sha256']='0'*64},
   ->(r) {r['verification_kind']='CALLER_PASS'}].each do |change|
    altered=original.deep_dup;change.call(altered);bad=packet.deep_dup;bad['run']=sign_qa(altered,key,Qldapm::QaEvidenceReceipt::RUN_DOMAIN)
    begin
      Qldapm::QaEvidenceReceipt.verify(bad,item,User.registry[18],'REVIEW',key_file:path)
      raise 'UNTRUSTED_APPLICATION_PROOF_ACCEPTED'
    rescue ArgumentError
    end
  end
  File.write(File.join(root,Qldapm::ApplicationQaSources::PATHS.first),'changed deployed source')
  begin
    Qldapm::QaEvidenceReceipt.verify(packet,item,User.registry[18],'REVIEW',key_file:path)
    raise 'APPLICATION_CORE_CODE_DRIFT_ACCEPTED'
  rescue ArgumentError
  end
end
puts 'Application QA signed proof, source/producer pin, independent review and existing Native phase/gate: PASS (isolated fixture only)'

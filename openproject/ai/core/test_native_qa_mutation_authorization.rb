require_relative 'test_qa_evidence_receipt'
Dir.mktmpdir do |directory|
  key='isolated-native-mutation-key';path=File.join(directory,'ui.key');File.binwrite(path,key)
  old=ENV['QLDAPM_UI_KEY_FILE'];ENV['QLDAPM_UI_KEY_FILE']=path
  item=QaReceiptItem.new;actor=User.registry[19];proposal='33333333-3333-4333-8333-333333333333'
  payload={'action'=>'transition','lock_version'=>7,'status_id'=>9,'request_id'=>'QLDAPM-request-'+Digest::SHA256.hexdigest("19:proposal-#{proposal}"),
    'qa_proof'=>{},'qa_authorization'=>{'proposal_id'=>proposal,'proposal_hash'=>'a'*64,'qa_evidence_id'=>'22222222-2222-4222-8222-222222222222','qa_evidence_hash'=>'b'*64}}
  def qa_mutation_headers(payload,item,key,at=Time.now.to_i)
    sha=Digest::SHA256.hexdigest(JSON.generate(Qldapm::Mutations.canonical(payload.merge('id'=>item.id))))
    {'X-Qldapm-At'=>at.to_s,'X-Qldapm-Mutation'=>OpenSSL::HMAC.hexdigest('SHA256',key,"19:#{at}:#{sha}")}
  end
  cases=[
    [payload,{},'QA_GATEWAY_SIGNATURE_REQUIRED'],
    [payload,{'X-Qldapm-At'=>Time.now.to_i.to_s,'X-Qldapm-Mutation'=>'0'*64},'AI_SIGNATURE_DENIED'],
    [payload,qa_mutation_headers(payload,item,key,Time.now.to_i-60),'AI_SIGNATURE_EXPIRED']
  ]
  missing=payload.reject { |k,_| k=='qa_authorization' };cases << [missing,qa_mutation_headers(missing,item,key),'QA_PROOF_AND_AUTHORIZATION_REQUIRED']
  altered=payload.merge('qa_authorization'=>payload['qa_authorization'].merge('approved'=>true));cases << [altered,qa_mutation_headers(altered,item,key),'QA_APPROVED_REQUEST_BINDING_REQUIRED']
  wrong=payload.merge('request_id'=>'QLDAPM-request-'+'b'*64);cases << [wrong,qa_mutation_headers(wrong,item,key),'QA_APPROVED_REQUEST_BINDING_REQUIRED']
  update=payload.merge('action'=>'update_work_package');cases << [update,qa_mutation_headers(update,item,key),'QA_TRANSITION_ONLY']
  cases.each do |body,headers,expected|
    begin
      Qldapm::Mutations.call(item,actor,body,headers)
      raise 'QA_MUTATION_AUTHORIZATION_BYPASSED'
    rescue ArgumentError => error
      check(error.message==expected,"WRONG_QA_MUTATION_DENIAL: #{error.message}, expected #{expected}")
    end
  end
ensure
  ENV['QLDAPM_UI_KEY_FILE']=old
end
puts 'Native QA mutation authorization: no/missing/expired/forged signature, missing proof/auth, altered scope/hash and wrong action denied before persistence PASS'

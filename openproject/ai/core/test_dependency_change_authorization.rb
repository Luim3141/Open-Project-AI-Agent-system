require 'tmpdir'
require_relative 'overlay/app/services/qldapm/dependency_mutation'
require_relative 'overlay/app/services/qldapm/dependency_change'

Dir.mktmpdir do |directory|
  path=File.join(directory,'key');key='isolated-dependency-change-key';File.binwrite(path,key)
  old=ENV['QLDAPM_UI_KEY_FILE'];ENV['QLDAPM_UI_KEY_FILE']=path
  actor=Struct.new(:id).new(18);proposal='11111111-1111-4111-8111-111111111111'
  base={'relation_id'=>353,'predecessor_id'=>376,'successor_id'=>377,'scope_hash'=>'a'*64,
        'proposal_id'=>proposal,'proposal_hash'=>'b'*64,
        'request_id'=>'QLDAPM-request-'+Digest::SHA256.hexdigest("18:proposal-#{proposal}")}
  sign=lambda do |body|
    at=Time.now.to_i;{'X-Qldapm-At'=>at.to_s,'X-Qldapm-Mutation'=>OpenSSL::HMAC.hexdigest('SHA256',key,"18:#{at}:#{Qldapm::DependencyChange.fingerprint(body)}")}
  end
  [base.merge('operation'=>'update','lag'=>2),base.merge('operation'=>'delete')].each do |payload|
    Qldapm::DependencyChange.validate!(payload)
    Qldapm::DependencyChange.verify_signature!(actor,payload,sign.call(payload))
    invalid=[payload.merge('relation_id'=>true),payload.merge('relation_id'=>0),payload.merge('operation'=>'create'),
             payload.merge('actor_id'=>18),payload.merge('approved'=>true),payload.merge('scope_hash'=>'x'),
             payload.merge('successor_id'=>376),payload.reject { |key,_| key=='proposal_hash' }]
    invalid << (payload['operation']=='delete' ? payload.merge('lag'=>0) : payload.merge('lag'=>2001))
    invalid.each do |body|
      begin
        Qldapm::DependencyChange.validate!(body);raise 'INVALID_DEPENDENCY_CHANGE_ACCEPTED'
      rescue ArgumentError
      end
    end
    [payload.merge('relation_id'=>354),payload.merge('operation'=>payload['operation']=='update' ? 'delete' : 'update')].each do |body|
      begin
        Qldapm::DependencyChange.verify_signature!(actor,body,sign.call(payload));raise 'ALTERED_DEPENDENCY_CHANGE_ACCEPTED'
      rescue ArgumentError
      end
    end
    begin
      Qldapm::DependencyChange.verify_signature!(Struct.new(:id).new(19),payload,sign.call(payload));raise 'CROSS_ACTOR_CHANGE_ACCEPTED'
    rescue ArgumentError
    end
  end
ensure
  ENV['QLDAPM_UI_KEY_FILE']=old
end
puts 'Dependency update/delete exact schema, actor, relation, hash and signed operation binding PASS'

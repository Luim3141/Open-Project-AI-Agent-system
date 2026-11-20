require 'tmpdir'
require 'ostruct'
require_relative 'overlay/app/services/qldapm/native_deletion'

Dir.mktmpdir do |directory|
  key='isolated-native-deletion-key';path=File.join(directory,'key');File.binwrite(path,key)
  old=ENV['QLDAPM_UI_KEY_FILE'];ENV['QLDAPM_UI_KEY_FILE']=path
  actor=Struct.new(:id).new(18);proposal='11111111-1111-4111-8111-111111111111'
  payload={'id'=>376,'lock_version'=>0,'snapshot_sha256'=>'a'*64,'proposal_id'=>proposal,'proposal_hash'=>'b'*64,
    'request_id'=>'QLDAPM-request-'+Digest::SHA256.hexdigest("18:proposal-#{proposal}")}
  at=Time.now.to_i
  headers={'X-Qldapm-At'=>at.to_s,'X-Qldapm-Mutation'=>OpenSSL::HMAC.hexdigest('SHA256',key,"18:#{at}:#{Qldapm::NativeDeletion.fingerprint(payload)}")}
  Qldapm::NativeDeletion.verify_signature!(actor,payload,headers)
  project=Object.new;item=OpenStruct.new(project_id:5,project:project,lock_version:0)
  native_user=Object.new
  native_user.define_singleton_method(:allowed_in_project?) { |permission,target| raise 'DELETE_PERMISSION_CONTEXT_OR_PROJECT_WRONG' unless permission==:delete_work_packages && target.equal?(project);true }
  begin
    Qldapm::NativeDeletion.eligible!(native_user,item,{'lock_version'=>1});raise 'STALE_DELETE_NOT_BLOCKED'
  rescue ArgumentError => error
    raise unless error.message=='NATIVE_DELETE_STALE_SOURCE'
  end
  [payload.merge('id'=>true),payload.merge('id'=>0),payload.merge('lock_version'=>-1),payload.merge('lock_version'=>false),
   payload.merge('approved'=>true),payload.merge('actor_id'=>18),payload.merge('snapshot_sha256'=>'x'),
   payload.merge('proposal_id'=>'x'),payload.reject { |k,_| k=='proposal_hash' }].each do |body|
    begin
      Qldapm::NativeDeletion.validate!(body);raise 'INVALID_DELETE_SCHEMA_ACCEPTED'
    rescue ArgumentError
    end
  end
  [payload.merge('id'=>377),payload.merge('lock_version'=>1),payload.merge('proposal_hash'=>'c'*64)].each do |body|
    begin
      Qldapm::NativeDeletion.verify_signature!(actor,body,headers);raise 'ALTERED_DELETE_ACCEPTED'
    rescue ArgumentError
    end
  end
  begin
    Qldapm::NativeDeletion.verify_signature!(Struct.new(:id).new(19),payload,headers);raise 'CROSS_ACTOR_DELETE_ACCEPTED'
  rescue ArgumentError
  end
ensure
  ENV['QLDAPM_UI_KEY_FILE']=old
end
puts 'Native permanent deletion schema, version, source hash, proposal and authenticated actor binding PASS'

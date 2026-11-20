require 'json'
require 'digest'
require 'openssl'
require 'tmpdir'
require_relative 'overlay/app/services/qldapm/dependency_mutation'

def check(value, message)
  raise message unless value
end

Dir.mktmpdir do |directory|
  path = File.join(directory, 'key'); key = 'isolated-dependency-key'
  File.binwrite(path, key); old = ENV['QLDAPM_UI_KEY_FILE']; ENV['QLDAPM_UI_KEY_FILE'] = path
  actor = Struct.new(:id).new(18)
  proposal = '11111111-1111-4111-8111-111111111111'
  payload = {'predecessor_id'=>376,'successor_id'=>377,'lag'=>2,'scope_hash'=>'a'*64,
             'proposal_id'=>proposal,'proposal_hash'=>'b'*64,
             'request_id'=>'QLDAPM-request-'+Digest::SHA256.hexdigest("18:proposal-#{proposal}")}
  sign = lambda do |body, at=Time.now.to_i|
    sha = Digest::SHA256.hexdigest(JSON.generate(Qldapm::DependencyMutation.canonical(body)))
    {'X-Qldapm-At'=>at.to_s,'X-Qldapm-Mutation'=>OpenSSL::HMAC.hexdigest('SHA256',key,"18:#{at}:#{sha}")}
  end
  Qldapm::DependencyMutation.validate!(payload)
  Qldapm::DependencyMutation.verify_signature!(actor,payload,sign.call(payload))
  invalid = [payload.merge('lag'=>true),payload.merge('lag'=>2001),payload.merge('predecessor_id'=>377),
             payload.merge('successor_id'=>0),payload.merge('scope_hash'=>'x'),payload.merge('approved'=>true)]
  invalid.each do |body|
    begin
      Qldapm::DependencyMutation.validate!(body)
      raise 'DEPENDENCY_INVALID_PAYLOAD_ACCEPTED'
    rescue ArgumentError
    end
  end
  wrong_actor = payload.merge('request_id'=>'QLDAPM-request-'+'c'*64)
  [[payload,{}],[payload,sign.call(payload,Time.now.to_i-60)],
   [wrong_actor,sign.call(wrong_actor)],
   [payload.merge('lag'=>3),sign.call(payload)],
   [payload,sign.call(payload).merge('X-Qldapm-Mutation'=>'0'*64)]].each do |body, headers|
    begin
      Qldapm::DependencyMutation.verify_signature!(actor,body,headers)
      raise 'DEPENDENCY_SIGNATURE_BYPASSED'
    rescue ArgumentError
    end
  end
ensure
  ENV['QLDAPM_UI_KEY_FILE'] = old
end
puts 'Dependency canonical signature, exact actor/proposal request binding, stale/forged/altered proof and strict payload boundaries PASS'

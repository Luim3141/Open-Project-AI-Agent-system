# Owner-approved BE/FE/QA enrollment; no password, TOTP, role or existing-token changes.
require "json"
require "fileutils"
require "digest"

target=ENV.fetch("QLDAPM_TOKEN_ENROLLMENT_TARGET")
raise "TARGET_DENIED" unless %w[qualification main-owner-approved-20261020].include?(target)
host=ActiveRecord::Base.connection_db_config.configuration_hash[:host]
raise "WRONG_QUALIFICATION" if target=="qualification" && (ENV["QLDAPM_QUALIFICATION"]!="codex-main-20261020" || host!="qa-db")
raise "WRONG_MAIN" if target!="qualification" && (ENV["QLDAPM_QUALIFICATION"].present? || host!="db")
project=Project.find_by!(identifier:"qldapm-local")
raise "WRONG_PROJECT_OR_TOKENS_DISABLED" unless project.id==5 && Setting.api_tokens_enabled?
directory=target=="qualification" ? "/qa-private/token-enrollment" : "/tmp/qldapm-approved-token-enrollment-20261020"
raise "ENROLLMENT_EXISTS_RESUME_REQUIRED" if File.exist?(directory)
FileUtils.mkdir_p(directory,mode:0700)
roles={21=>["be","BE"],22=>["fe","FE"],23=>["qa","QA"]}
security=lambda { User.where(id:18..23).order(:id).map { |u| u.attributes.except("updated_at","last_login_on","last_failed_login_on","failed_login_count") } }
tokens=lambda { Token::API.order(:id).map { |t| t.attributes.except("updated_at","last_used_at") } }
before_security=security.call
before_devices=TwoFactorAuthentication::Device.order(:id).map(&:attributes)
before_tokens=tokens.call
created=[]
ActiveRecord::Base.transaction do
  roles.each do |id,(login,role)|
    user=User.lock.find(id)
    membership=Member.find_by!(project:project,user_id:id)
    raise "IDENTITY_OR_ROLE_MISMATCH" unless user.login==login && user.active? && !user.admin? && membership.roles.map(&:name)==["QLDAPM #{role}"]
    result=APITokens::CreateService.new(user:user,model:Token::API.new).call(token_name:"QLDAPM Main AI Owner Approved 20261020")
    raise "NATIVE_TOKEN_CREATION_FAILED" unless result.success?
    token=result.result
    raise "NATIVE_TOKEN_IDENTITY_FAILED" unless Token::API.find_by_plaintext_value(token.plain_value)&.user_id==id
    File.open(File.join(directory,"user-#{id}.api-token"),File::WRONLY|File::CREAT|File::EXCL,0600) do |file|
      file.write(token.plain_value);file.flush;file.fsync
    end
    created << {user_id:id,token_id:token.id}
  end
  raise "ACCOUNT_SECURITY_CHANGED" unless security.call==before_security
  raise "TOTP_CHANGED" unless TwoFactorAuthentication::Device.order(:id).map(&:attributes)==before_devices
  current=tokens.call
  raise "EXISTING_TOKEN_CHANGED" unless before_tokens.all? { |t| current.include?(t) }
end
receipt={created:created,target:target,existing_tokens_preserved:true,account_security_preserved:true,totp_preserved:true}
File.write(File.join(directory,"receipt.json"),JSON.generate(receipt),mode:"wx",perm:0600)
puts JSON.generate(receipt)

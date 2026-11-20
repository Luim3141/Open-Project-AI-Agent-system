# Owner spec 2de7a2a7: a new real, non-admin Project6-only service principal.
require 'json'
require 'digest'
require 'fileutils'
require 'securerandom'

target=ENV.fetch('QLDAPM_DELEGATED_TARGET')
host=ActiveRecord::Base.connection_db_config.configuration_hash[:host]
raise 'DELEGATED_ENROLLMENT_TARGET_DENIED' unless (target=='qualification' && host=='qa-db') || (target=='main-demo-20261104' && host=='db')
project=Project.find_by!(identifier:'ai-dev-demo')
raise 'DELEGATED_PROJECT_OR_TOKENS_DISABLED' unless project.id==6 && project.active? && Setting.api_tokens_enabled?
role=Role.find_by!(name:'QLDAPM PM')
directory='/tmp/qldapm-owner-delegated-20261104'
raise 'ENROLLMENT_EXISTS_RECONCILE_NO_REPLAY' if File.exist?(directory) || User.exists?(login:'qldapm-demo-delegate')
FileUtils.mkdir_p(directory,mode:0700)
fingerprint=->(rows) { Digest::SHA256.hexdigest(rows.order(:id).map(&:attributes).to_json) }
protected_state=-> { {'project5_members'=>fingerprint.call(Member.where(project_id:5)),
  'project5_work_packages'=>fingerprint.call(WorkPackage.where(project_id:5)),
  'roles'=>fingerprint.call(Role.all),'permissions'=>fingerprint.call(RolePermission.all)} }
before=protected_state.call
receipt=nil
ActiveRecord::Base.transaction do
  password='Aa1!'+SecureRandom.urlsafe_base64(32)
  user=User.create!(login:'qldapm-demo-delegate',firstname:'QLDAPM Demo',lastname:'Delegated Policy',
    mail:'qldapm-demo-delegate@example.invalid',language:'en',password:password,password_confirmation:password,
    status:1,admin:false,force_password_change:false)
  raise 'DISTINCT_SERVICE_PRINCIPAL_REQUIRED' unless user.id>23 && !user.admin?
  membership=Member.create!(project:project,principal:user,roles:[role])
  created=APITokens::CreateService.new(user:user,model:Token::API.new).call(token_name:'Owner-delegated Project6 demo 20261104')
  raise 'NATIVE_TOKEN_CREATION_FAILED' unless created.success?
  token=created.result
  raise 'NATIVE_CREDENTIAL_IDENTITY_MISMATCH' unless Token::API.find_by_plaintext_value(token.plain_value)&.user_id==user.id
  raise 'PROJECT_MEMBERSHIP_SCOPE_CHANGED' unless Member.where(user_id:user.id).pluck(:project_id)==[6]
  raise 'PROTECTED_PROJECT5_OR_ROLE_CHANGED' unless before==protected_state.call
  secret={'principal_id'=>user.id,'api_token'=>token.plain_value}
  File.write(File.join(directory,'principal-secret.json'),JSON.generate(secret),mode:'wx',perm:0600)
  receipt={'principal_id'=>user.id,'login'=>user.login,'admin'=>false,'project_ids'=>[6],
    'membership_id'=>membership.id,'role_id'=>role.id,'role'=>role.name,'token_id'=>token.id,
    'authority'=>'Owner spec 2de7a2a7','decision_source'=>'OWNER_DELEGATED_POLICY_APPROVED',
    'target'=>target,'protected_before'=>before,'protected_after'=>protected_state.call}
  File.write(File.join(directory,'receipt.json'),JSON.generate(receipt),mode:'wx',perm:0600)
end
puts JSON.generate(receipt)

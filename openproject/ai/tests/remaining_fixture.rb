# Isolated backup clone only. Creates new synthetic accounts; existing identities/devices stay untouched.
require 'json'
raise 'ISOLATED_FIXTURE_ONLY' unless ENV['QLDAPM_QUALIFICATION'] == 'remaining-20261018' && URI(ENV.fetch('DATABASE_URL')).host == 'rd-db'
input=JSON.parse(File.read('/qa/fixture-input.json'))
project=Project.find_by!(identifier:'qldapm-local')
records=[]
ActiveRecord::Base.transaction do
input.each do |row|
  raise 'FIXTURE_LOGIN_ONLY' unless row.fetch('login').start_with?('rd-fixture-')
  user=User.find_by(login:row['login']) || User.create!(login:row['login'],firstname:'RD Fixture',lastname:row['role'],mail:row['login']+'@example.invalid',
    language:'en',password:row['password'],password_confirmation:row['password'],status:1,admin:false,force_password_change:false)
  raise 'NOT_SYNTHETIC_USER' unless user.firstname=='RD Fixture' && !user.admin?
  role=Role.find_by(name:'QLDAPM '+row['role']) || (row['role']=='BA' && Role.find_by!(name:'QLDAPM BA-PM'))
  raise 'ROLE_NOT_FOUND' unless role
  Member.create!(project:project,principal:user,roles:[role]) unless Member.exists?(project:project,user_id:user.id)
  device=TwoFactorAuthentication::Device::Totp.find_by(user:user,identifier:'RD isolated fixture') || TwoFactorAuthentication::Device::Totp.create!(user:user,identifier:'RD isolated fixture',active:true,default:true)
  records << row.merge('role'=>role.name.delete_prefix('QLDAPM '),'id'=>user.id,'token'=>Token::API.create_and_return_value(user),'totp_secret'=>device.otp_secret)
end
File.write('/qa/fixture-credentials.json',JSON.generate({'users'=>records,'project_id'=>project.id,'work_package_id'=>nil,
  'fixture_pending_native_creation'=>true}))
end
puts 'ISOLATED_FIXTURE_CREATED'

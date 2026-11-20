require "json"
require "securerandom"
raise "QUALIFICATION_ONLY" unless ENV["QLDAPM_QUALIFICATION"]=="codex-main-20261020" && ActiveRecord::Base.connection_db_config.configuration_hash[:host]=="qa-db"
path="/qa-private/browser-accounts.json"
raise "FIXTURE_ALREADY_EXISTS" if File.exist?(path)
project=Project.find_by!(identifier:"qldapm-local")
records=[]
ActiveRecord::Base.transaction do
  %w[PM BA BE FE QA].each do |name|
    password="Aa1!"+SecureRandom.urlsafe_base64(25)
    login="codex-main-ui-"+name.downcase
    raise "FIXTURE_LOGIN_EXISTS" if User.exists?(login:login)
    user=User.create!(login:login,firstname:"Codex Qualification",lastname:name,mail:login+"@example.invalid",language:"en",password:password,password_confirmation:password,status:1,admin:false,force_password_change:false)
    role=Role.find_by!(name:"QLDAPM "+name)
    Member.create!(project:project,principal:user,roles:[role])
    device=TwoFactorAuthentication::Device::Totp.create!(user:user,identifier:"Codex isolated fixture",active:true,default:true)
    token=Token::API.create_and_return_value(user)
    records << {id:user.id,login:login,password:password,role:name,token:token,totp_secret:device.otp_secret}
  end
  File.write(path,JSON.generate(project_id:project.id,users:records),mode:"wx",perm:0600)
end
puts JSON.generate(fixture_only:true,accounts:records.map { |r| r.slice(:id,:login,:role) },main_writes:0)

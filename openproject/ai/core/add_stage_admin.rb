require "json"
require "digest"
require "securerandom"

raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
raise "ACCOUNT_ALREADY_EXISTS" if User.exists?(login: "system-admin")
path = "/private/admin-access/system-admin-18091.credentials.txt"
raise "CREDENTIAL_FILE_EXISTS" if File.exist?(path)
fingerprint = ->(scope) { Digest::SHA256.hexdigest(JSON.generate(scope.order(:id).map(&:attributes))) }
before = {users: fingerprint.call(User.all), tokens: fingerprint.call(Token::API.all),
          work_packages: fingerprint.call(WorkPackage.all), roles: fingerprint.call(Role.all),
          memberships: fingerprint.call(Member.all)}
old_ids = User.pluck(:id)
old_members = Member.pluck(:id)
password = "Aa1!" + SecureRandom.urlsafe_base64(28)
User.current = User.find_by!(login: "stage-owner")
result = nil
ActiveRecord::Base.transaction do
  user = User.create!(login: "system-admin", firstname: "QLDAPM", lastname: "System Administrator",
    mail: "system-admin@qldapm.local", status: :active, admin: true,
    password:, password_confirmation: password, force_password_change: true)
  role = ProjectRole.find_by!(name: "QLDAPM PM")
  Project.order(:id).each { |project| Member.create!(project:, principal: user, roles: [role]) }
  raise "OLD_USERS_CHANGED" unless fingerprint.call(User.where(id: old_ids)) == before[:users]
  raise "OLD_MEMBERS_CHANGED" unless fingerprint.call(Member.where(id: old_members)) == before[:memberships]
  raise "TOKENS_CHANGED" unless fingerprint.call(Token::API.all) == before[:tokens]
  raise "TASKS_CHANGED" unless fingerprint.call(WorkPackage.all) == before[:work_packages]
  raise "ROLES_CHANGED" unless fingerprint.call(Role.all) == before[:roles]
  raise "PASSWORD_INVALID" unless user.check_password?(password, update_legacy: false)
  result = {id: user.id, login: user.login, admin: user.admin?, active: user.active?,
    force_password_change: user.force_password_change, projects: user.memberships.pluck(:project_id),
    old_users_tokens_roles_memberships_and_tasks_unchanged: true}
  File.open(path, File::WRONLY | File::CREAT | File::EXCL, 0600) do |file|
    file.write("URL: http://localhost:18091\nLogin: #{user.login}\nTemporary password: #{password}\nScope: System Administrator, all projects on 18091\nChange password and enroll TOTP on first login.\n")
  end
end
puts JSON.generate(result)

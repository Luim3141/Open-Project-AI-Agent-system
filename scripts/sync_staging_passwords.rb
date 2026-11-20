require 'json'
accs = JSON.parse(File.read('/private/accounts.json'))['users']
accs.each do |a|
  u = User.find_by(login: a['login'])
  if u
    u.password = a['password']
    u.force_password_change = false
    u.save!
    puts "#{a['login']}: synced (force_pw=#{u.force_password_change?})"
  end
end

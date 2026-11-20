require 'bcrypt'

raw = File.read('/tmp/h4.txt', encoding: 'UTF-8')
hash = raw.sub(/\A\xef\xbb\xbf/, '').sub(/\A\ufeff/, '').strip
puts "Testing user 4 hash: #{hash[0..10]}..."

passwords = [
  'admin', 'admin123', 'Admin123!', 'Admin@123', 'adminadmin', 'openproject', 'OpenProject123',
  'op-owner', 'owner', 'PUBLICATION_REDACTED', 'root', '12345678', 'qldapm', 'qldapm123', 'QLDAPM123!',
  'Owner@123', 'qldapm-owner', '123456', 'password', 'OpenProject', 'admin1234', 'admin@123',
  'Secret123!', 'Qldapm@2026', 'Welcome123!', 'p4ssw0rd', 'OpenProjectAdmin123!'
]

passwords.each do |p|
  if BCrypt::Password.new(hash) == p
    puts "MATCH FOUND FOR USER 4: #{p}"
    exit 0
  end
end
puts "NO MATCH FOUND"

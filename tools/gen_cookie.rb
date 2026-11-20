user = User.find(18)
sid = Rack::Session::SessionId.new(SecureRandom.hex(16))
session_record = ActiveRecord::SessionStore::Session.new(
  session_id: sid.private_id,
  user_id: user.id,
  data: {'user_id' => user.id, 'updated_at' => Time.now}
)
session_record.save!
puts 'COOKIE_VALUE=' + sid.public_id

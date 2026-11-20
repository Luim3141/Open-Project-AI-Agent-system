require 'securerandom'
require 'base64'

raw_id = SecureRandom.hex(16)
sid = Rack::Session::SessionId.new(raw_id)
private_id = sid.private_id
puts "Raw cookie value: #{raw_id}"
puts "Private ID stored in DB: #{private_id}"

# OpenProject requires updated_at to be a Time object, not an Integer!
data = {
  'user_id' => 18,
  'updated_at' => Time.now,
  '_csrf_token' => SecureRandom.base64(32)
}
marshaled = Base64.encode64(Marshal.dump(data))

ActiveRecord::Base.connection.execute("DELETE FROM sessions WHERE user_id = 18")
ActiveRecord::Base.connection.execute("INSERT INTO sessions (session_id, data, user_id, updated_at) VALUES ('#{private_id}', '#{marshaled}', 18, NOW())")
puts "INSERTED_SESSION_FOR_USER_18_SUCCESS"

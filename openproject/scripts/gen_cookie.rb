user = User.find(18)
sid = SecureRandom.hex(16)

# OpenProject uses ActionDispatch::Session::MemCacheStore or similar with Rack::Session
# In Rails with cache store:
session_data = {
  'user_id' => user.id,
  'updated_at' => Time.now.to_i
}

# Try both rack:session and standard session keys
Rails.cache.write("rack:session:#{sid}", session_data)
Rails.cache.write("session:#{sid}", session_data)
Rails.cache.write(sid, session_data)

puts "COOKIE_VALUE=#{sid}"

puts "Rails cache store: " + Rails.cache.inspect
puts "Session store: " + Rails.application.config.session_store.to_s

# Let's inspect ActionDispatch session store class
store_class = Rails.application.config.session_store
puts "Session store options: " + Rails.application.config.session_options.inspect

# Let's see how session is written
user = User.find(18)
sid = SecureRandom.hex(16)

# Test creating session via Rails store
req = ActionDispatch::TestRequest.create
req.session_options[:id] = sid
req.session[:user_id] = user.id
req.session[:updated_at] = Time.now.to_i

# Commit session to store
session = req.session
# In ActionDispatch::Request::Session, to write to store:
session.send(:load!)
session[:user_id] = user.id
session[:updated_at] = Time.now.to_i

# In Rails 7/8, session is committed by session_store.write_session
# Let's get the store instance
store = store_class.new(nil, Rails.application.config.session_options)
rack_sid = Rack::Session::SessionId.new(sid)
store.write_session(req, rack_sid, {'user_id' => user.id, 'updated_at' => Time.now.to_i}, {})

puts "WROTE_SESSION_ID=#{sid}"

require 'action_dispatch'

user = User.find(18)

# Create a test env and request
env = Rack::MockRequest.env_for('http://127.0.0.1:18088/')
req = ActionDispatch::Request.new(env)

# Create session
session_options = Rails.application.config.session_options
session_store = Rails.application.config.session_store.new(nil, session_options)

# In Rails, ActionDispatch::Session::CookieStore
# We can use Rails.application.message_verifier or cookies
cookie_name = Rails.application.config.session_options[:key] || '_open_project_session'
puts "COOKIE_KEY=#{cookie_name}"

# Sign session data
session_data = {
  'session_id' => Rack::Session::SessionId.new(SecureRandom.hex(16)),
  'user_id' => user.id,
  'updated_at' => Time.now.to_i
}

# In Rails 7+, cookies are encrypted by default
cookies = ActionDispatch::Cookies::CookieJar.build(req, {})
cookies.encrypted[cookie_name] = session_data
cookie_header = cookies[cookie_name]
puts "COOKIE_VALUE=#{cookie_header}"

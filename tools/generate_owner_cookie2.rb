app = Rails.application
env = app.env_config.dup
env['rack.session'] = { 'user_id' => 18, 'session_id' => Rack::Session::SessionId.new(SecureRandom.hex(16)) }

# We call the session store middleware to serialize and set the cookie in header
store = Rails.application.config.session_store.new(
  lambda { |e| [200, {}, ['ok']] },
  Rails.application.config.session_options
)

status, headers, body = store.call(env)
cookie_val = headers['set-cookie'] || headers['Set-Cookie']
puts "FINAL_COOKIE=#{cookie_val}"

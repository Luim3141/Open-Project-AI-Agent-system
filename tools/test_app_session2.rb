app = ActionDispatch::Integration::Session.new(Rails.application)
u = User.find(18)

# Set session
app.get '/login'
# In Rails session, openproject stores user_id
# Let's inspect session keys after a request
puts "SESSION_BEFORE=#{app.session.to_hash.keys}"

# Let's see how OpenProject handles user session:
# OpenProject uses User.current = u, or session[:user_id] = u.id
# Let's see if setting session[:user_id] works:
app.session[:user_id] = u.id
app.get '/projects/6/qldapm_ai/engineering'
puts "STATUS=#{app.response.status}"
puts "SESSION_AFTER=#{app.session.to_hash.keys}"
puts "COOKIE=#{app.cookies['_open_project_session']}"

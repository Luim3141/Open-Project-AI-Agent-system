# Use Rails integration app helper
app = ActionDispatch::Integration::Session.new(Rails.application)
u = User.find(18)
# Post directly to OpenProject internal sign-in or set session
# In OpenProject, AccountController#login handles login
# Or we can see how session is populated
puts "APP_CLASS=#{app.class}"

# Rails integration session lets us do:
# app.cookies['_open_project_session'] ...
# Let's inspect session serializer in Rails.application:
verifier = Rails.application.message_verifier('signed cookie') rescue nil
puts "HAS_VERIFIER=#{verifier.present?}"

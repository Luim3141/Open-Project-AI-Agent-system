raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
raise "STAGING_REDIRECTS_TO_LIVE" unless Setting.host_name == "localhost:18091"

%w[qldapm-ai qldapm-insights qldapm-gates].each do |screen|
  route = Rails.application.routes.recognize_path("/projects/qldapm-local/#{screen}", method: :get)
  expected = screen == "qldapm-gates" ? "qldapm_gates" : "qldapm_ai"
  raise "UI_ROUTE_CHANGED" unless route[:controller] == expected
  request = ActionDispatch::Integration::Session.new(Rails.application)
  request.host! "localhost:18091"
  request.get("/projects/qldapm-local/#{screen}")
  redirect = URI.parse(request.response.location.to_s)
  raise "UI_ANONYMOUS_AUTHORIZATION_FAILED: #{request.response.status}" unless request.response.status == 302 &&
    redirect.host == "localhost" && redirect.port == 18091 && redirect.path == "/login"
end
puts "Native AI Assistant/Insights route resolution PASS with production inflections."

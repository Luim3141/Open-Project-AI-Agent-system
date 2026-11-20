import subprocess

code = '''
app = Rails.application
session = ActionDispatch::Integration::Session.new(app)
session.host! "localhost:8088"
session.https! false

# 1. GET /login to obtain session cookie and authenticity_token
session.get "/login"
puts "GET /login status: #{session.response.status}"
csrf_match = session.response.body.match(/name="authenticity_token" value="([^"]+)"/)
csrf_token = csrf_match ? csrf_match[1] : nil
puts "Login CSRF token: #{csrf_token ? csrf_token.slice(0, 15) + '...' : 'nil'}"

# 2. POST /login with credentials
pm = User.find_by!(login: 'ba-pm')
puts "PM user found: #{pm.login} (id: #{pm.id})"

# Let's see if login works with password
session.post "/login", params: {
  username: "ba-pm",
  password: "PUBLICATION_REDACTED",
  authenticity_token: csrf_token
}
puts "POST /login status: #{session.response.status}"
puts "POST /login location: #{session.response.location}"

if session.response.status == 200 && session.response.body.include?("Invalid user or password")
  puts "Password failed: Invalid user or password"
end
'''

res = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=code.encode(),
    capture_output=True
)
print("STDOUT:")
print(res.stdout.decode())
if res.stderr:
    print("STDERR:")
    print(res.stderr.decode()[:500])

import subprocess

ruby_code = '''
puts "=== 2FA CONTROLLER & FLOW INSPECTION ==="
routes = Rails.application.routes.routes.select { |r| r.path.spec.to_s.include?("two_factor") }
routes.each do |r|
  puts "#{r.verb} #{r.path.spec.to_s} -> #{r.defaults}"
end
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

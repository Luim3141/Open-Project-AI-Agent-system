import subprocess

ruby_code = '''
path = Rails.root.join("modules/gantt/lib/open_project/gantt/engine.rb")
lines = File.readlines(path)
puts lines[15..60].join
'''

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
    input=ruby_code, capture_output=True, text=True, timeout=60
)
print(res.stdout)

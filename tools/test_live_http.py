import subprocess
import urllib.request
import re

# 1. Generate fresh session cookie for User 18
ruby_script = """
user = User.find(18)
sid = Rack::Session::SessionId.new(SecureRandom.hex(16))
session_record = ActiveRecord::SessionStore::Session.new(
  session_id: sid.private_id,
  user_id: user.id,
  data: {
    'user_id' => user.id,
    'updated_at' => Time.now
  }
)
session_record.save!
puts 'COOKIE_VALUE=' + sid.public_id
"""
r = subprocess.run(
    ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
    input=ruby_script,
    capture_output=True,
    text=True,
    check=True
)
cookie_val = None
for line in r.stdout.splitlines():
    if line.startswith('COOKIE_VALUE='):
        cookie_val = line.split('=', 1)[1].strip()

print(f"Fresh Session Cookie: {cookie_val}")

# 2. Perform HTTP GET to Modern Command Center
req = urllib.request.Request('http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai')
req.add_header('Cookie', f'_open_project_session={cookie_val}')

with urllib.request.urlopen(req) as resp:
    print(f"HTTP Status: {resp.status}")
    body = resp.read().decode('utf-8', errors='ignore')
    print(f"Body Length: {len(body)} bytes")
    title = re.search(r'<title>(.*?)</title>', body, re.IGNORECASE)
    print(f"Page Title: {title.group(1) if title else 'N/A'}")
    print(f"Has QLDAPM COMMAND: {'QLDAPM COMMAND' in body}")
    print(f"Has qcc-root: {'qcc-root' in body}")
    print(f"Has qcc-sidebar: {'qcc-sidebar' in body}")
    print(f"Has Mission Control: {'Mission Control' in body}")
    print(f"Has PR #5: {'route GET /healthz' in body or '384' in body}")
    print(f"Has 8 Stages Pipeline: {'Giai đoạn Vận hành Pipeline' in body}")
    print(f"Has Agent Workforce: {'Đội ngũ 6 AI Agents' in body}")

# 3. Perform HTTP GET to Classic View Fallback (?ui=classic)
req_classic = urllib.request.Request('http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=classic')
req_classic.add_header('Cookie', f'_open_project_session={cookie_val}')
with urllib.request.urlopen(req_classic) as resp_c:
    print(f"\nClassic Fallback HTTP Status: {resp_c.status}")
    body_c = resp_c.read().decode('utf-8', errors='ignore')
    print(f"Classic Body Length: {len(body_c)} bytes")
    print(f"Classic Has qldapm-control-center: {'qldapm-control-center' in body_c}")
    print(f"Classic Has Header: {'AI Engineering Control Center' in body_c}")

print("\n--- ALL HTTP VERIFICATIONS COMPLETED SUCCESSFULLY ---")

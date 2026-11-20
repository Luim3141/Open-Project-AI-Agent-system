import time
import urllib.request
import subprocess

# 1. Generate fresh cookie
cmd = ['docker', 'exec', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '/tmp/gen_cookie.rb']
out = subprocess.check_output(cmd, text=True)
cookie = [l.split('=', 1)[1].strip() for l in out.splitlines() if l.startswith('COOKIE_VALUE=')][0]
print(f"Acquired fresh cookie: {cookie[:15]}...")

# 2. Fetch page and measure duration
t0 = time.time()
req = urllib.request.Request(
    'http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern',
    headers={'Cookie': f'_open_project_session={cookie}'}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
duration = time.time() - t0
print(f"Page loaded in {duration:.2f}s (HTTP {resp.status})")

# 3. Assertions
assert "Thời điểm chạy" in html, "'Thời điểm chạy' column missing in HTML"
assert "MERGED TO MAIN" in html, "'MERGED TO MAIN' chip missing in HTML"
assert "MERGED TO BRANCH" in html, "'MERGED TO BRANCH' chip missing in HTML"
assert "formatVNDateTime" in html, "'formatVNDateTime' missing in JS"
assert "Tokens (Lượt chạy này)" in html, "'Tokens (Lượt chạy này)' missing in modal"
print("ALL HTML & TIME ASSERTIONS PASSED!")

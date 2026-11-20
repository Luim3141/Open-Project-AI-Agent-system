import time
import urllib.request
import subprocess

# Acquire fresh cookie
cmd = ['docker', 'exec', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '/tmp/gen_cookie.rb']
out = subprocess.check_output(cmd, text=True)
cookie = [l.split('=', 1)[1].strip() for l in out.splitlines() if l.startswith('COOKIE_VALUE=')][0]

t0 = time.time()
req = urllib.request.Request(
    'http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern',
    headers={'Cookie': f'_open_project_session={cookie}'}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
duration = time.time() - t0
print(f"Second fetch duration: {duration:.2f}s (HTTP {resp.status})")
assert "Thời điểm chạy" in html
print("CACHED LOAD TIME IS EXTREMELY FAST!")

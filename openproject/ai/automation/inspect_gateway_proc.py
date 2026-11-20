import subprocess

inner = """
import os
for pid in os.listdir('/proc'):
    if pid.isdigit():
        try:
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmd = f.read().replace('\\x00', ' ')
            print(f'PID {pid}: {cmd}')
        except Exception:
            pass
"""

res = subprocess.run(["docker", "exec", "qldapm-ai-gateway-1", "python", "-c", inner], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)

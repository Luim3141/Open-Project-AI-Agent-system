import subprocess

code = """
import sqlite3
d = sqlite3.connect('/state/gateway.sqlite')
d.execute("DELETE FROM ai_runs WHERE id='b20a73af-21dd-436b-a656-df5c59f101e8'")
d.execute("DELETE FROM ai_queue WHERE id='b20a73af-21dd-436b-a656-df5c59f101e8'")
d.execute("DELETE FROM requests WHERE key LIKE 'auto-health-check-v1%'")
d.execute("UPDATE engineering_control SET mode='OFF' WHERE project=6")
d.commit()
print("CLEANED UP TEST RUN b20a73af")
"""

cmd = ['docker', 'exec', 'qldapm-ai-gateway-1', 'python', '-c', code]
p = subprocess.run(cmd, capture_output=True, text=True)
print(p.stdout)

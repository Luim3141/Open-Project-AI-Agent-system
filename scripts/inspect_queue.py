import subprocess

script = """
import sqlite3, json
db = sqlite3.connect('/state/gateway.sqlite')
db.row_factory = sqlite3.Row
r = db.execute("SELECT q.id, q.state, q.payload, q.created, r.result FROM ai_queue q LEFT JOIN ai_runs r ON r.id=q.id WHERE q.id='b1cca031-81f5-4df1-870b-cbeb23d51e66'").fetchone()
if r:
    print('Payload:')
    print(r['payload'])
    print('Result:')
    print(r['result'])
"""

out = subprocess.check_output(
    ['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'],
    input=script, text=True
)
print(out)

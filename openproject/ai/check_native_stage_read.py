"""Five existing actor tokens, read-only native smoke after host/protocol changes."""
import json
from jira_sync_backup import command

program = '''import json
from pathlib import Path
from gateway.native import Native
root=Path('/state')
config=json.loads((root/'config.json').read_text())
tokens=json.loads((root/'credentials.json').read_text())
result=[]
for actor,expected in [(7,'PM'),(6,'BA'),(8,'BE'),(9,'FE'),(10,'QA')]:
 native=Native(config['openproject_url'],tokens[str(actor)],3)
 identity=native.identity(actor)
 role=identity['role'].replace('BA-PM','BA')
 assert role==expected
 count=len(native.packages())
 assert count==335
 result.append({'actor':actor,'role':role,'native_identity':True,'visible_work_packages':count})
print(json.dumps({'passed':True,'native_reads':result,'google_called':False,'remote_clients_tested':False}))
'''
print(command(['docker', 'exec', 'qldapm-ai-stage-staging-gateway-1', 'python', '-c', program]).decode().strip())

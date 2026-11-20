"""Resume exactly after container creation; do not repeat stop/rename/create."""
from support import *
import os,re,secrets,urllib.request
assert CONTEXT['stage']=='N8N_OLD_CONTAINER_PRESERVED'
old=json.loads((PRIVATE/'qldapm-n8n-main-inspect.json').read_text())
new=inspect('qldapm-n8n-main');previous=inspect(CONTEXT['n8n_previous_name'])
assert previous['Id']==old['Id'] and previous['State']['Status']=='exited'
assert new['State']['Status']=='created' and new['Image']==PROPOSAL['images']['n8n']
for key in ['Env','Entrypoint','Cmd','User','WorkingDir','Labels','ExposedPorts']:
    assert new['Config'].get(key)==old['Config'].get(key),key
envfile=PRIVATE/'n8n-preserved.env'
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
core_runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject'
stage('N8N_OLD_CONTAINER_PRESERVED','Ruling: empty DNS []/null and OomKillDisable null/false are equivalent defaults; every other HostConfig key must match. No DNS or OOM policy change.')
source=(RUN/'apply_approved.py').read_text()
tail=source[source.index("for key,value in old['HostConfig'].items():"):]
assert tail.count('docker(*create')==0
exec(compile(tail,str(RUN/'apply_approved.py')+' [resume]', 'exec'))

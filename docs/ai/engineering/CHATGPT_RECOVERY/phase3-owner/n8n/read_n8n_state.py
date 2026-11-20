"""Read-only workflow publication/retention inventory, without credentials or execution payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
CODE = r'''
const sqlite=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));
const crypto=require('node:crypto');
const db=new sqlite.Database('/home/node/.n8n/database.sqlite',sqlite.OPEN_READONLY);
const allowedSettings=['executionOrder','timezone','saveDataErrorExecution','saveDataSuccessExecution','saveExecutionProgress','saveManualExecutions','binaryMode','executionTimeout'];
db.all('SELECT w.id,w.name,w.active,w.activeVersionId,w.versionId,w.settings,h.nodes,h.connections FROM workflow_entity w LEFT JOIN workflow_history h ON h.workflowId=w.id AND h.versionId=w.activeVersionId ORDER BY w.name',(error,rows)=>{
 if(error){console.log(JSON.stringify({status:'READ_FAILED'}));process.exitCode=1;return;}
 console.log(JSON.stringify({status:'READ_ONLY_WORKFLOW_METADATA',workflows:rows.map(row=>({id:row.id,name:row.name,active:row.active,
  published_version:row.activeVersionId,draft_version:row.versionId,published_found:!!row.nodes,
  published_graph_sha256:crypto.createHash('sha256').update(JSON.stringify([row.nodes,row.connections])).digest('hex'),
  settings:Object.fromEntries(Object.entries(JSON.parse(row.settings||'{}')).filter(([key])=>allowedSettings.includes(key)))}))}));
 db.close();
});'''

if __name__ == '__main__':
    started = datetime.now(timezone.utc).isoformat()
    command = ['docker', 'exec', '-i', 'qldapm-n8n-main', 'node', '-']
    result = subprocess.run(command, input=CODE, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('READ_ONLY_N8N_PROBE_FAILED')
    report = json.loads(result.stdout)
    report.update(started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(), command=command,
                  route='SQLite OPEN_READONLY', probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  image=subprocess.check_output(['docker', 'inspect', 'qldapm-n8n-main', '--format', '{{.Image}}'], text=True).strip())
    (HERE / 'n8n-readback.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'workflows': len(report['workflows']), 'published': sum(row['published_found'] for row in report['workflows'])}))

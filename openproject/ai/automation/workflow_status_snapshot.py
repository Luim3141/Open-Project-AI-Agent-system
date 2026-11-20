"""Fixed local n8n metadata for the existing host worker health pulse; no execution payloads."""
import json
import os
from pathlib import Path
import subprocess
import time

READ = r"""
const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});
const crypto=require('node:crypto');
const stamp=t=>t==null?null:Date.parse(t.includes('T')?t:t.replace(' ','T')+'Z')/1000;
const execution=r=>r?{id:String(r.id),status:r.status,mode:r.mode,started_at:stamp(r.startedAt||r.createdAt),stopped_at:stamp(r.stoppedAt)}:null;
const rows=d.prepare('SELECT w.id,w.name,w.active,w.activeVersionId,h.nodes,h.connections,w.settings FROM workflow_entity w LEFT JOIN workflow_history h ON h.versionId=w.activeVersionId ORDER BY w.name').all();
const data=rows.map(r=>{
 const nodes=r.nodes?JSON.parse(r.nodes):[];
 const trigger_types=[...new Set(nodes.filter(n=>!n.disabled).map(n=>n.type==='n8n-nodes-base.webhook'?'webhook':n.type==='n8n-nodes-base.scheduleTrigger'?'schedule':null).filter(Boolean))];
 return {code:r.name.slice(0,4),id:r.id,name:r.name,active:!!r.active,published_version_id:r.activeVersionId,
 definition_sha256:crypto.createHash('sha256').update(JSON.stringify([r.nodes,r.connections,r.settings])).digest('hex'),trigger_types,
 last_execution:execution(d.prepare('SELECT id,status,mode,startedAt,stoppedAt,createdAt FROM execution_entity WHERE workflowId=? AND deletedAt IS NULL ORDER BY id DESC LIMIT 1').get(r.id)),
 last_success:execution(d.prepare("SELECT id,status,mode,startedAt,stoppedAt,createdAt FROM execution_entity WHERE workflowId=? AND deletedAt IS NULL AND status='success' ORDER BY id DESC LIMIT 1").get(r.id)),
 last_failure:execution(d.prepare("SELECT id,status,mode,startedAt,stoppedAt,createdAt FROM execution_entity WHERE workflowId=? AND deletedAt IS NULL AND status IN ('error','canceled','crashed') ORDER BY id DESC LIMIT 1").get(r.id))};
});d.close();console.log(JSON.stringify({schema_version:1,checked_at:Date.now()/1000,workflows:data}));
"""


def validate(data):
    if not isinstance(data,dict) or set(data)!={'schema_version','checked_at','workflows'} or data['schema_version']!=1:
        raise ValueError('WORKFLOW_METADATA_INVALID')
    rows=data['workflows']
    if not isinstance(rows,list) or len(rows)!=16 or {r.get('code') for r in rows}!={f'WF{i:02}' for i in range(1,17)}:
        raise ValueError('WORKFLOW_INVENTORY_CHANGED')
    if type(data['checked_at']) not in (float,int) or not 0<=time.time()-data['checked_at']<60:
        raise ValueError('WORKFLOW_OBSERVATION_STALE')
    if len(json.dumps(data).encode())>65536:
        raise ValueError('WORKFLOW_METADATA_TOO_LARGE')
    return data


def persist(root=None):
    result=subprocess.run(['docker','exec','qldapm-n8n-main','node','-e',READ],capture_output=True,timeout=15)
    if result.returncode or len(result.stdout)>65536:
        raise RuntimeError('WORKFLOW_OBSERVATION_UNAVAILABLE')
    data=validate(json.loads(result.stdout))
    root=Path(root or Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway')
    target=root/'n8n-workflow-status.json';temp=target.with_suffix('.tmp')
    temp.write_text(json.dumps(data)+'\n',encoding='utf-8');temp.replace(target)
    return {'workflow_count':len(data['workflows']),'checked_at':data['checked_at']}


if __name__=='__main__':
    print(json.dumps(persist()))

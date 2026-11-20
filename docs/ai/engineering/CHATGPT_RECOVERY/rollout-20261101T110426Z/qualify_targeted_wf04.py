from support import *
assert CONTEXT['stage']=='PREFLIGHT_AND_FRESH_BACKUP_VERIFIED'
code=r'''
const fs=require('fs'),cp=require('child_process'),crypto=require('crypto'),{DatabaseSync}=require('node:sqlite');
fs.copyFileSync('/backup/auxiliary-backup/n8n.sqlite','/home/node/.n8n/database.sqlite');
fs.copyFileSync('/backup/auxiliary-backup/n8n-config','/home/node/.n8n/config');fs.chmodSync('/home/node/.n8n/config',0o600);
const k=JSON.parse(fs.readFileSync('/backup/auxiliary-backup/n8n-key.json'));if(k.env_key)process.env.N8N_ENCRYPTION_KEY=k.env_key;
const target=JSON.parse(fs.readFileSync('/backup/wf04-candidate.json'));const id=target.id;
fs.writeFileSync('/tmp/single-wf04.json',JSON.stringify([target]));
const snapshot=()=>{const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const names=d.prepare("SELECT name FROM sqlite_master WHERE type='table'").all().map(x=>x.name);
 const rows=d.prepare('SELECT * FROM workflow_entity ORDER BY id').all();const hashes={};
 for(const table of ['user','credentials_entity','shared_workflow','shared_credentials','project','project_relation','folder','workflow_tag_mapping'])if(names.includes(table))hashes[table]=crypto.createHash('sha256').update(JSON.stringify(d.prepare('SELECT * FROM "'+table+'" ORDER BY rowid').all())).digest('hex');
 d.close();return {rows,hashes};};
const before=snapshot();
for(const args of [['import:workflow','--input=/tmp/single-wf04.json'],['publish:workflow','--id='+id]])cp.execFileSync('n8n',args,{stdio:'pipe',timeout:120000});
const after=snapshot();
if(JSON.stringify(before.rows.filter(x=>x.id!==id))!==JSON.stringify(after.rows.filter(x=>x.id!==id)))throw Error('UNRELATED_WORKFLOW_CHANGED');
if(JSON.stringify(before.hashes)!==JSON.stringify(after.hashes))throw Error('OWNER_CREDENTIAL_OR_SHARING_CHANGED');
const a=after.rows.find(x=>x.id===id),b=before.rows.find(x=>x.id===id);
const nodes=JSON.parse(a.nodes),old=JSON.parse(b.nodes),settings=JSON.parse(a.settings);
if(nodes.length!==old.length+4||JSON.stringify(nodes.slice(0,old.length))!==JSON.stringify(old))throw Error('OLD_GRAPH_CHANGED');
if(!a.active||!a.activeVersionId||a.activeVersionId===b.activeVersionId)throw Error('TARGET_NOT_PUBLISHED_NEW_VERSION');
console.log(JSON.stringify({status:'TARGETED_IMPORT_PUBLISH_CLONE_VERIFIED',other_workflows_unchanged:true,owner_credentials_sharing_unchanged:true,workflow_count:after.rows.length,active_workflows:after.rows.filter(x=>x.active).length,target_nodes:nodes.length,target_active_version_changed:true,retention:settings}));
'''
result=json.loads(docker('run','--rm','--pull','never','--network','none','--read-only','--tmpfs','/tmp:size=128m,mode=1777','--tmpfs','/home/node/.n8n:size=128m,mode=1777','--mount',f'type=bind,source={PRIVATE},target=/backup,readonly','-e','N8N_DIAGNOSTICS_ENABLED=false','-e','N8N_VERSION_NOTIFICATIONS_ENABLED=false','--entrypoint','node',PROPOSAL['images']['n8n'],'-e',code,timeout=300,name='wf04-clone'))
assert result['workflow_count']==16 and result['active_workflows']==16
write('wf04-targeted-clone.json',result)
stage('TARGETED_WF04_IMPORT_QUALIFIED')

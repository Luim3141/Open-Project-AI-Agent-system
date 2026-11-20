// Only imported into a disposable n8n clone. The private mount contains clone-created credentials.
const fs=require('fs'),root='/qualification',base='http://localhost:5678';let cookie='';
async function call(path,body){fs.writeFileSync(root+'/setup-stage.json',JSON.stringify({path,mutation:!!body,at:new Date().toISOString()}));let r;try{r=await fetch(base+path,{method:body?'POST':'GET',headers:{'content-type':'application/json',connection:'close',cookie},body:body?JSON.stringify(body):undefined});}catch(e){throw Error('CLONE_API_'+path+'_'+(e.cause?.code||e.name));}const d=await r.json();if(!r.ok)throw Error('CLONE_API_'+r.status);const cs=r.headers.getSetCookie();if(cs.length)cookie=cs.map(x=>x.split(';')[0]).join('; ');return d.data;}
(async()=>{
for(let i=0;i<90;i++){try{await call('/rest/settings');break;}catch(e){if(i===89)throw e;await new Promise(r=>setTimeout(r,1000));}}
const owner=JSON.parse(fs.readFileSync(root+'/owner.json'));await call('/rest/owner/setup',owner);await call('/rest/login',{emailOrLdapLoginId:owner.email,password:owner.password});
require('child_process').execFileSync('n8n',['import:credentials','--input='+root+'/credentials.json'],{stdio:'pipe'});
await call('/rest/settings');
const definitions=JSON.parse(fs.readFileSync(root+'/workflows.json')),published=[];
for(const spec of definitions){let saved=await call('/rest/workflows',spec);await call('/rest/workflows/'+saved.id+'/activate',{versionId:saved.versionId,...(saved.checksum?{expectedChecksum:saved.checksum}:{})});saved=await call('/rest/workflows/'+saved.id);if(!saved.active||!saved.activeVersionId)throw Error('NOT_PUBLISHED');published.push({id:saved.id,name:saved.name,version:saved.activeVersionId});}
fs.writeFileSync(root+'/published.json',JSON.stringify(published));console.log('CLONE_PUBLISHED');
})().catch(e=>{console.error(e.message);process.exit(1)});

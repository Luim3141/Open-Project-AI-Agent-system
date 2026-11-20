"""Preview only: Compose config and private n8n/WF04 snapshots. Never apply/import/publish."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,uuid
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.n8n_lifecycle_adapter import attach_lifecycle_adapter
RUN=Path(__file__).parent;DOC=RUN.parent
images=json.loads((RUN/'candidate-images.json').read_text())
previous=json.loads((DOC/'run-20261101T035551Z/compose-preview.json').read_text())
previews=[]
for record in previous:
    kind=record['kind'];service='gateway' if kind=='gateway' else 'web'
    overlay=DOC/('compose.'+kind+'.candidate.json')
    overlay.write_text(json.dumps({'services':{service:{'image':images[kind]['id'],'pull_policy':'never'}}},indent=2)+'\n')
    prefix=record['command_prefix']
    before=json.loads(subprocess.check_output(prefix+['config','--format','json'],stderr=subprocess.PIPE))
    after=json.loads(subprocess.check_output(prefix+['-f',str(overlay),'config','--format','json'],stderr=subprocess.PIPE))
    changes=[]
    for name,item in before['services'].items():
        keys=[k for k in set(item)|set(after['services'][name]) if item.get(k)!=after['services'][name].get(k)]
        if keys:changes.append({'service':name,'changed_keys':sorted(keys)})
    assert len(changes)==1 and changes[0]['service']==service and set(changes[0]['changed_keys'])<={'image','pull_policy'}
    rollback=DOC/('compose.'+kind+'.rollback.json')
    restored=json.loads(subprocess.check_output(prefix+['-f',str(rollback),'config','--format','json'],stderr=subprocess.PIPE))
    assert all({k:v for k,v in before['services'][name].items() if k not in {'image','pull_policy'}}==
               {k:v for k,v in restored['services'][name].items() if k not in {'image','pull_policy'}} for name in before['services'])
    previews.append({'kind':kind,'changes':changes,'candidate_image':images[kind]['id'],'rollback_config_valid':True,
                     'command_prefix':prefix,'candidate_override':str(overlay),'applied':False})
(RUN/'compose-preview.json').write_text(json.dumps(previews,indent=2)+'\n')
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('phase2-rollout-preview-'+uuid.uuid4().hex[:8]);private.mkdir()
inspect=json.loads(subprocess.check_output(['docker','inspect','qldapm-n8n-main']))[0]
raw=json.dumps(inspect,indent=2).encode();(private/'n8n-before-private.json').write_bytes(raw)
query="""const sqlite=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));const db=new sqlite.Database('/home/node/.n8n/database.sqlite',sqlite.OPEN_READONLY);db.all("SELECT w.id,w.name,w.activeVersionId,w.settings,h.nodes,h.connections FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId WHERE w.name LIKE 'WF04:%'",(e,r)=>{if(e)throw e;console.log(JSON.stringify(r));db.close()});"""
rows=json.loads(subprocess.check_output(['docker','exec','qldapm-n8n-main','node','-e',query]));assert len(rows)==1
old=rows[0]
for key in ['nodes','connections','settings']:
    if isinstance(old[key],str):old[key]=json.loads(old[key])
config=json.loads((Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/config.json').read_text())
url='http://host.docker.internal:18089'
hosts=config.get('hosts',[])
callback_host='localhost:18089';assert callback_host in hosts
new=attach_lifecycle_adapter(old,url,gateway_host=callback_host)
assert new['nodes'][:len(old['nodes'])]==old['nodes']
assert all(new['connections'][k]==v for k,v in old['connections'].items())
(private/'wf04-before.json').write_text(json.dumps(old,indent=2))
(private/'wf04-candidate.json').write_text(json.dumps(new,indent=2))
summary={'private_preview':str(private),'n8n_before_sha256':hashlib.sha256(raw).hexdigest(),
 'n8n_old_image':inspect['Image'],'n8n_candidate_image':images['n8n']['id'],
 'n8n_change':'image only; keep Env/HostConfig/Mounts/networks/ports/owner/encryption credential configuration',
 'workflow_id':old['id'],'expected_active_version':old['activeVersionId'],'old_nodes':len(old['nodes']),'added_nodes':4,
 'existing_graph_preserved':True,'gateway_callback_host':callback_host,'gateway_callback_host_allowed':callback_host in hosts,
 'gateway_lifecycle_config':'disabled now; generate private 64hex signing key only on approved activation',
 'history_purge':False,'credential_rotation':False,'main_mutations':0}
(RUN/'n8n-rollout-preview.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'compose_preview':'PASS','n8n_preview':summary},indent=2))

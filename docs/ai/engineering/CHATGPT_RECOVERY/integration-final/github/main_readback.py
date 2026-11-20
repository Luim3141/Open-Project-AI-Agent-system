"""Read-only actual owner-authorized GitHub/Native projection; no sync action."""
import datetime,json,subprocess
from pathlib import Path

OUT=Path(__file__).parent
code=r'''
import json,sqlite3,time
from pathlib import Path
from types import SimpleNamespace
from gateway.native import Native
from gateway.engineering_github_sync import fetch_pull_requests,get_pr_wp_map
from gateway.engineering_github_details import deployment_projection
root=Path('/state');config=json.loads((root/'config.json').read_text());credential=json.loads((root/'credentials.json').read_text())['18']
native=Native(config['openproject_url'],credential,6);identity=native.identity(18);project=native.call('/api/v3/projects/6')
assert identity['user_id']==18 and identity['role']=='AI_SYSTEM_OWNER' and project['identifier']=='ai-dev-demo' and project['active']
class ReadOnlyStore:
    def __init__(self):self.root=root
    def connect(self):
        db=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;return db
service=SimpleNamespace(store=ReadOnlyStore());db=service.store.connect()
poll=db.execute('SELECT project,next_at,lease_until,error FROM engineering_github_poll WHERE project=6').fetchone()
meta=db.execute('SELECT last_synced_at,total_checked,total_changed,status,error_message,correlation_id FROM engineering_github_sync_meta WHERE id=1').fetchone()
activation=1793709936
rows=[dict(r) for r in db.execute("SELECT operation_key,wp_id,state,updated FROM engineering_github_sync_journal WHERE updated>=? ORDER BY wp_id,updated",(activation,))]
allstates=[dict(r) for r in db.execute('SELECT state,count(*) n FROM engineering_github_sync_journal GROUP BY state')]
assert poll and meta
activities=[]
for wp in sorted({r['wp_id'] for r in rows}):
    package=native.package(wp);assert package['_links']['project']['href']=='/api/v3/projects/6' and package['_links']['parent']['href']=='/api/v3/work_packages/379'
    found=native.collection('/api/v3/work_packages/'+str(wp)+'/activities')
    for row in (r for r in rows if r['wp_id']==wp):
        marker='[qldapm-github-sync:'+row['operation_key']+']'
        ids=[item['id'] for item in found if marker in str((item.get('comment') or {}).get('raw',''))]
        activities.append({'work_package_id':wp,'journal_state':row['state'],'marker_count':len(ids),'activity_ids':ids})
prs=fetch_pull_requests('Luim3141/mini-task-manager',include_details=True)
mapping=get_pr_wp_map(service)
release,projection=deployment_projection(service,[dict(pr,wp_id=mapping.get(pr['number'])) for pr in prs])
print(json.dumps({'utc':time.time(),'owner_identity':{'user_id':identity['user_id'],'role':identity['role'],'project_id':6},
 'poll':dict(poll),'sync_meta':dict(meta),'journal_states':allstates,'latest_operations':activities,
 'release':release,'prs':[{'number':p['number'],'state':p['state'],'head_sha':p['head_sha'],'wp_id':p['wp_id'],
 'merge_target':p['merge_target'],'reviews_state':p['reviews_state'],'checks_state':p['checks_state'],
 'details_error':p.get('details_error'),'deployment_state':p.get('deployment_state')} for p in projection]}))
'''
result=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=120)
if result.returncode:raise RuntimeError('READ_ONLY_OWNER_PROJECTION_FAILED')
data=json.loads(result.stdout);data['observed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
data['scope']='Read-only SQLite/Native/GitHub/HTTP release, Owner18 identity verified; no manual sync, no application writes.'
name='main-github-readback-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json'
(OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'file':name,'sync_status':data['sync_meta']['status'],'checked':data['sync_meta']['total_checked'],
                  'changed':data['sync_meta']['total_changed'],'operations':len(data['latest_operations']),
                  'duplicate_markers':sum(a['marker_count']!=1 for a in data['latest_operations']),
                  'release_state':data['release']['state'],'prs':len(data['prs'])}))

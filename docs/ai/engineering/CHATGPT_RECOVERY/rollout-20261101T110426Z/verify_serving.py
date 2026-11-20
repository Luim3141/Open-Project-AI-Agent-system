from support import *
import re,urllib.request,urllib.error,uuid
assert CONTEXT['stage']=='MAIN_IMAGES_APPLIED_WORKER_HELD_FOR_VERIFICATION'
checks={}
for kind,name in [('gateway','qldapm-ai-gateway-1'),('core','qldapm-openproject-web-1'),('n8n','qldapm-n8n-main')]:
    row=inspect(name);assert row['Image']==PROPOSAL['images'][kind]
    checks[kind]={'image':row['Image'],'id':row['Id'],'health':row['State'].get('Health',{}).get('Status','not_configured')}
for record in json.loads((PHASE/'candidate-final-parity.json').read_text()):
    local=record['file']
    if local.startswith('gateway/'):name='qldapm-ai-gateway-1';path='/app/'+local
    elif local.startswith('core/overlay/'):name='qldapm-openproject-web-1';path='/app/'+local.removeprefix('core/overlay/')
    else:name='qldapm-n8n-main';path='/opt/qldapm/n8n_storage_redaction.js'
    assert hashlib.sha256(docker('exec',name,'cat',path)).hexdigest()==record['sha256'],local
checks['source_parity_files']=15
before=json.loads((PRIVATE/'all-containers-before.json').read_text())
allowed={'qldapm-ai-gateway-1','qldapm-openproject-web-1','qldapm-n8n-main'}
unchanged=[]
for row in before:
    name=row['Name'].lstrip('/')
    if name in allowed:continue
    current=inspect(name)
    assert (current['Id'],current['Image'],current['State']['StartedAt'])==(row['Id'],row['Image'],row['State']['StartedAt']),name
    unchanged.append(name)
checks['unrelated_containers_unchanged']=unchanged
assert sql("SELECT project_id,count(*),max(lock_version),max(updated_at) FROM work_packages WHERE project_id IN(5,6) GROUP BY project_id ORDER BY project_id; SELECT id,status_id,lock_version FROM work_packages WHERE id IN(379,386) ORDER BY id; SELECT count(*) FROM work_packages WHERE id=385")==json.loads((RUN/'preflight.json').read_text())['sql_baseline']
# pg_restore without -d only emits SQL; comparison never executes restored statements.
def copy_table(data,table):
    pattern=rb'COPY public\.'+re.escape(table.encode())+rb' \(([^\n]+)\) FROM stdin;\n(.*?)\n\\\.\n'
    match=re.search(pattern,data,re.S);assert match,table
    columns=[s.strip().strip('"') for s in match[1].decode().split(',')]
    rows=[line.split('\t') for line in match[2].decode().splitlines()] if match[2] else []
    return columns,rows
security={}
toc=docker('exec','-i','qldapm-openproject-db-1','pg_restore','--list',data=(PRIVATE/'native-backup/postgres.dump').read_bytes())
tables=['work_packages','relations','users','members','member_roles','roles','tokens']
tables += re.findall(r'TABLE DATA public ([^ ]*two_factor[^ ]*) ',toc.decode())
for table in tables:
    if ('TABLE DATA public '+table+' ') not in toc.decode():continue
    original=docker('exec','-i','qldapm-openproject-db-1','pg_restore','--data-only','--file=-','--table='+table,data=(PRIVATE/'native-backup/postgres.dump').read_bytes())
    current=docker('exec','qldapm-openproject-db-1','pg_dump','-U','postgres','--data-only','--table=public.'+table,'openproject')
    columns,oldrows=copy_table(original,table);newcolumns,newrows=copy_table(current,table);assert columns==newcolumns
    volatile={'updated_at','updated_on','last_login_on','last_active_on','last_active_at','last_used_at'} if table in {'users','tokens'} else set()
    indexes=[i for i,k in enumerate(columns) if k not in volatile]
    canonical=lambda rows:json.dumps(sorted([[r[i] for i in indexes] for r in rows]),separators=(',',':')).encode()
    assert canonical(oldrows)==canonical(newrows),'NATIVE_TABLE_CHANGED_'+table
    security[table]={'rows':len(oldrows),'preserved_columns':[columns[i] for i in indexes],
                     'sha256':hashlib.sha256(canonical(oldrows)).hexdigest()}
checks['native_business_security_preserved']=security
assert queue()=={'mode':'OFF','active':0,'provider_receipts':358}
code="""import json,hashlib,sqlite3
from automation.main_operations import work_state
"""
# Compare durable Native pending/unknown receipt fingerprint through the established host helper.
from automation.main_operations import work_state
work=work_state();oldwork=json.loads((PRIVATE/'main-manifest-before.json').read_text())
assert work['active']==0 and work['unknown_sha256']==oldwork['unknown_sha256']
checks['unknown_native_receipts_preserved']=True
rows=n8n_read('SELECT id,name,active,activeVersionId,versionId,nodes,connections,settings FROM workflow_entity ORDER BY id')
oldrows=json.loads((PRIVATE/'workflow-rows-before.json').read_text());target=PROPOSAL['workflow']['id']
assert [r for r in rows if r['id']!=target]==[r for r in oldrows if r['id']!=target]
wf=next(r for r in rows if r['id']==target);original=next(r for r in oldrows if r['id']==target)
assert wf['active']==1 and wf['activeVersionId']!=original['activeVersionId']
assert len(json.loads(wf['nodes']))==8 and json.loads(wf['nodes'])[:4]==json.loads(original['nodes'])
assert len(rows)==16 and sum(r['active'] for r in rows)==16
checks['n8n']={**checks['n8n'],'workflow_count':16,'active_workflows':16,'unchanged_other_workflows':15,'wf04_version':wf['activeVersionId'],'wf04_nodes':8}
def http(url,body=None,headers=None):
    try:
        req=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
        with urllib.request.urlopen(req,timeout=10) as r:return r.status
    except urllib.error.HTTPError as e:return e.code
checks['http']={name:http(url) for name,url in [('gateway','http://127.0.0.1:18089/health'),('n8n','http://127.0.0.1:5679/healthz/readiness'),('demo_health','http://127.0.0.1:18791/healthz'),('demo_summary','http://127.0.0.1:18791/tasks/summary')]}
assert checks['http']=={'gateway':200,'n8n':200,'demo_health':404,'demo_summary':405}
assert http('http://127.0.0.1:18089/internal/automation/lifecycle-observation',{'invalid':True})==403
checks['invalid_lifecycle_signature_http']=403
write('serving-verification.json',checks)
stage('SERVING_IMAGES_DATA_AND_SECURITY_VERIFIED')

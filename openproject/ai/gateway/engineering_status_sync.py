"""Native workflow reconciliation; one journaled edge, never an engineering scheduler."""
import json
import copy
import time
from collections import deque
from datetime import datetime

from .native import Native, NativeError
from .store import canonical, digest

OWNER_GRANT='3e6ec9ea98c1fe7d2e39f0cee5ca8b526dccdcc374cc1b0f5c494a87356fc457'


def setup(db):
    db.execute('CREATE TABLE IF NOT EXISTS engineering_status_sources(native_id INTEGER PRIMARY KEY,sequence INTEGER NOT NULL,document TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS engineering_status_moves(id INTEGER PRIMARY KEY AUTOINCREMENT,native_id INTEGER NOT NULL,run_id TEXT NOT NULL,sequence INTEGER NOT NULL,before_version INTEGER NOT NULL,after_version INTEGER,from_status INTEGER NOT NULL,target INTEGER NOT NULL,fingerprint TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL,document TEXT NOT NULL,UNIQUE(native_id,before_version))')


def fingerprint(item):
    # Permission-dependent links differ between the worker and the reconciliation principal.
    fields={k:v for k,v in item.items() if k in {'subject','description','startDate','dueDate','estimatedTime','percentageDone'} or k.startswith('customField')}
    fields['_links']={k:{'href':v.get('href')} for k,v in item.get('_links',{}).items()
                      if k in {'project','type','parent','assignee','responsible','priority','version','category'}}
    if isinstance(fields.get('description'),dict):fields['description']={'raw':fields['description'].get('raw','')}
    return digest(canonical(fields))


def owned_source_matches(store,run_id,version,item):
    with store.connect() as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_status_moves'").fetchone():return False
        rows=db.execute("SELECT * FROM engineering_status_moves WHERE run_id=? AND native_id=? AND before_version>=? ORDER BY before_version",(run_id,item['id'],version)).fetchall()
    current=version;proof=fingerprint(item)
    for row in rows:
        if row['before_version']!=current or row['state']!='VERIFIED' or row['fingerprint']!=proof:return False
        current=row['after_version']
        if current==item['lockVersion']:
            return item['_links']['status']['href']==f"/api/v3/statuses/{row['target']}"
    return False


def _context(service,source):
    policy=service.config.get('engineering',{}).get('status_sync',{})
    if service.config.get('project_id')!=6 or source.get('project_id')!=6:raise PermissionError('STATUS_SYNC_PROJECT_DENIED')
    if policy.get('enabled') is not True or policy.get('owner_grant')!=OWNER_GRANT or policy.get('project_id')!=6 or policy.get('principal_id')!=25:
        raise PermissionError('STATUS_SYNC_NOT_AUTHORIZED')
    actor=policy['principal_id'];token=service.store.credential(actor)
    native=getattr(service,'native_factory',Native)(service.config['openproject_url'],token,6)
    who=native.identity(actor)
    if who.get('user_id')!=actor or who.get('project_id')!=6 or who.get('role') not in {'PM','AI_SYSTEM_OWNER'}:raise PermissionError('STATUS_SYNC_PRINCIPAL_DENIED')
    item=native.package(source['native_id'])
    if (item['_links']['project']['href']!='/api/v3/projects/6' or
            item['_links']['type']['href']!=f"/api/v3/types/{policy['type_id']}"):raise PermissionError('STATUS_SYNC_RESOURCE_DENIED')
    return policy,native,item


def _target(policy,source):
    stage=source.get('stage','');result=source.get('result') or {}
    if source.get('engineering_state')=='succeeded':
        review=result.get('review_evidence') or {};qa=review.get('qa') or {};tests=result.get('test_evidence') or {}
        if not (result.get('head_sha') and result.get('pr_url') and tests.get('exit_code')==0 and
                review.get('verdict')=='PASS' and not review.get('findings') and qa.get('status')=='PASS' and qa.get('exit_code')==0):
            raise ValueError('VERIFIED_DEV_REVIEW_QA_REQUIRED')
        key='release'
    else:
        key={'PLANNING':'analysis','READY':'ready','DEVELOPING':'development','REWORK':'development',
             'REVIEWING':'review','TESTING':'testing'}.get(stage)
        if not key:raise ValueError('NO_SUPPORTED_NATIVE_PROGRESS_TRANSITION')
    state=policy['states'][key]
    if state.get('is_closed'):raise ValueError('AUTOMATIC_CLOSED_STATUS_FORBIDDEN')
    return state['id']


def _path(policy,current,target):
    allowed={v['id'] for v in policy['states'].values() if v.get('is_closed') is False}
    if current not in allowed or target not in allowed:raise ValueError('NATIVE_STATUS_OUTSIDE_APPROVED_MAPPING')
    queue=deque([(current,[])]);seen={current}
    while queue:
        node,path=queue.popleft()
        if node==target:return path
        for a,b in policy['edges']:
            if a==node and b in allowed and b not in seen:seen.add(b);queue.append((b,path+[b]))
    raise ValueError('NO_VALID_WORKFLOW_PATH')


def _view(source,state,reason,**details):
    return {'native_id':source['native_id'],'run_id':source['run_id'],'source_event_id':source['event_id'],
            'source_sequence':source['sequence'],'engineering_state':source.get('engineering_state'),
            'delivery_state':source.get('delivery_state','NOT_OBSERVED'),'state':state,'reason':reason,**details}


def preview(service,source):
    policy,native,item=_context(service,source)
    try:
        target=_target(policy,source);path=_path(policy,int(item['_links']['status']['href'].rsplit('/',1)[1]),target)
        if item['lockVersion']!=source['expected_native_version']:raise ValueError('HUMAN_OR_SOURCE_CHANGED')
        return _view(source,'DRY_RUN','VALID_WORKFLOW_PATH',path=path,target_status_id=target,native_version=item['lockVersion'])
    except ValueError as error:return _view(source,'STATUS_SYNC_BLOCKED',str(error))


def _timestamp(value):
    return float(value) if isinstance(value,(int,float)) else datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()


def _own_activity(native,source,move,principal):
    activities=native.call(f"/api/v3/work_packages/{source['native_id']}/activities").get('_embedded',{}).get('elements',[])
    changes=[a for a in activities if any('Status' in d.get('raw','') for d in a.get('details',[]))]
    recent=[a for a in changes if _timestamp(a['createdAt'])>=move['created']-1]
    return len(recent)==1 and recent[0].get('_links',{}).get('user',{}).get('href')==f'/api/v3/users/{principal}'


def reconcile(service,source):
    policy,native,item=_context(service,source);identifier=source['native_id'];now=time.time()
    try:target=_target(policy,source)
    except ValueError as error:return _view(source,'STATUS_SYNC_BLOCKED',str(error))
    current=int(item['_links']['status']['href'].rsplit('/',1)[1]);proof=fingerprint(item)
    with service.store.connect() as db:
        setup(db);db.execute('BEGIN IMMEDIATE')
        previous=db.execute('SELECT * FROM engineering_status_sources WHERE native_id=?',(identifier,)).fetchone()
        if previous and source['sequence']<previous['sequence']:return _view(source,'IGNORED','SOURCE_EVENT_SUPERSEDED')
        move=db.execute('SELECT * FROM engineering_status_moves WHERE native_id=? ORDER BY id DESC LIMIT 1',(identifier,)).fetchone()
        expected=move['after_version'] if move and move['state']=='VERIFIED' else source['expected_native_version']
        if move and move['state'] in {'CLAIMED','OUTCOME_UNKNOWN'}:
            if move['state']=='CLAIMED' and now-move['created']<120:return _view(source,'SYNCING','NATIVE_WRITE_IN_PROGRESS')
            unknown=dict(move)
        else:unknown=None
        published=_published_source(service.store,source,item) if move and item['lockVersion']!=expected else False
        if not unknown and not published and (item['lockVersion']!=expected or (move and (proof!=move['fingerprint'] or current!=move['target']))):
            return _view(source,'STATUS_SYNC_BLOCKED','HUMAN_OR_SOURCE_CHANGED')
        if not unknown:
            try:path=_path(policy,current,target)
            except ValueError as error:return _view(source,'STATUS_SYNC_BLOCKED',str(error))
            db.execute('INSERT INTO engineering_status_sources VALUES(?,?,?) ON CONFLICT(native_id) DO UPDATE SET sequence=excluded.sequence,document=excluded.document',
                       (identifier,source['sequence'],canonical(source)))
            if not path:return _view(source,'STATUS_SYNC_VERIFIED','NATIVE_READBACK_VERIFIED',target_status_id=target,native_status_id=current,native_version=item['lockVersion'])
            next_status=path[0]
            payload={'lockVersion':item['lockVersion'],'_links':{'status':{'href':f'/api/v3/statuses/{next_status}'}}}
            # A known rejection remains blocked; only a newer source or explicit operator review may retry.
            if move and move['state']=='REJECTED':return _view(source,'STATUS_SYNC_BLOCKED',json.loads(move['document']).get('error','NATIVE_REJECTED'))
            cursor=db.execute('INSERT INTO engineering_status_moves(native_id,run_id,sequence,before_version,from_status,target,fingerprint,state,created,updated,document) VALUES(?,?,?,?,?,?,?,\'CLAIMED\',?,?,?)',
                (identifier,source['run_id'],source['sequence'],item['lockVersion'],current,next_status,proof,now,now,canonical({'source':source,'payload':payload})))
            move_id=cursor.lastrowid
    if unknown:
        matches=item['lockVersion']==unknown['before_version']+1 and current==unknown['target'] and proof==unknown['fingerprint']
        if matches and _own_activity(native,source,unknown,policy['principal_id']):
            with service.store.connect() as db:db.execute("UPDATE engineering_status_moves SET state='VERIFIED',after_version=?,updated=? WHERE id=?",(item['lockVersion'],now,unknown['id']))
            return _view(source,'SYNCING','OWN_WRITE_RECONCILED',native_version=item['lockVersion'])
        return _view(source,'OUTCOME_UNKNOWN','NATIVE_WRITE_RECONCILIATION_REQUIRED')
    try:
        form=native.call(f'/api/v3/work_packages/{identifier}/form','POST',payload);embedded=form.get('_embedded',{})
        values=embedded.get('schema',{}).get('status',{}).get('_embedded',{}).get('allowedValues',[])
        if embedded.get('validationErrors') or not any(v.get('id')==next_status or v.get('href')==f'/api/v3/statuses/{next_status}' for v in values):raise NativeError(422,'STATUS_SYNC_FORM_REJECTED')
    except Exception as error:
        with service.store.connect() as db:db.execute("UPDATE engineering_status_moves SET state='REJECTED',updated=?,document=? WHERE id=?",(time.time(),canonical({'source':source,'payload':payload,'error':str(error)}),move_id))
        return _view(source,'STATUS_SYNC_BLOCKED',str(error))
    try:
        native.call(f'/api/v3/work_packages/{identifier}','PATCH',payload)
        after=native.package(identifier)
        if after['lockVersion']!=item['lockVersion']+1 or after['_links']['status']['href']!=payload['_links']['status']['href'] or fingerprint(after)!=proof:
            raise ValueError('NATIVE_READBACK_MISMATCH')
    except Exception as error:
        rejected=isinstance(error,NativeError) and error.status in {400,401,403,404,409,422}
        state='REJECTED' if rejected else 'OUTCOME_UNKNOWN'
        with service.store.connect() as db:db.execute('UPDATE engineering_status_moves SET state=?,updated=?,document=? WHERE id=?',(state,time.time(),canonical({'source':source,'payload':payload,'error':str(error)}),move_id))
        return _view(source,'STATUS_SYNC_BLOCKED' if rejected else state,str(error))
    with service.store.connect() as db:db.execute("UPDATE engineering_status_moves SET state='VERIFIED',after_version=?,updated=? WHERE id=?",(after['lockVersion'],time.time(),move_id))
    return _view(source,'SYNCING','NATIVE_STEP_VERIFIED',native_status_id=next_status,native_version=after['lockVersion'],target_status_id=target)


def _published_source(store,source,item):
    if source.get('engineering_state')!='succeeded' or source.get('expected_native_version')!=item['lockVersion']:return False
    key='engineering-'+source['run_id']+'-child'
    with store.connect() as db:
        rows=db.execute("SELECT payload,result FROM requests WHERE actor=20 AND state='done' AND (key=? OR key GLOB ?)",(key,key+'-retry-*')).fetchall()
    for row in rows:
        request=json.loads(row['payload']);published=json.loads(row['result'])
        if (request.get('project_id')==6 and request.get('method')=='PATCH' and request.get('path')==f"/api/v3/work_packages/{item['id']}"
                and published.get('id')==item['id'] and published.get('lockVersion')==item['lockVersion']
                and published.get('_links',{}).get('status',{}).get('href')==item['_links']['status']['href']
                and fingerprint(published)==fingerprint(item)):return True
    return False


def sources(service):
    """Only persisted, worker-owned Project6 contracts enter reconciliation."""
    with service.store.connect() as db:
        rows=db.execute("SELECT q.id,q.created,q.payload,r.result,(SELECT COALESCE(MAX(sequence),0) FROM execution_events e WHERE e.run_id=q.id) AS seq FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.actor=20 AND json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw' ORDER BY q.created DESC").fetchall()
    seen=set();out=[]
    from .engineering_github_sync import read_projection
    github=read_projection(service)
    for row in rows:
        contract=json.loads(row['payload']);result=json.loads(row['result'] or '{}');identifier=contract.get('native_id')
        if identifier in seen or identifier in {None,379,385} or contract.get('kind')=='planning':continue
        seen.add(identifier)
        if result.get('status')=='succeeded':
            readback=result.get('native_readback') or {}
            if readback.get('child_id')!=identifier or readback.get('project_id')!=6:continue
            expected=readback.get('child_version')
            stage='COMPLETE'
        elif result.get('status')=='running':expected=contract.get('source_version');stage=result.get('stage')
        else:continue
        if type(expected) is not int:continue
        delivery='PR_RECORDED_NOT_OBSERVED' if result.get('pr_url') else 'NOT_OBSERVED'
        for pr in github.get('prs',[]):
            if pr.get('head_sha')==result.get('head_sha') and pr.get('html_url')==result.get('pr_url'):
                if pr.get('is_merged') is True or pr.get('state')=='MERGED':delivery='MERGED_PENDING_DEPLOYMENT'
                elif str(pr.get('state','')).lower()=='open':delivery='PR_OPEN'
                else:delivery='PR_CLOSED_NOT_MERGED'
                if pr.get('deployment_state')=='DEPLOYED_TO_DEMO' and github.get('release',{}).get('state')=='DEPLOYED_TO_DEMO':delivery='DEPLOYED_PENDING_ACCEPTANCE'
                break
        sequence=int(row['created']*1000000)+row['seq']
        out.append({'event_id':digest(row['id']+canonical(result)+delivery),'run_id':row['id'],'native_id':identifier,'project_id':6,
                    'sequence':sequence,'event_at':row['created'],'stage':stage,'engineering_state':result.get('status'),
                    'expected_native_version':expected,'delivery_state':delivery,'result':result})
    return out


def tick(service):
    if time.monotonic()<getattr(service,'_status_sync_next_at',0):return
    service._status_sync_next_at=time.monotonic()+10
    runtime=service.store.root/'config.json'
    if runtime.is_file():
        current=json.loads(runtime.read_text())
        service=copy.copy(service);service.config=copy.deepcopy(service.config)
        service.config['maintenance']=current.get('maintenance',False)
        service.config.setdefault('engineering',{})['status_sync']=current.get('engineering',{}).get('status_sync',{})
    if service.config.get('maintenance') or service.config.get('engineering',{}).get('status_sync',{}).get('enabled') is not True:return
    if service.config.get('project_id')!=6:
        from .engineering import scoped_service
        service=scoped_service(service,6)
    with service.store.connect() as db:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_status_results'").fetchone()
        if not exists:
            db.execute('CREATE TABLE IF NOT EXISTS engineering_status_results(native_id INTEGER PRIMARY KEY,updated REAL NOT NULL,document TEXT NOT NULL)')
        observed={r['native_id']:dict(r) for r in db.execute('SELECT * FROM engineering_status_results')}
    for source in sources(service):
        old=observed.get(source['native_id'])
        if old:
            previous=json.loads(old['document'])
            same=previous.get('source_event_id')==source['event_id']
            if same and (previous['state'] in {'STATUS_SYNC_VERIFIED','STATUS_SYNC_BLOCKED'} or time.time()-old['updated']<10):continue
        try:result=reconcile(service,source)
        except (NativeError,PermissionError,ValueError) as error:
            result=_view(source,'STATUS_SYNC_BLOCKED','NATIVE_HTTP_'+str(error.status) if isinstance(error,NativeError) else str(error)[:160])
        with service.store.connect() as db:
            db.execute('INSERT INTO engineering_status_results VALUES(?,?,?) ON CONFLICT(native_id) DO UPDATE SET updated=excluded.updated,document=excluded.document',(source['native_id'],time.time(),canonical(result)))


def snapshot(service):
    with service.store.connect() as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_status_results'").fetchone():return []
        return [{**json.loads(r['document']),'checked_at':r['updated']} for r in db.execute('SELECT * FROM engineering_status_results ORDER BY native_id')]

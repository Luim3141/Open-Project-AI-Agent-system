"""Durable GitHub sync admission, executed by the existing reconciliation worker."""
import json,time,uuid
from .store import canonical


def setup(db):
    db.execute('CREATE TABLE IF NOT EXISTS engineering_github_operations(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,request_id TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL,result TEXT,UNIQUE(actor,request_id))')


def _view(row):
    return {'operation_id':row['id'],'request_id':row['request_id'],'state':row['state'],
            'created_at':row['created'],'updated_at':row['updated'],'result':json.loads(row['result']) if row['result'] else None}


def enqueue(service,actor,request_id,*,authority=None):
    if service.config.get('project_id')!=6:raise PermissionError('ENGINEERING_PROJECT_REQUIRED')
    from .engineering import authorized
    if authority is None:authorized(service,actor)
    elif authority[1].get('user_id')!=actor or authority[1].get('project_id')!=6 or authority[1].get('role') not in {'PM','AI_SYSTEM_OWNER'}:
        raise PermissionError('ENGINEERING_SYNC_AUTHORITY_MISMATCH')
    if not isinstance(request_id,str) or not 1<=len(request_id)<=120:raise ValueError('REQUEST_ID_REQUIRED')
    with service.store.connect() as db:
        setup(db);db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT * FROM engineering_github_operations WHERE actor=? AND request_id=?',(actor,request_id)).fetchone()
        if not row:row=db.execute("SELECT * FROM engineering_github_operations WHERE actor=? AND state IN ('QUEUED','RUNNING','OUTCOME_UNKNOWN') ORDER BY created LIMIT 1",(actor,)).fetchone()
        if not row:
            identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f'qldapm:github-sync:6:{actor}:{request_id}'));now=time.time()
            db.execute("INSERT INTO engineering_github_operations VALUES(?,?,?,'QUEUED',?,?,NULL)",(identifier,actor,request_id,now,now))
            row=db.execute('SELECT * FROM engineering_github_operations WHERE id=?',(identifier,)).fetchone()
    return {'operation_id':row['id'],'operation_state':row['state'],'status':row['state'],
            'message':'Đã nhận GitHub Sync; theo dõi operation để xác nhận kết quả, không cần F5.' if row['state']!='OUTCOME_UNKNOWN' else 'Kết quả sync trước chưa rõ; cần đối chiếu, không gửi lại.',
            'requires_reconciliation':row['state']=='OUTCOME_UNKNOWN'}


def snapshot(service,actor):
    with service.store.connect() as db:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_github_operations'").fetchone()
        if not exists:return []
        return [_view(r) for r in db.execute('SELECT * FROM engineering_github_operations WHERE actor=? OR ?=18 ORDER BY created DESC LIMIT 10',(actor,actor))]


def process_pending(service):
    if service.config.get('project_id')!=6:
        from .engineering import scoped_service
        service=scoped_service(service,6)
    with service.store.connect() as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_github_operations'").fetchone():return None
        if not db.execute("SELECT 1 FROM engineering_github_operations WHERE state IN ('QUEUED','RUNNING') LIMIT 1").fetchone():return None
        db.execute('BEGIN IMMEDIATE');now=time.time()
        db.execute("UPDATE engineering_github_operations SET state='OUTCOME_UNKNOWN',updated=? WHERE state='RUNNING' AND updated<?",(now,now-180))
        if db.execute("SELECT 1 FROM engineering_github_operations WHERE state='RUNNING'").fetchone():return None
        row=db.execute("SELECT * FROM engineering_github_operations WHERE state='QUEUED' ORDER BY created LIMIT 1").fetchone()
        if not row:return None
        db.execute("UPDATE engineering_github_operations SET state='RUNNING',updated=? WHERE id=?",(now,row['id']))
    try:
        from .engineering import authorized
        from .engineering_github_sync import reconcile_github_with_openproject
        native,_=authorized(service,row['actor'])
        result=reconcile_github_with_openproject(service,native,actor=row['actor'],request_id=row['request_id'])
        unknown=any(item.get('status')=='UNKNOWN' for item in result.get('items',[]))
        state='OUTCOME_UNKNOWN' if unknown else 'COMPLETED' if result.get('status')=='SUCCESS' else 'FAILED'
    except Exception as error:
        from .engineering_github_sync import _error_code
        result={'status':'SYNC_FAILED','error':_error_code(error)};state='FAILED'
    with service.store.connect() as db:
        db.execute("UPDATE engineering_github_operations SET state=?,updated=?,result=? WHERE id=? AND state='RUNNING'",
                   (state,time.time(),canonical(result),row['id']))
    return {'scheduled':True,'operation_id':row['id'],'operation_state':state,**result}

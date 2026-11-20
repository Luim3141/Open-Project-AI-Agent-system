"""Opt-in bounded reconciliation from the existing worker tick, never a coding scheduler."""
import threading
import time
import uuid


def tick(service):
    configured=service.config.get('engineering',{}).get('github_sync') or {}
    if configured.get('enabled') is not True:return {'scheduled':False,'reason':'DISABLED'}
    if set(configured)-{'enabled','actor','interval_seconds'} or configured.get('actor')!=18:
        raise ValueError('GITHUB_POLL_POLICY_INVALID')
    interval=configured.get('interval_seconds',300)
    if type(interval) is not int or not 60<=interval<=3600:raise ValueError('GITHUB_POLL_POLICY_INVALID')
    now=time.time();lease=str(uuid.uuid4())
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS engineering_github_poll(project INTEGER PRIMARY KEY,next_at REAL NOT NULL,lease TEXT,lease_until REAL NOT NULL,error TEXT)')
        row=db.execute('SELECT next_at,lease_until FROM engineering_github_poll WHERE project=6').fetchone()
        if row and max(row[0],row[1])>now:return {'scheduled':False,'reason':'NOT_DUE'}
        db.execute('INSERT INTO engineering_github_poll VALUES(6,?,?,?,NULL) ON CONFLICT(project) DO UPDATE SET next_at=excluded.next_at,lease=excluded.lease,lease_until=excluded.lease_until,error=NULL',
            (now+interval,lease,now+120))
    error=None
    try:
        from .engineering import scoped_service,authorized
        from .engineering_github_sync import reconcile_github_with_openproject
        scoped=scoped_service(service,6);native,_=authorized(scoped,18)
        result=reconcile_github_with_openproject(scoped,native,actor=18,request_id='automatic:'+lease)
        error=result.get('error')
        return {'scheduled':True,**result}
    except Exception as failure:
        from .engineering_github_sync import _error_code
        error=_error_code(failure)
        return {'scheduled':True,'status':'SYNC_FAILED','error':error}
    finally:
        with service.store.connect() as db:
            db.execute('UPDATE engineering_github_poll SET lease=NULL,lease_until=0,error=? WHERE project=6 AND lease=?',(error,lease))


def dispatch(service):
    # Native/GitHub timeout must not stall the independent indexing/outbox worker.
    if service.config.get('engineering',{}).get('github_sync',{}).get('enabled') is not True:return
    previous=getattr(service,'_github_poll_thread',None)
    if previous is not None and previous.is_alive():return
    worker=threading.Thread(target=tick,args=(service,),name='github-reconciliation',daemon=True)
    service._github_poll_thread=worker
    worker.start()

"""Local metadata sink only. External delivery requires an explicitly configured destination adapter."""
import os
import json
import time
import uuid
from pathlib import Path

from .store import canonical,digest
from .knowledge_lock import lease
from .permissions import business_manager


def status(store, actor, role, project):
    with store.connect() as db:
        rows=db.execute("SELECT state,count(*) FROM local_deliveries WHERE json_extract(document,'$.project_id')=? AND (? OR json_extract(document,'$.actor')=?) GROUP BY state",
            (project,business_manager(role),actor)).fetchall()
    return {'counts':dict(rows),'scope':'MAIN_COUNTS_ONLY' if business_manager(role) else 'OWN_COUNTS_ONLY',
            'delivery':'LOCAL_METADATA_ONLY','external_delivery':'BLOCKED_CONFIGURATION'}


def metadata(source, identifier, actor, project, sha):
    if source not in {'report','daily_brief','health_monitor'} or project != 5:
        raise ValueError('MAIN_LOCAL_DELIVERY_SOURCE_REQUIRED')
    return {'version':1,'source':source,'source_id':identifier,'actor':actor,'project_id':project,
            'source_sha256':sha,'scope':'STORED_REPORT_SNAPSHOT_METADATA_ONLY'}


def enqueue(db, source, identifier, actor, project, sha):
    if project != 5:return
    body=canonical(metadata(source,identifier,actor,project,sha));key=digest(body)
    db.execute("INSERT OR IGNORE INTO local_deliveries VALUES(?,?,?,'pending',0,0,NULL)",(key,body,digest(body)))


def enqueue_monitor(store, identifier):
    with store.connect() as db:
        row=db.execute("SELECT outcome,version FROM audit WHERE id=? AND actor IS NULL AND action='health_monitor'",(identifier,)).fetchone()
        if row is None or json.loads(row['outcome']).get('project_id') != 5:return
        if digest(row['outcome']) != row['version']:raise ValueError('MONITOR_RECEIPT_HASH_CHANGED')
        enqueue(db,'health_monitor',identifier,None,5,row['version'])


def verify_source(store, body):
    source,identifier,actor,project=body['source'],body['source_id'],body['actor'],body['project_id']
    if source=='report':
        sha=store.report(actor,project,identifier)['sha256']
    elif source=='daily_brief':
        report=store.daily_brief(actor,project,identifier)
        if report is None:raise ValueError('DAILY_SOURCE_MISSING')
        sha=digest(canonical(report))
    elif source=='health_monitor':
        with store.connect() as db:
            row=db.execute("SELECT outcome,version FROM audit WHERE id=? AND actor IS NULL AND action='health_monitor'",(identifier,)).fetchone()
        if row is None or json.loads(row['outcome']).get('project_id')!=project or digest(row['outcome'])!=row['version']:
            raise ValueError('MONITOR_RECEIPT_HASH_CHANGED')
        sha=row['version']
    else:raise ValueError('LOCAL_DELIVERY_SOURCE_DENIED')
    if body != metadata(source,identifier,actor,project,sha):raise ValueError('LOCAL_DELIVERY_SOURCE_CHANGED')


def publish_metadata(store, identifier, body):
    directory=store.root/'local-notifications';directory.mkdir(exist_ok=True)
    if directory.is_symlink():raise ValueError('LOCAL_DELIVERY_SYMLINK_DENIED')
    target=directory/(identifier+'.json');temporary=directory/(uuid.uuid4().hex+'.tmp');raw=canonical(body).encode()
    try:
        with temporary.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        try:os.link(temporary,target)
        except FileExistsError:pass
        if target.is_symlink() or target.read_bytes()!=raw:raise ValueError('LOCAL_DELIVERY_RECEIPT_MISMATCH')
        if os.name!='nt':
            fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
    finally:temporary.unlink(missing_ok=True)


def process_pending(store, now=None):
    now=time.time() if now is None else now
    try:
        with lease(store.root/'local-delivery.lock'):
            with store.connect() as db:
                row=db.execute("SELECT * FROM local_deliveries WHERE state='pending' AND next_at<=? ORDER BY next_at,id LIMIT 1",(now,)).fetchone()
                if row is None:return None
                attempt=row['attempts']+1
                db.execute('UPDATE local_deliveries SET attempts=? WHERE id=?',(attempt,row['id']))
            error=None
            try:
                if attempt>6:raise ValueError('LOCAL_DELIVERY_ATTEMPTS_EXHAUSTED')
                if digest(row['document'])!=row['hash'] or digest(row['document'])!=row['id']:
                    raise ValueError('LOCAL_DELIVERY_QUEUE_HASH_CHANGED')
                body=json.loads(row['document']);verify_source(store,body);publish_metadata(store,row['id'],body)
                state='delivered'
            except Exception as failure:
                error=type(failure).__name__;state='dlq' if attempt>=6 else 'pending'
            with store.connect() as db:
                db.execute('UPDATE local_deliveries SET state=?,next_at=?,error=? WHERE id=?',
                    (state,now+min(300,2**min(attempt,9)),error,row['id']))
            return {'id':row['id'],'state':state,'attempts':attempt,'error':error,'external_delivery':'BLOCKED_CONFIGURATION'}
    except ValueError as error:
        if 'KNOWLEDGE_BUSY' in str(error):return None
        raise


def deliver_local(store, directory, actor, project, report_id):
    report=store.report(actor,project,report_id)
    body={'version':1,'actor':actor,'project_id':project,'report_id':report_id,
          'report_sha256':report['sha256'],'kind':report['kind'],'scope':'STORED_REPORT_SNAPSHOT_METADATA_ONLY'}
    raw=canonical(body).encode();identifier=digest(canonical([actor,project,report_id]))
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    target=directory/(identifier+'.json')
    # A complete temporary file is hard-linked once; duplicates never replace an existing receipt.
    import tempfile
    with tempfile.NamedTemporaryFile(dir=directory,delete=False) as stream:
        temporary=Path(stream.name)
        try:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        except BaseException:
            stream.close();temporary.unlink();raise
    try:
        try:os.link(temporary,target)
        except FileExistsError:pass
        if target.read_bytes()!=raw:raise ValueError('LOCAL_DELIVERY_RECEIPT_MISMATCH')
    finally:temporary.unlink()
    return {'state':'DELIVERED_LOCAL_METADATA_ONLY','receipt_id':identifier,'sha256':digest(raw.decode()),
            'external_delivery':'BLOCKED_CONFIGURATION','native_writes':0}

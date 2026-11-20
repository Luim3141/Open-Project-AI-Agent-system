"""Durable Native visibility/version/hash inventory and cache-only refresh outbox."""
import json
import time
from datetime import datetime

from .knowledge_lock import lease
from .knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
from .native import NativeError
from .openproject_loader import work_package_to_document, actor_work_package_document
from .permissions import require
from .store import canonical, digest


def status(store, actor, project):
    with store.connect() as db:
        row = db.execute('SELECT generation,document FROM native_index_scans WHERE actor=? AND project=?', (actor,project)).fetchone()
    return {'state':'NOT_OBSERVED','generation':0,'actor':actor,'project_id':project} if row is None else {
        **json.loads(row['document']),'generation':row['generation']}


def scan(service, actor, authority='actor'):
    if service.mode != 'native':
        raise ValueError('NATIVE_MODE_REQUIRED')
    native, who = service.native_actor(actor)
    require(who['role'], 'knowledge_incremental_sync', service.mode)
    project = service.config['project_id']
    try:
        with lease(service.store.root/f'native-index-{actor}-{project}.lock'):
            # Native.collection fails on incomplete pagination; no visibility tombstone on failed reads.
            items = native.packages()
            if (any(type(p.get('id')) is not int or p['id']<=0 or type(p.get('lockVersion')) is not int
                    or p['lockVersion']<0 for p in items) or len({p['id'] for p in items}) != len(items)):
                raise NativeError(502, 'NATIVE_INDEX_INVALID_COLLECTION')
            storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(service.store.root/'knowledge.sqlite')))
            indexed = {d.source_id:d for d in storage.query_documents(str(project))}
            with service.store.connect() as db:
                cursors={r['native_id']:dict(r) for r in db.execute('SELECT * FROM native_index_cursor WHERE actor=? AND project=?',(actor,project))}
            generation=status(service.store,actor,project)['generation']
            ordered=sorted(item['id'] for item in items)
            # Bound journal API reads; updatedAt catches additions immediately, round-robin catches edits/removal too.
            audit_ids={ordered[(generation*32+i)%len(ordered)] for i in range(min(32,len(ordered)))}
            observations = []
            for item in items:
                doc = work_package_to_document(item, str(project))
                old = indexed.get(doc.source_id)
                current = old is not None and old.source_hash==doc.source_hash and old.metadata.get('lock_version')==item['lockVersion']
                previous = indexed.get(f'actor:{actor}:wp:{item["id"]}')
                cursor=cursors.get(item['id'])
                updated=item.get('updatedAt')
                if updated is not None:
                    try:updated_time=datetime.fromisoformat(updated.replace('Z','+00:00')).timestamp()
                    except (AttributeError,TypeError,ValueError):raise NativeError(502,'NATIVE_INDEX_INVALID_UPDATED_AT') from None
                    if previous and 'source_updated_at' in previous.metadata:
                        current = current and previous.metadata['source_updated_at']==updated
                    elif cursor and updated_time>cursor['observed']:
                        current=False
                revision = digest(canonical({'source_hash':doc.source_hash,'updated_at':updated}))
                if current and item['id'] in audit_ids:
                    activities = native.collection(f'/api/v3/work_packages/{item["id"]}/activities')
                    snapshot = actor_work_package_document(item,project,actor,who['role'],activities)
                    if previous is not None or snapshot.metadata['activity_ids']:
                        current = previous is not None and previous.source_hash==snapshot.source_hash and previous.metadata==snapshot.metadata and previous.allowed_roles==snapshot.allowed_roles
                        revision += '-'+digest(canonical({'snapshot_hash':snapshot.source_hash,'metadata':snapshot.metadata}))
                observations.append((item['id'],item['lockVersion'],revision,current))
            now, jobs = time.time(), []
            with service.store.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                for identifier, version, sha, current in observations:
                    if not current:
                        key = f'native-event-{project}-{identifier}-{version}-{sha}'
                        result = {}
                        service.store._enqueue_knowledge_sync(db,actor,key,identifier,result)
                        job_id = result['knowledge_sync']['id']
                        # Only a proven cache drift may requeue a verified cache-refresh job; never a Native write.
                        db.execute("UPDATE knowledge_sync SET state='pending',attempts=0,next_at=0,error=NULL WHERE id=? AND state='verified'", (job_id,))
                        jobs.append({'id':job_id,'native_id':identifier,'lock_version':version,'source_hash':sha})
                    db.execute('INSERT INTO native_index_cursor VALUES(?,?,?,?,?,1,?) ON CONFLICT(actor,project,native_id) DO UPDATE SET version=excluded.version,hash=excluded.hash,visible=1,observed=excluded.observed',
                        (actor,project,identifier,version,sha,now))
                observed = {identifier for identifier,_,_,_ in observations}
                previous = [row[0] for row in db.execute('SELECT native_id FROM native_index_cursor WHERE actor=? AND project=? AND visible=1',(actor,project))]
                withdrawn = sorted(set(previous)-observed)
                for identifier in withdrawn:
                    db.execute('UPDATE native_index_cursor SET visible=0,observed=? WHERE actor=? AND project=? AND native_id=?',(now,actor,project,identifier))
                retained = db.execute('SELECT count(*) FROM native_index_cursor WHERE actor=? AND project=? AND visible=0',(actor,project)).fetchone()[0]
                report = {'state':'OBSERVED','actor':actor,'project_id':project,'authority':authority,'observed_at':now,
                    'activity_audit_ids':sorted(audit_ids),'activity_audit_batch_limit':32,
                    'visible':len(items),'changed':len(jobs),'jobs':jobs,'visibility_withdrawn_ids':withdrawn,
                    'not_visible_retained':retained,
                    'inventory_sha256':digest(canonical(sorted((i,v,h) for i,v,h,_ in observations))),
                    'native_writes':0,'model_calls':0,'physical_deletion':'DENIED_WITHOUT_TRUSTED_DELETE_PROOF',
                    'visibility_policy':'Fresh Native collection gates retrieval; withdrawn index content is retained',
                    'vector_integrity':'NOT_CHECKED_USE_KNOWLEDGE_INTEGRITY'}
                db.execute('INSERT INTO native_index_scans VALUES(?,?,1,?) ON CONFLICT(actor,project) DO UPDATE SET generation=native_index_scans.generation+1,document=excluded.document',
                    (actor,project,canonical(report)))
            service.store.record(actor,'native_incremental_scan',str(project),'MACHINE_READ_ONLY' if authority=='machine' else 'ACTOR_READ_ONLY')
            return status(service.store,actor,project)
    except ValueError as error:
        if 'KNOWLEDGE_BUSY' in str(error):
            raise NativeError(503,'NATIVE_INDEX_SCAN_BUSY') from None
        raise

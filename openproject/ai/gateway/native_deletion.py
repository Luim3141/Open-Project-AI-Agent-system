"""Exact approved Native deletion and cache-only recovery from its signed commit ledger."""
import hashlib
import hmac
import json
import re
import time
from contextlib import closing, nullcontext

from .native import NativeError
from .permissions import business_manager
from .store import canonical, digest

DOMAIN=b'qldapm.native-delete.v1\0'


def arguments(service,args,sealed=False):
    fields={'id','lock_version'}|({'snapshot_sha256'} if sealed else set())
    service.keys(args,fields,fields)
    if type(args['id']) is not int or args['id']<=0 or type(args['lock_version']) is not int or args['lock_version']<0:
        raise ValueError('NATIVE_DELETE_ID_VERSION_INVALID')
    if sealed and (not isinstance(args['snapshot_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',args['snapshot_sha256'])):
        raise ValueError('NATIVE_DELETE_SOURCE_HASH_REQUIRED')


def preview(service,who,native,args,request_key=None):
    if service.mode!='native' or service.config['project_id']!=5 or not business_manager(who['role']):
        raise PermissionError('NATIVE_DELETE_MAIN_MANAGER_REQUIRED')
    with service.store.connect() as db:
        for row in db.execute("SELECT actor,key,payload FROM requests WHERE state!='done'"):
            pending=json.loads(row['payload']) if row['payload'] else {}
            # Cache-only failures never leave an unknown Native write; keep their receipts without blocking deletion.
            if pending.get('action') in {'knowledge_ingest','knowledge_deindex'}:continue
            values=pending.get('arguments',{})
            if (row['actor']!=who['user_id'] or row['key']!=request_key) and args['id'] in [values.get(k) for k in ['id','parent_id','predecessor_id','successor_id']]:
                raise NativeError(409,'NATIVE_DELETE_PENDING_SOURCE_WRITE_HOLD')
    result=native.call('/api/v3/qldapm/native_deletion_forms','POST',{k:args[k] for k in ['id','lock_version']})
    if (result.get('id')!=args['id'] or result.get('lock_version')!=args['lock_version'] or result.get('project_id')!=5 or
            result.get('permanent_delete') is not True or result.get('cascade') is not False or
            not isinstance(result.get('snapshot_sha256'),str) or not re.fullmatch('[a-f0-9]{64}',result['snapshot_sha256'])):
        raise NativeError(502,'NATIVE_DELETE_PREVIEW_INVALID')
    return result


def authorization(service,actor,args,key,states=('executing',)):
    if not isinstance(key,str) or not re.fullmatch(r'proposal-[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}',key):
        raise PermissionError('NATIVE_DELETE_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    proposal=service.store.proposal(actor,key[9:]);command=proposal['command']
    if (proposal['state'] not in states or command.get('action')!='delete_work_package' or command.get('arguments')!=args or
            command.get('_gateway_mode')!='native' or digest(canonical({'actor':actor,'command':command}))!=proposal['hash']):
        raise PermissionError('NATIVE_DELETE_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    return proposal


def payload(actor,proposal):
    return {**proposal['command']['arguments'],'proposal_id':proposal['id'],'proposal_hash':proposal['hash'],
        'request_id':'QLDAPM-request-'+digest(f'{actor}:proposal-{proposal["id"]}')}


def verify(service,bundle,actor,proposal):
    if not isinstance(bundle,dict) or set(bundle)!={'document','signature'} or not isinstance(bundle['document'],str) or len(bundle['document'].encode())>8192 or not isinstance(bundle['signature'],str):
        raise ValueError('NATIVE_DELETE_SIGNED_LEDGER_REQUIRED')
    expected=hmac.new((service.store.root/'ui.key').read_bytes(),DOMAIN+bundle['document'].encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,bundle['signature']):raise ValueError('NATIVE_DELETE_SIGNATURE_INVALID')
    document=json.loads(bundle['document']);args=proposal['command']['arguments'];packet=payload(actor,proposal)
    expected={'schema':'QLDAPM_NATIVE_DELETE_V1','producer':'qldapm-native-delete-v1','project_id':5,'native_id':args['id'],
        'source_version':args['lock_version'],'snapshot_sha256':args['snapshot_sha256'],'actor_id':actor,
        'proposal_id':proposal['id'],'proposal_hash':proposal['hash'],'request_id':packet['request_id'],'request_hash':digest(canonical(packet))}
    if (not isinstance(document,dict) or set(document)!=set(expected)|{'event_id','deleted_at'} or
            any(document.get(k)!=v or type(document.get(k)) is not type(v) for k,v in expected.items()) or
            not isinstance(document['event_id'],str) or not re.fullmatch(r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}',document['event_id']) or
            not isinstance(document['deleted_at'],str)):
        raise ValueError('NATIVE_DELETE_LEDGER_BINDING_INVALID')
    return document


def readback(service,native,result,actor,proposal):
    document=verify(service,result,actor,proposal)
    try:native.package(document['native_id'])
    except NativeError as error:
        if error.status==404:return result
        raise
    raise NativeError(409,'NATIVE_DELETE_SOURCE_STILL_PRESENT_HOLD')


def execute(service,who,native,args,key):
    arguments(service,args,sealed=True);proposal=authorization(service,who['user_id'],args,key)
    current=preview(service,who,native,args,key)
    if current['snapshot_sha256']!=args['snapshot_sha256']:raise NativeError(409,'NATIVE_DELETE_STALE_SOURCE')
    body=payload(who['user_id'],proposal);at=int(time.time())
    native.mutation_headers={'X-Qldapm-At':str(at),'X-Qldapm-Mutation':hmac.new((service.store.root/'ui.key').read_bytes(),f'{who["user_id"]}:{at}:{digest(canonical(body))}'.encode(),hashlib.sha256).hexdigest()}
    result=native.call('/api/v3/qldapm/native_deletions','POST',body)
    try:return readback(service,native,result,who['user_id'],proposal)
    except (NativeError,KeyError,TypeError,ValueError):raise NativeError(503,'NATIVE_DELETE_OUTCOME_UNKNOWN; inspect signed ledger, never replay') from None


def reconcile(service,who,native,args,key):
    if service.mode!='native' or not business_manager(who['role']):raise PermissionError('NATIVE_DELETE_MAIN_MANAGER_REQUIRED')
    proposal=authorization(service,who['user_id'],args,key,states=('executing','failed_or_unknown'));arguments(service,args,sealed=True)
    try:result=native.call('/api/v3/qldapm/native_deletions/'+payload(who['user_id'],proposal)['request_id'])
    except NativeError as error:
        if error.status==404:return None
        raise
    return readback(service,native,result,who['user_id'],proposal)


def synchronize(service,claim,vector=None):
    """Never mutates Native. Persist an exact owned-point plan before the first vector delete."""
    from .knowledge_lock import lease
    from .knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
    from .vector_client import VectorClient
    native,who=service.native_actor(claim['actor'])
    if not business_manager(who['role']):raise PermissionError('NATIVE_DELETE_RECOVERY_MANAGER_REQUIRED')
    key=claim['request_key'];proposal=authorization(service,who['user_id'],service.store.proposal(who['user_id'],key[9:])['command']['arguments'],key,states=('done',))
    with service.store.connect() as db:
        row=db.execute("SELECT result FROM requests WHERE actor=? AND key=? AND state='done'",(who['user_id'],key)).fetchone()
    if row is None:raise ValueError('NATIVE_DELETE_DURABLE_RECEIPT_REQUIRED')
    receipt=json.loads(row['result']);proof=receipt['result'];event=verify(service,proof,who['user_id'],proposal)
    if event['native_id']!=claim['native_id']:raise ValueError('NATIVE_DELETE_SYNC_SCOPE_INVALID')
    # GET rechecks the authoritative own commit ledger, not merely source absence.
    actual=native.call('/api/v3/qldapm/native_deletions/'+event['request_id'])
    if actual!=proof:raise ValueError('NATIVE_DELETE_LEDGER_CHANGED')
    readback(service,native,actual,who['user_id'],proposal)
    path=service.store.root/'knowledge.sqlite'
    with lease(str(path)+'.ingest.lock'):
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(path)))
        context=closing(VectorClient()) if vector is None else nullcontext(vector)
        with context as client:
            if not client.enabled:raise ValueError('NATIVE_DELETE_VECTOR_REQUIRED')
            docs=[d for d in storage.query_documents('5') if d.metadata.get('native_id')==event['native_id']]
            from .knowledge_classifier import _compute_hash
            for doc in docs:
                actor_id=doc.metadata.get('actor_id');source=f'actor:{actor_id}:wp:{event["native_id"]}' if actor_id is not None else f'op:wp:{event["native_id"]}'
                if (type(doc.metadata['native_id']) is not int or doc.source_id!=source or type(doc.metadata.get('lock_version')) is not int or not 0<=doc.metadata['lock_version']<=event['source_version'] or
                        _compute_hash(doc.content,doc.doc_type.value,doc.source_id,doc.project_id)!=doc.source_hash):
                    raise ValueError('NATIVE_DELETE_CACHE_SOURCE_SCOPE_HOLD')
            plan=receipt.get('cache_delete_plan')
            if plan is None:
                chunks=storage._mock_tables[f'{storage.schema_name}.knowledge_chunks'].values();targets=[]
                for doc in docs:
                    for chunk in [c for c in chunks if c['document_id']==doc.source_hash]:
                        if digest(f'{chunk["chunk_index"]}:{chunk["chunk_text"]}')!=chunk['chunk_hash']:raise ValueError('NATIVE_DELETE_CACHE_CHUNK_HASH_HOLD')
                        data={'document_id':doc.source_hash,'source_id':doc.source_id,'project_id':'5','doc_type':doc.doc_type.value,
                            'title':doc.title,'chunk_index':chunk['chunk_index'],'chunk_text':chunk['chunk_text'],'chunk_hash':chunk['chunk_hash'],
                            'allowed_roles':doc.allowed_roles,'metadata':doc.metadata,'work_package_id':event['native_id']}
                        if 'actor_id' in doc.metadata:data['actor_id']=doc.metadata['actor_id']
                        targets.append({'id':client.deterministic_uuid(f'{doc.source_hash}:{chunk["chunk_index"]}'),'payload':data})
                plan={'event_id':event['event_id'],'documents':sorted(d.source_hash for d in docs),'points':targets}
                with service.store.connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    latest=json.loads(db.execute('SELECT result FROM requests WHERE actor=? AND key=?',(who['user_id'],key)).fetchone()[0])
                    latest['cache_delete_plan']=plan
                    db.execute('UPDATE requests SET result=? WHERE actor=? AND key=?',(canonical(latest),who['user_id'],key))
            if plan['event_id']!=event['event_id'] or not {d.source_hash for d in docs}<=set(plan['documents']):raise ValueError('NATIVE_DELETE_CACHE_PLAN_CHANGED_HOLD')
            # Exact point IDs only; unrelated/unregistered legacy points are never selected.
            client.delete_verified_points(plan['points'])
            for source_hash in plan['documents']:storage.delete_document(source_hash)
            remaining=[d for d in storage.query_documents('5') if d.metadata.get('native_id')==event['native_id']]
            if remaining:raise ValueError('NATIVE_DELETE_SQLITE_READBACK_FAILED')
            return {'vector_indexed':True,'native_deleted':True,'event_id':event['event_id'],'documents_removed':len(plan['documents']),
                'points_removed':len(plan['points']),'native_writes':0,'scope':'exact registered Native documents/chunks only'}

"""Review a source-bound feedback request; feedback text never becomes indexed knowledge."""
import json
import re
import time
import uuid

from .agent_trace import current_run
from .file_knowledge import load_source
from .native import NativeError
from .openproject_loader import work_package_to_document
from .permissions import business_manager
from .store import canonical, digest


def source_document(service, who, native, source):
    if set(source)=={'source_key'}:
        return load_source(service.config,who,source['source_key'])
    if set(source)!={'native_id'} or type(source['native_id']) is not int or source['native_id']<=0:
        raise ValueError('ONE_NATIVE_ID_OR_REGISTERED_SOURCE_KEY_REQUIRED')
    return work_package_to_document(native.package(source['native_id']),str(service.config['project_id']))


def binding(doc):
    return {'source_id':doc.source_id,'document_id':doc.source_hash,
        'version':doc.metadata.get('lock_version',doc.metadata.get('source_sha256'))}


def read(service, who, native, identifier):
    try:
        if not isinstance(identifier,str) or str(uuid.UUID(identifier))!=identifier:raise ValueError()
    except (ValueError,TypeError,AttributeError):raise ValueError('FEEDBACK_UUID_REQUIRED') from None
    with service.store.connect() as db:
        row=db.execute('SELECT * FROM knowledge_feedback WHERE id=? AND project=?',(identifier,service.config['project_id'])).fetchone()
    if row is None or row['actor']!=who['user_id'] and not business_manager(who['role']):
        raise PermissionError('FEEDBACK_SCOPE_DENIED')
    body=json.loads(row['document'])
    if digest(canonical(body))!=row['hash'] or (body.get('id'),body.get('actor'),body.get('project_id'))!=(row['id'],row['actor'],row['project']):
        raise ValueError('FEEDBACK_HASH_MISMATCH')
    current=source_document(service,who,native,body['source'])
    if row['actor']!=who['user_id']:
        service.store.record(who['user_id'],'feedback_review_oversight',identifier,'SOURCE_AUTHORIZED_READ')
    return {**body,'hash':row['hash'],'state':row['state'],'created_at':row['created'],'reviewer':row['reviewer'],
        'result':json.loads(row['result']) if row['result'] else None,'source_current':binding(current)==body['binding'],
        'feedback_content_promoted':False,'verification_basis':'TRUSTED_SOURCE_IDENTITY_AND_REVISION_ONLY'}


def submit(service,who,native,args,key):
    service.keys(args,{'native_id','source_key','note'},{'note'})
    if not isinstance(args['note'],str) or not 1<=len(args['note'].strip())<=1000:
        raise ValueError('FEEDBACK_NOTE_1_1000_REQUIRED')
    source={k:v for k,v in args.items() if k!='note'}
    identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f"qldapm.knowledge-feedback:{who['user_id']}:{service.config['project_id']}:{key}"))
    with service.store.connect() as db:
        existing=db.execute('SELECT id FROM knowledge_feedback WHERE id=?',(identifier,)).fetchone()
    if existing:
        saved=read(service,who,native,identifier)
        if saved['source']!=source or saved['note']!=args['note'].strip():
            raise ValueError('FEEDBACK_REQUEST_KEY_REUSED')
        return saved
    doc=source_document(service,who,native,source)
    body={'id':identifier,'actor':who['user_id'],'project_id':service.config['project_id'],
        'source':source,'binding':binding(doc),'note':args['note'].strip()}
    sha=digest(canonical(body))
    with service.store.connect() as db:
        db.execute("INSERT OR IGNORE INTO knowledge_feedback VALUES(?,?,?,?,?,'pending',?,NULL,NULL)",
            (identifier,who['user_id'],service.config['project_id'],canonical(body),sha,time.time()))
    return read(service,who,native,identifier)


def decide(service,bearer,identifier,decision,fingerprint):
    actor=service.store.authenticate(bearer)['user_id']
    native,who=service.native_actor(actor)
    if not business_manager(who['role']) or current_run.get() is not None:
        raise PermissionError('INDEPENDENT_AUTHENTICATED_REVIEW_REQUIRED')
    if decision not in {'accept','reject'} or not isinstance(fingerprint,str) or not re.fullmatch('[a-f0-9]{64}',fingerprint):
        raise ValueError('FEEDBACK_DECISION_AND_EXACT_HASH_REQUIRED')
    feedback=read(service,who,native,identifier)
    if feedback['actor']==actor:
        raise PermissionError('FEEDBACK_SELF_REVIEW_DENIED')
    if feedback['hash']!=fingerprint or feedback['state']!='pending' or decision=='accept' and not feedback['source_current']:
        raise NativeError(409,'FEEDBACK_CHANGED_STALE_OR_ALREADY_DECIDED')
    with service.store.connect() as db:
        changed=db.execute("UPDATE knowledge_feedback SET state=?,reviewer=? WHERE id=? AND project=? AND state='pending' AND hash=?",
            ('accepted' if decision=='accept' else 'rejected',actor,identifier,service.config['project_id'],fingerprint)).rowcount
    if changed!=1:raise NativeError(409,'FEEDBACK_ALREADY_DECIDED')
    service.store.record(actor,'feedback_'+decision,identifier,'EXACT_SOURCE_REVIEW')
    return read(service,who,native,identifier)


def apply(service,who,native,identifier):
    feedback=read(service,who,native,identifier)
    if not business_manager(who['role']):raise PermissionError('FEEDBACK_MANAGER_REQUIRED')
    if not feedback['source_current']:raise NativeError(409,'FEEDBACK_SOURCE_CHANGED')
    if feedback['state']=='applied':return feedback
    if feedback['state']!='accepted' or not feedback['source_current']:
        raise NativeError(409,'ACCEPTED_CURRENT_FEEDBACK_REQUIRED')
    if 'native_id' in feedback['source']:
        result=service.sync_canonical_native(who['user_id'],feedback['source']['native_id'])
    else:
        from .file_knowledge import execute
        result=execute(service,who,'knowledge_file_ingest',feedback['source'])
    if not read(service,who,native,identifier)['source_current']:
        raise NativeError(409,'FEEDBACK_SOURCE_CHANGED_DURING_REINDEX')
    with service.store.connect() as db:
        db.execute("UPDATE knowledge_feedback SET state='applied',result=? WHERE id=? AND state='accepted'",(canonical(result),identifier))
    return read(service,who,native,identifier)

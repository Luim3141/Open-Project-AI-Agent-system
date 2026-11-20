"""Native source phase drafts and independent human reviews; neither executes a mutation."""
import hashlib
import hmac
import json
import re
import time
import uuid

from .agent_trace import current_run
from .native import NativeError
from .native_qa_runs import snapshot,signing_key
from .permissions import business_manager
from .store import canonical,digest

DOMAIN=b'qldapm.native-phase-source.v1\0'
REVIEW_DOMAIN=b'qldapm.native-phase-review.v1\0'


def signed(service,document,domain):
    body=canonical(document)
    return {'document':body,'signature':hmac.new(signing_key(service),domain+body.encode(),hashlib.sha256).hexdigest()}


def validate_source(item,kind):
    description=item.get('description',{}).get('raw','').replace('\r\n','\n').replace('\r','\n')
    criteria=re.findall(r'(?m)^[ \t]*(AC[1-9][0-9]{0,3}):[ \t]+([^\r\n]+)$',description)
    labels=re.findall(r'(?m)^[ \t]*(AC[0-9]+):',description)
    if not 1<=len(criteria)<=100 or any(not c[1].strip() for c in criteria) or len({c[0] for c in criteria})!=len(criteria) or [c[0] for c in criteria]!=labels:raise ValueError('PHASE_UNIQUE_AC_REQUIRED')
    keys=['Story','Scope']+(['Analysis'] if kind=='analysis' else [])
    if any(not re.search(r'(?m)^[ \t]*'+name+r':[ \t]+\S[^\r\n]*$',description) for name in keys):raise ValueError('PHASE_NATIVE_SOURCE_SECTIONS_REQUIRED')


def source(native,identifier):
    if type(identifier) is not int or identifier<=0:raise ValueError('PHASE_NATIVE_POSITIVE_ID_REQUIRED')
    item=native.package(identifier)
    if item.get('id')!=identifier or type(item.get('lockVersion')) is not int or item['lockVersion']<0:raise NativeError(502,'PHASE_NATIVE_IDENTITY_INVALID')
    if item.get('_links',{}).get('project',{}).get('href')!='/api/v3/projects/5':raise PermissionError('PHASE_MAIN_SOURCE_REQUIRED')
    gate=native.call('/api/v3/qldapm/gates/'+str(identifier))
    if gate.get('id')!=identifier or gate.get('lockVersion')!=item['lockVersion'] or type(gate.get('gate',{}).get('revision')) is not int:raise NativeError(409,'PHASE_SOURCE_CHANGED')
    return item,gate['gate']


def get(service,actor,identifier):
    native,who=service.native_actor(actor)
    if not isinstance(identifier,str) or str(uuid.UUID(identifier))!=identifier:raise ValueError('PHASE_UUID_REQUIRED')
    with service.store.connect() as db:
        row=db.execute('SELECT * FROM native_phase_documents WHERE id=? AND project=?',(identifier,service.config['project_id'])).fetchone()
        review=db.execute('SELECT document FROM native_phase_reviews WHERE artifact=?',(identifier,)).fetchone()
    if row is None or not (business_manager(who['role']) or who['role'] in {'BA','BA-PM'} and row['actor']==actor):raise PermissionError('PHASE_PRIVATE_ARTIFACT_DENIED')
    document=json.loads(row['document'])
    if digest(canonical(document))!=row['hash'] or document['actor']!=row['actor'] or document['id']!=identifier or document['project_id']!=5:
        raise ValueError('PHASE_DOCUMENT_TAMPERED')
    item,gate=source(native,document['source']['id'])
    result={**document,'hash':row['hash'],'state':row['state'],'source_current':snapshot(item)==document['source'] and gate.get('revision',0)==document['gate_revision'],'review':None}
    result['can_review']=business_manager(who['role']) and row['state']=='pending' and actor not in {document['actor'],document['source']['fields']['assignee_id'],*gate.get('contributors',[])}
    if review:
        bundle=json.loads(review[0]);data=json.loads(bundle['document'])
        if not hmac.compare_digest(signed(service,data,REVIEW_DOMAIN)['signature'],bundle['signature']) or data['hash']!=row['hash'] or data['artifact_id']!=identifier:
            raise NativeError(409,'PHASE_REVIEW_TAMPERED')
        reviewer_native,reviewer=service.native_actor(data['actor'])
        reviewer_native.package(document['source']['id'])
        result['review']=data
        result['reviewer_current']=business_manager(reviewer['role']) and reviewer['role']==data['role']
    if who['role']=='AI_SYSTEM_OWNER' and actor!=row['actor']:service.store.record(actor,'owner_oversight','native_phase:'+identifier,'READ_ONLY')
    return result


def create(service,actor,identifier,kind):
    if service.mode!='native' or service.config['project_id']!=5:raise PermissionError('PHASE_NATIVE_MAIN_ONLY')
    native,who=service.native_actor(actor)
    if not (business_manager(who['role']) or who['role'] in {'BA','BA-PM'}):raise PermissionError('PHASE_SOURCE_PRODUCER_REQUIRED')
    if not isinstance(kind,str) or kind not in {'scope','analysis'}:raise ValueError('PHASE_KIND_NOT_IMPLEMENTED')
    item,gate=source(native,identifier);validate_source(item,kind);current=snapshot(item)
    identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f'qldapm.native-phase:5:{actor}:{kind}:{digest(canonical(current))}:{gate.get("revision",0)}'))
    with service.store.connect() as db:
        exists=db.execute('SELECT 1 FROM native_phase_documents WHERE id=?',(identifier,)).fetchone()
        if not exists:
            document={'version':1,'id':identifier,'actor':actor,'project_id':5,'kind':kind,'source':current,'gate_revision':gate.get('revision',0),'created_at':time.time()}
            body=canonical(document)
            if len(body.encode())>100000:raise ValueError('PHASE_SOURCE_TOO_LARGE')
            db.execute('INSERT INTO native_phase_documents VALUES(?,?,?,?,?,?,?)',(identifier,actor,5,body,digest(body),'pending',document['created_at']))
            service.store.record(actor,'native_phase_draft',identifier,'DRAFT_ONLY',version=digest(body),connection=db)
    return get(service,actor,identifier)


def review(service,actor,identifier,decision,fingerprint):
    native,who=service.native_actor(actor)
    if not business_manager(who['role']) or current_run.get() is not None:raise PermissionError('PHASE_INDEPENDENT_HUMAN_REVIEW_REQUIRED')
    if decision not in {'accept','reject'} or not isinstance(fingerprint,str) or not re.fullmatch('[a-f0-9]{64}',fingerprint):raise ValueError('PHASE_EXACT_REVIEW_REQUIRED')
    document=get(service,actor,identifier);item,gate=source(native,document['source']['id'])
    if actor in {document['actor'],document['source']['fields']['assignee_id'],*gate.get('contributors',[])}:raise PermissionError('PHASE_INDEPENDENT_HUMAN_REVIEW_REQUIRED')
    if document['state']!='pending' or document['hash']!=fingerprint or decision=='accept' and not document['source_current']:raise NativeError(409,'PHASE_STALE_OR_ALREADY_DECIDED')
    data={'artifact_id':identifier,'hash':fingerprint,'actor':actor,'role':who['role'],'decision':decision,'kind':document['kind'],
        'approvals':['scope'] if document['kind']=='scope' else ['scope','analysis'],'at':time.time()}
    with service.store.connect() as db:
        changed=db.execute("UPDATE native_phase_documents SET state=? WHERE id=? AND state='pending' AND hash=?",('accepted' if decision=='accept' else 'rejected',identifier,fingerprint)).rowcount
        if changed!=1:raise NativeError(409,'PHASE_ALREADY_DECIDED')
        db.execute('INSERT INTO native_phase_reviews VALUES(?,?)',(identifier,canonical(signed(service,data,REVIEW_DOMAIN))))
        service.store.record(actor,'native_phase_'+decision,identifier,'EXACT_HUMAN_REVIEW',version=fingerprint,connection=db)
    return get(service,actor,identifier)


def packet(service,actor,identifier):
    _,who=service.native_actor(actor)
    if not business_manager(who['role']):raise PermissionError('PHASE_NATIVE_MANAGER_REQUIRED')
    document=get(service,actor,identifier)
    if document['state']!='accepted' or not document['source_current'] or not document.get('reviewer_current') or document['review']['decision']!='accept':
        raise NativeError(409,'PHASE_CURRENT_ACCEPTED_REVIEW_REQUIRED')
    producer_native,producer=service.native_actor(document['actor'])
    producer_native.package(document['source']['id'])
    if not (business_manager(producer['role']) or producer['role'] in {'BA','BA-PM'}):raise PermissionError('PHASE_PRODUCER_REVOKED')
    fields={'version','id','actor','project_id','kind','source','gate_revision','created_at'}
    return {'version':1,'artifact':signed(service,{k:v for k,v in document.items() if k in fields},DOMAIN),'review':signed(service,document['review'],REVIEW_DOMAIN)}


def validate_request(service,actor,action,args):
    if service.mode!='native' or service.config['project_id']!=5:raise PermissionError('PHASE_NATIVE_MAIN_ONLY')
    if action=='phase_draft':
        service.keys(args,{'native_id','kind'},{'native_id','kind'})
        if not isinstance(args['kind'],str) or args['kind'] not in {'scope','analysis'}:raise ValueError('PHASE_KIND_NOT_IMPLEMENTED')
        native,_=service.native_actor(actor);item,_=source(native,args['native_id']);validate_source(item,args['kind'])
        return
    service.keys(args,{'id','hash','status_id'},{'id','hash','status_id'})
    document=get(service,actor,args['id'])
    if not isinstance(args['hash'],str) or not hmac.compare_digest(document['hash'],args['hash']):raise NativeError(409,'PHASE_EXACT_HASH_REQUIRED')
    return {'id':document['source']['id'],'lock_version':document['source']['version'],'status_id':args['status_id'],
        'phase_id':document['id'],'phase_hash':document['hash']}


def perform(service,actor,action,args,key):
    if service.mode!='native' or service.config['project_id']!=5:raise PermissionError('PHASE_NATIVE_MAIN_ONLY')
    if action=='phase_draft':
        service.keys(args,{'native_id','kind'},{'native_id','kind'})
        return create(service,actor,args['native_id'],args['kind'])
    if action=='phase_list':
        service.keys(args,set(),set());_,who=service.native_actor(actor)
        with service.store.connect() as db:
            rows=db.execute('SELECT id FROM native_phase_documents WHERE project=? AND (actor=? OR ?) ORDER BY created DESC LIMIT 20',
                (5,actor,business_manager(who['role']))).fetchall()
        items=[]
        for row in rows:
            try:document=get(service,actor,row['id'])
            except PermissionError:continue
            except NativeError as error:
                if error.status in {403,404}:continue
                raise
            items.append({k:document[k] for k in ['id','actor','kind','state','hash','source_current']}
                | {'native_id':document['source']['id'],'version':document['source']['version']})
        return {'items':items,'limit':20,'scope':'CURRENT_NATIVE_AUTHORIZED_PHASES'}
    if action=='phase_transition_prepare':
        return service.execute_actor(actor,{'action':'transition','idempotency_key':'phase-transition-'+key,
            'arguments':validate_request(service,actor,action,args)})['result']
    service.keys(args,{'id'},{'id'})
    document=get(service,actor,args['id'])
    if action=='phase_get':
        native,who=service.native_actor(actor);values=[]
        if business_manager(who['role']) and document['source_current']:
            form=native.call('/api/v3/work_packages/'+str(document['source']['id'])+'/form','POST',{'lockVersion':document['source']['version']})
            values=form.get('_embedded',{}).get('schema',{}).get('status',{}).get('_embedded',{}).get('allowedValues',[])
        document['status_options']=[{'id':v['id'],'name':v['name']} for v in values if type(v.get('id')) is int and v['id']>0 and isinstance(v.get('name'),str)]
        return document

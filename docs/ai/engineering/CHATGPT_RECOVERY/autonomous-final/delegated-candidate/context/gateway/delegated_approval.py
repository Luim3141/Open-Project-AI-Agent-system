"""Owner-delegated Project6 fixture policy; Native executes as a separate real PM."""
import json,re,time,uuid
from .store import canonical,digest

POLICY='OWNER_DELEGATED_DEMO_APPROVAL'
ACTIONS={'SET_FIXTURE_NOTE','TRANSITION_FIXTURE_BUG'}
TERMINAL={'BUSINESS_VERIFIED','REJECTED','REQUIRES_HUMAN_APPROVAL','OUTCOME_UNKNOWN'}


def setup(store):
    with store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS delegated_control(project INTEGER PRIMARY KEY,enabled INTEGER NOT NULL,revision INTEGER NOT NULL)')
        db.execute('INSERT OR IGNORE INTO delegated_control VALUES(6,0,0)')
        db.execute('CREATE TABLE IF NOT EXISTS delegated_proposals(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,request_key TEXT NOT NULL,hash TEXT NOT NULL,document TEXT NOT NULL,UNIQUE(actor,request_key))')
        db.execute('CREATE TABLE IF NOT EXISTS delegated_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,proposal_id TEXT NOT NULL,stage TEXT NOT NULL,document TEXT NOT NULL,UNIQUE(proposal_id,stage))')


def _requester(service,actor):
    if service.config.get('project_id')!=6 or actor not in (18,20):raise PermissionError('DELEGATED_PROJECT6_REQUESTER_REQUIRED')
    _,who=service.native_actor(actor)
    if who['user_id']!=actor or who['role'] not in {'AI_SYSTEM_OWNER','PM'}:raise PermissionError('DELEGATED_PROJECT6_REQUESTER_REQUIRED')
    return who


def _rules(service):
    rules=service.config.get('delegated_demo',{})
    if not isinstance(rules,dict) or set(rules)!={'principal_id','fixtures'}:raise PermissionError('DELEGATED_POLICY_NOT_CONFIGURED')
    actor=rules['principal_id'];fixtures=rules['fixtures']
    if type(actor) is not int or actor<=23 or not isinstance(fixtures,dict) or not 1<=len(fixtures)<=10:raise PermissionError('DELEGATED_DISTINCT_PRINCIPAL_REQUIRED')
    for identifier,row in fixtures.items():
        if (not re.fullmatch('[1-9][0-9]*',identifier) or not isinstance(row,dict) or set(row)!={'marker','type_id','transitions'}
                or not isinstance(row['marker'],str) or not re.fullmatch('OWNER-DELEGATED-[A-Za-z0-9-]{4,80}',row['marker'])
                or type(row['type_id']) is not int or row['type_id']<=0 or not isinstance(row['transitions'],list)
                or len(row['transitions'])>4 or any(not isinstance(pair,list) or len(pair)!=2 or any(type(n) is not int or n<=0 for n in pair) or pair[0]==pair[1] for pair in row['transitions'])):
            raise PermissionError('DELEGATED_FIXTURE_REGISTRY_INVALID')
    return rules,digest(canonical({'policy':POLICY,'project_id':6,'actions':sorted(ACTIONS),'registry':rules}))


def status(service,actor,*,packages=None):
    _requester(service,actor);setup(service.store)
    with service.store.connect() as db:
        control=dict(db.execute('SELECT * FROM delegated_control WHERE project=6').fetchone())
        proposals=[json.loads(r[0]) for r in db.execute('SELECT document FROM delegated_proposals WHERE (?=18 OR actor=?) ORDER BY rowid DESC LIMIT 20',(actor,actor))]
    try:rules,fingerprint=_rules(service)
    except PermissionError:rules={};fingerprint=None
    current=[]
    if rules:
        if packages is None:
            native,_=service.native_actor(actor)
            packages=[native.package(int(identifier)) for identifier in rules['fixtures']]
        for item in packages:
            fixture=rules['fixtures'].get(str(item.get('id')))
            if fixture and item['_links']['project']['href']=='/api/v3/projects/6' and fixture['marker'] in item['subject']:
                current.append({'native_id':item['id'],'lock_version':item['lockVersion'],'status_id':_snapshot(item)['status_id'],
                                'marker':fixture['marker'],'transitions':fixture['transitions']})
    return {'policy':POLICY,'project_id':6,'enabled':bool(control['enabled']),'revision':control['revision'],
            'principal_id':rules.get('principal_id'),'policy_hash':fingerprint,'fixtures':rules.get('fixtures',{}),
            'allowlist':sorted(ACTIONS),'current_fixtures':current,'proposals':proposals,'human_approval_claimed':False}


def control(service,actor,enabled,expected_revision):
    who=_requester(service,actor);setup(service.store)
    if actor!=18 or who['role']!='AI_SYSTEM_OWNER':raise PermissionError('DELEGATED_OWNER_CONTROL_REQUIRED')
    if type(enabled) is not bool or type(expected_revision) is not int:raise ValueError('DELEGATED_CONTROL_INVALID')
    if enabled:_rules(service)
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM delegated_control WHERE project=6').fetchone()
        if row['revision']!=expected_revision:raise ValueError('DELEGATED_CONTROL_STALE')
        db.execute('UPDATE delegated_control SET enabled=?,revision=revision+1 WHERE project=6',(int(enabled),))
        record={'actor':actor,'enabled':enabled,'revision':expected_revision+1,'at':time.time(),'kind':'AUTHENTICATED_OWNER_CONTROL','decision_source':POLICY}
        db.execute('INSERT INTO delegated_audit(proposal_id,stage,document) VALUES(?,?,?)',('control:'+str(expected_revision+1),'CONTROL',canonical(record)))
    return status(service,actor)


def _snapshot(item):
    return {'native_id':item['id'],'lock_version':item['lockVersion'],
            'status_id':int(item['_links']['status']['href'].rsplit('/',1)[1]),
            'description':item['description']['raw'],'description_sha256':digest(item['description']['raw'])}


def _inspect(service,args):
    rules,fingerprint=_rules(service)
    if not isinstance(args,dict) or set(args)!={'native_id','lock_version','action','value'}:raise ValueError('DELEGATED_ARGUMENTS_INVALID')
    identifier=args['native_id'];version=args['lock_version'];action=args['action'];value=args['value']
    if type(identifier) is not int or type(version) is not int or version<0 or action not in ACTIONS:raise ValueError('DELEGATED_ACTION_OR_ID_DENIED')
    fixture=rules['fixtures'].get(str(identifier))
    if fixture is None:raise PermissionError('DELEGATED_FIXTURE_NOT_REGISTERED')
    native=service.native_factory(service.config['openproject_url'],service.store.credential(rules['principal_id']),6)
    identity=native.identity(rules['principal_id']);project=native.call('/api/v3/projects/6')
    if identity.get('user_id')!=rules['principal_id'] or identity.get('role')!='PM' or identity.get('project_id')!=6 or project.get('identifier')!='ai-dev-demo' or project.get('active') is not True:
        raise PermissionError('DELEGATED_REAL_PRINCIPAL_OR_PROJECT_DENIED')
    item=native.package(identifier)
    if (item.get('id')!=identifier or item['_links']['project']['href']!='/api/v3/projects/6'
            or item['_links']['type']['href']!=f"/api/v3/types/{fixture['type_id']}"
            or fixture['marker'] not in item['subject'] or not item['description']['raw'].startswith(fixture['marker']+'\n')):
        raise PermissionError('DELEGATED_RESOURCE_IDENTITY_DENIED')
    before=_snapshot(item)
    if before['lock_version']!=version:raise ValueError('DELEGATED_SOURCE_VERSION_STALE')
    payload={'lockVersion':version}
    if action=='SET_FIXTURE_NOTE':
        if value not in ('BASELINE','CHECKED'):raise ValueError('DELEGATED_NOTE_VALUE_DENIED')
        payload['description']={'format':'markdown','raw':fixture['marker']+'\nDelegated fixture state: '+value}
        if payload['description']['raw']==before['description']:raise ValueError('DELEGATED_NO_CHANGE')
    else:
        if type(value) is not int or not item['subject'].startswith('[Bug] ') or fixture['type_id']!=1 or [before['status_id'],value] not in fixture['transitions']:
            raise ValueError('DELEGATED_BUG_TRANSITION_DENIED')
        payload['_links']={'status':{'href':f'/api/v3/statuses/{value}'}}
    form=native.call(f'/api/v3/work_packages/{identifier}/form','POST',payload)
    if form.get('_embedded',{}).get('validationErrors'):raise ValueError('DELEGATED_NATIVE_FORM_REJECTED')
    if action=='TRANSITION_FIXTURE_BUG':
        allowed=form.get('_embedded',{}).get('schema',{}).get('status',{}).get('_embedded',{}).get('allowedValues',[])
        if not any(row.get('id')==value or row.get('_links',{}).get('self',{}).get('href')==f'/api/v3/statuses/{value}' for row in allowed):raise ValueError('DELEGATED_NATIVE_STATUS_NOT_ALLOWED')
    return native,before,payload,fingerprint,rules['principal_id']


def _save(service,doc,stage,expected=None):
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT document FROM delegated_proposals WHERE id=?',(doc['id'],)).fetchone()
        if expected is not None and json.loads(row[0])['state']!=expected:raise ValueError('DELEGATED_STAGE_CONCURRENT')
        db.execute('UPDATE delegated_proposals SET document=? WHERE id=?',(canonical(doc),doc['id']))
        db.execute('INSERT OR IGNORE INTO delegated_audit(proposal_id,stage,document) VALUES(?,?,?)',(doc['id'],stage,canonical(doc)))


def _emit(service,doc,kind):
    from .integration_events import enqueue
    return enqueue(service.store,kind,'delegated:'+doc['id'],doc['hash'],correlation_id=doc['id'],
                   payload={'proposal_id':doc['id'],'native_id':doc['arguments']['native_id'],'action':doc['arguments']['action']})


def publish(service):
    setup(service.store)
    with service.store.connect() as db:rows=[json.loads(r[0]) for r in db.execute('SELECT document FROM delegated_proposals ORDER BY rowid DESC LIMIT 100')]
    for doc in rows:
        if doc['state']=='ACCEPTED':_emit(service,doc,'DELEGATED_BUG_REQUEST' if doc['arguments']['action']=='TRANSITION_FIXTURE_BUG' else 'DELEGATED_PREVIEW')
        elif doc['state']=='BUG_PREVIEWED':_emit(service,doc,'DELEGATED_PREVIEW')
        elif doc['state']=='APPROVED':_emit(service,doc,'DELEGATED_EXECUTE')
        elif doc['state']=='BUSINESS_VERIFIED' and doc['arguments']['action']=='TRANSITION_FIXTURE_BUG':_emit(service,doc,'DELEGATED_BUG_VERIFIED')


def preview(service,actor,args,key):
    _requester(service,actor);setup(service.store)
    if not isinstance(key,str) or not re.fullmatch('[A-Za-z0-9_-]{8,100}',key):raise ValueError('DELEGATED_IDEMPOTENCY_KEY_REQUIRED')
    fingerprint=digest(canonical({'actor':actor,'project_id':6,'arguments':args}))
    with service.store.connect() as db:
        existing=db.execute('SELECT * FROM delegated_proposals WHERE actor=? AND request_key=?',(actor,key)).fetchone()
    if existing:
        if existing['hash']!=fingerprint:raise ValueError('DELEGATED_IDEMPOTENCY_CONFLICT')
        return json.loads(existing['document'])
    doc={'id':str(uuid.uuid4()),'actor':actor,'project_id':6,'policy':POLICY,'arguments':args,'hash':fingerprint,
         'created':time.time(),'expires':time.time()+600,'state':'ACCEPTED','decision':None,'human_approval_claimed':False}
    try:
        _,before,payload,policy_hash,principal=_inspect(service,args)
        doc.update(before=before,payload=payload,policy_hash=policy_hash,decision_principal=principal,
                   impact='One registered Project6 fixture field; original snapshot retained for explicit compensation.')
    except (PermissionError,ValueError) as error:doc.update(state='REJECTED',decision='REJECTED',reason=str(error))
    with service.store.connect() as db:
        db.execute('INSERT OR IGNORE INTO delegated_proposals VALUES(?,?,?,?,?)',(doc['id'],actor,key,fingerprint,canonical(doc)))
        existing=db.execute('SELECT * FROM delegated_proposals WHERE actor=? AND request_key=?',(actor,key)).fetchone()
        if existing['hash']!=fingerprint:raise ValueError('DELEGATED_IDEMPOTENCY_CONFLICT')
        doc=json.loads(existing['document'])
        db.execute('INSERT OR IGNORE INTO delegated_audit(proposal_id,stage,document) VALUES(?,?,?)',(doc['id'],'PREVIEW',canonical(doc)))
    publish(service)
    return doc


def _result(doc):
    result={key:doc[key] for key in ('id','state','decision','decision_principal','execution_principal','before','after','reason','human_approval_claimed') if key in doc}
    result['source_version']=(doc.get('after') or doc.get('before') or {}).get('lock_version')
    return result


def business(service,event):
    from .engineering import scoped_service
    service=scoped_service(service,6)
    setup(service.store);identifier=event.get('payload',{}).get('proposal_id')
    with service.store.connect() as db:row=db.execute('SELECT document FROM delegated_proposals WHERE id=?',(identifier,)).fetchone()
    if not row:raise PermissionError('DELEGATED_PROPOSAL_NOT_FOUND')
    doc=json.loads(row[0]);kind=event['kind']
    from .integration_events import ROUTES
    if (event.get('project_id')!=6 or event.get('workflow')!=ROUTES.get(kind) or event.get('source_id')!='delegated:'+identifier
            or event.get('source_version')!=doc['hash'] or event.get('correlation_id')!=identifier
            or event.get('payload')!={'proposal_id':identifier,'native_id':doc['arguments']['native_id'],'action':doc['arguments']['action']}):
        raise PermissionError('DELEGATED_EVENT_BINDING_DENIED')
    if kind=='DELEGATED_BUG_VERIFIED':
        if doc['state']!='BUSINESS_VERIFIED':raise ValueError('DELEGATED_BUG_RESULT_REQUIRED')
        rules,_=_rules(service);native=service.native_factory(service.config['openproject_url'],service.store.credential(rules['principal_id']),6)
        native.identity(rules['principal_id']);current=_snapshot(native.package(doc['arguments']['native_id']))
        return {**_result(doc),'state':'BUG_NATIVE_VERIFIED' if current==doc['after'] else 'SUPERSEDED'}
    if kind=='DELEGATED_BUG_REQUEST':
        if doc['arguments']['action']!='TRANSITION_FIXTURE_BUG':raise PermissionError('DELEGATED_BUG_ACTION_REQUIRED')
        if doc['state']!='ACCEPTED':return _result(doc)
        try:
            _requester(service,doc['actor']);_inspect(service,doc['arguments'])
            doc['state']='BUG_PREVIEWED'
        except (PermissionError,ValueError) as error:doc.update(state='REJECTED',decision='REJECTED',reason=str(error))
        _save(service,doc,'BUG_PREVIEW',expected='ACCEPTED');publish(service);return _result(doc)
    if kind not in {'DELEGATED_PREVIEW','DELEGATED_EXECUTE'}:raise PermissionError('DELEGATED_EVENT_KIND_DENIED')
    if doc['state'] in TERMINAL:return _result(doc)
    if kind=='DELEGATED_PREVIEW' and doc['state']=='APPROVED':publish(service);return _result(doc)
    if doc['state']=='EXECUTING':return {**_result(doc),'state':'OUTCOME_UNKNOWN','reason':'RECONCILE_REQUIRED_NO_AUTOMATIC_REPLAY'}
    try:
        _requester(service,doc['actor'])
        try:_,current_hash=_rules(service)
        except PermissionError:current_hash=None
        with service.store.connect() as db:control=dict(db.execute('SELECT * FROM delegated_control WHERE project=6').fetchone())
        if not control['enabled'] or current_hash!=doc['policy_hash'] or doc['expires']<time.time() or kind=='DELEGATED_EXECUTE' and doc.get('control_revision')!=control['revision']:
            doc.update(state='REQUIRES_HUMAN_APPROVAL',decision='REQUIRES_HUMAN_APPROVAL',reason='POLICY_OFF_CHANGED_EXPIRED_OR_REVOKED');_save(service,doc,'BLOCKED');return _result(doc)
        native,before,payload,_,principal=_inspect(service,doc['arguments'])
        if before!=doc['before'] or payload!=doc['payload']:raise ValueError('DELEGATED_PRECONDITION_CHANGED')
        if kind=='DELEGATED_PREVIEW':
            doc.update(state='APPROVED',decision='OWNER_DELEGATED_POLICY_APPROVED',control_revision=control['revision'],approved_at=time.time())
            _save(service,doc,'DECISION',expected='BUG_PREVIEWED' if doc['arguments']['action']=='TRANSITION_FIXTURE_BUG' else 'ACCEPTED');publish(service);_notify(service,doc);return _result(doc)
        if doc['state']!='APPROVED' or doc['decision']!='OWNER_DELEGATED_POLICY_APPROVED':raise PermissionError('DELEGATED_APPROVED_DECISION_REQUIRED')
        doc.update(state='EXECUTING',execution_principal=principal)
        # Claim and policy revision share one lock; disabling blocks every subsequent claim.
        with service.store.connect() as db:
            db.execute('BEGIN IMMEDIATE');control=db.execute('SELECT * FROM delegated_control WHERE project=6').fetchone()
            saved=json.loads(db.execute('SELECT document FROM delegated_proposals WHERE id=?',(identifier,)).fetchone()[0])
            if not control['enabled'] or control['revision']!=doc['control_revision']:raise ValueError('DELEGATED_POLICY_REVOKED')
            if saved['state']!='APPROVED':raise ValueError('DELEGATED_EXECUTION_ALREADY_CLAIMED')
            db.execute('UPDATE delegated_proposals SET document=? WHERE id=?',(canonical(doc),identifier))
            db.execute('INSERT INTO delegated_audit(proposal_id,stage,document) VALUES(?,?,?)',(identifier,'EXECUTING',canonical(doc)))
    except (PermissionError,ValueError) as error:
        if str(error) in {'DELEGATED_STAGE_CONCURRENT','DELEGATED_EXECUTION_ALREADY_CLAIMED'}:
            with service.store.connect() as db:return _result(json.loads(db.execute('SELECT document FROM delegated_proposals WHERE id=?',(identifier,)).fetchone()[0]))
        doc.update(state='REJECTED',decision='REJECTED',reason=str(error));_save(service,doc,'REJECTED');_notify(service,doc);return _result(doc)
    try:
        native.call(f"/api/v3/work_packages/{doc['arguments']['native_id']}",'PATCH',payload)
        after=_snapshot(native.package(doc['arguments']['native_id']))
        expected_description=payload.get('description',{}).get('raw',before['description'])
        expected_status=doc['arguments']['value'] if doc['arguments']['action']=='TRANSITION_FIXTURE_BUG' else before['status_id']
        if after['lock_version']<=before['lock_version'] or after['description']!=expected_description or after['status_id']!=expected_status:raise ValueError('DELEGATED_NATIVE_READBACK_MISMATCH')
        doc.update(state='BUSINESS_VERIFIED',after=after,verified_at=time.time())
    except Exception as error:
        doc.update(state='OUTCOME_UNKNOWN',reason='NATIVE_WRITE_OR_READBACK_'+type(error).__name__)
    _save(service,doc,'RESULT',expected='EXECUTING');publish(service);_notify(service,doc)
    return _result(doc)


def _notify(service,doc):
    from .engineering_observability import notification
    notification(service,'delegated:'+doc['id']+':'+doc['state'],'DELEGATED_'+doc['state'],native_id=doc['arguments']['native_id'],
                 extra={'proposal_id':doc['id'],'decision':doc['decision'],'principal_id':doc.get('execution_principal',doc.get('decision_principal')),
                        'human_approval_claimed':False},message='Project6 delegated policy: '+doc['state']+'; decision '+str(doc['decision']))
    if doc['state']=='BUSINESS_VERIFIED':
        identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,'qldapm-delegated-report:'+doc['id']))
        report={'id':identifier,'project_id':6,'report_type':'WORKFLOW_AUDIT','title':'Project6 delegated Native read-back',
                'generated_at':time.time(),'facts':_result(doc),'narrative':None,'narrative_status':'NOT_REQUESTED',
                'provenance':{'policy':POLICY,'proposal_hash':doc['hash'],'principal_id':doc['execution_principal'],
                              'native_id':doc['arguments']['native_id'],'lock_version':doc['after']['lock_version']}}
        with service.store.connect() as db:
            db.execute('INSERT OR IGNORE INTO engineering_reports VALUES(?,6,?,?,?,?)',
                       (identifier,'WORKFLOW_AUDIT',report['title'],canonical(report),report['generated_at']))

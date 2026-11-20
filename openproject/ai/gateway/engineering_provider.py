"""Claim-bound per-request provider admission using the existing shared project ledger."""
import hmac
import json
import math
import re
import time
import uuid

from .store import canonical, digest
from .engineering_fencing import bound, ensure_current

PATH='/internal/engineering/provider'
HEADER='x-qldapm-provider-token'

def effective_policy(service):
    policy=dict(service.gemini.settings())
    if policy.get('model')!='gemini-3.5-flash-lite':raise ValueError('ENGINEERING_PROVIDER_POLICY_CHANGED')
    configured=service.config.get('engineering',{}).get('provider_limits',{})
    if not isinstance(configured,dict) or set(configured)-{'rpm','tpm','rpd'}:raise ValueError('ENGINEERING_PROVIDER_LIMIT_INVALID')
    limits=dict(policy['limits'])
    for key,value in configured.items():
        if type(value) is not int or value<1 or value>limits[key]:raise ValueError('ENGINEERING_PROVIDER_LIMIT_INVALID')
        limits[key]=value
    return {**policy,'limits':limits}

def setup(db):
    db.execute('CREATE TABLE IF NOT EXISTS engineering_provider_requests(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,hash TEXT NOT NULL,document TEXT NOT NULL)')

def operate(service,document):
    if not isinstance(document,dict) or set(document)!={'action','claim','session_id','step','request_id','details'}:raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
    action,claim,details=document['action'],document['claim'],document['details']
    if not isinstance(claim,dict) or set(claim)!={'run_id','worker_id','claim_token'} or not isinstance(details,dict):raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
    for key in ['session_id','request_id']:
        if not isinstance(document[key],str) or str(uuid.UUID(document[key]))!=document[key]:raise ValueError('ENGINEERING_PROVIDER_ID_INVALID')
    if not isinstance(action,str) or action not in {'reserve','settle','status'} or not isinstance(document['step'],str) or not re.fullmatch(r'(?:dev|rework|review|qa)-[0-9]{1,3}',document['step']):raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
    with bound(claim,service.store):
        if action=='settle':
            from .engineering_fencing import check
            check(service.store,claim)
        else:ensure_current()
        policy=effective_policy(service) if action!='settle' else None
        if action=='status':
            if details:raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
            waiting=service.store.provider_wait(policy)
            return {'state':('BLOCKED_KEY_OR_MODEL' if waiting.get('queue_state')=='BLOCKED_KEY_OR_MODEL' else 'WAITING_FOR_PROVIDER' if waiting.get('queue_state')=='WAITING_PROVIDER' else 'WAITING_FOR_QUOTA') if waiting else 'ADMISSIBLE','retry_at':(waiting or {}).get('retry_at'),'limits':policy['limits']}
        rid=document['request_id']
        identity={k:document[k] for k in ['claim','session_id','step','request_id']}
        if action=='reserve':
            if set(details)!={'request_sha256','input_token_bound','phase'} or details['phase'] not in {'generateContent','streamGenerateContent','countTokens'}:raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
            tokens=details['input_token_bound']
            if type(tokens) is not int or not 1<=tokens<=265144 or not isinstance(details['request_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',details['request_sha256']):raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
            fingerprint=digest(canonical({**identity,**details}))
            from .engineering_observability import policy as continuation_policy
            caps=continuation_policy(service)
            if tokens>policy['limits']['tpm']:raise ValueError('ENGINEERING_PROVIDER_CONTEXT_LIMIT')
            with service.store.connect() as db:
                db.execute('BEGIN IMMEDIATE');setup(db)
                row=db.execute('SELECT hash,document FROM engineering_provider_requests WHERE id=?',(rid,)).fetchone()
                if row:
                    if row['hash']!=fingerprint:raise ValueError('ENGINEERING_PROVIDER_REQUEST_CONFLICT')
                    if json.loads(row['document'])['state']=='PENDING':raise ValueError('ENGINEERING_PROVIDER_RESERVATION_UNKNOWN')
                    return json.loads(row['document'])
                completed=[json.loads(r[0]) for r in db.execute("SELECT document FROM gemini_call_receipts WHERE run_id=?",(claim['run_id'],))]
                outstanding=[json.loads(r[0]) for r in db.execute("SELECT document FROM engineering_provider_requests WHERE run_id=?",(claim['run_id'],))]
                outstanding=[r for r in outstanding if r.get('state') in {'RESERVED','PENDING'}]
                session_used=sum(r.get('session_id')==document['session_id'] for r in completed+outstanding)
                total_used=sum(r.get('phase')=='generateContent' for r in completed)+sum(r.get('phase')!='countTokens' for r in outstanding)
                session_cap=min(caps['attempt_calls'],caps['task_calls']-total_used+sum(r.get('session_id')==document['session_id'] and r.get('phase')!='countTokens' for r in completed+outstanding))
                if total_used>=caps['task_calls']:raise ValueError('ENGINEERING_CUMULATIVE_BUDGET_EXHAUSTED')
                if session_used>=session_cap:raise ValueError('ENGINEERING_PROVIDER_ATTEMPT_BUDGET_EXHAUSTED')
                pending={'state':'PENDING','session_id':document['session_id'],'step':document['step'],'phase':details['phase'],'model':policy['model'],'call_cap':session_cap}
                db.execute('INSERT INTO engineering_provider_requests VALUES(?,?,?,?)',(rid,claim['run_id'],fingerprint,canonical(pending)))
            try:
                reservation=service.store.reserve_gemini(policy['project'],policy['limits'],tokens)
            except ValueError as error:
                waiting=service.store.provider_wait(policy) or {}
                waiting_result={'state':'BLOCKED_KEY_OR_MODEL' if waiting.get('queue_state')=='BLOCKED_KEY_OR_MODEL' else 'WAITING_FOR_PROVIDER' if waiting.get('queue_state')=='WAITING_PROVIDER' else 'WAITING_FOR_QUOTA','reason':str(error).split(';')[0],'retry_at':getattr(error,'retry_at',None) or waiting.get('retry_at'),'limits':policy['limits']}
                with service.store.connect() as db:db.execute('UPDATE engineering_provider_requests SET document=? WHERE id=?',(canonical(waiting_result),rid))
                service.store.progress_run(20,claim['run_id'],{'status':'running','stage':'WAITING_FOR_QUOTA','text':'Đang chờ quota Project; chưa gửi request model.','retry_at':waiting_result['retry_at']})
                return waiting_result
            receipt={'state':'RESERVED','reservation':reservation,'project':policy['project'],'limits':policy['limits'],
                     'session_id':document['session_id'],'step':document['step'],'phase':details['phase'],'model':policy['model'],
                     'request_sha256':details['request_sha256'],'input_token_bound':tokens,'call_cap':session_cap,'claim_sha256':digest(canonical(claim)),'at':time.time()}
            with service.store.connect() as db:
                db.execute('UPDATE engineering_provider_requests SET document=? WHERE id=?',(canonical(receipt),rid))
            ensure_current()
            return receipt
        if set(details)!={'http_status','usage','started','finished','retry_after','call_cap'}:raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
        if type(details['http_status']) is not int or details['http_status'] not in range(0,600) or type(details['call_cap']) is not int or not 1<=details['call_cap']<=12:raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
        with service.store.connect() as db:
            setup(db)
            row=db.execute('SELECT document FROM engineering_provider_requests WHERE id=? AND run_id=?',(rid,claim['run_id'])).fetchone()
        if not row:raise ValueError('ENGINEERING_PROVIDER_RESERVATION_REQUIRED')
        saved=json.loads(row['document'])
        if saved.get('state') not in {'RESERVED','SETTLED'}:raise ValueError('ENGINEERING_PROVIDER_RESERVATION_REQUIRED')
        if saved.get('claim_sha256')!=digest(canonical(claim)) or saved.get('session_id')!=document['session_id'] or saved['step']!=document['step']:raise ValueError('ENGINEERING_PROVIDER_REQUEST_CONFLICT')
        if saved['state']=='SETTLED':return saved
        usage=details['usage'] or {}
        if any(type(details[key]) not in (int,float) or not math.isfinite(details[key]) or details[key]<0 for key in ['started','finished']):raise ValueError('ENGINEERING_PROVIDER_TIME_INVALID')
        if not isinstance(usage,dict) or any(type(v) is not int or v<0 for k,v in usage.items() if k in {'promptTokenCount','candidatesTokenCount','totalTokenCount'}):raise ValueError('ENGINEERING_PROVIDER_USAGE_INVALID')
        usage={k:v for k,v in usage.items() if k in {'promptTokenCount','candidatesTokenCount','totalTokenCount'}}
        if details['finished']<details['started']:raise ValueError('ENGINEERING_PROVIDER_TIME_INVALID')
        status=details['http_status'];retry=details['retry_after']
        if retry is not None and (type(retry) not in (int,float) or not math.isfinite(retry) or not 0<=retry<=86400):raise ValueError('ENGINEERING_PROVIDER_RETRY_INVALID')
        if 'totalTokenCount' in usage:service.store.settle_gemini_input(saved['reservation'],saved['project'],usage['totalTokenCount'])
        if status==429:service.store.block_gemini(saved['project'],'GEMINI_QUOTA_429',max(60,retry or 60))
        elif status in {401,403}:service.store.block_gemini(saved['project'],'GEMINI_AUTH_FAILED')
        elif status in {0,408,500,502,503,504}:service.store.block_gemini(saved['project'],'GEMINI_TEMPORARILY_UNAVAILABLE',max(60,retry or 60))
        receipt={'id':rid,'actor':20,'run_id':claim['run_id'],'project':saved['project'],'provider':'google','model':saved['model'],
            'agent':'reviewer' if document['step'].startswith('review') else 'qa' if document['step'].startswith('qa') else 'dev',
            'phase':'countTokens' if saved['phase']=='countTokens' else 'generateContent','session_id':document['session_id'],'step':document['step'],
            'request_sha256':saved['request_sha256'],'source':'openclaw-gate-per-request','http_status':status,'usage':usage,
            'state':'LIVE_SUCCESS' if status==200 else 'PROVIDER_ERROR','at':details['started'],'completed_at':details['finished'],'call_cap':saved.get('call_cap',details['call_cap']),
            'input_token_bound':saved['input_token_bound'],'usage_source':'PROVIDER_RECEIPT' if usage else 'BYTE_UPPER_BOUND_RESERVATION',
            'retry_after_seconds':retry}
        service.store.provider_receipt(receipt)
        settled={**saved,'state':'SETTLED','http_status':status}
        with service.store.connect() as db:db.execute('UPDATE engineering_provider_requests SET document=? WHERE id=?',(canonical(settled),rid))
        return settled

def response(service,root,scope,headers,body):
    from starlette.responses import JSONResponse
    try:
        token=(root/'engineering-provider-token').read_text().strip()
        if len(token)<32 or not hmac.compare_digest(token,headers.get(HEADER,'')) or scope['method']!='POST' or scope.get('query_string') or headers.get('authorization') or headers.get('origin'):raise PermissionError('ENGINEERING_PROVIDER_AUTH_DENIED')
        from .engineering import scoped_service
        result=operate(scoped_service(service,6),json.loads(body))
        return JSONResponse(result,status_code=429 if result.get('state') in {'WAITING_FOR_QUOTA','WAITING_FOR_PROVIDER'} else 403 if result.get('state')=='BLOCKED_KEY_OR_MODEL' else 200)
    except (ValueError,KeyError,TypeError,PermissionError,OSError) as error:
        code=str(error).split(';')[0]
        if not code.replace('_','').isalnum():code='ENGINEERING_PROVIDER_DENIED'
        return JSONResponse({'error':code},status_code=403)

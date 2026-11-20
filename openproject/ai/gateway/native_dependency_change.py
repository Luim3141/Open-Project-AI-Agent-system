"""Exact approved changes to an existing follows relation; never deletes a Work Package."""
import hashlib
import hmac
import re
import time

from .native import NativeError
from .permissions import business_manager
from .store import canonical, digest

ACTIONS={'update_dependency':'update','delete_dependency':'delete'}


def arguments(service,args,action,sealed=False):
    if action not in ACTIONS:raise ValueError('DEPENDENCY_CHANGE_ACTION_INVALID')
    fields={'relation_id'} | ({'lag'} if action=='update_dependency' else set())
    if sealed:fields|={'scope_hash','predecessor_id','successor_id'}
    service.keys(args,fields,fields)
    ids=['relation_id']+(['predecessor_id','successor_id'] if sealed else [])
    if any(type(args[key]) is not int or args[key]<=0 for key in ids):raise ValueError('DEPENDENCY_CHANGE_IDS_INVALID')
    if action=='update_dependency' and (type(args['lag']) is not int or not -2000<=args['lag']<=2000):raise ValueError('DEPENDENCY_LAG_INVALID')
    if sealed and (args['predecessor_id']==args['successor_id'] or not isinstance(args['scope_hash'],str) or not re.fullmatch('[a-f0-9]{64}',args['scope_hash'])):raise ValueError('DEPENDENCY_CHANGE_SCOPE_INVALID')


def preview(service,who,native,args,action):
    if service.mode!='native' or service.config['project_id']!=5 or not business_manager(who['role']):raise PermissionError('DEPENDENCY_NATIVE_MAIN_MANAGER_REQUIRED')
    payload={key:args[key] for key in ['relation_id','lag'] if key in args}|{'operation':ACTIONS[action]}
    result=native.call('/api/v3/qldapm/dependency_change_forms','POST',payload)
    if (result.get('project_id')!=5 or result.get('operation')!=payload['operation'] or result.get('relation_id')!=args['relation_id'] or
            action=='update_dependency' and result.get('lag')!=args['lag'] or
            not isinstance(result.get('scope_hash'),str) or not re.fullmatch('[a-f0-9]{64}',result['scope_hash']) or
            not isinstance(result.get('before'),dict) or 'lag' not in result['before'] or 'lag' not in result or
            result['before']['lag'] is not None and (type(result['before']['lag']) is not int or not -2000<=result['before']['lag']<=2000) or
            action=='delete_dependency' and result['lag']!=result['before']['lag']):raise NativeError(502,'DEPENDENCY_CHANGE_NATIVE_PREVIEW_INVALID')
    endpoints=[result.get(key) for key in ['predecessor_id','successor_id']]
    rows=result.get('possible_affected');ids=[row.get('id') for row in rows] if isinstance(rows,list) and all(isinstance(row,dict) for row in rows) else []
    if (any(type(identifier) is not int or identifier<=0 for identifier in endpoints+ids) or endpoints[0]==endpoints[1] or
            not 2<=len(ids)<=2000 or len(set(ids))!=len(ids) or not set(endpoints)<=set(ids) or
            any(type(row.get('lockVersion')) is not int or row['lockVersion']<0 for row in rows)):raise NativeError(502,'DEPENDENCY_CHANGE_NATIVE_SCOPE_INVALID')
    return result


def authorization(service,actor,args,key,states=('executing',)):
    if not isinstance(key,str) or not re.fullmatch(r'proposal-[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}',key):raise PermissionError('DEPENDENCY_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    proposal=service.store.proposal(actor,key[9:]);command=proposal['command']
    if (proposal['state'] not in states or command.get('action') not in ACTIONS or command.get('arguments')!=args or
            command.get('_gateway_mode')!='native' or digest(canonical({'actor':actor,'command':command}))!=proposal['hash']):raise PermissionError('DEPENDENCY_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    return proposal


def readback(native,result,args,actor,proposal):
    operation=ACTIONS[proposal['command']['action']];marker='QLDAPM-request-'+digest(f'{actor}:proposal-{proposal["id"]}');relation=result.get('relation',{})
    expected={'id':args['relation_id'],'type':'follows','predecessor_id':args['predecessor_id'],'successor_id':args['successor_id'],'lag':proposal['command']['preview']['lag']}
    if (result.get('id')!=args['successor_id'] or result.get('request_id')!=marker or result.get('provenance')!='ai_gateway' or
            result.get('proposal_id')!=proposal['id'] or result.get('proposal_hash')!=proposal['hash'] or result.get('scope_hash')!=args['scope_hash'] or
            result.get('operation')!=operation or any(relation.get(key)!=value for key,value in expected.items())):raise NativeError(409,'DEPENDENCY_CHANGE_RECEIPT_MISMATCH_HOLD')
    allowed={row['id'] for row in proposal['command']['preview']['possible_affected']};changed=result.get('changed_ids');rows=result.get('readback')
    if (not isinstance(changed,list) or any(type(identifier) is not int or identifier not in allowed for identifier in changed) or
            len(set(changed))!=len(changed) or not isinstance(rows,list) or not all(isinstance(row,dict) for row in rows)):raise NativeError(409,'DEPENDENCY_CHANGE_RECEIPT_SCOPE_HOLD')
    ids=[row.get('id') for row in rows]
    if any(type(identifier) is not int for identifier in ids) or len(set(ids))!=len(ids) or set(ids)!=set(changed)|{args['predecessor_id'],args['successor_id']}:raise NativeError(409,'DEPENDENCY_CHANGE_READBACK_SCOPE_HOLD')
    try:current=native.call('/api/v3/relations/'+str(args['relation_id']))
    except NativeError as error:
        if operation!='delete' or error.status!=404:raise
        current=None
    if operation=='delete':
        # Absence alone is insufficient: the exact durable Core commit receipt was checked above.
        if current is not None:raise NativeError(409,'DEPENDENCY_CHANGE_RELATION_STILL_PRESENT_HOLD')
    elif (current.get('type')!='follows' or current.get('lag')!=args['lag'] or any(current.get('_links',{}).get(key,{}).get('href')!=f'/api/v3/work_packages/{args[field]}' for key,field in [('from','successor_id'),('to','predecessor_id')])):raise NativeError(409,'DEPENDENCY_CHANGE_RELATION_CHANGED_HOLD')
    for row in rows:
        item=native.package(row['id'])
        if any(item.get(key)!=value for key,value in row.items()):raise NativeError(409,'DEPENDENCY_CHANGE_SOURCE_CHANGED_HOLD')
    return result


def execute(service,who,native,args,key,action):
    arguments(service,args,action,sealed=True);proposal=authorization(service,who['user_id'],args,key)
    if proposal['command']['action']!=action:raise PermissionError('DEPENDENCY_CHANGE_ACTION_BINDING_REQUIRED')
    current=preview(service,who,native,args,action)
    if current['scope_hash']!=args['scope_hash'] or any(current[field]!=args[field] for field in ['predecessor_id','successor_id']):raise NativeError(409,'DEPENDENCY_STALE_APPROVED_SCOPE')
    payload={**args,'operation':ACTIONS[action],'proposal_id':proposal['id'],'proposal_hash':proposal['hash'],'request_id':'QLDAPM-request-'+digest(f'{who["user_id"]}:{key}')};at=int(time.time())
    native.mutation_headers={'X-Qldapm-At':str(at),'X-Qldapm-Mutation':hmac.new((service.store.root/'ui.key').read_bytes(),f'{who["user_id"]}:{at}:{digest(canonical(payload))}'.encode(),hashlib.sha256).hexdigest()}
    result=native.call('/api/v3/qldapm/dependency_changes','POST',payload)
    try:return readback(native,result,args,who['user_id'],proposal)
    except (NativeError,KeyError,TypeError,ValueError):raise NativeError(503,'DEPENDENCY_CHANGE_READBACK_OUTCOME_UNKNOWN; inspect receipt, never replay') from None


def reconcile(service,who,native,args,key):
    if service.mode!='native' or not business_manager(who['role']):raise PermissionError('DEPENDENCY_NATIVE_MANAGER_REQUIRED')
    proposal=authorization(service,who['user_id'],args,key,states=('executing','failed_or_unknown'));arguments(service,args,proposal['command']['action'],sealed=True)
    marker='QLDAPM-request-'+digest(f'{who["user_id"]}:{key}')
    try:result=native.call('/api/v3/qldapm/mutation_receipts/'+marker)
    except NativeError as error:
        if error.status==404:return None
        raise
    return readback(native,result,args,who['user_id'],proposal)

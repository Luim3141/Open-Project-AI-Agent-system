"""Exact approved Native dependency with bounded derived scope and receipt readback."""
import hashlib
import hmac
import re
import time

from .native import NativeError
from .permissions import business_manager
from .store import canonical, digest


def arguments(service, args, sealed=False):
    fields = {'predecessor_id','successor_id','lag'} | ({'scope_hash'} if sealed else set())
    service.keys(args, fields, fields)
    if (any(type(args[k]) is not int or args[k] <= 0 for k in ['predecessor_id','successor_id']) or
            args['predecessor_id'] == args['successor_id'] or type(args['lag']) is not int or not -2000 <= args['lag'] <= 2000):
        raise ValueError('DEPENDENCY_IDS_OR_LAG_INVALID')
    if sealed and (not isinstance(args['scope_hash'],str) or not re.fullmatch('[a-f0-9]{64}',args['scope_hash'])):
        raise ValueError('DEPENDENCY_SCOPE_HASH_INVALID')


def preview(service, who, native, args):
    if service.mode != 'native' or service.config['project_id'] != 5 or not business_manager(who['role']):
        raise PermissionError('DEPENDENCY_NATIVE_MAIN_MANAGER_REQUIRED')
    result = native.call('/api/v3/qldapm/dependency_forms','POST',{k:args[k] for k in ['predecessor_id','successor_id','lag']})
    if (result.get('project_id') != 5 or result.get('type') != 'follows' or
            any(result.get(k) != args[k] for k in ['predecessor_id','successor_id','lag']) or
            not isinstance(result.get('scope_hash'),str) or not re.fullmatch('[a-f0-9]{64}',result['scope_hash']) or
            not isinstance(result.get('possible_affected'),list) or not 2 <= len(result['possible_affected']) <= 2000):
        raise NativeError(502,'DEPENDENCY_NATIVE_PREVIEW_INVALID')
    ids = [r.get('id') for r in result['possible_affected']]
    if (any(type(i) is not int or i <= 0 for i in ids) or len(ids) != len(set(ids)) or
            not {args['predecessor_id'],args['successor_id']} <= set(ids) or
            any(type(r.get('lockVersion')) is not int or r['lockVersion'] < 0 for r in result['possible_affected'])):
        raise NativeError(502,'DEPENDENCY_NATIVE_SCOPE_INVALID')
    return result


def authorization(service, actor, args, request_key, states=('executing',)):
    if not isinstance(request_key,str) or not re.fullmatch(r'proposal-[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}',request_key):
        raise PermissionError('DEPENDENCY_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    proposal = service.store.proposal(actor,request_key[9:])
    if (proposal['state'] not in states or proposal['command'].get('action') != 'create_dependency' or
            proposal['command'].get('arguments') != args or proposal['command'].get('_gateway_mode') != 'native' or
            digest(canonical({'actor':actor,'command':proposal['command']})) != proposal['hash']):
        raise PermissionError('DEPENDENCY_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    return proposal


def readback(native, result, args, actor, proposal):
    marker = 'QLDAPM-request-'+digest(f'{actor}:proposal-{proposal["id"]}')
    relation = {'type':'follows','predecessor_id':args['predecessor_id'],'successor_id':args['successor_id'],'lag':args['lag']}
    preview_ids = {r['id'] for r in proposal['command']['preview']['possible_affected']}
    if (result.get('id') != args['successor_id'] or result.get('request_id') != marker or result.get('provenance') != 'ai_gateway' or
            result.get('proposal_id') != proposal['id'] or result.get('proposal_hash') != proposal['hash'] or
            result.get('scope_hash') != args['scope_hash'] or
            any(result.get('relation',{}).get(k) != v for k,v in relation.items())):
        raise NativeError(409,'DEPENDENCY_NATIVE_RECEIPT_MISMATCH_HOLD')
    identifier = result['relation'].get('id')
    rows = result.get('readback'); changed = result.get('changed_ids')
    if (type(identifier) is not int or identifier <= 0 or not isinstance(rows,list) or not isinstance(changed,list) or
            any(type(i) is not int or i not in preview_ids for i in changed) or len(changed) != len(set(changed))):
        raise NativeError(409,'DEPENDENCY_NATIVE_RECEIPT_SCOPE_MISMATCH_HOLD')
    ids = [r.get('id') for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(changed) | {args['predecessor_id'],args['successor_id']}:
        raise NativeError(409,'DEPENDENCY_NATIVE_READBACK_SCOPE_MISMATCH_HOLD')
    current = native.call('/api/v3/relations/'+str(identifier))
    if (current.get('type') != 'follows' or current.get('lag') != args['lag'] or
            any(current.get('_links',{}).get(key,{}).get('href') != f'/api/v3/work_packages/{args[field]}'
                for key,field in [('from','successor_id'),('to','predecessor_id')])):
        raise NativeError(409,'DEPENDENCY_NATIVE_RELATION_CHANGED_HOLD')
    for row in rows:
        item = native.package(row['id'])
        if any(item.get(k) != v for k,v in row.items()):
            raise NativeError(409,'DEPENDENCY_NATIVE_SOURCE_CHANGED_HOLD')
    return result


def execute(service, who, native, args, request_key):
    arguments(service,args,sealed=True)
    proposal = authorization(service,who['user_id'],args,request_key)
    current = preview(service,who,native,args)
    if current['scope_hash'] != args['scope_hash']:
        raise NativeError(409,'DEPENDENCY_STALE_APPROVED_SCOPE')
    payload = {**args,'proposal_id':proposal['id'],'proposal_hash':proposal['hash'],
               'request_id':'QLDAPM-request-'+digest(f'{who["user_id"]}:{request_key}')}
    at = int(time.time())
    native.mutation_headers = {'X-Qldapm-At':str(at),'X-Qldapm-Mutation':hmac.new((service.store.root/'ui.key').read_bytes(),
        f'{who["user_id"]}:{at}:{digest(canonical(payload))}'.encode(),hashlib.sha256).hexdigest()}
    result = native.call('/api/v3/qldapm/dependencies','POST',payload)
    try:
        return readback(native,result,args,who['user_id'],proposal)
    except (NativeError,KeyError,TypeError,ValueError):
        raise NativeError(503,'DEPENDENCY_NATIVE_READBACK_OUTCOME_UNKNOWN; inspect exact receipt, never replay') from None


def reconcile(service, who, native, args, request_key):
    if service.mode != 'native' or not business_manager(who['role']):
        raise PermissionError('DEPENDENCY_NATIVE_MANAGER_REQUIRED')
    arguments(service,args,sealed=True)
    proposal = authorization(service,who['user_id'],args,request_key,states=('executing','failed_or_unknown'))
    marker = 'QLDAPM-request-'+digest(f'{who["user_id"]}:{request_key}')
    try:
        result = native.call('/api/v3/qldapm/mutation_receipts/'+marker)
    except NativeError as error:
        if error.status == 404:
            return None
        raise
    return readback(native,result,args,who['user_id'],proposal)

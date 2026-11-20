"""An accepted source review is input to a separately claimed exact Native proposal."""
import hashlib
import hmac
import re
import time

from .native import NativeError
from .native_phase import packet
from .store import canonical,digest


def preflight(service,who,native,item,args):
    if not all(k in args for k in ['phase_id','phase_hash']) or {'qa_evidence_id','qa_evidence_hash'} & args.keys():raise ValueError('ONE_COMPLETE_NATIVE_PROOF_DOMAIN_REQUIRED')
    capability=native.call('/api/v3/qldapm/capabilities')
    if type(capability.get('native_phase_bridge_version')) is not int or capability.get('native_phase_bridge_version')!=1 or capability.get('project_id')!=5 or capability.get('enforced') is not True:raise NativeError(422,'NATIVE_PHASE_BRIDGE_UNSUPPORTED')
    if not isinstance(args['phase_hash'],str) or not re.fullmatch('[a-f0-9]{64}',args['phase_hash']):raise ValueError('PHASE_EXACT_HASH_REQUIRED')
    proof=packet(service,who['user_id'],args['phase_id'])
    result=native.call('/api/v3/qldapm/phase_transition_forms','POST',{'id':item['id'],'lock_version':item['lockVersion'],'status_id':args['status_id'],'phase_proof':proof})
    if (result.get('valid') is not True or result.get('id')!=args['phase_id'] or result.get('hash')!=args['phase_hash'] or
            result.get('lockVersion')!=item['lockVersion'] or result.get('status_id')!=args['status_id']):raise NativeError(409,'PHASE_NATIVE_PREFLIGHT_CHANGED')
    return proof


def authorization(service,actor,args,key):
    if not isinstance(key,str) or not key.startswith('proposal-'):raise PermissionError('PHASE_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    p=service.store.proposal(actor,key[9:])
    if (p['state']!='executing' or p['hash']!=digest(canonical({'actor':actor,'command':p['command']})) or
            p['command'].get('action')!='transition' or p['command'].get('_gateway_mode')!='native' or p['command'].get('arguments')!=args):raise PermissionError('PHASE_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    return {'proposal_id':p['id'],'proposal_hash':p['hash'],'phase_id':args['phase_id'],'phase_hash':args['phase_hash']}


def readback(native,actor,item,args,key,result,approved):
    marker='QLDAPM-request-'+digest(f'{actor}:{key}');summary=result.get('phase_native',{})
    expected={'id':args['phase_id'],'hash':args['phase_hash'],'source_version':args['lock_version'],
        'status_id':args['status_id'],'proposal_id':approved['proposal_id'],'proposal_hash':approved['proposal_hash']}
    current=native.package(item['id'])
    gate=native.call('/api/v3/qldapm/gates/'+str(item['id']))['gate']
    event={'actor_id':actor,'request_id':marker,'proposal_id':approved['proposal_id'],'proposal_hash':approved['proposal_hash'],
        'phase_id':args['phase_id'],'phase_hash':args['phase_hash']}
    if (result.get('id')!=item['id'] or result.get('request_id')!=marker or result.get('provenance')!='ai_gateway' or
            result.get('lockVersion')!=current['lockVersion'] or current['lockVersion']<=args['lock_version'] or
            current.get('_links',{}).get('status',{}).get('href')!='/api/v3/statuses/'+str(args['status_id']) or
            any(summary.get(k)!=v for k,v in expected.items()) or not any(all(row.get(k)==v for k,v in event.items()) for row in gate.get('events',[]))):
        raise NativeError(409,'PHASE_NATIVE_RECEIPT_READBACK_HOLD')
    return {**current,'phase_native':summary,'native_receipt_request_id':marker}


def execute(service,actor,native,item,args,key,proof=None):
    approved=authorization(service,actor,args,key)
    proof=proof or preflight(service,{'user_id':actor},native,item,args)
    marker='QLDAPM-request-'+digest(f'{actor}:{key}')
    payload={'id':item['id'],'action':'transition','lock_version':item['lockVersion'],'status_id':args['status_id'],
        'request_id':marker,'phase_proof':proof,'phase_authorization':approved}
    at=int(time.time());secret=(service.store.root/'ui.key').read_bytes()
    native.mutation_headers={'X-Qldapm-At':str(at),'X-Qldapm-Mutation':hmac.new(secret,f'{actor}:{at}:{digest(canonical(payload))}'.encode(),hashlib.sha256).hexdigest()}
    result=native.call('/api/v3/qldapm/mutations','POST',payload)
    try:return readback(native,actor,item,args,key,result,approved)
    except (NativeError,ValueError,KeyError,TypeError):raise NativeError(503,'PHASE_NATIVE_READBACK_OUTCOME_UNKNOWN; reconcile own receipt, never replay') from None


def reconcile(service,native,actor,key,args):
    if not {'phase_id','phase_hash'}<=args.keys():return None
    if not isinstance(key,str) or not key.startswith('proposal-'):raise PermissionError('PHASE_PROPOSAL_RECEIPT_REQUIRED')
    p=service.store.proposal(actor,key[9:])
    if p['command'].get('arguments')!=args or p['command'].get('action')!='transition' or p['hash']!=digest(canonical({'actor':actor,'command':p['command']})):
        raise PermissionError('PHASE_EXACT_STORED_PROPOSAL_REQUIRED')
    marker='QLDAPM-request-'+digest(f'{actor}:{key}')
    try:result=native.call('/api/v3/qldapm/mutation_receipts/'+marker)
    except NativeError as error:
        if error.status==404:return None
        raise
    return readback(native,actor,{'id':args['id']},args,key,result,{'proposal_id':p['id'],'proposal_hash':p['hash']})

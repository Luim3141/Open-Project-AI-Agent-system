"""Internal signed QA proof, distinct from the separately approved Native mutation."""
import json
import hashlib
import hmac
import re
import time

from .native import NativeError
from .native_qa import AUTOMATED_KINDS, read
from .permissions import business_manager
from .store import canonical,digest


def signed_bundle(document):
    body=json.loads(document);signature=body.pop('signature')
    return {'document':canonical(body),'signature':signature}


def packet(service, actor, identifier):
    native,who=service.native_actor(actor)
    if not business_manager(who['role']):raise PermissionError('QA_BRIDGE_NATIVE_MANAGER_REQUIRED')
    evidence=read(service,who,native,identifier)
    if evidence['verification_kind'] not in AUTOMATED_KINDS or not evidence['ready']:
        raise NativeError(409,'QA_CURRENT_ACCEPTED_AUTOMATED_EVIDENCE_REQUIRED')
    with service.store.connect() as db:
        row=db.execute('SELECT document,hash,state FROM qa_evidence WHERE id=? AND project=?',
            (identifier,service.config['project_id'])).fetchone()
        run=db.execute('SELECT document FROM qa_test_runs WHERE id=? AND project=?',
            (evidence['run_id'],service.config['project_id'])).fetchone()
        reviews={r['stage']:r['document'] for r in db.execute('SELECT stage,document FROM qa_evidence_reviews WHERE evidence=?',(identifier,))}
    if row is None or run is None or row['state']!='accepted' or row['hash']!=evidence['hash'] or digest(row['document'])!=evidence['hash']:
        raise NativeError(409,'QA_BRIDGE_EVIDENCE_CHANGED')
    result={'version':1,'run':signed_bundle(run['document']),'evidence_document':row['document'],
            'reviews':[signed_bundle(reviews[stage]) for stage in ['qa','manager']]}
    if len(canonical(result).encode())>1_048_576:raise ValueError('QA_BRIDGE_PROOF_TOO_LARGE')
    return result


def preflight(service, who, native, item, args):
    capabilities=native.call('/api/v3/qldapm/capabilities')
    version=capabilities.get('qa_bridge_version',0)
    if type(version) is not int:raise NativeError(502,'QA_NATIVE_CAPABILITY_INVALID')
    if version==0:
        if read(service,who,native,args['qa_evidence_id'])['verification_kind']=='AUTOMATED_APPLICATION_WBS':
            raise NativeError(422,'APPLICATION_QA_NATIVE_TRANSITION_NOT_IMPLEMENTED')
        return None
    if version!=1 or capabilities.get('project_id')!=5 or capabilities.get('enforced') is not True:
        raise NativeError(502,'QA_NATIVE_CAPABILITY_INVALID')
    proof=packet(service,who['user_id'],args['qa_evidence_id'])
    result=native.call('/api/v3/qldapm/qa_transition_forms','POST',{'id':item['id'],'lock_version':item['lockVersion'],
        'status_id':args['status_id'],'qa_proof':proof})
    if result.get('valid') is not True:raise NativeError(422,'QA_NATIVE_GATE_REJECTED',result.get('errors',[]))
    if (result.get('lockVersion')!=item['lockVersion'] or result.get('qa_evidence_id')!=args['qa_evidence_id'] or
            result.get('hash')!=args['qa_evidence_hash']):raise NativeError(409,'QA_NATIVE_PREFLIGHT_SOURCE_CHANGED')
    return proof


def authorization(service, actor, args, request_key):
    if not isinstance(request_key,str) or not re.fullmatch(r'proposal-[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}',request_key):
        raise PermissionError('QA_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    proposal=service.store.proposal(actor,request_key[9:])
    if (proposal['state']!='executing' or proposal['command'].get('action')!='transition' or
            digest(canonical({'actor':actor,'command':proposal['command']}))!=proposal['hash'] or
            proposal['command'].get('arguments')!=args or proposal['command'].get('_gateway_mode')!='native'):
        raise PermissionError('QA_EXACT_CLAIMED_PROPOSAL_REQUIRED')
    return {'proposal_id':proposal['id'],'proposal_hash':proposal['hash'],
            'qa_evidence_id':args['qa_evidence_id'],'qa_evidence_hash':args['qa_evidence_hash']}


def execute(service, actor, native, item, args, request_key, proof=None):
    approved=authorization(service,actor,args,request_key)
    proof=proof or packet(service,actor,args['qa_evidence_id'])
    try:
        evidence=json.loads(proof['evidence_document'])
        valid=(evidence['id']==approved['qa_evidence_id'] and digest(proof['evidence_document'])==approved['qa_evidence_hash'] and
            evidence['binding']['native_id']==args['id'] and evidence['binding']['version']==args['lock_version'])
    except (KeyError,TypeError,ValueError):valid=False
    if not valid:raise PermissionError('QA_EXACT_APPROVED_EVIDENCE_BINDING_REQUIRED')
    marker='QLDAPM-request-'+digest(f'{actor}:{request_key}')
    payload={'id':item['id'],'action':'transition','lock_version':item['lockVersion'],'status_id':args['status_id'],
        'request_id':marker,'qa_proof':proof,'qa_authorization':approved}
    at=int(time.time());key=(service.store.root/'ui.key').read_bytes();fingerprint=digest(canonical(payload))
    native.mutation_headers={'X-Qldapm-At':str(at),'X-Qldapm-Mutation':hmac.new(key,f'{actor}:{at}:{fingerprint}'.encode(),hashlib.sha256).hexdigest()}
    result=native.call('/api/v3/qldapm/mutations','POST',payload)
    try:
        readback=native.package(item['id']);summary=result['qa_native']
        expected={'evidence_id':args['qa_evidence_id'],'hash':args['qa_evidence_hash'],'source_version':item['lockVersion'],
            'artifact_sha256':json.loads(proof['run']['document'])['artifact_sha256']}
        gate=native.call(f"/api/v3/qldapm/gates/{item['id']}")['gate']
        event={'actor_id':actor,'request_id':marker,'proposal_id':approved['proposal_id'],'proposal_hash':approved['proposal_hash']}
        if (result.get('id')!=item['id'] or result.get('request_id')!=marker or result.get('provenance')!='ai_gateway' or
                readback.get('lockVersion')!=result.get('lockVersion') or result['lockVersion']<=item['lockVersion'] or
                readback.get('_links',{}).get('status',{}).get('href')!=f"/api/v3/statuses/{args['status_id']}" or
                any(summary.get(k)!=v or gate.get('qa_bridge',{}).get(k)!=v for k,v in expected.items()) or
                not any(all(row.get(k)==v for k,v in event.items()) for row in gate.get('events',[]))):
            raise ValueError('QA_NATIVE_READBACK_MISMATCH')
        return {**readback,'qa_native':summary,'native_receipt_request_id':marker}
    except (NativeError,PermissionError,ValueError,KeyError,TypeError):
        raise NativeError(503,'QA_NATIVE_READBACK_OUTCOME_UNKNOWN; inspect exact Native receipt, never replay') from None


def reconcile(native, actor, request_key, args):
    if not all(k in args for k in ['qa_evidence_id','qa_evidence_hash']) or not isinstance(request_key,str) or not request_key.startswith('proposal-'):
        return None
    marker='QLDAPM-request-'+digest(f'{actor}:{request_key}')
    native.package(args['id'])
    try:receipt=native.call('/api/v3/qldapm/mutation_receipts/'+marker)
    except NativeError as error:
        if error.status==404:return None
        raise
    expected={'evidence_id':args['qa_evidence_id'],'hash':args['qa_evidence_hash'],'source_version':args['lock_version']}
    if (receipt.get('id')!=args['id'] or receipt.get('request_id')!=marker or receipt.get('provenance')!='ai_gateway' or
            any(receipt.get('qa_native',{}).get(k)!=v for k,v in expected.items())):
        raise NativeError(409,'QA_NATIVE_RECEIPT_MISMATCH_HOLD')
    current=native.package(args['id'])
    if (current.get('lockVersion')!=receipt.get('lockVersion') or
            current.get('_links',{}).get('status',{}).get('href')!=f"/api/v3/statuses/{args['status_id']}"):
        raise NativeError(409,'QA_NATIVE_RECEIPT_SOURCE_CHANGED_HOLD')
    return {**current,'qa_native':receipt['qa_native'],'native_receipt_request_id':marker}

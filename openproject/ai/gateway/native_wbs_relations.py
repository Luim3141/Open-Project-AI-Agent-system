"""Explicit WBS follows relations reuse existing human proposals, Native receipts and RAG jobs."""
import copy
import json
import time
import uuid

from .native import NativeError
from .store import canonical,digest


def specification(service,relations,nodes):
    if not isinstance(relations,list) or len(relations)>100:raise ValueError('WBS_NATIVE_RELATIONS_0_100_REQUIRED')
    by_key={node['key']:node for node in nodes};seen=set();graph={key:[] for key in by_key}
    def ancestors(key):
        result=[]
        while by_key[key]['parent'] is not None:
            key=by_key[key]['parent'];result.append(key)
        return result
    for row in relations:
        service.keys(row,{'predecessor','successor','lag'},{'predecessor','successor','lag'})
        pre,suc=row['predecessor'],row['successor'];lag=row['lag']
        if (not isinstance(pre,str) or not isinstance(suc,str) or pre not in by_key or suc not in by_key or pre==suc or
                type(lag) is not int or not -2000<=lag<=2000 or (pre,suc) in seen):raise ValueError('WBS_NATIVE_RELATION_INVALID_OR_DUPLICATE')
        if pre in ancestors(suc) or suc in ancestors(pre):raise ValueError('WBS_NATIVE_ANCESTOR_RELATION_DENIED')
        seen.add((pre,suc));graph[suc].append(pre)
    visited=set();active=set()
    def visit(key):
        if key in active:raise ValueError('WBS_NATIVE_RELATION_CYCLE')
        if key in visited:return
        active.add(key)
        for parent in graph[key]:visit(parent)
        active.remove(key);visited.add(key)
    for key in graph:visit(key)
    return copy.deepcopy(relations)


def baseline(service,doc):
    from .native_wbs import private_record
    return private_record(service,doc,'dependency_baseline',doc['id'])


def scope(item):
    parent=item.get('_links',{}).get('parent',{}).get('href')
    return {'id':item['id'],'lockVersion':item['lockVersion'],'startDate':item.get('startDate'),
        'dueDate':item.get('dueDate'),'scheduleManually':item.get('scheduleManually'),
        'parent_id':int(parent.rsplit('/',1)[-1]) if parent else None}


def progress(service,doc,native,base):
    from .native_wbs import arguments
    from .business_runs import create_matches
    nodes=copy.deepcopy(base['nodes']);ids=base['native_ids'];snapshots=copy.deepcopy(base['snapshots']);rows=[]
    for index,edge in enumerate(doc['spec']['relations']):
        prefix=f'wbs-rel-{doc["id"]}-{index}-'
        with service.store.connect() as db:
            found=db.execute("SELECT id,payload FROM proposals WHERE actor=? AND json_extract(payload,'$.idempotency_key') GLOB ?",(doc['actor'],prefix+'*')).fetchall()
        versions=[(int(json.loads(row['payload'])['idempotency_key'][len(prefix):]),row['id']) for row in found]
        if len({v for v,_ in versions})!=len(versions):raise ValueError('WBS_DUPLICATE_RELATION_PROPOSAL')
        row={'index':index,**edge,'generation':-1,'state':'NOT_PROPOSED'};rows.append(row)
        if not versions:continue
        generation,identifier=max(versions);p=service.store.proposal(doc['actor'],identifier);command=p['command'];args=command['arguments']
        expected={'predecessor_id':ids[edge['predecessor']],'successor_id':ids[edge['successor']],'lag':edge['lag']}
        if (p['hash']!=digest(canonical({'actor':doc['actor'],'command':command})) or command['action']!='create_dependency' or
                set(args)!=set(expected)|{'scope_hash'} or any(args[k]!=v for k,v in expected.items()) or command.get('_gateway_mode')!='native'):
            raise ValueError('WBS_RELATION_PROPOSAL_PLAN_MISMATCH')
        row.update(generation=generation,proposal=p,state='AWAITING_APPROVAL' if p['state']=='pending' else 'UNKNOWN_HOLD')
        if p['state']=='pending' and p['expires']<=time.time():row['state']='EXPIRED'
        if p['state']=='rejected':row['state']='REJECTED'
        try:request=service.store.request_status(doc['actor'],'proposal-'+identifier)
        except ValueError:request=None
        receipt=request['result'] if request and request['state']=='done' else None
        if receipt and receipt.get('error')=='NATIVE_REJECTED' and receipt.get('outcome_unknown') is False:row['state']='FAILED_KNOWN'
        if not receipt or 'result' not in receipt:continue
        if p['state']!='done':row['state']='UNKNOWN_HOLD';continue
        result=receipt['result'];marker='QLDAPM-request-'+digest(f'{doc["actor"]}:proposal-{identifier}')
        committed=native.call('/api/v3/qldapm/mutation_receipts/'+marker)
        if (committed!=result or result.get('request_id')!=marker or result.get('proposal_id')!=identifier or result.get('proposal_hash')!=p['hash'] or
                result.get('scope_hash')!=args['scope_hash'] or result.get('provenance')!='ai_gateway' or
                any(result.get('relation',{}).get(k)!=v for k,v in {'type':'follows',**expected}.items())):
            raise NativeError(409,'WBS_NATIVE_RELATION_RECEIPT_HOLD')
        prior=command['preview']['possible_affected']
        if any(str(item['id']) not in snapshots or item!=scope(snapshots[str(item['id'])]) for item in prior):
            raise NativeError(409,'WBS_NATIVE_RELATION_SCOPE_CHAIN_HOLD')
        changed=result['changed_ids'];readback=result['readback'];expected_ids=set(changed)|{expected['predecessor_id'],expected['successor_id']}
        if ({item['id'] for item in readback}!=expected_ids or len(readback)!=len(expected_ids) or not set(changed)<={item['id'] for item in prior}):
            raise NativeError(409,'WBS_NATIVE_RELATION_READBACK_SCOPE_HOLD')
        for item in readback:
            key=str(item['id'])
            if set(item)!={'id','lockVersion','startDate','dueDate','scheduleManually'} or key not in snapshots:raise NativeError(409,'WBS_NATIVE_RELATION_READBACK_HOLD')
            snapshots[key].update(item)
        relation=native.call('/api/v3/relations/'+str(result['relation']['id']))
        if (relation.get('type')!='follows' or relation.get('lag')!=edge['lag'] or
                relation.get('_links',{}).get('from',{}).get('href')!=f'/api/v3/work_packages/{expected["successor_id"]}' or
                relation.get('_links',{}).get('to',{}).get('href')!=f'/api/v3/work_packages/{expected["predecessor_id"]}'):
            raise NativeError(409,'WBS_NATIVE_RELATION_CHANGED_HOLD')
        syncs=receipt.get('knowledge_syncs',[])
        if {job['native_id'] for job in syncs}!=expected_ids:raise NativeError(409,'WBS_NATIVE_RELATION_RAG_SCOPE_HOLD')
        jobs=[service.store.knowledge_sync(doc['actor'],job['id']) for job in syncs];row['knowledge_syncs']=jobs
        row['native_relation_id']=result['relation']['id'];states={job['state'] for job in jobs}
        row['state']='VERIFIED' if states=={'verified'} else 'RAG_FAILED' if 'dlq' in states else 'RAG_PENDING'
    states={row['state'] for row in rows}
    if 'UNKNOWN_HOLD' not in states:
        latest_jobs={job['native_id']:job for row in rows for job in row.get('knowledge_syncs',[])}
        for node,row in zip(doc['spec']['nodes'],nodes):
            item=native.package(row['native_id']);expected=arguments(service,doc,node,ids,row['proposal']['command']['idempotency_key'])
            expected.pop('start_date',None);expected.pop('due_date',None)
            previous=snapshots[str(item['id'])]
            children=lambda value:sorted(link['href'] for link in value.get('_links',{}).get('children',[]))
            if not create_matches(service,doc['actor'],item,expected) or scope(item)!=scope(previous) or children(item)!=children(previous):
                row['state']='SOURCE_CHANGED';states.add('SOURCE_CHANGED')
            elif item['id'] in latest_jobs:
                job=latest_jobs[item['id']];row['knowledge_sync']=job
                row['state']='VERIFIED' if job['state']=='verified' else 'RAG_FAILED' if job['state']=='dlq' else 'RAG_PENDING'
                states.add(row['state'])
                row['native_dependency_change']={'from_version':base['snapshots'][str(item['id'])]['lockVersion'],'to_version':item['lockVersion']}
    else:
        for row in nodes:row['state']='UNKNOWN_HOLD'
    state=next((s for s in ['UNKNOWN_HOLD','SOURCE_CHANGED','RAG_FAILED','RAG_PENDING','AWAITING_APPROVAL','REJECTED','FAILED_KNOWN','EXPIRED'] if s in states),
        'VERIFIED_COMPLETED' if states=={'VERIFIED'} else 'READY_FOR_DEPENDENCIES')
    return {'state':state,'phase':'NATIVE_DEPENDENCIES','nodes':nodes,'native_ids':ids,'relations':rows,'atomic_multi_wp':False,
        'dependency_scope':'Explicit follows relations only; each exact human approval, Native commit receipt and full affected RAG sync required'}


def next_proposal(service,who,native,doc,state,retry_hash=None):
    from .native_wbs import save,arguments
    from .business_runs import create_matches
    from . import native_dependency
    base=baseline(service,doc)
    if base is None:
        snapshots={}
        for node,row in zip(doc['spec']['nodes'],state['nodes']):
            item=native.package(row['native_id']);version=row.get('native_parent_change',{}).get('to_version',row['receipt']['result']['lockVersion'])
            if item['lockVersion']!=version or not create_matches(service,who['user_id'],item,arguments(service,doc,node,state['native_ids'],row['proposal']['command']['idempotency_key'])):
                raise NativeError(409,'WBS_NATIVE_BASELINE_SOURCE_CHANGED')
            snapshots[str(item['id'])]=item
        base=save(service,who['user_id'],'dependency_baseline',{'plan_hash':doc['hash'],'snapshots':snapshots,
            'nodes':state['nodes'],'native_ids':state['native_ids']},doc['id'])['spec']
        state=progress(service,doc,native,base)
    if state['state']=='AWAITING_APPROVAL':
        row=next(row for row in state['relations'] if row['state']=='AWAITING_APPROVAL')
        return {'state':'AWAITING_APPROVAL','relation_index':row['index'],'proposal':row['proposal']}
    retry=state['state'] in {'REJECTED','FAILED_KNOWN','EXPIRED'}
    if retry:
        row=next(row for row in state['relations'] if row['state']==state['state'])
        if retry_hash is None:return state
        if retry_hash!=row['proposal']['hash']:raise ValueError('WBS_EXACT_RETRY_HASH_REQUIRED')
    elif state['state']=='READY_FOR_DEPENDENCIES':row=next(row for row in state['relations'] if row['state']=='NOT_PROPOSED')
    else:return state
    ids=base['native_ids'];args={'predecessor_id':ids[row['predecessor']],'successor_id':ids[row['successor']],'lag':row['lag']}
    preview=native_dependency.preview(service,who,native,args)
    if not {item['id'] for item in preview['possible_affected']}<=set(ids.values()):raise NativeError(409,'WBS_NATIVE_DEPENDENCY_EXTERNAL_SCOPE_HOLD')
    key=f'wbs-rel-{doc["id"]}-{row["index"]}-{row["generation"]+1}'
    proposal=service.execute_actor(who['user_id'],{'action':'create_dependency','arguments':args,'idempotency_key':key})['result']
    if proposal['command']['preview']['scope_hash']!=preview['scope_hash']:raise NativeError(409,'WBS_NATIVE_DEPENDENCY_PREVIEW_CHANGED_HOLD')
    return {'state':'AWAITING_APPROVAL','relation_index':row['index'],'proposal':proposal}

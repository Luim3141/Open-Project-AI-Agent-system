"""Immutable WBS plans; progressive existing proposals, receipts and RAG jobs own execution."""
import json
import re
import time
import uuid
from datetime import date,datetime

from .business_runs import create_matches
from .knowledge_lock import lease
from .native import NativeError
from .store import canonical,digest

TYPES={'Epic':5,'Task':1,'Subtask':10}
PLANNING_FIELDS={'assignee_role','priority_id','start_date','due_date'}


def scheduling(args, form=None):
    dates={k:args[k] for k in ('start_date','due_date') if k in args}
    if dates:
        if len(dates)!=2:raise ValueError('WBS_BOTH_SCHEDULE_DATES_REQUIRED')
        try:
            if any(not isinstance(v,str) or date.fromisoformat(v).isoformat()!=v for v in dates.values()):raise ValueError()
        except ValueError:raise ValueError('WBS_SCHEDULE_ISO_DATES_REQUIRED') from None
        if dates['start_date']>dates['due_date']:raise ValueError('WBS_SCHEDULE_RANGE_INVALID')
    if 'priority_id' in args and (type(args['priority_id']) is not int or args['priority_id']<=0):raise ValueError('WBS_PRIORITY_INVALID')
    if 'assignee_role' in args and (not isinstance(args['assignee_role'],str) or args['assignee_role'] not in {'PM','BA','BA-PM','BE','FE','QA'}):
        raise ValueError('WBS_ASSIGNEE_ROLE_INVALID')
    payload={ {'start_date':'startDate','due_date':'dueDate'}[k]:v for k,v in dates.items()}
    if payload and form is not None:
        actual=form.get('_embedded',{}).get('payload',{})
        if any(actual.get(k)!=v for k,v in payload.items()):
            raise NativeError(422,'OPENPROJECT_SCHEDULE_ADJUSTMENT_REQUIRES_NEW_DRAFT',
                              {k:actual.get(k) for k in payload})
    return payload


def from_ba(service, who, native, args, key):
    from .agent_models import AgentResult
    service.keys(args, {'run_id','output_hash','share_for_review'}, {'run_id','output_hash'})
    run = service.perform(who,native,'get_ai_run',{'id':args['run_id']})
    result = run.get('result') or {}
    if result.get('stale'):
        raise NativeError(409,'WBS_BA_SOURCE_CHANGED')
    if (run['state'] not in {'done','reconciled_success'} or result.get('status') not in {'succeeded','proposed'} or
            result.get('engine') not in {'local_supervisor','gemini_supervisor'}):
        raise ValueError('WBS_COMPLETED_BA_ANALYSIS_REQUIRED')
    outputs = [o for o in result.get('agent_outputs',[]) if o.get('agent') == 'ba']
    if len(outputs) != 1:
        raise ValueError('WBS_SINGLE_BA_OUTPUT_REQUIRED')
    output = outputs[0]
    if digest(canonical(output)) != args['output_hash']:
        raise ValueError('WBS_BA_EXACT_OUTPUT_HASH_REQUIRED')
    steps = result.get('plan',{}).get('steps',[])
    if not any(s.get('step_id') == output.get('step_id') and s.get('agent') == 'ba' for s in steps):
        raise PermissionError('WBS_BA_STEP_PROVENANCE_REQUIRED')
    analysis = AgentResult.from_json(canonical(output['result']))
    if (analysis.actor_id != who['user_id'] or analysis.project_id != service.config['project_id'] or
            analysis.run_id != run['id'] or analysis.state == 'FAILED' or not analysis.references):
        raise PermissionError('WBS_BA_OUTPUT_SCOPE_REQUIRED')
    try:
        payload = json.loads(analysis.summary)
    except ValueError:
        raise ValueError('WBS_BA_STRUCTURED_OUTPUT_REQUIRED') from None
    if not isinstance(payload,dict):raise ValueError('WBS_BA_STRUCTURED_OUTPUT_REQUIRED')
    fields={'schema','requirements','nodes'}|({'relations'} if payload.get('schema')=='QLDAPM_WBS_V2' else set())
    if set(payload)!=fields or payload['schema'] not in {'QLDAPM_WBS_V1','QLDAPM_WBS_V2'}:
        raise ValueError('WBS_BA_STRUCTURED_OUTPUT_REQUIRED')
    from .wbs_analysis import native_keys
    payload,key_mapping=native_keys(payload)
    spec = specification(service, {k:payload[k] for k in fields-{'schema'}} | {'share_for_review':args.get('share_for_review',False)})
    spec['source_references'] = [{'work_package_id':r.work_package_id,'lock_version':r.lock_version} for r in analysis.references]
    validate_sources(native,spec)
    origin={'run_id':run['id'],'output_hash':args['output_hash'],'actor':who['user_id']}
    if key_mapping:origin['native_key_mapping']=key_mapping
    return save(service,who['user_id'],'draft',spec,key,origin)


def validate_sources(native, spec):
    refs=spec.get('source_references',[])
    if (not isinstance(refs,list) or len(refs)>10 or any(not isinstance(r,dict) or set(r)!={'work_package_id','lock_version'} or
            type(r['work_package_id']) is not int or r['work_package_id']<=0 or type(r['lock_version']) is not int or r['lock_version']<0 for r in refs)):
        raise ValueError('WBS_NATIVE_SOURCE_REFERENCES_INVALID')
    if len({r['work_package_id'] for r in refs})!=len(refs):raise ValueError('WBS_NATIVE_SOURCE_REFERENCES_INVALID')
    for ref in refs:
        if native.package(ref['work_package_id'])['lockVersion'] != ref['lock_version']:
            raise NativeError(409,'WBS_BA_SOURCE_CHANGED')


def text(value,limit):
    if not isinstance(value,str) or not 1<=len(value.strip())<=limit:raise ValueError('WBS_TEXT_REQUIRED_OR_TOO_LONG')
    return value.strip()


def specification(service,args):
    service.keys(args,{'requirements','nodes','share_for_review','relations'},{'requirements','nodes'})
    requirements,nodes=args['requirements'],args['nodes']
    if not isinstance(requirements,list) or not 1<=len(requirements)<=80 or not isinstance(nodes,list) or not 1<=len(nodes)<=50:
        raise ValueError('WBS_REQUIREMENTS_1_80_NODES_1_50')
    shared=args.get('share_for_review',False)
    if type(shared) is not bool:raise ValueError('WBS_SHARE_BOOLEAN_REQUIRED')
    reqs={}
    for row in requirements:
        if not isinstance(row,dict):raise ValueError('WBS_REQUIREMENT_INVALID')
        service.keys(row,{'id','text'},{'id','text'});key=text(row['id'],40)
        if key in reqs:raise ValueError('WBS_DUPLICATE_REQUIREMENT')
        reqs[key]=text(row['text'],1000)
    normalized=[];keys=set();covered=set()
    for row in nodes:
        if not isinstance(row,dict):raise ValueError('WBS_NODE_INVALID')
        service.keys(row,{'key','kind','subject','description','parent','depends_on','requirement_ids','status_id','duplicate_disposition'}|PLANNING_FIELDS,
                     {'key','kind','subject','requirement_ids'})
        key=row['key'];kind=row['kind'];status=row.get('status_id',1);refs=row['requirement_ids'];deps=row.get('depends_on',[])
        if not isinstance(key,str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,23}',key) or key in keys:raise ValueError('WBS_NODE_KEY_INVALID_OR_DUPLICATE')
        if not isinstance(kind,str) or kind not in TYPES or TYPES[kind] not in service.config['type_ids']:raise ValueError('WBS_NATIVE_TYPE_DENIED')
        if type(status) is not int or status not in service.config['status_ids']:raise ValueError('WBS_STATUS_DENIED')
        if (not isinstance(refs,list) or not refs or any(not isinstance(r,str) or r not in reqs for r in refs)
                or len(set(refs))!=len(refs) or not isinstance(deps,list) or any(not isinstance(d,str) for d in deps) or len(set(deps))!=len(deps)):
            raise ValueError('WBS_REQUIREMENT_OR_DEPENDENCY_INVALID')
        description=row.get('description','')
        if not isinstance(description,str) or len(description)>4000:raise ValueError('WBS_DESCRIPTION_INVALID')
        disposition=text(row['duplicate_disposition'],1000) if 'duplicate_disposition' in row else None
        planning={k:row[k] for k in PLANNING_FIELDS if k in row};scheduling(planning)
        normalized.append({'key':key,'kind':kind,'subject':text(row['subject'],240),'description':description,'parent':row.get('parent'),
                           'depends_on':deps,'requirement_ids':refs,'status_id':status,'duplicate_disposition':disposition,**planning})
        keys.add(key);covered.update(refs)
    if covered!=set(reqs):raise ValueError('WBS_REQUIREMENT_COVERAGE_INCOMPLETE')
    by_key={n['key']:n for n in normalized};edges={}
    for n in normalized:
        parent=n['parent']
        if n['kind']=='Epic':
            if parent is not None:raise ValueError('WBS_EPIC_MUST_BE_ROOT')
        elif not isinstance(parent,str) or parent not in by_key or by_key[parent]['kind']!={'Task':'Epic','Subtask':'Task'}[n['kind']]:
            raise ValueError('WBS_PARENT_KIND_INVALID')
        edges[n['key']]=n['depends_on']+([parent] if parent else [])
        if any(d not in keys or d==n['key'] for d in edges[n['key']]):raise ValueError('WBS_DEPENDENCY_INVALID')
        if 'start_date' in n:
            if any('due_date' in by_key[d] and n['start_date']<=by_key[d]['due_date'] for d in n['depends_on']):
                raise ValueError('WBS_DEPENDENCY_SCHEDULE_CONFLICT')
            if parent and 'start_date' in by_key[parent] and not (by_key[parent]['start_date']<=n['start_date']<=n['due_date']<=by_key[parent]['due_date']):
                raise ValueError('WBS_CHILD_SCHEDULE_OUTSIDE_PARENT')
    seen=set();visiting=set()
    def visit(key):
        if key in visiting:raise ValueError('WBS_DEPENDENCY_CYCLE')
        if key in seen:return
        visiting.add(key)
        for dep in edges[key]:visit(dep)
        visiting.remove(key);seen.add(key)
    for key in keys:visit(key)
    result={'requirements':reqs,'nodes':normalized,'share_for_review':shared}
    if 'relations' in args:
        from .native_wbs_relations import specification as relations
        result['relations']=relations(service,args['relations'],normalized)
    return result


def load(service,identifier):
    if not isinstance(identifier,str) or str(uuid.UUID(identifier))!=identifier:raise ValueError('WBS_UUID_REQUIRED')
    with service.store.connect() as db:row=db.execute('SELECT * FROM wbs_documents WHERE id=?',(identifier,)).fetchone()
    if row is None:raise PermissionError('WBS_NOT_FOUND')
    doc=json.loads(row['document'])
    if (digest(canonical(doc))!=row['hash'] or doc['id']!=row['id'] or doc['actor']!=row['actor'] or doc['project_id']!=row['project']
            or doc['project_id']!=service.config['project_id']):raise ValueError('WBS_DOCUMENT_TAMPERED')
    return {**doc,'hash':row['hash']}


def private_record(service,doc,kind,key):
    identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f'qldapm.wbs:{doc["actor"]}:{doc["project_id"]}:{kind}:{key}'))
    with service.store.connect() as db:exists=db.execute('SELECT 1 FROM wbs_documents WHERE id=?',(identifier,)).fetchone()
    if not exists:return None
    result=load(service,identifier)
    if result['kind']!=kind or result['actor']!=doc['actor'] or result['spec']['plan_hash']!=doc['hash']:raise ValueError('WBS_PRIVATE_RECORD_SCOPE_INVALID')
    return result['spec']


def save(service,actor,kind,spec,key,origin=None):
    identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,f'qldapm.wbs:{actor}:{service.config["project_id"]}:{kind}:{key}'))
    doc={'id':identifier,'actor':actor,'project_id':service.config['project_id'],'kind':kind,'spec':spec,'origin':origin}
    fingerprint=digest(canonical(doc))
    with service.store.connect() as db:
        db.execute('INSERT OR IGNORE INTO wbs_documents VALUES(?,?,?,?,?)',(identifier,actor,service.config['project_id'],fingerprint,canonical(doc)))
    existing=load(service,identifier)
    if existing['hash']!=fingerprint:raise ValueError('WBS_REQUEST_KEY_REUSED')
    return existing


def arguments(service,doc,node,ids,proposal_key=None):
    spec=doc['spec'];parent=node['parent']
    description=(node['description']+'\n\n## Requirement trace\n'+'\n'.join(f'- {r}: {spec["requirements"][r]}' for r in node['requirement_ids'])+
                 f'\n\nWBS plan: {doc["id"]}; node: {node["key"]}\nDependency sequencing: '+', '.join(node['depends_on']))
    if node['duplicate_disposition']:description+='\nDuplicate disposition: '+node['duplicate_disposition']
    args={'source_id':'wbs_'+doc['id'].replace('-','')+'_'+node['key'],'subject':node['subject'],
          'type_id':TYPES[node['kind']],'status_id':node['status_id'],'description':description}
    if spec.get('source_references'):args['source_references']=spec['source_references']
    args.update({k:node[k] for k in PLANNING_FIELDS if k in node})
    if parent:
        if parent not in ids:raise ValueError('WBS_PARENT_RECEIPT_REQUIRED')
        args['parent_id']=ids[parent]
        if doc['spec'].get('_hierarchy_readback')==1 and proposal_key is not None:
            proof=private_record(service,doc,'hierarchy_before',proposal_key)
            if proof is None or proof['before']['id']!=ids[parent]:raise ValueError('WBS_PARENT_PROOF_REQUIRED')
            refs=list(args.get('source_references',[]));reference={'work_package_id':ids[parent],'lock_version':proof['before']['lock_version']}
            if any(r['work_package_id']==ids[parent] for r in refs):raise ValueError('WBS_PARENT_REFERENCE_CONFLICT')
            args['source_references']=refs+[reference]
    return args


def parent_reschedule(service,doc,native,node,row,item,nodes):
    children=[r for n,r in zip(doc['spec']['nodes'],nodes) if n['parent']==node['key'] and r['state'] in {'VERIFIED','RAG_PENDING'}]
    if doc['spec'].get('_hierarchy_readback')==1 and any('start_date' in r['proposal']['command']['arguments'] for r in children):
        from .native_wbs_hierarchy import dated_parent_effect
        proof=dated_parent_effect(service,doc,native,node,item,children,row['receipt']['result']['lockVersion'])
        if proof is None:return None
        return parent_knowledge(service,doc,item,children,proof)
    before=row['receipt']['result'];version=before.get('lockVersion')
    if (type(version) is not int or item.get('lockVersion')!=version+1 or
            before.get('scheduleManually') is not True or item.get('scheduleManually') is not False):return None
    # shortcut: only first-child automatic scheduling is qualified; qualify other Native effects before widening.
    ignored={'lockVersion','updatedAt','scheduleManually','_links','_embedded'}
    if {k:v for k,v in before.items() if k not in ignored}!={k:v for k,v in item.items() if k not in ignored}:return None
    old_links=before.get('_links',{});links=item.get('_links',{})
    if old_links.get('children') or {k:v for k,v in old_links.items() if k!='children'}!={k:v for k,v in links.items() if k!='children'}:return None
    expected={f'/api/v3/work_packages/{r["native_id"]}' for r in children}
    linked=links.get('children',[])
    if not expected or not isinstance(linked,list) or len(linked)!=len(expected) or {r.get('href') for r in linked}!=expected:return None
    try:
        updated=datetime.fromisoformat(item['updatedAt'].replace('Z','+00:00'))
        if not any(0 <= (updated-datetime.fromisoformat(r['receipt']['result']['createdAt'].replace('Z','+00:00'))).total_seconds() <= 5 for r in children):return None
    except (KeyError,ValueError,TypeError):return None
    if doc['spec'].get('_hierarchy_readback')==1:
        from .native_wbs_hierarchy import parent_effect
        proof=parent_effect(service,doc,native,item,children,version)
        if proof is None:return None
    else:
        changes=[a for a in native.collection(f'/api/v3/work_packages/{item["id"]}/activities') if a.get('version',0)>version+1]
        if (len(changes)!=1 or changes[0].get('version')!=item['lockVersion']+1 or changes[0].get('createdAt')!=item['updatedAt'] or
                changes[0].get('_links',{}).get('user',{}).get('href')!=f'/api/v3/users/{doc["actor"]}' or
                changes[0].get('_links',{}).get('workPackage',{}).get('href')!=f'/api/v3/work_packages/{item["id"]}'):return None
        proof={'kind':'NATIVE_FIRST_CHILD_AUTOMATIC_SCHEDULING','from_version':version,'to_version':item['lockVersion'],
               'verified_child_ids':sorted(r['native_id'] for r in children),'native_activity_id':changes[0]['id']}
    return parent_knowledge(service,doc,item,children,proof)


def parent_knowledge(service,doc,item,children,proof):
    if any(r['state']!='VERIFIED' for r in children):return proof
    with service.store.connect() as db:
        jobs=[r[0] for r in db.execute("SELECT id FROM knowledge_sync WHERE actor=? AND native_id=? AND state='verified'",(doc['actor'],item['id']))]
    for identifier in jobs:
        job=service.store.knowledge_sync(doc['actor'],identifier);result=job.get('result') or {};canonical=result.get('canonical') or {}
        if all(r.get('native_id')==item['id'] and r.get('lock_version')==item['lockVersion'] and r.get('vector_indexed') is True for r in [result,canonical]):
            return {**proof,'knowledge_sync':job}
    return proof


def progress(service,doc,native):
    if doc['kind']!='plan':return {'state':'DRAFT_NON_EXECUTABLE','nodes':[]}
    if doc['spec'].get('relations'):
        from . import native_wbs_relations
        base=native_wbs_relations.baseline(service,doc)
        if base is not None:return native_wbs_relations.progress(service,doc,native,base)
    actor=doc['actor'];nodes=[];ids={}
    for node in doc['spec']['nodes']:
        prefix='wbs-'+doc['id']+'-'+node['key']+'-'
        with service.store.connect() as db:
            matches=db.execute("SELECT id,payload FROM proposals WHERE actor=? AND json_extract(payload,'$.idempotency_key') GLOB ?",(actor,prefix+'*')).fetchall()
        proposals=[(int(json.loads(r['payload'])['idempotency_key'][len(prefix):]),r['id']) for r in matches]
        if len({p[0] for p in proposals})!=len(proposals):raise ValueError('WBS_DUPLICATE_NODE_PROPOSAL')
        row={'key':node['key'],'state':'NOT_PROPOSED','generation':-1}
        if proposals:
            generation,identifier=max(proposals);p=service.store.proposal(actor,identifier);command=p['command']
            if p['hash']!=digest(canonical({'actor':actor,'command':command})) or command['action']!='create_work_package':raise ValueError('WBS_PROPOSAL_TAMPERED')
            row.update(generation=generation,proposal=p,state='AWAITING_APPROVAL' if p['state']=='pending' else 'UNKNOWN_HOLD')
            if p['state']=='pending' and p['expires']<=time.time():row['state']='EXPIRED'
            if p['state']=='rejected':row['state']='REJECTED'
            receipt=p.get('result')
            try:request=service.store.request_status(actor,'proposal-'+p['id'])
            except ValueError:request=None
            if request and request['state']=='done':receipt=request['result']
            if receipt and receipt.get('error')=='NATIVE_REJECTED' and receipt.get('outcome_unknown') is False:row['state']='FAILED_KNOWN'
            if receipt and type(receipt.get('result',{}).get('id')) is int:
                row['receipt']=receipt;row['native_id']=receipt['result']['id'];ids[node['key']]=row['native_id']
                row['state']='NATIVE_CONFIRMED'
        nodes.append(row)
    for node,row in reversed(list(zip(doc['spec']['nodes'],nodes))):
        if 'proposal' not in row:continue
        expected=arguments(service,doc,node,ids,row['proposal']['command']['idempotency_key'])
        if row['proposal']['command']['arguments']!=expected:raise ValueError('WBS_PROPOSAL_PLAN_MISMATCH')
        if row['state']!='NATIVE_CONFIRMED':continue
        item=native.package(row['native_id']);receipt=row['receipt']
        if not create_matches(service,actor,item,expected):
            row['state']='SOURCE_CHANGED';continue
        if item['lockVersion']!=receipt['result']['lockVersion']:
            proof=parent_reschedule(service,doc,native,node,row,item,nodes)
            if proof is None:row['state']='SOURCE_CHANGED';continue
            row['native_parent_change']={k:v for k,v in proof.items() if k!='knowledge_sync'}
            row['state']='VERIFIED' if 'knowledge_sync' in proof else 'RAG_PENDING'
            if 'knowledge_sync' in proof:row['knowledge_sync']=proof['knowledge_sync']
            continue
        sync=receipt.get('knowledge_sync')
        if not sync:row['state']='UNKNOWN_HOLD';continue
        job=service.store.knowledge_sync(actor,sync['id']);row['knowledge_sync']=job
        row['state']='VERIFIED' if job['state']=='verified' else 'RAG_FAILED' if job['state']=='dlq' else 'RAG_PENDING'
    states={r['state'] for r in nodes}
    state=next((v for v in ['UNKNOWN_HOLD','SOURCE_CHANGED','RAG_FAILED','RAG_PENDING','AWAITING_APPROVAL','REJECTED','FAILED_KNOWN','EXPIRED'] if v in states),
               'VERIFIED_COMPLETED' if states=={'VERIFIED'} else 'READY_TO_PROPOSE')
    result={'state':state,'nodes':nodes,'native_ids':ids,'atomic_multi_wp':False,'dependency_scope':'Validated sequencing only; no inferred Native relation writes'}
    if doc['spec'].get('relations') and state=='VERIFIED_COMPLETED':
        result.update(state='READY_FOR_DEPENDENCIES',relations=[{'index':i,**row,'state':'NOT_PROPOSED'} for i,row in enumerate(doc['spec']['relations'])])
    return result


def next_proposal(service,who,native,args):
    service.keys(args,{'id','hash','retry_hash'},{'id','hash'});doc=load(service,args['id'])
    if doc['actor']!=who['user_id'] or doc['kind']!='plan':raise PermissionError('WBS_OWN_MANAGER_PLAN_REQUIRED')
    validate_sources(native,doc['spec'])
    if doc['hash']!=args['hash']:raise ValueError('WBS_EXACT_HASH_REQUIRED')
    with lease(service.store.root/('wbs-'+doc['id']+'.lock')):
        state=progress(service,doc,native);rows=state['nodes'];by_key={r['key']:r for r in rows}
        if state.get('phase')=='NATIVE_DEPENDENCIES' or state['state']=='READY_FOR_DEPENDENCIES':
            from .native_wbs_relations import next_proposal as relations
            return relations(service,who,native,doc,state,args.get('retry_hash'))
        if state['state']=='AWAITING_APPROVAL':
            row=next(r for r in rows if r['state']=='AWAITING_APPROVAL')
            return {'state':state['state'],'node_key':row['key'],'proposal':row['proposal']}
        retry=state['state'] in {'REJECTED','FAILED_KNOWN','EXPIRED'}
        if retry:
            row=next(r for r in rows if r['state']==state['state'])
            if 'retry_hash' not in args:return state
            if args['retry_hash']!=row['proposal']['hash']:raise ValueError('WBS_EXACT_RETRY_HASH_REQUIRED')
            node=next(n for n in doc['spec']['nodes'] if n['key']==row['key'])
        elif state['state']!='READY_TO_PROPOSE':return state
        else:
            node=next((n for n in doc['spec']['nodes'] if by_key[n['key']]['state']=='NOT_PROPOSED' and
                       all(by_key[k]['state']=='VERIFIED' for k in n['depends_on']+([n['parent']] if n['parent'] else []))),None)
            if node is None:raise ValueError('WBS_NO_READY_NODE')
            row=by_key[node['key']]
        key=f'wbs-{doc["id"]}-{node["key"]}-{row["generation"]+1}'
        if doc['spec'].get('_hierarchy_readback')==1 and node['parent']:
            from .native_wbs_hierarchy import capture_parent
            capture_parent(service,doc,native,state['native_ids'][node['parent']],key)
        command_args=arguments(service,doc,node,state['native_ids'],key);items=native.packages()
        if any(i.get(service.config['source_field'])==command_args['source_id'] for i in items):return {**state,'state':'UNKNOWN_SOURCE_HOLD'}
        if any(i.get('subject','').casefold()==node['subject'].casefold() for i in items) and not node['duplicate_disposition']:
            raise ValueError('WBS_DUPLICATE_DISPOSITION_REQUIRED')
        links={'project':{'href':f'/api/v3/projects/{native.project_id}'},'type':{'href':f'/api/v3/types/{command_args["type_id"]}'},
               'status':{'href':f'/api/v3/statuses/{command_args["status_id"]}'}}
        if 'parent_id' in command_args:links['parent']={'href':f'/api/v3/work_packages/{command_args["parent_id"]}'}
        if 'assignee_role' in command_args:links['assignee']={'href':f"/api/v3/users/{service.role_assignee(command_args['assignee_role'])}"}
        if 'priority_id' in command_args:links['priority']={'href':f"/api/v3/priorities/{command_args['priority_id']}"}
        form=native.call(f'/api/v3/projects/{native.project_id}/work_packages/form','POST',{'subject':command_args['subject'],
                         'description':{'format':'markdown','raw':command_args['description']},service.config['source_field']:command_args['source_id'],'_links':links,**scheduling(command_args)})
        if errors:=form.get('_embedded',{}).get('validationErrors'):raise NativeError(422,'OPENPROJECT_FORM_REJECTED',errors)
        scheduling(command_args,form)
        proposal=service.execute_actor(who['user_id'],{'action':'create_work_package','arguments':command_args,'idempotency_key':key})['result']
        return {'state':'AWAITING_APPROVAL','node_key':node['key'],'proposal':proposal}


def perform(service,who,native,action,args,key):
    engineering_draft=(service.config['project_id']==6 and service.config.get('_engineering_scope') is True
        and service.config.get('engineering',{}).get('enabled') is True and action in {'wbs_draft','wbs_get'})
    if service.mode!='native' or (service.config['project_id']!=5 and not engineering_draft):raise PermissionError('WBS_NATIVE_MAIN_ONLY')
    if action=='wbs_draft':return save(service,who['user_id'],'draft',specification(service,args),key)
    if action=='wbs_from_ba':return from_ba(service,who,native,args,key)
    if action=='wbs_next':return next_proposal(service,who,native,args)
    service.keys(args,{'id','hash'} if action=='wbs_adopt' else {'id'},{'id','hash'} if action=='wbs_adopt' else {'id'})
    doc=load(service,args['id'])
    if doc['kind'] not in {'draft','plan'}:raise PermissionError('WBS_PRIVATE_RECORD_DENIED')
    if action=='wbs_adopt':
        if doc['kind']!='draft' or (doc['actor']!=who['user_id'] and not doc['spec']['share_for_review']):raise PermissionError('WBS_DRAFT_NOT_SHARED')
        validate_sources(native,doc['spec'])
        if doc['hash']!=args['hash']:raise ValueError('WBS_EXACT_HASH_REQUIRED')
        service.store.record(who['user_id'],'wbs_adopt_shared_draft',doc['id'],'ok')
        spec=doc['spec']
        try:capability=native.call('/api/v3/qldapm/capabilities')
        except NativeError as error:
            if error.status!=404:raise
            capability={}
        version=capability.get('wbs_hierarchy_readback_version',0)
        if type(version) is not int or version not in {0,1}:raise NativeError(502,'WBS_HIERARCHY_CAPABILITY_INVALID')
        if version==1:
            if capability.get('project_id')!=5 or capability.get('enforced') is not True:raise NativeError(502,'WBS_HIERARCHY_CAPABILITY_INVALID')
            spec={**spec,'_hierarchy_readback':1}
        return save(service,who['user_id'],'plan',spec,key,{k:doc[k] for k in ['id','hash','actor']})
    if doc['actor']!=who['user_id']:raise PermissionError('WBS_NOT_FOUND')
    validate_sources(native,doc['spec'])
    return {**doc,'progress':progress(service,doc,native)}

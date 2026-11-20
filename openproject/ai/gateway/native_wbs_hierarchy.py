"""Read-only Native model proofs survive journal merging without trusting caller claims."""
import re

from .native import NativeError
from .store import canonical,digest


def read(native,actor,identifier):
    result=native.call('/api/v3/qldapm/wbs_hierarchy/'+str(identifier))
    state=result.get('snapshot') if isinstance(result,dict) else None
    attributes=state.get('attributes') if isinstance(state,dict) else None
    if (not isinstance(attributes,dict) or result.get('actor_id')!=actor or result.get('id')!=identifier or result.get('project_id')!=5 or
            type(result.get('lock_version')) is not int or result['lock_version']<0 or
            attributes.get('id')!=identifier or attributes.get('project_id')!=5 or attributes.get('lock_version')!=result['lock_version'] or
            not isinstance(result.get('snapshot_sha256'),str) or not re.fullmatch('[a-f0-9]{64}',result['snapshot_sha256']) or
            result['snapshot_sha256']!=digest(canonical(state))):raise NativeError(502,'WBS_HIERARCHY_NATIVE_READBACK_INVALID')
    return result


def capture_parent(service,doc,native,identifier,key):
    from .native_wbs import save,private_record
    previous=private_record(service,doc,'hierarchy_before',key)
    if previous is not None:return previous
    before=read(native,doc['actor'],identifier)
    api=native.package(identifier)
    if api['lockVersion']!=before['lock_version']:raise NativeError(409,'WBS_PARENT_CAPTURE_CHANGED')
    return save(service,doc['actor'],'hierarchy_before',{'plan_hash':doc['hash'],'before':before,'api':api},key)['spec']


def dated_parent_effect(service,doc,native,node,item,children,version):
    from datetime import datetime
    from .native_wbs import private_record,save
    if not children:return None
    current=read(native,doc['actor'],item['id']);records=[]
    for child in children:
        command=child['proposal']['command'];args=command['arguments'];result=child['receipt']['result']
        planned=next(n for n in doc['spec']['nodes'] if n['key']==child['key'])
        if (any(key not in planned or args.get(key)!=planned[key] for key in ['start_date','due_date']) or
                result.get('startDate')!=args['start_date'] or result.get('dueDate')!=args['due_date']):return None
        key=command['idempotency_key'];before=private_record(service,doc,'hierarchy_before',key)
        if before is None or 'api' not in before or before['before']['id']!=item['id']:return None
        records.append((result['createdAt'],key,child,before))
    records.sort();chain_version=version;chain_hash=None;previous_api=None;known=set();last=None
    for _,key,child,before in records:
        prior=before['before'];a=prior['snapshot']['attributes'];old=before['api']
        if (prior['lock_version']!=chain_version or old['lockVersion']!=chain_version or
                chain_hash is not None and prior['snapshot_sha256']!=chain_hash):return None
        if previous_api is not None and {k:v for k,v in old.items() if k!='_embedded'}!={k:v for k,v in previous_api.items() if k!='_embedded'}:return None
        if {r.get('href') for r in old.get('_links',{}).get('children',[])}!=known:return None
        known.add(f'/api/v3/work_packages/{child["native_id"]}')
        effect=private_record(service,doc,'hierarchy_effect',key)
        if effect is None:
            if key!=records[-1][1]:return None
            after=current;api=item
        else:after=effect['after'];api=effect['api']
        b=after['snapshot']['attributes'];changed={k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
        allowed={'lock_version','updated_at','schedule_manually','start_date','due_date','duration'}
        if not changed<=allowed or prior['snapshot'].get('parent_id')!=after['snapshot'].get('parent_id'):return None
        subset=[row for _,_,row,_ in records if f'/api/v3/work_packages/{row["native_id"]}' in known]
        start=min(row['receipt']['result']['startDate'] for row in subset);due=max(row['receipt']['result']['dueDate'] for row in subset)
        if (api.get('startDate')!=start or api.get('dueDate')!=due or api.get('derivedStartDate')!=start or api.get('derivedDueDate')!=due or
                b.get('start_date')!=start or b.get('due_date')!=due or b.get('schedule_manually') is not False or api.get('scheduleManually') is not False or
                type(after.get('working_duration')) is not int or after['working_duration']<=0 or
                b.get('duration')!=after['working_duration'] or api.get('duration')!=f'P{after["working_duration"]}D'):return None
        toggle=int(a.get('schedule_manually') is True)
        dates=int(any(a.get(k)!=b.get(k) for k in ['start_date','due_date','duration']))
        delta=toggle+dates
        if after['lock_version']!=chain_version+delta or api['lockVersion']!=after['lock_version']:return None
        ignored={'lockVersion','updatedAt','scheduleManually','startDate','dueDate','derivedStartDate','derivedDueDate','duration','_links','_embedded'}
        if {k:v for k,v in old.items() if k not in ignored}!={k:v for k,v in api.items() if k not in ignored}:return None
        links=lambda value:{k:v for k,v in value.get('_links',{}).items() if k!='children'}
        if links(old)!=links(api) or {r.get('href') for r in api.get('_links',{}).get('children',[])}!=known:return None
        try:
            elapsed=(datetime.fromisoformat(api['updatedAt'].replace('Z','+00:00'))-datetime.fromisoformat(child['receipt']['result']['createdAt'].replace('Z','+00:00'))).total_seconds()
            if delta and not 0<=elapsed<=5:return None
            if not delta and api['updatedAt']!=old['updatedAt']:return None
        except (KeyError,ValueError,TypeError):return None
        if effect is None:save(service,doc['actor'],'hierarchy_effect',{'plan_hash':doc['hash'],'after':after,'api':api},key)
        chain_version=after['lock_version'];chain_hash=after['snapshot_sha256'];previous_api=api;last=after
    if last!=current or {k:v for k,v in previous_api.items() if k!='_embedded'}!={k:v for k,v in item.items() if k!='_embedded'}:return None
    return {'kind':'NATIVE_DATED_CHILD_MODEL_CHAIN','from_version':version,'to_version':chain_version,
        'verified_child_ids':sorted(child['native_id'] for child in children),'after_sha256':chain_hash,
        'schedule_basis':'Exact approved child dates, Native working-day calendar, immutable before/after model chain'}


def parent_effect(service,doc,native,item,children,version):
    from .native_wbs import private_record
    current=read(native,doc['actor'],item['id'])
    if current['lock_version']!=item['lockVersion']:return None
    for child in children:
        key=child['proposal']['command']['idempotency_key'];record=private_record(service,doc,'hierarchy_before',key)
        if record is None:continue
        old=record['before']
        if old['id']!=item['id'] or old['lock_version']!=version:continue
        before=old['snapshot'];after=current['snapshot'];a=before['attributes'];b=after['attributes']
        changed={k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
        if (changed<= {'lock_version','updated_at','schedule_manually'} and a.get('schedule_manually') is True and b.get('schedule_manually') is False and
                b['lock_version']==a['lock_version']+1 and before.get('parent_id')==after.get('parent_id')):
            return {'kind':'NATIVE_FIRST_CHILD_MODEL_READBACK','from_version':version,'to_version':item['lockVersion'],
                'verified_child_ids':sorted(row['native_id'] for row in children),'trigger_child_id':child['native_id'],
                'before_sha256':old['snapshot_sha256'],'after_sha256':current['snapshot_sha256'],
                'journal_policy':'No journal-count assumption; exact bounded model delta plus own child receipt/time/parent version reference'}
    return None

"""Request-local read scope: one SQLite reader, current Native ACL, no shared cache."""
import copy,json,sqlite3,time
from contextlib import contextmanager
from urllib.parse import urlencode
from .native import NativeError

class ReadNative:
    def __init__(self,native,metrics=None,deadline=None):
        self.native=copy.copy(native);self.packages={};self.missing=set();self.batch_supported=True
        if hasattr(native,'deadline'):self.native.deadline=min(native.deadline,deadline or time.monotonic()+8)
        if metrics is not None and hasattr(native,'call'):
            original=self.native.call
            def measured(*args,**kwargs):
                start=time.perf_counter()
                try:
                    result=original(*args,**kwargs)
                    if isinstance(result,dict):metrics['native_sql_ms']+=result.get('diagnostics',{}).get('sql_ms',0)
                    return result
                finally:metrics['native_calls']+=1;metrics['native_ms']+=(time.perf_counter()-start)*1000
            self.native.call=measured
    def __getattr__(self,key):return getattr(self.native,key)
    def prime(self,identifiers):
        ids=sorted(set(i for i in identifiers if type(i) is int and i>0)-self.packages.keys()-self.missing)
        if not ids or not self.batch_supported or not hasattr(self.native,'observer_packages'):return
        for offset in range(0,len(ids),100):
            chunk=ids[offset:offset+100]
            try:result=self.native.observer_packages(chunk)
            except NativeError as error:
                if error.status!=404:raise
                self.batch_supported=False;return
            if not isinstance(result,dict) or result.get('project_id')!=self.native.project_id or not isinstance(result.get('items'),list):raise ValueError('OBSERVER_METADATA_SCOPE_INVALID')
            found=set()
            for item in result['items']:
                identifier=item.get('id')
                if identifier not in chunk or item.get('_links',{}).get('project',{}).get('href')!='/api/v3/projects/'+str(self.native.project_id):raise PermissionError('OBSERVER_METADATA_SCOPE_INVALID')
                self.packages[identifier]=item;found.add(identifier)
            self.missing.update(set(chunk)-found)
    def package(self,identifier):
        if identifier in self.missing:raise PermissionError('OBSERVER_NATIVE_REFERENCE_NOT_VISIBLE')
        if identifier not in self.packages:self.packages[identifier]=self.native.package(identifier)
        return self.packages[identifier]

@contextmanager
def read_scope(service,*,timeout=8):
    """Nested legacy readers reuse page cache; SQLite enforces read-only operations."""
    scoped=copy.copy(service);scoped.store=copy.copy(service.store)
    metrics={'database_ms':0,'database_queries':0,'native_ms':0,'native_calls':0,'native_sql_ms':0}
    scoped._observer_metrics=metrics;scoped._observer_deadline=time.monotonic()+timeout
    class ReadConnection(sqlite3.Connection):
        def execute(self,*args,**kwargs):
            start=time.perf_counter()
            try:return super().execute(*args,**kwargs)
            finally:metrics['database_ms']+=(time.perf_counter()-start)*1000;metrics['database_queries']+=1
    db=sqlite3.connect(service.store.root.joinpath('gateway.sqlite').as_uri()+'?mode=ro',uri=True,timeout=2,factory=ReadConnection)
    db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON')
    db.set_progress_handler(lambda: int(time.monotonic()>scoped._observer_deadline),5000)
    @contextmanager
    def connection():yield db
    scoped.store.connect=connection
    try:yield scoped
    finally:db.close()

def reference_ids(rows):
    identifiers=set()
    for row in rows:
        payload=json.loads(row['payload'] or '{}');task=json.loads(row['task']);result=json.loads(row['result'] or '{}')
        identifiers.update(r.get('work_package_id') for r in task.get('references',[]) if isinstance(r,dict))
        identifiers.add(payload.get('native_id'));publication=result.get('native_readback') or {}
        identifiers.add(publication.get('child_id'))
        identifiers.update(v.get('id') for v in publication.values() if isinstance(v,dict))
    return {i for i in identifiers if type(i) is int and i>0}

def summary(value):
    if not value or value=='NOT_RECORDED':return 'Chưa ghi nhận kết quả'
    try:data=json.loads(value)
    except (ValueError,TypeError):return ' '.join(str(value).split())[:240]
    if not isinstance(data,dict):return 'Recorded artifact · mở Inspector'
    parts=[]
    if data.get('files'):parts.append(str(len(data['files']))+' files · '+', '.join(data['files'])[:100])
    if data.get('head_sha'):parts.append('commit '+data['head_sha'][:8])
    if data.get('verdict'):parts.append('Review '+str(data['verdict']))
    qa=data.get('qa') or data.get('host_test') or {}
    if qa.get('status'):parts.append(str(qa['status']))
    if qa.get('exit_code') is not None:parts.append('exit code '+str(qa['exit_code']))
    return ' · '.join(parts) or 'Recorded artifact · mở Inspector'

def graph_summary(snapshot):
    result=dict(snapshot);result['view']='graph';result['events']=[];result['artifacts']=[]
    result['stages']=[{**stage,'summary':summary(stage.get('summary')),'summary_origin':'DETERMINISTIC_STORED_OUTPUT',
                      'artifact_count':sum(a['run_id']==stage['latest_run_id'] and a['type']==stage['agent_role']+'_output' for a in snapshot['artifacts']),
                      'checkpoint':{k:v for k,v in stage.get('checkpoint',{}).items() if k in {'version','stage','resumable','error'}},
                      'resume':{k:v for k,v in stage.get('resume',{}).items() if k in {'eligible','reason'}}} for stage in snapshot['stages']]
    result['runs']=[{k:v for k,v in run.items() if k not in {'checkpoint','resume','error_message'}} for run in snapshot['runs']]
    result['checkpoint']={k:v for k,v in snapshot.get('checkpoint',{}).items() if k in {'version','stage','resumable','error'}}
    result['resume']={k:v for k,v in snapshot.get('resume',{}).items() if k in {'eligible','reason'}}
    return result

def detail_page(snapshot,section,offset,limit,monitors=None,stage=None):
    if section in {'events','artifacts','runs'}:
        values=list(reversed(snapshot[section]));page=values[offset:offset+limit]
        if section=='runs':
            by_id={m['run_id']:m for m in monitors or []}
            page=[{**run,'nodes':[{k:v for k,v in node.items() if k in {'id','agent','name','objective','state','started_at','ended_at','calls','retries','errors','error_code'}}|
                                {'output':summary(node.get('output'))} for node in by_id.get(run['run_id'],{}).get('nodes',[]) if node.get('agent') not in {'supervisor','final','tools','provider','native'}]} for run in page]
        return {'task_id':snapshot['task_id'],'project_id':snapshot['project_id'],'revision':snapshot['revision'],'section':section,
                'items':page,'offset':offset,'next_offset':offset+len(page) if offset+len(page)<len(values) else None,
                'total_available':len(values),'truncated':snapshot['truncated'],'source_limits':{'runs':50,'events_per_run':200},'observed_at':snapshot['freshness']['observed_at']}
    if section=='overview':
        result=graph_summary(snapshot)
        result['stages']=[s for s in snapshot['stages'] if not stage or s['stage_key']==stage]
        result['artifacts']=[a for a in snapshot['artifacts'] if a['type']=='github_pr' or stage and a['type']==stage+'_output'][-10:]
        result['checkpoint']=snapshot['checkpoint'];result['resume']=snapshot['resume'];result['runs']=snapshot['runs'][-10:]
        return result
    raw={k:v for k,v in snapshot.items() if k not in {'events','artifacts','runs','stages'}}
    raw['stages']=[s for s in snapshot['stages'] if not stage or s['stage_key']==stage];raw['runs']=snapshot['runs'][-1:]
    return {'task_id':snapshot['task_id'],'project_id':snapshot['project_id'],'revision':snapshot['revision'],'section':'technical','snapshot':raw}

def light_list(service,actor,native,args):
    from .agent_observer import _rows,STATES,public
    limit=args.get('limit',20);offset=args.get('offset',0);query=args.get('query','');state=args.get('state','ALL')
    if type(limit) is not int or not 1<=limit<=50 or type(offset) is not int or not 0<=offset<=200 or not isinstance(query,str) or len(query)>160 or state not in set(STATES.values())|{'UNKNOWN','ALL'}:raise ValueError('OBSERVER_FILTER_INVALID')
    rows=_rows(service,actor,limit=200);by_task={}
    for row in rows:
        identifiers=[row['owner_id']] if row['owner_id'] else [r.get('work_package_id') for r in json.loads(row['task']).get('references',[]) if isinstance(r,dict)]
        for identifier in identifiers:
            if type(identifier) is int and identifier>0:by_task.setdefault(identifier,[]).append(row)
    reader=ReadNative(native,getattr(service,'_observer_metrics',None),getattr(service,'_observer_deadline',None))
    response=None
    if hasattr(native,'observer_task_list'):
        try:response=reader.native.observer_task_list(query,200)
        except NativeError as error:
            if error.status!=404:raise
            reader.batch_supported=False
    if response is not None:
        if response.get('project_id')!=service.config['project_id']:raise PermissionError('OBSERVER_METADATA_SCOPE_INVALID')
        packages=response['items'];truncated=response.get('truncated',False)
    else:
        reader.prime(by_task);packages=[];truncated=len(rows)>=200
        for identifier in by_task:
            try:packages.append(reader.package(identifier))
            except (PermissionError,NativeError):continue
    items=[];now=time.time()
    for package in packages:
        identifier=package['id']
        if query and query.lstrip('#').casefold() not in (str(identifier)+' '+package.get('subject','')).casefold():continue
        history=by_task.get(identifier,[]);latest=history[0] if history else None
        raw=json.loads(latest['document']) if latest else {};result=json.loads(latest['result']) if latest else {}
        runtime=STATES.get(raw.get('state'),'UNKNOWN')
        if result.get('status')=='blocked':runtime='BLOCKED'
        updated=raw.get('updated_at') or raw.get('created_at');age=max(0,now-updated) if type(updated) in (int,float) else None
        fresh='UNKNOWN' if not history else 'STALE' if age is None or age>120 else 'FRESH'
        if runtime=='RUNNING' and fresh!='FRESH':runtime='UNKNOWN'
        if state!='ALL' and runtime!=state:continue
        items.append({'project_id':service.config['project_id'],'task_id':identifier,'task_title':package.get('subject'),
                      'business_status':package.get('_links',{}).get('status',{}).get('title','UNKNOWN'),'workflow_status':runtime,
                      'current_stage':result.get('stage') if runtime=='RUNNING' else None,'latest_run_id':latest['id'] if latest else None,
                      'updated_at':updated,'run_count':len(history),'freshness':{'freshness_status':fresh,'source_updated_at':updated,'observed_at':now},
                      'partial':bool(history and raw.get('state') not in STATES)})
    page=items[offset:offset+limit]
    return public({'view':'list','project_id':service.config['project_id'],'items':page,'observed_at':now,'limit':limit,'offset':offset,
                   'next_offset':offset+len(page) if offset+len(page)<len(items) else None,'truncated':truncated or len(rows)>=200,'source_run_scan_limit':200})

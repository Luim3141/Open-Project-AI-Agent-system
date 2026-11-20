"""Approved Task[Bug] mapping; persistence uses existing exact-hash proposals."""
import re

from .native import NativeError
from .store import digest

MAPPING_APPROVAL='02bae765000c1c152179db1d357519898fc923445d4e31392ff00029fddb9e40'
REPORT_FIELDS={'subject','reproduction','expected','actual','severity','evidence'}


def positive(value):
    if type(value) is not int or value<=0:raise ValueError('POSITIVE_NATIVE_ID_REQUIRED')
    return value


def text(value,maximum=4000):
    if not isinstance(value,str) or not 1<=len(value.strip())<=maximum:raise ValueError('BUG_TEXT_REQUIRED_OR_TOO_LONG')
    return value.strip()


def mapping(service,read_only=False):
    if (read_only and service.mode=='native' and service.config['project_id']==6
            and service.config.get('_engineering_scope') is True and service.config.get('engineering',{}).get('enabled') is True):
        return
    if service.mode!='native' or service.config['project_id']!=5 or service.config.get('bug_task_mapping_sha256')!=MAPPING_APPROVAL:
        raise PermissionError('BUG_MAPPING_NOT_APPROVED')


def report_fields(service,report):
    if not isinstance(report,dict):raise ValueError('BUG_REPORT_REQUIRED')
    service.keys(report,REPORT_FIELDS,REPORT_FIELDS)
    report={k:text(v,240 if k=='subject' else 4000) for k,v in report.items()}
    if report['severity'] not in {'low','medium','high','critical'}:raise ValueError('BUG_SEVERITY_INVALID')
    report['subject']=re.sub(r'^\[Bug\]\s*','',report['subject'],flags=re.I).strip()
    if not report['subject']:raise ValueError('BUG_SUBJECT_REQUIRED')
    return report


def bug(native,identifier):
    item=native.package(positive(identifier))
    if not (item.get('subject','').startswith('[Bug] ') and item.get('_links',{}).get('type',{}).get('href')=='/api/v3/types/1'):
        raise ValueError('BUG_TASK_REQUIRED')
    return item


def duplicates(native,subject,exclude=None):
    # Lexical candidates inform human triage; they never prove equivalence or uniqueness.
    tokens=lambda value:set(re.findall(r'\w+',re.sub(r'^\[Bug\]\s*','',value,flags=re.I).casefold()))
    wanted=tokens(subject);rows=[]
    for item in native.packages():
        if item['id']==exclude:continue
        candidate=tokens(item.get('subject',''));score=len(wanted&candidate)/max(1,len(wanted|candidate))
        if score>=0.6:
            rows.append({'id':item['id'],'lock_version':item['lockVersion'],'subject':item['subject'],
                         'score':round(score,3),'citation':f"/work_packages/{item['id']}"})
    return sorted(rows,key=lambda r:(-r['score'],r['id']))[:20]


def triage(service,who,native,args):
    mapping(service,read_only=True);service.keys(args,{'id','report'})
    if ('id' in args)==('report' in args):raise ValueError('ONE_BUG_TARGET_REQUIRED')
    if 'report' in args:
        report=report_fields(service,args['report']);item=None;subject=report['subject'];comments=[]
    else:
        item=bug(native,args['id']);subject=item['subject'];report=None
        comments=[{'id':r['id'],'comment':r.get('comment',{}),'author':r.get('_links',{}).get('user'),
                   'created_at':r.get('createdAt')} for r in native.collection(f"/api/v3/work_packages/{item['id']}/activities")
                  if r.get('comment',{}).get('raw')]
    return {'actor_id':who['user_id'],'project_id':service.config['project_id'],'classification':'Bug report',
            'native_type_id':1,'mapping_approval_sha256':MAPPING_APPROVAL if service.config['project_id']==5 else None,'report':report,
            'native_id':item['id'] if item else None,'native_version':item['lockVersion'] if item else None,
            'native_status':item.get('_links',{}).get('status') if item else None,
            'native_assignee':item.get('_links',{}).get('assignee') if item else None,
            'duplicates':duplicates(native,subject,item['id'] if item else None),'duplicate_method':'LEXICAL_CANDIDATES_REQUIRE_HUMAN_REVIEW',
            'description':item.get('description') if item else None,'submitted_evidence':comments,
            'qa_verification':'NOT_VERIFIED','native_mutations':False,'approval_required_for_native_write':True}


def propose(service,who,native,args,request_key):
    mapping(service);operation=args.get('operation')
    if operation=='create':
        service.keys(args,{'operation','report','source_id','duplicate_disposition','assignee_id'},{'operation','report','source_id'})
        report=report_fields(service,args['report']);source=args['source_id']
        if not isinstance(source,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',source):raise ValueError('SOURCE_ID_REQUIRED')
        matches=duplicates(native,report['subject'])
        disposition=text(args['duplicate_disposition']) if 'duplicate_disposition' in args else None
        if matches and not disposition:raise ValueError('DUPLICATE_DISPOSITION_REQUIRED')
        refs='\n'.join(f"- #{r['id']} v{r['lock_version']} — {r['subject']} (score {r['score']})" for r in matches)
        sections={'Report and reproduction':report['reproduction'],
                  'Expected/actual behavior':f"Expected: {report['expected']}\nActual: {report['actual']}",
                  'Severity and source evidence':f"Severity: {report['severity']}\n{report['evidence']}\nEvidence verification: NOT_VERIFIED_BY_SYSTEM",
                  'Duplicate references':(refs or 'No lexical candidate in current visible snapshot; not proof of uniqueness.')+'\nDisposition: '+(disposition or 'No candidate to disposition'),
                  'Fix tracking':'Not submitted','QA retest evidence':'Not submitted; NOT_VERIFIED_BY_SYSTEM','Review':'Not submitted'}
        description='\n\n'.join('## '+key+'\n'+value for key,value in sections.items())
        command={'action':'create_work_package','arguments':{'source_id':source,'type_id':1,'status_id':1,
                 'subject':'[Bug] '+report['subject'],'description':description}}
        links={'project':{'href':f'/api/v3/projects/{native.project_id}'},'type':{'href':'/api/v3/types/1'},'status':{'href':'/api/v3/statuses/1'}}
        if 'assignee_id' in args:
            identifier=positive(args['assignee_id']);service.assignee(identifier)
            command['arguments']['assignee_id']=identifier;links['assignee']={'href':f'/api/v3/users/{identifier}'}
        payload={'subject':command['arguments']['subject'],'description':{'format':'markdown','raw':description},
                 service.config['source_field']:source,'_links':links}
        form=native.call(f'/api/v3/projects/{native.project_id}/work_packages/form','POST',payload)
        if errors:=form.get('_embedded',{}).get('validationErrors'):raise NativeError(422,'OPENPROJECT_FORM_REJECTED',errors)
    else:
        extra={'assign':{'assignee_id'},'fix':{'text'},'retest':{'text'},'review':{'text'},'transition':{'status_id'}}
        if operation not in extra:raise ValueError('BUG_OPERATION_INVALID')
        required={'operation','id','lock_version'}|extra[operation]
        allowed=required|({'qa_evidence_id','qa_evidence_hash'} if operation=='transition' else set())
        service.keys(args,allowed,required)
        item=bug(native,args['id'])
        if type(args['lock_version']) is not int or args['lock_version']!=item['lockVersion']:raise ValueError('STALE_WORK_PACKAGE')
        target={'id':item['id'],'lock_version':item['lockVersion']}
        if operation=='assign':
            identifier=positive(args['assignee_id']);service.assignee(identifier)
            command={'action':'update_work_package','arguments':{**target,'changes':{'assignee_id':identifier}}}
        elif operation=='transition':
            status=positive(args['status_id'])
            if status not in service.config['status_ids']:raise ValueError('STATUS_DENIED')
            command={'action':'transition','arguments':{**target,'status_id':status}}
            command['arguments'].update({k:args[k] for k in ('qa_evidence_id','qa_evidence_hash') if k in args})
        else:
            command={'action':'comment','arguments':{**target,'text':f'[Bug] {operation} evidence — NOT_VERIFIED_BY_SYSTEM\n'+text(args['text'])}}
    key='bug-draft-'+digest(f"{who['user_id']}:{request_key}")
    # Existing preview/decision/lock/RAG outbox owns execution; this adapter only drafts.
    return service.execute_actor(who['user_id'],{**command,'idempotency_key':key})['result']

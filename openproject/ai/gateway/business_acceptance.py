"""Private one-shot Owner consent: exact create only, durable claim, bounded provider calls."""
import json
import math
import time
import uuid
from pathlib import Path

from .gemini import ProviderError
from .store import canonical, digest


class BusinessAcceptance:
    def __init__(self, service, payload):
        self.service, self.payload = service, payload
        self.document = json.loads((service.store.root/'business-acceptance.json').read_text())
        d = self.document
        if (set(d) != {'id','actor','project','prompt_sha256','scope','create','expires'} or
                str(uuid.UUID(d['id'])) != d['id'] or d['actor'] != payload['actor'] or
                d['project'] != service.config['project_id'] or d['scope'] != payload['write_scope_ids'] or
                d['prompt_sha256'] != digest(payload['prompt']) or payload['allow_routine_writes'] is not True or
                type(d['expires']) not in (int,float) or not math.isfinite(d['expires']) or not time.time() < d['expires'] or
                set(d['create']) != {'subject','type_id','parent_id','assignee_id'} or
                not isinstance(d['create']['subject'],str) or not d['create']['subject'].strip() or
                any(type(d['create'][k]) is not int or d['create'][k]<=0 for k in ('type_id','parent_id','assignee_id')) or
                d['scope'] != [d['create']['parent_id']]):
            raise ProviderError('OWNER_BUSINESS_CONSENT_MISMATCH')
        with service.store.connect() as db:
            row = db.execute('select created from ai_runs where id=? and actor=?',(payload['id'],payload['actor'])).fetchone()
        if not row:raise ProviderError('OWNER_STORED_RUN_REQUIRED')
        from .live_agents import LiveBudget, LiveConfig
        self.budget = LiveBudget(LiveConfig(enabled=True,max_model_calls=3,max_http_attempts=6,
            max_output_tokens=1500,timeout_seconds=180,call_timeout_seconds=90,retry_limit=0))
        self.budget.deadline=min(self.budget.deadline,time.monotonic()+180-(time.time()-row['created']),
                                 time.monotonic()+d['expires']-time.time())
        key='owner-run-'+d['id']
        claimed=service.store.begin(payload['actor'],key,{'run':payload['id'],'consent_sha256':digest(canonical(d))})
        if claimed is not None:raise ProviderError('OWNER_BUSINESS_REQUEST_ALREADY_CLAIMED')
        service.store.finish(payload['actor'],key,{'run':payload['id'],'state':'CLAIMED_NO_AUTOMATIC_REPLAY'})
        self.create_key='owner-create-'+d['id']

    @classmethod
    def load(cls,service,payload):
        path=service.store.root/'business-acceptance.json'
        if not path.exists():return None
        document=json.loads(path.read_text())
        return cls(service,payload) if document.get('actor')==payload['actor'] else None

    def command(self,action,arguments):
        self.budget.check_cancel()
        if time.monotonic()>=self.budget.deadline:raise ProviderError('GEMINI_RUN_DEADLINE')
        if action not in {'identity','get_project_options','get_work_package','list_work_packages','analyze','create_work_package'}:
            raise PermissionError('OWNER_ONLY_EXACT_CREATE_AUTHORIZED')
        if action=='get_work_package' and arguments.get('id') not in self.document['scope']:
            # Readback of a newly created item remains valid, but cannot expand mutation consent.
            try:r=self.service.store.request_status(self.payload['actor'],self.create_key)
            except ValueError:r={}
            if arguments.get('id')!=(r.get('result') or {}).get('result',{}).get('id'):
                raise PermissionError('OWNER_READ_TARGET_OUTSIDE_SCOPE')
        if action!='create_work_package':return arguments
        args=dict(arguments)
        if args.get('assignee_role')=='QA' and self.service.role_assignee('QA')==self.document['create']['assignee_id']:
            args.pop('assignee_role');args['assignee_id']=self.document['create']['assignee_id']
        args.pop('source_id',None)
        if args.get('description')=='':args.pop('description')
        if canonical(args)!=canonical(self.document['create']):raise PermissionError('OWNER_CREATE_FIELDS_MISMATCH')
        native,_=self.service.native_actor(self.payload['actor']);native.package(args['parent_id'])
        matches=[p for p in native.packages() if p.get('_links',{}).get('parent',{}).get('href')==f"/api/v3/work_packages/{args['parent_id']}"
                 and ' '.join(p['subject'].split()).casefold()==' '.join(args['subject'].split()).casefold()]
        if matches:
            try:r=self.service.store.request_status(self.payload['actor'],self.create_key)
            except ValueError:r={}
            if len(matches)!=1 or r.get('state')!='done' or (r.get('result') or {}).get('result',{}).get('id')!=matches[0]['id']:
                raise PermissionError('OWNER_SUBTASK_ALREADY_EXISTS_RECONCILE')
        return {**args,'source_id':'owner-'+self.document['id']}

    def post(self,gemini,client,store,policy,phase,body):
        self.budget.before_attempt(phase)
        receipt={'id':str(uuid.uuid4()),'project':policy['project'],'native_project_id':self.document['project'],
            'actor':self.payload['actor'],'run_id':self.payload['id'],'agent':'business_worker','phase':phase,
            'model':policy['model'],'at':time.time(),'state':'ATTEMPTING','attempt':0,'usage':None,'http_status':None}
        store.provider_receipt(receipt)
        try:
            answer=gemini.sdk_post(client,policy,phase,body)
            receipt.update(state='MOCK_SUCCESS' if getattr(client[1],'is_mock_transport',False) else 'LIVE_SUCCESS',
                http_status=getattr(client[1],'last_status',200),usage=answer.get('usageMetadata'),
                input_tokens=answer.get('totalTokens') if phase=='countTokens' else None)
            return answer
        except Exception as error:
            receipt.update(state='FAILED',http_status=getattr(client[1],'last_status',None),error_type=type(error).__name__)
            raise
        finally:store.provider_receipt(receipt)

    def metadata(self):
        return {'approval_id':self.document['id'],'max_http':6,'max_generations':3,'max_output_tokens':1500,
                'timeout_seconds':180,'http_attempts':self.budget.http_attempts,'generations':self.budget.generations,
                'native_create_request_key':self.create_key}

    @staticmethod
    def recovered_view(store,actor,run,native):
        """Show proven recovery without rewriting the failed worker or inventing a model summary."""
        if run.get('state')!='failed_or_unknown':return run
        with store.connect() as db:
            rows=db.execute("""SELECT r.result FROM requests c JOIN requests r ON r.actor=c.actor
                AND r.key='owner-create-'||substr(c.key,11) WHERE c.actor=? AND c.key LIKE 'owner-run-%'
                AND json_extract(c.payload,'$.run')=? AND c.state='done' AND r.state='done'""",(actor,run['id'])).fetchall()
        if len(rows)!=1:return run
        receipt=json.loads(rows[0]['result'])
        if receipt.get('reconciled') is not True:return run
        native.package(receipt['result']['id'])  # A historical receipt never bypasses current Native visibility.
        from .gemini import Gemini
        from .presentation import execution_report
        result=json.loads(json.dumps(run.get('result') or {}));calls=result.get('tools',[])
        unknown=[c for c in calls if c.get('action')=='create_work_package' and c.get('result',{}).get('outcome_unknown')]
        if len(unknown)!=1:return run
        unknown[0]['result']=Gemini.business_result('create_work_package',receipt)
        result.update(execution_report(calls))
        result.update(tools=calls,native_reconciled=True,provider_report_completed=False,
            original_worker_state=run['state'],status='partial',
            heading='Native đã xác nhận sau timeout — không gửi lại yêu cầu',
            message='Subtask đã được đối soát bằng source marker và author. Gemini đã dừng trong ngân sách; không có bản tổng hợp model mới.')
        return {**run,'result':result}

"""Isolated Native QA attestations, independent review and ordinary exact approvals."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.native import NativeError
from gateway.service import Service,Command
from gateway.store import Store,canonical


class NativeQaEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name);self.store=Store(self.root)
        roles={18:'AI_SYSTEM_OWNER',19:'PM',20:'BA',21:'BE',22:'FE',23:'QA'}
        self.tokens={a:self.store.issue_token(a,r,r) for a,r in roles.items()}
        self.artifact=b'Isolated manually reviewed test log: expected401, observed401. Not a Main execution.'
        self.manifest={'schema':'QLDAPM_QA_EVIDENCE_V1','work_package_id':371,'source_version':1,
            'criteria':{'AC1':'Unauthorized requests receive401'},'tests':[{'criterion_id':'AC1','reference':'TC-AUTH-1',
            'expected':'HTTP401','actual':'HTTP401','outcome':'PASSED'}],
            'attachment_id':99,'attachment_sha256':hashlib.sha256(self.artifact).hexdigest(),
            'related_run_id':None}
        class Native:
            project_id=5;writes=[];denied=False;form_errors={};artifact=self.artifact
            row={'id':371,'lockVersion':1,'subject':'[Bug] Isolated auth check','description':{'raw':'AC1: Unauthorized requests receive401'},
                '_links':{'project':{'href':'/api/v3/projects/5'},'type':{'href':'/api/v3/types/1'},'status':{'href':'/api/v3/statuses/7'},
                    'assignee':{'href':'/api/v3/users/21'}}}
            activity={'id':4242,'createdAt':'2026-10-25T00:00:00Z','comment':{'raw':canonical(self.manifest)},
                '_links':{'workPackage':{'href':'/api/v3/work_packages/371'},'user':{'href':'/api/v3/users/23'}}}
            attachment={'id':99,'fileName':'manual-test.log','fileSize':len(self.artifact),'contentType':'text/plain',
                '_links':{'container':{'href':'/api/v3/work_packages/371'},'author':{'href':'/api/v3/users/23'},
                    'staticDownloadLocation':{'href':'/api/v3/attachments/99/content'}}}
            def __init__(self,url,credential,project):self.role=credential
            def identity(self,actor):return {'user_id':actor,'role':self.role,'project_id':5,'capabilities':[self.role]}
            def package(self,identifier):
                if identifier!=371 or self.denied:raise NativeError(403,'NOT_VISIBLE')
                return copy.deepcopy(self.row)
            def collection(self,path):
                if path=='/api/v3/work_packages/371/activities':return [copy.deepcopy(self.activity)]
                raise AssertionError(path)
            def call(self,path,method='GET',payload=None,**kwargs):
                if path=='/api/v3/qldapm/capabilities':return {'project_id':5,'qa_bridge_version':0,'enforced':True}
                if path=='/api/v3/attachments/99':return copy.deepcopy(self.attachment)
                if path=='/api/v3/attachments/99/content' and kwargs.get('binary'):return self.artifact
                if path=='/api/v3/statuses/9':return {'id':9,'name':'REVIEW','isClosed':False}
                if path.endswith('/form'):return {'_embedded':{'validationErrors':self.form_errors}}
                if method=='PATCH':
                    if payload['lockVersion']!=self.row['lockVersion']:raise NativeError(409,'STALE_NATIVE')
                    self.writes.append(copy.deepcopy(payload));self.row['lockVersion']+=1;self.row['_links'].update(payload.get('_links',{}))
                    return copy.deepcopy(self.row)
                raise AssertionError((path,method))
        self.native=Native
        self.service=Service(self.store,{'project_id':5,'gateway_mode':'native','openproject_url':'http://127.0.0.1:8088',
            'users':{str(a):r for a,r in roles.items()},'type_ids':[1,5,10],'status_ids':[1,7,9],'source_field':'customField1'},self.root/'workspace',Native)

    def call(self,actor,action,args,key=None):
        c={'action':action,'arguments':args}
        if key:c['idempotency_key']=key
        return self.service.execute(self.tokens[actor],c)['result']

    def capture(self,key='capture-qa'):
        return self.call(23,'qa_evidence_capture',{'native_id':371,'activity_id':4242},key)

    def accept(self,evidence,actor=18):return self.service.decide_qa_evidence(self.tokens[actor],evidence['id'],'accept',evidence['hash'])

    def test_native_filtered_inbox_rechecks_target_permission_without_deciding_evidence(self):
        evidence=self.capture()
        result=self.call(18,'qa_evidence_list',{'native_id':371})
        self.assertEqual([r['id'] for r in result['items']],[evidence['id']])
        self.assertEqual(result['items'][0]['state'],'pending')
        for invalid in [None,True,0,'371']:
            with self.subTest(native_id=invalid),self.assertRaises(ValueError):
                self.call(18,'qa_evidence_list',{'native_id':invalid})
        self.native.denied=True
        with self.assertRaises(NativeError):self.call(18,'qa_evidence_list',{'native_id':371})
        self.assertEqual(self.native.writes,[])

    def test_other_roles_and_caller_qa_claims_cannot_capture_qa_attestation(self):
        for actor in [18,19,20,21,22]:
            with self.assertRaisesRegex(PermissionError,'QA_NATIVE_AUTHOR_REQUIRED'):
                self.call(actor,'qa_evidence_capture',{'native_id':371,'activity_id':4242},'not-qa-'+str(actor))
        with self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):
            self.call(23,'qa_evidence_capture',{'native_id':371,'activity_id':4242,'qa_pass':True,'actor_id':23},'forged')
        self.assertEqual(self.native.writes,[])

    def test_native_author_version_criteria_container_or_attachment_tamper_are_denied(self):
        original=copy.deepcopy(self.native.activity)
        variants=[lambda m:m.update(source_version=0),lambda m:m['criteria'].update(AC2='Not in Native source'),
                  lambda m:m.update(attachment_sha256='0'*64),lambda m:m.update(qa_pass=True),
                  lambda m:m['criteria'].update(AC1='Unauthorized requests')]
        for i,mutate in enumerate(variants):
            m=copy.deepcopy(self.manifest);mutate(m);self.native.activity['comment']['raw']=canonical(m)
            with self.assertRaises((ValueError,NativeError)):self.capture('invalid-'+str(i))
        self.native.activity=copy.deepcopy(original);self.native.activity['_links']['user']['href']='/api/v3/users/21'
        with self.assertRaises(PermissionError):self.capture('forged-author')
        self.native.activity=copy.deepcopy(original);self.native.attachment['_links']['container']['href']='/api/v3/work_packages/999'
        with self.assertRaises(PermissionError):self.capture('foreign-attachment')

    def test_model_context_self_review_wrong_hash_and_replay_remain_denied(self):
        from gateway.agent_trace import current_run
        e=self.capture()
        with self.assertRaises(PermissionError):self.accept(e,23)
        with self.assertRaises(NativeError):self.service.decide_qa_evidence(self.tokens[18],e['id'],'accept','0'*64)
        from types import SimpleNamespace
        token=current_run.set((self.store,SimpleNamespace(actor_id=23,project_id=5,run_id='isolated-model-context',trace_id='isolated-trace',task_id=None)))
        try:
            with self.assertRaises(PermissionError):self.capture('model-capture')
            with self.assertRaises(PermissionError):self.capture()
            with self.assertRaises(PermissionError):self.accept(e)
        finally:current_run.reset(token)
        self.accept(e)
        with self.assertRaises(NativeError):self.accept(e)

    def test_manual_evidence_review_and_transition_still_need_exact_native_approval(self):
        e=self.capture();self.assertEqual(e['verification_kind'],'MANUAL_ATTESTATION');self.assertFalse(e['ready'])
        self.assertEqual(e['role'],'QA');self.assertGreater(e['captured_at'],0)
        self.assertEqual(e['binding']['activity_created_at'],'2026-10-25T00:00:00Z')
        self.assertEqual(self.capture()['id'],e['id']);self.assertEqual(e['actor'],23)
        with self.assertRaises(NativeError):self.call(18,'qa_transition_prepare',{'id':e['id'],'hash':e['hash'],'status_id':9},'not-reviewed')
        accepted=self.accept(e);self.assertTrue(accepted['ready']);self.assertEqual(accepted['reviewer'],18)
        with self.assertRaises(NativeError):self.call(18,'transition',{'id':371,'lock_version':1,'status_id':9},'bypass-ledger')
        p=self.call(18,'qa_transition_prepare',{'id':e['id'],'hash':e['hash'],'status_id':9},'qa-draft')
        self.assertEqual(p['state'],'pending');self.assertEqual(self.native.writes,[])
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],p['id'],'approve','0'*64)
        receipt=self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.assertEqual(receipt['result']['lockVersion'],2);self.assertEqual(len(self.native.writes),1)
        claim=self.store.claim_knowledge_sync();self.assertEqual(claim['native_id'],371)
        self.store.finish_knowledge_sync(claim,{'vector_indexed':True,'fixture':'isolated receipt'})
        self.assertEqual(self.store.knowledge_sync(18,receipt['knowledge_sync']['id'])['state'],'verified')
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        with self.assertRaisesRegex(ValueError,'CUSTOM_GATE_UNSUPPORTED_IN_NATIVE_MODE'):self.call(18,'get_gate',{'id':371})

    def test_stale_native_comment_artifact_and_revoked_access_block_review_or_write(self):
        e=self.capture();self.accept(e)
        p=self.call(18,'qa_transition_prepare',{'id':e['id'],'hash':e['hash'],'status_id':9},'before-drift')
        self.native.artifact=b'Changed after review'
        with self.assertRaises((NativeError,ValueError)):self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.assertEqual(self.native.writes,[])
        self.native.artifact=self.artifact;self.native.row['lockVersion']=2
        self.assertFalse(self.call(23,'qa_evidence_get',{'id':e['id']})['source_current'])
        self.native.denied=True
        with self.assertRaises(NativeError):self.call(18,'qa_evidence_get',{'id':e['id']})

    def test_failed_or_incomplete_test_outcomes_never_become_ready(self):
        m=copy.deepcopy(self.manifest);m['tests'][0]['outcome']='FAILED';self.native.activity['comment']['raw']=canonical(m)
        e=self.capture();accepted=self.accept(e);self.assertFalse(accepted['ready'])
        with self.assertRaises(NativeError):self.call(18,'qa_transition_prepare',{'id':e['id'],'hash':e['hash'],'status_id':9},'failed-test')
        self.assertEqual(self.native.writes,[])

    def test_native_form_rejection_is_preserved_and_does_not_create_write(self):
        e=self.capture();self.accept(e);self.native.form_errors={'status':{'message':'Native policy disallows transition'}}
        with self.assertRaisesRegex(NativeError,'OPENPROJECT_FORM_REJECTED'):
            self.call(18,'qa_transition_prepare',{'id':e['id'],'hash':e['hash'],'status_id':9},'native-policy')
        self.assertEqual(self.native.writes,[])

    def test_review_http_auth_scope_forgery_and_no_mcp_review_tool(self):
        from gateway.app import create_app
        from starlette.testclient import TestClient
        e=self.capture();path='/api/v1/qa-evidence/'+e['id']+'/decision'
        self.assertNotIn('qa_evidence_review',Command.model_fields['action'].annotation.__args__)
        with TestClient(create_app(service=self.service),base_url='http://localhost:8090') as client:
            self.assertEqual(client.post(path,json={'decision':'accept','hash':e['hash']}).status_code,401)
            self.assertEqual(client.post(path,headers={'Authorization':'Bearer '+self.tokens[20]},json={'decision':'accept','hash':e['hash']}).status_code,403)
            self.assertEqual(client.post(path,headers={'Authorization':'Bearer '+self.tokens[18]},json={'decision':'accept','hash':e['hash'],'qa_pass':True}).status_code,422)
            self.assertEqual(client.post(path,headers={'Authorization':'Bearer '+self.tokens[18]},json={'decision':'accept','hash':e['hash']}).status_code,200)
            for actor in [18,19,20,21,22,23]:
                headers={'Authorization':'Bearer '+self.tokens[actor],'Accept':'application/json, text/event-stream'}
                response=client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':'tools/list'})
                names={tool['name'] for tool in response.json()['result']['tools']}
                self.assertEqual('qa_evidence_capture' in names,actor==23)
                self.assertNotIn('qa_evidence_review',names)

    def test_concurrent_review_has_one_winner_and_restart_preserves_consumed_decision(self):
        import concurrent.futures
        import threading
        e=self.capture();barrier=threading.Barrier(2)
        def review(actor):
            barrier.wait()
            try:self.accept(e,actor);return 200
            except NativeError as error:return error.status
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            outcomes=list(pool.map(review,[18,19]))
        self.assertEqual(sorted(outcomes),[200,409])
        self.store=Store(self.root)
        self.service=Service(self.store,self.service.config,self.root/'workspace',self.native)

    def test_signed_human_ui_review_uses_fresh_actor_policy_and_cannot_be_a_model_tool(self):
        import hmac,time,uuid
        from gateway.app import create_app
        from starlette.testclient import TestClient
        e=self.capture();key=b'isolated-ui-key';(self.root/'ui.key').write_bytes(key)
        def request(actor=18,command=None,operation='qa_review',signature=None):
            payload={'actor':actor,'project':5,'audience':'qldapm-ai-ui','at':time.time(),
                'nonce':uuid.uuid4().hex,'operation':operation,
                'command':command or {'id':e['id'],'hash':e['hash'],'decision':'accept'}}
            body=canonical(payload).encode()
            return client.post('/internal/ui',content=body,headers={
                'Content-Type':'application/json','X-Qldapm-Signature':signature or hmac.new(key,body,hashlib.sha256).hexdigest()})
        with TestClient(create_app(service=self.service),base_url='http://localhost:8090') as client:
            self.assertEqual(request(signature='0'*64).status_code,403)
            for actor in [20,21,22,23]:self.assertEqual(request(actor).status_code,403)
            with patch.object(self.native,'identity',side_effect=PermissionError('NATIVE_ROLE_REVOKED')):
                self.assertEqual(request().status_code,403)
            self.assertEqual(request(command={'id':e['id'],'hash':e['hash'],'decision':'accept','approved':True}).status_code,422)
            self.assertEqual(request(command={'id':e['id'],'hash':'0'*64,'decision':'accept'}).status_code,409)
            self.assertEqual(request(command={'id':e['id'],'hash':e['hash'],'decision':['accept']}).status_code,422)
            self.assertEqual(request(command={'action':'qa_review','arguments':{},'idempotency_key':'model-review'},operation='command').status_code,422)
            accepted=request();self.assertEqual(accepted.status_code,200,accepted.text)
            self.assertEqual(accepted.json()['result']['reviewer'],18)
            self.assertTrue(accepted.json()['result']['ready'])
            self.assertEqual(client.post('/internal/ui',content=accepted.request.content,
                headers={'Content-Type':'application/json','X-Qldapm-Signature':accepted.request.headers['X-Qldapm-Signature']}).status_code,403)
            self.assertEqual(request(19).status_code,409)
        self.assertEqual(self.native.writes,[])
        self.assertTrue(self.call(23,'qa_evidence_get',{'id':e['id']})['ready'])
        with self.assertRaises(NativeError):self.accept(e)
        self.assertEqual(self.capture('recovered-capture')['id'],e['id'])
        self.assertEqual(self.native.writes,[])

    def test_omitted_native_criteria_model_claims_and_changed_comment_never_become_ready(self):
        self.native.row['description']['raw']+='\nAC2: Response contains no token'
        with self.assertRaisesRegex(ValueError,'QA_ALL_NATIVE_CRITERIA_REQUIRED'):self.capture('missing-criterion')
        self.native.row['description']['raw']=self.native.row['description']['raw'].split('\n')[0]
        e=self.capture();self.native.activity['comment']['raw']+=' '
        self.assertFalse(self.call(23,'qa_evidence_get',{'id':e['id']})['source_current'])
        with self.assertRaises(NativeError):self.accept(e)
        self.native.activity['comment']['raw']=canonical(self.manifest)
        self.native.row['_links']['assignee']['href']='/api/v3/users/18'
        e=self.capture('assigned-reviewer')
        with self.assertRaises(PermissionError):self.accept(e)
        with self.assertRaises(PermissionError):self.call(21,'qa_evidence_get',{'id':e['id']})

    def test_bug_transition_binds_independently_reviewed_qa_without_elevating_developers(self):
        from gateway.bug_lifecycle import MAPPING_APPROVAL
        self.service.config['bug_task_mapping_sha256']=MAPPING_APPROVAL
        e=self.capture();self.accept(e)
        args={'operation':'transition','id':371,'lock_version':1,'status_id':9,
              'qa_evidence_id':e['id'],'qa_evidence_hash':e['hash']}
        with self.assertRaises(PermissionError):self.call(21,'bug_propose',args,'developer-transition')
        p=self.call(18,'bug_propose',args,'reviewed-bug-transition')
        self.assertEqual(p['command']['arguments']['qa_evidence_hash'],e['hash'])
        self.assertEqual(self.native.writes,[])
        receipt=self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.assertEqual(receipt['result']['lockVersion'],2)
        self.assertEqual(len(self.native.writes),1)


    def test_manual_review_state_and_exact_hash_audit_are_atomic(self):
        import sqlite3
        e=self.capture()
        with self.store.connect() as db:
            db.execute("CREATE TRIGGER fail_manual_review_audit BEFORE INSERT ON audit WHEN NEW.action='qa_evidence_accept' BEGIN SELECT RAISE(ABORT,'AUDIT_UNAVAILABLE'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.accept(e)
        with self.store.connect() as db:
            row=db.execute('select state,reviewer from qa_evidence where id=?',(e['id'],)).fetchone()
            self.assertEqual(tuple(row),('pending',None))
            db.execute('DROP TRIGGER fail_manual_review_audit')
        self.accept(e)
        with self.store.connect() as db:
            self.assertEqual([r[0] for r in db.execute("select version from audit where action='qa_evidence_accept' and target=?",(e['id'],))],[e['hash']])

    def test_manual_reviewer_revocation_blocks_ready_without_erasing_historical_accept(self):
        e=self.capture();self.accept(e)
        original=self.native.identity
        def identity(client,actor):
            if actor==18:raise NativeError(403,'REVIEWER_REVOKED')
            return original(client,actor)
        with patch.object(self.native,'identity',identity):
            result=self.call(23,'qa_evidence_get',{'id':e['id']})
            self.assertFalse(result['ready']);self.assertFalse(result['reviewers_current'])
            self.assertEqual(result['state'],'accepted');self.assertEqual(result['reviewer'],18)


class NativeQaArtifactTransportTests(unittest.TestCase):
    def call(self,body=b'not json',status=200,headers=None):
        import httpx
        from contextlib import contextmanager
        from gateway.native import Native
        @contextmanager
        def stream(*args,**kwargs):
            self.request=(args,kwargs)
            yield httpx.Response(status,content=body,headers=headers or {'content-type':'application/octet-stream'})
        with patch('gateway.native.httpx.stream',stream):
            return Native('http://127.0.0.1:8088','isolated-key',5).call('/api/v3/attachments/99/content',binary=True)

    def test_bounded_native_only_binary_transport_never_follows_download_urls(self):
        from gateway.native import Native
        self.assertEqual(self.call(),b'not json');self.assertFalse(self.request[1]['follow_redirects'])
        self.assertFalse(self.request[1]['trust_env'])
        self.assertEqual(self.call(body=b'not valid json',headers={'content-type':'application/json'}),b'not valid json')
        with self.assertRaisesRegex(NativeError,'TOO_LARGE'):self.call(body=b'x'*1048577)
        with self.assertRaisesRegex(NativeError,'REDIRECT_REFUSED'):self.call(status=302,headers={'location':'http://external.invalid/file'})
        with self.assertRaises(NativeError):self.call(status=403)
        native=Native('http://127.0.0.1:8088','isolated-key',5)
        for path in ['http://external.invalid/file','/api/v3/users/me','/api/v3/attachments/99/content?url=external','/api/v3/attachments/../99/content']:
            with self.assertRaises(ValueError):native.call(path,binary=True)
        with self.assertRaises(ValueError):native.call('/api/v3/attachments/99/content','POST',binary=True)




if __name__=='__main__':unittest.main()

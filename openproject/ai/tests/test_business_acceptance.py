"""One-shot Owner envelope; synthetic SDK transport, never calls Google or Main."""
import json
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from gateway.business_acceptance import BusinessAcceptance
from gateway.gemini import Gemini, ProviderError
from gateway.store import Store, digest


class BusinessAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.store=Store(self.root)
        self.payload={'id':self.store.create_run(19),'actor':19,'prompt':'Create one test child for 50',
                      'allow_routine_writes':True,'write_scope_ids':[50]}
        self.fields={'subject':'test','type_id':10,'parent_id':50,'assignee_id':23}
        self.doc={'id':str(uuid.uuid4()),'actor':19,'project':5,'prompt_sha256':digest(self.payload['prompt']),
                  'scope':[50],'create':self.fields,'expires':time.time()+600}
        self.save()
        self.rows=[]
        self.service=SimpleNamespace(store=self.store,config={'project_id':5},role_assignee=lambda role:23,
            native_actor=lambda actor:(SimpleNamespace(package=lambda i:{'id':i},packages=lambda:self.rows),None))
        (self.root/'gemini.key').write_text('synthetic-test-key-only')
        self.policy={'model':'gemini-3.5-flash-lite','data_scope':'project-business-content','project':'fixture',
                     'limits':{'rpm':100,'rpd':100,'tpm':1000000}}

    def save(self):
        (self.root/'business-acceptance.json').write_text(json.dumps(self.doc))

    def test_exact_fields_foreign_mutations_and_duplicate_guard(self):
        a=BusinessAcceptance.load(self.service,self.payload)
        expected={**self.fields,'source_id':'owner-'+self.doc['id']}
        self.assertEqual(a.command('create_work_package',self.fields),expected)
        for fields in ({**self.fields,'parent_id':51},{**self.fields,'assignee_id':24},
                       {**self.fields,'start_date':'2026-10-21'},{**self.fields,'subject':'test2'}):
            with self.assertRaisesRegex(PermissionError,'FIELDS_MISMATCH'):a.command('create_work_package',fields)
        for action in ('update_work_package','transition','comment','write_code','propose_operation'):
            with self.assertRaises(PermissionError):a.command(action,{'id':50})
        with self.assertRaises(PermissionError):a.command('get_work_package',{'id':51})
        self.rows.append({'id':367,'subject':'  TeST ','_links':{'parent':{'href':'/api/v3/work_packages/50'}}})
        with self.assertRaisesRegex(PermissionError,'ALREADY_EXISTS'):a.command('create_work_package',self.fields)
        self.store.begin(19,a.create_key,self.fields)
        self.store.finish(19,a.create_key,{'result':{'id':367}})
        self.assertEqual(a.command('create_work_package',self.fields),expected)
        self.assertEqual(a.command('get_work_package',{'id':367}),{'id':367})

    def test_durable_claim_forbids_second_run_and_worker_replay(self):
        BusinessAcceptance.load(self.service,self.payload)
        with self.assertRaisesRegex(ProviderError,'ALREADY_CLAIMED'):BusinessAcceptance.load(self.service,self.payload)
        p={**self.payload,'id':self.store.create_run(19)}
        with self.assertRaises(ValueError):BusinessAcceptance.load(self.service,p)

    def test_expiry_scope_prompt_and_false_checkbox_fail_before_claim(self):
        for delta in ({'expires':time.time()-1},{'expires':float('inf')},{'scope':[51]}, {'prompt_sha256':'bad'}):
            with self.subTest(delta=delta):
                original=dict(self.doc);self.doc.update(delta);self.save()
                with self.assertRaises(ProviderError):BusinessAcceptance.load(self.service,self.payload)
                self.doc=original
        self.save()
        with self.assertRaises(ProviderError):BusinessAcceptance.load(self.service,{**self.payload,'allow_routine_writes':False})
        self.assertIsNone(BusinessAcceptance.load(self.service,{**self.payload,'actor':23}))

    def test_real_sdk_loop_limits_usage_and_mock_provenance(self):
        a=BusinessAcceptance.load(self.service,self.payload);seen=[]
        turns=iter([[{'functionCall':{'name':'create_work_package','args':self.fields}}],
                    [{'text':'{"claims":[],"explanation":"Created #367"}'}]])
        def wire(request):
            body=json.loads(request.content);seen.append(request.url.path)
            if request.url.path.endswith(':countTokens'):return httpx.Response(200,json={'totalTokens':123})
            self.assertEqual(body['generationConfig']['maxOutputTokens'],1500)
            tools=[t['name'] for t in body['tools'][0]['functionDeclarations']]
            self.assertNotIn('update_work_package',tools);self.assertIn('create_work_package',tools)
            return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':next(turns)}}],
                'usageMetadata':{'promptTokenCount':123,'candidatesTokenCount':12,'totalTokenCount':135}})
        writes=[]
        def execute(action,args):
            writes.append(a.command(action,args));return {'result':{'id':367,'subject':'test','lockVersion':0,
                '_type':'WorkPackage','_links':{'status':{'href':'/api/v3/statuses/13'},
                'type':{'href':'/api/v3/types/10','title':'Subtask'},'parent':{'href':'/api/v3/work_packages/50'}}},'native_confirmed':True}
        with patch.object(Gemini,'settings',return_value=self.policy):
            result=Gemini(self.root).run(self.payload['prompt'],execute,httpx.MockTransport(wire),True,[50],actor_role='PM',acceptance=a)
        self.assertEqual(len(writes),1);self.assertEqual(len(seen),4)
        self.assertEqual(result['business_acceptance']['generations'],2);self.assertFalse(result['model_used'])
        with self.store.connect() as db:
            receipts=[json.loads(r[0]) for r in db.execute('select document from gemini_call_receipts')]
        self.assertEqual(len(receipts),4);self.assertTrue(all(r['state']=='MOCK_SUCCESS' and r['run_id']==self.payload['id'] for r in receipts))
        self.assertEqual(sum(r['usage']['totalTokenCount'] for r in receipts if r['phase']=='generateContent'),270)

    def test_429_503_never_retry_and_record_failure(self):
        for status in (429,503):
            with self.subTest(status=status):
                self.doc['id']=str(uuid.uuid4());self.save();a=BusinessAcceptance.load(self.service,self.payload);seen=[]
                def wire(request):
                    seen.append(request.url.path)
                    return httpx.Response(status,json={'error':{'code':status,'status':'RESOURCE_EXHAUSTED' if status==429 else 'UNAVAILABLE','message':'synthetic'}})
                with patch.object(Gemini,'settings',return_value=self.policy):
                    with self.assertRaises(ProviderError):Gemini(self.root).run(self.payload['prompt'],lambda *args:self.fail('NO_WRITE'),httpx.MockTransport(wire),True,[50],actor_role='PM',acceptance=a)
                self.assertEqual(len(seen),1)
                with self.store.connect() as db:
                    r=json.loads(db.execute('select document from gemini_call_receipts order by rowid desc limit 1').fetchone()[0])
                    db.execute('delete from gemini_blocks');db.execute('delete from gemini_recovery')
                self.assertEqual(r['state'],'FAILED');self.assertEqual(r['http_status'],status)

    def test_budget_stops_fourth_generation_before_http(self):
        a=BusinessAcceptance.load(self.service,self.payload)
        for _ in range(3):a.budget.before_attempt('countTokens');a.budget.before_attempt('generateContent')
        with self.assertRaisesRegex(ProviderError,'BUDGET_EXHAUSTED'):a.budget.before_attempt('countTokens')
        self.assertEqual(a.budget.http_attempts,6);self.assertEqual(a.budget.generations,3)
        a.budget.deadline=time.monotonic()-1
        with self.assertRaisesRegex(ProviderError,'DEADLINE'):a.command('create_work_package',self.fields)


if __name__=='__main__':unittest.main()

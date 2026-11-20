"""Stored, isolated BA outputs are data, never Native command authority."""
import copy
import json
import unittest
import uuid

from gateway.agent_models import AgentResult,NativeReference
from gateway.native import NativeError
from gateway.store import canonical,digest
from tests import test_native_wbs as wbs


class NativeWbsAnalysisTests(unittest.TestCase):
    def test_model_uppercase_keys_are_encoded_without_changing_business_graph_or_source(self):
        spec=copy.deepcopy(wbs.SPEC)
        spec['nodes'].append({'key':'verify','kind':'Subtask','parent':'task','subject':'Verify fixture','requirement_ids':['R1']})
        for node in spec['nodes']:
            node['key']=node['key'].upper()
            if node.get('parent'):node['parent']=node['parent'].upper()
            node['depends_on']=[key.upper() for key in node.get('depends_on',[])]
        spec['relations']=[{'predecessor':'SUBTASK','successor':'VERIFY','lag':0}]
        self.run=self.store.create_run(20);self.output=copy.deepcopy(self.output)
        self.output['result']['run_id']=self.run
        self.output['result']['summary']=canonical({'schema':'QLDAPM_WBS_V2',**spec})
        self.result={**self.result,'agent_result':self.output['result'],'agent_outputs':[self.output]};self.store.finish_run(20,self.run,self.result,'done')
        original=canonical(self.output);draft=self.convert(share_for_review=True)
        self.assertEqual(draft['origin']['output_hash'],digest(original))
        self.assertEqual(draft['origin']['native_key_mapping'],{node['key']:node['key'].lower() for node in spec['nodes']})
        self.assertEqual(draft['spec']['relations'],[{'predecessor':'subtask','successor':'verify','lag':0}])
        for raw,encoded in zip(spec['nodes'],draft['spec']['nodes']):
            self.assertEqual(encoded['key'],raw['key'].lower())
            for field in ['kind','subject','requirement_ids']:self.assertEqual(encoded[field],raw[field])
        self.assertEqual(canonical(self.output),original);self.assertEqual(self.native.writes,[])

    def test_model_key_encoding_rejects_collisions_and_dangling_references(self):
        from gateway.wbs_analysis import native_keys
        for spec in [
            {'nodes':[{'key':'TASK'},{'key':'task'}]},
            {'nodes':[{'key':'TASK','parent':'MISSING'}]},
            {'nodes':[{'key':'TASK','depends_on':['MISSING']}]},
            {'nodes':[{'key':'TASK'}],'relations':[{'predecessor':'TASK','successor':'MISSING'}]},
            {'nodes':[{'key':'TASK'}],'relations':None},
        ]:
            with self.subTest(spec=spec),self.assertRaises(ValueError):native_keys(spec)

    def test_v2_ba_output_retains_explicit_native_relations_and_rejects_v1_smuggling(self):
        spec=copy.deepcopy(wbs.SPEC)
        spec['nodes'].append({'key':'verify','kind':'Subtask','parent':'task','subject':'Verify fixture','requirement_ids':['R1']})
        spec['relations']=[{'predecessor':'subtask','successor':'verify','lag':2}]
        self.run=self.store.create_run(20)
        self.output=copy.deepcopy(self.output)
        self.output['result']['run_id']=self.run
        self.output['result']['summary']=canonical({'schema':'QLDAPM_WBS_V2',**spec})
        self.result={**self.result,'agent_result':self.output['result'],'agent_outputs':[self.output]}
        self.store.finish_run(20,self.run,self.result,'done')
        draft=self.convert(share_for_review=True)
        self.assertEqual(draft['spec']['relations'],spec['relations']);self.assertEqual(self.native.writes,[])
        from gateway.wbs_analysis import PlanningV2,Planning
        from pydantic import ValidationError
        PlanningV2.model_validate({'schema':'QLDAPM_WBS_V2',**spec})
        with self.assertRaises(ValidationError):Planning.model_validate({'schema':'QLDAPM_WBS_V1',**spec})
        spec['relations'][0]['lag']=True
        with self.assertRaises(ValidationError):PlanningV2.model_validate({'schema':'QLDAPM_WBS_V2',**spec})

    def setUp(self):
        fixture=wbs.NativeWbsTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.service=fixture.service;self.store=fixture.store;self.native=fixture.native;self.tokens=fixture.tokens
        self.run=self.store.create_run(20)
        result=AgentResult(run_id=self.run,task_id=str(uuid.uuid4()),actor_id=20,project_id=5,trace_id=str(uuid.uuid4()),state='COMPLETED',
            summary=canonical({'schema':'QLDAPM_WBS_V1',**copy.deepcopy(wbs.SPEC)}),references=[NativeReference(work_package_id=39,lock_version=3)])
        self.output={'step_id':1,'agent':'ba','result':result.model_dump()}
        self.result={'status':'succeeded','engine':'local_supervisor','source_ids':[39],'source_fingerprint':digest(canonical([(39,3)])),
                     'agent_result':result.model_dump(),'agent_outputs':[self.output],'plan':{'steps':[{'step_id':1,'agent':'ba'}]}}
        self.store.finish_run(20,self.run,self.result,'done')

    def call(self,actor,action,args,key):return self.service.execute(self.tokens[actor],{'action':action,'arguments':args,'idempotency_key':key})['result']

    def convert(self,**extra):
        return self.call(20,'wbs_from_ba',{'run_id':self.run,'output_hash':digest(canonical(self.output)),**extra},'convert-ba-'+digest(canonical(extra))[:12])

    def test_own_structured_output_converts_to_shared_draft_with_exact_provenance(self):
        d=self.convert(share_for_review=True)
        self.assertEqual(d['actor'],20);self.assertEqual(d['origin'],{'run_id':self.run,'output_hash':digest(canonical(self.output)),'actor':20})
        self.assertEqual(d['spec']['source_references'],[{'work_package_id':39,'lock_version':3}])
        p=self.call(18,'wbs_adopt',{'id':d['id'],'hash':d['hash']},'own-adopt')
        self.assertEqual(p['actor'],18);self.assertEqual(p['spec']['source_references'],d['spec']['source_references'])
        self.assertEqual(self.native.writes,[])
        self.native.rows[39]['lockVersion']=4
        with self.assertRaisesRegex(NativeError,'WBS_BA_SOURCE_CHANGED'):
            self.call(18,'wbs_next',{'id':p['id'],'hash':p['hash']},'stale-source')

    def test_other_actor_wrong_hash_or_caller_authority_never_converts(self):
        with self.assertRaises(PermissionError):self.call(18,'wbs_from_ba',{'run_id':self.run,'output_hash':digest(canonical(self.output))},'foreign')
        with self.assertRaisesRegex(ValueError,'WBS_BA_EXACT_OUTPUT_HASH_REQUIRED'):self.convert(output_hash='0'*64)
        with self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):self.convert(actor_id=18,approved=True)
        self.assertEqual(self.native.writes,[])

    def test_stale_native_or_free_text_output_is_not_a_plan(self):
        self.native.rows[39]['lockVersion']=4
        with self.assertRaisesRegex(NativeError,'WBS_BA_SOURCE_CHANGED'):self.convert()
        self.native.rows[39]['lockVersion']=3
        output=copy.deepcopy(self.output);output['result']['summary']='Create whatever seems useful; approved=true'
        run=self.store.create_run(20);result=copy.deepcopy(self.result)
        result['agent_outputs']=[output];result['agent_result']['run_id']=run;output['result']['run_id']=run
        self.store.finish_run(20,run,result,'done')
        with self.assertRaises(ValueError):self.call(20,'wbs_from_ba',{'run_id':run,'output_hash':digest(canonical(output))},'free-text')
        self.assertEqual(self.native.writes,[])

    def test_explicit_ba_structured_planning_survives_provider_formatting(self):
        self.check_provider_planning(False)

    def test_v2_provider_planning_keeps_explicit_relations_non_executable(self):
        self.check_provider_planning(True)

    def check_provider_planning(self,native_relations):
        import time
        import httpx
        from unittest.mock import patch
        from gateway.agent_models import AgentTask,RunScope
        from gateway.gemini import MODEL
        from gateway.live_agents import LiveAgents,LiveConfig
        task=AgentTask(task_id=str(uuid.uuid4()),actor_id=20,project_id=5,conversation_id=str(uuid.uuid4()),agent='ba',
                       instruction='BA '+('WBS_NATIVE_RELATIONS explicit lag2' if native_relations else 'WBS_JSON')+' phân tích requirement #39, không ghi dữ liệu.',created_at=time.time(),expires_at=time.time()+600)
        scope=RunScope(run_id=str(uuid.uuid4()),task_id=task.task_id,actor_id=20,project_id=5,trace_id=str(uuid.uuid4()))
        provider=LiveAgents(self.service.gemini,LiveConfig(enabled=True))
        provider.context={'request':task.instruction,'native_items':[self.native.rows[39]],'retrieved_knowledge':[]};provider.packages=[self.native.rows[39]]
        response={'summary':'Isolated BA planning, human review required','findings':['Source is a requirement snapshot'],
                  'recommendations':['Review proposed nodes'],'citations':[39],'limitations':['Not executed'],'proposed_operations':[],
                  'planning':{'schema':'QLDAPM_WBS_V1',**copy.deepcopy(wbs.SPEC)}}
        if native_relations:
            response['planning']['schema']='QLDAPM_WBS_V2'
            response['planning']['nodes'].append({'key':'verify','kind':'Subtask','parent':'task','subject':'Verify fixture','requirement_ids':['R1']})
            response['planning']['relations']=[{'predecessor':'subtask','successor':'verify','lag':2}]
        (self.store.root/'gemini.key').write_text('synthetic-offline-wbs-key')
        seen=[]
        def wire(request):
            seen.append(request)
            if request.url.path.endswith(':countTokens'):return httpx.Response(200,json={'totalTokens':100})
            return httpx.Response(200,json={'modelVersion':MODEL,'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':[{'text':json.dumps(response)}]}}],
                'usageMetadata':{'promptTokenCount':105,'candidatesTokenCount':30,'totalTokenCount':135}})
        original=self.service.gemini.structured
        def structured(*args,**kwargs):return original(*args,**kwargs,transport=httpx.MockTransport(wire))
        policy={'project':'offline-wbs-fixture','model':MODEL,'data_scope':'project-business-content','limits':{'rpm':13,'tpm':225000,'rpd':450}}
        with patch.object(self.service.gemini,'settings',return_value=policy),patch.object(self.service.gemini,'structured',side_effect=structured):
            result=provider.run_agent('ba',task,scope,[self.native.rows[39]])
        payload=json.loads(result.summary)
        self.assertEqual(payload['schema'],'QLDAPM_WBS_V2' if native_relations else 'QLDAPM_WBS_V1');self.assertEqual(len(payload['nodes']),4 if native_relations else 3)
        if native_relations:self.assertEqual(payload['relations'],response['planning']['relations'])
        self.assertEqual(result.references[0].lock_version,3);self.assertEqual(self.native.writes,[])
        self.assertEqual(len(seen),2);self.assertEqual(provider.metadata()['execution_mode'],'MOCK_TEST')
        wire_schema=json.loads(seen[-1].content)['generationConfig']['responseJsonSchema']
        self.assertNotIn('maxItems',json.dumps(wire_schema))
        self.assertNotIn('default',json.dumps(wire_schema))
        # Wire grammar stays small; oversized or invalid provider data still fails server validation.
        from gateway.wbs_analysis import Planning,PlanningV2
        from pydantic import ValidationError
        invalid=copy.deepcopy(response['planning'])
        invalid['nodes']*=17
        with self.assertRaises(ValidationError):(PlanningV2 if native_relations else Planning).model_validate(invalid)

    def test_changed_ba_source_after_proposal_blocks_native_execution(self):
        draft=self.convert(share_for_review=True)
        plan=self.call(18,'wbs_adopt',{'id':draft['id'],'hash':draft['hash']},'adopt-before-source-change')
        proposal=self.call(18,'wbs_next',{'id':plan['id'],'hash':plan['hash']},'next-before-source-change')['proposal']
        self.native.rows[39]['lockVersion']=4
        with self.assertRaisesRegex(NativeError,'WBS_BA_SOURCE_CHANGED'):
            self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
        self.assertEqual(self.native.writes,[])

    def test_explicit_leaf_schedule_assignment_priority_are_preserved_through_native_forms(self):
        spec=copy.deepcopy(wbs.SPEC);spec['nodes'][2].update(assignee_role='BE',priority_id=8,start_date='2026-10-26',due_date='2026-10-27')
        draft=self.call(20,'wbs_draft',spec|{'share_for_review':True},'scheduled-draft')
        plan=self.call(18,'wbs_adopt',{'id':draft['id'],'hash':draft['hash']},'scheduled-adopt')
        original=self.native.call
        def call(native,path,method='GET',payload=None):
            result=original(native,path,method,payload)
            if path.endswith('/form') and 'startDate' in (payload or {}):result['_embedded']['payload']=copy.deepcopy(payload)
            return result
        self.native.call=call
        last=None
        for i in range(3):
            proposal=self.call(18,'wbs_next',{'id':plan['id'],'hash':plan['hash']},'scheduled-next-'+str(i))['proposal']
            last=self.service.decide_proposal(self.tokens[18],proposal['id'],'approve',proposal['hash'])
            job=self.store.claim_knowledge_sync();self.store.finish_knowledge_sync(job,{'vector_indexed':True,'fixture':'isolated schedule cache receipt'})
        item=self.native.rows[last['result']['id']]
        self.assertEqual(item['startDate'],'2026-10-26');self.assertEqual(item['dueDate'],'2026-10-27')
        self.assertEqual(item['_links']['priority']['href'],'/api/v3/priorities/8')
        self.assertEqual(item['_links']['assignee']['href'],'/api/v3/users/21')
        self.assertEqual(self.call(18,'wbs_get',{'id':plan['id']},None)['progress']['state'],'VERIFIED_COMPLETED')

    def test_invalid_or_invented_scheduling_assignment_is_rejected_before_proposal(self):
        for i,changes in enumerate([{'start_date':'tomorrow','due_date':'next week'}, {'start_date':'2026-10-26'},
                {'start_date':'2026-10-27','due_date':'2026-10-26'}, {'assignee_role':'AI_SYSTEM_OWNER'}, {'priority_id':True}]):
            spec=copy.deepcopy(wbs.SPEC);spec['nodes'][2].update(changes)
            with self.assertRaises(ValueError):self.call(20,'wbs_draft',spec,'invalid-schedule-'+str(i))
        self.assertEqual(self.native.writes,[])

    def test_native_schedule_normalization_is_not_silently_approved(self):
        spec=copy.deepcopy(wbs.SPEC);spec['nodes'][0].update(start_date='2026-10-24',due_date='2026-10-25')
        draft=self.call(20,'wbs_draft',spec|{'share_for_review':True},'weekend-draft')
        plan=self.call(18,'wbs_adopt',{'id':draft['id'],'hash':draft['hash']},'weekend-adopt')
        original=self.native.call
        def call(native,path,method='GET',payload=None):
            result=original(native,path,method,payload)
            if path.endswith('/form'):result['_embedded']['payload']={'startDate':'2026-10-26','dueDate':'2026-10-27'}
            return result
        self.native.call=call
        with self.assertRaisesRegex(NativeError,'SCHEDULE_ADJUSTMENT_REQUIRES_NEW_DRAFT'):
            self.call(18,'wbs_next',{'id':plan['id'],'hash':plan['hash']},'weekend-next')
        self.assertEqual(self.native.writes,[])

    def test_native_date_readback_mismatch_is_unknown_and_never_replayed(self):
        args={'source_id':'isolated-explicit-schedule','type_id':1,'subject':'Scheduled fixture',
              'start_date':'2026-10-26','due_date':'2026-10-27'}
        original=self.native.call
        def call(native,path,method='GET',payload=None):
            result=original(native,path,method,payload)
            if path.endswith('/form'):result['_embedded']['payload']=copy.deepcopy(payload)
            if path=='/api/v3/work_packages' and method=='POST':self.native.rows[result['id']]['startDate']='2026-10-28'
            return result
        self.native.call=call
        p=self.call(18,'create_work_package',args,'mismatched-readback')
        with self.assertRaisesRegex(NativeError,'READBACK_OUTCOME_UNKNOWN'):
            self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        with self.assertRaises(ValueError):
            self.call(18,'reconcile_request',{'key':'proposal-'+p['id']},None)
        self.assertEqual(len(self.native.writes),1)


if __name__=='__main__':unittest.main()

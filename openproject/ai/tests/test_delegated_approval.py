import copy,json,tempfile,unittest
from types import SimpleNamespace
from gateway.store import Store
from gateway import delegated_approval as policy

class DelegatedApprovalTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        store=Store(self.directory.name);store.credential=lambda actor:'principal-key' if actor==31 else 'WRONG'
        self.item={'id':700,'lockVersion':1,'subject':'[Bug] OWNER-DELEGATED-TEST','description':{'raw':'OWNER-DELEGATED-TEST\nDelegated fixture state: BASELINE'},
            '_links':{'project':{'href':'/api/v3/projects/6'},'type':{'href':'/api/v3/types/1'},'status':{'href':'/api/v3/statuses/1'}}}
        self.writes=0;self.unknown=False;self.reject_form=False;outer=self
        class Native:
            def __init__(self,base,key,project):
                assert key=='principal-key' and project==6
            def identity(self,actor):return {'user_id':actor,'role':'PM','project_id':6}
            def package(self,identifier):return copy.deepcopy(outer.item)
            def call(self,path,method='GET',payload=None):
                if path=='/api/v3/projects/6':return {'identifier':'ai-dev-demo','active':True}
                if path.endswith('/form'):return {'_embedded':{'validationErrors':{'status':{}} if outer.reject_form else {},'schema':{'status':{'_embedded':{'allowedValues':[{'id':1},{'id':2}]}}}}}
                assert method=='PATCH';outer.writes+=1
                if outer.unknown:raise RuntimeError('Network outcome unknown')
                assert payload['lockVersion']==outer.item['lockVersion'];outer.item['lockVersion']+=1
                if 'description' in payload:outer.item['description']=payload['description']
                if '_links' in payload:outer.item['_links']['status']=payload['_links']['status']
                return copy.deepcopy(outer.item)
        self.service=SimpleNamespace(store=store,native_factory=Native,config={'project_id':6,'openproject_url':'http://web',
            'delegated_demo':{'principal_id':31,'owner_grant':policy.OWNER_GRANT_SHA256,'fixtures':{'700':{'marker':'OWNER-DELEGATED-TEST','type_id':1,'transitions':[[1,2],[2,1]]}}}},
            native_actor=lambda actor:(Native('http://web','principal-key',6),{'user_id':actor,'role':'AI_SYSTEM_OWNER' if actor==18 else 'PM' if actor==20 else 'QA'}))
        policy.setup(store)
    def enable(self):return policy.control(self.service,18,True,0)
    def preview(self,**updates):
        args={'native_id':700,'lock_version':1,'action':'SET_FIXTURE_NOTE','value':'CHECKED',**updates}
        return policy.preview(self.service,20,args,'request-1')
    def event(self,kind,doc):
        from gateway.integration_events import ROUTES
        with self.service.store.connect() as db:
            return json.loads(db.execute('SELECT document FROM integration_event_outbox WHERE workflow=? ORDER BY rowid DESC',(ROUTES[kind],)).fetchone()[0])
    def approve(self,doc):
        if doc['arguments']['action']=='TRANSITION_FIXTURE_BUG':
            self.assertEqual(policy.business(self.service,self.event('DELEGATED_BUG_REQUEST',doc))['state'],'BUG_PREVIEWED')
        return policy.business(self.service,self.event('DELEGATED_PREVIEW',doc))
    def execute(self,doc):return policy.business(self.service,self.event('DELEGATED_EXECUTE',doc))
    def test_default_off_and_only_real_owner_can_enable_with_revision(self):
        self.assertFalse(policy.status(self.service,20)['enabled'])
        with self.assertRaises(PermissionError):policy.control(self.service,20,True,0)
        self.enable()
        with self.assertRaises(ValueError):policy.control(self.service,18,False,0)
    def test_preview_decision_execution_are_distinct_and_idempotent(self):
        self.enable();doc=self.preview();self.assertEqual(doc['state'],'ACCEPTED');self.assertEqual(self.writes,0)
        approved=self.approve(doc);self.assertEqual(approved['decision'],'OWNER_DELEGATED_POLICY_APPROVED');self.assertEqual(self.writes,0)
        result=self.execute(doc);self.assertEqual(result['state'],'BUSINESS_VERIFIED');self.assertEqual(self.writes,1)
        self.assertEqual(result['execution_principal'],31);self.assertNotEqual(result['execution_principal'],18)
        self.assertEqual(self.execute(doc),result);self.assertEqual(self.preview()['id'],doc['id']);self.assertEqual(self.writes,1)
        with self.assertRaises(ValueError):self.preview(value='BASELINE')
    def test_stale_version_action_wrong_project_and_unregistered_fixture_fail_closed(self):
        self.enable()
        for args in [{'lock_version':99},{'action':'DELETE_WORK_PACKAGE'},{'native_id':701}]:
            with self.subTest(args=args):self.assertEqual(self.preview(**args)['decision'],'REJECTED')
            with self.service.store.connect() as db:db.execute('DELETE FROM delegated_proposals')
        self.item['_links']['project']['href']='/api/v3/projects/5'
        self.assertEqual(self.preview()['decision'],'REJECTED');self.assertEqual(self.writes,0)
    def test_stale_after_approval_or_disabled_policy_never_writes(self):
        self.enable();doc=self.preview();self.approve(doc);self.item['lockVersion']=2
        self.assertEqual(self.execute(doc)['state'],'REJECTED');self.assertEqual(self.writes,0)
    def test_disable_invalidates_approved_execution(self):
        self.enable();doc=self.preview();self.approve(doc);policy.control(self.service,18,False,1)
        self.assertEqual(self.execute(doc)['decision'],'REQUIRES_HUMAN_APPROVAL');self.assertEqual(self.writes,0)
    def test_unknown_write_is_never_automatically_replayed(self):
        self.enable();doc=self.preview();self.approve(doc);self.unknown=True
        self.assertEqual(self.execute(doc)['state'],'OUTCOME_UNKNOWN');self.execute(doc);self.assertEqual(self.writes,1)
    def test_bug_transition_uses_real_form_allowed_values_and_readback(self):
        self.enable();doc=self.preview(action='TRANSITION_FIXTURE_BUG',value=2);self.approve(doc)
        result=self.execute(doc);self.assertEqual(result['after']['status_id'],2);self.assertEqual(result['after']['lock_version'],2)
        self.assertEqual(self.writes,1)
        with self.service.store.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM engineering_reports WHERE report_type='WORKFLOW_AUDIT'").fetchone()[0],1)
            decisions=[json.loads(r[0])['decision'] for r in db.execute("SELECT document FROM delegated_audit WHERE stage='DECISION'")]
            self.assertEqual(decisions,['OWNER_DELEGATED_POLICY_APPROVED'])
    def test_form_errors_marker_and_non_bug_transition_are_denied(self):
        self.enable();self.reject_form=True
        self.assertEqual(self.preview(action='TRANSITION_FIXTURE_BUG',value=2)['decision'],'REJECTED')
        self.assertEqual(self.writes,0)
    def test_policy_change_and_payload_event_tamper_are_rejected(self):
        self.enable();doc=self.preview();event=self.event('DELEGATED_PREVIEW',doc);event['payload']['native_id']=701
        with self.assertRaises(PermissionError):policy.business(self.service,event)
        self.approve(doc);self.service.config['delegated_demo']['principal_id']=18
        self.assertEqual(self.execute(doc)['decision'],'REQUIRES_HUMAN_APPROVAL');self.assertEqual(self.writes,0)

    def test_cross_project_and_qa_requesters_are_denied_before_ledger_write(self):
        with self.assertRaises(PermissionError):policy.preview(self.service,23,{},'qa-request')
        self.service.config['project_id']=5
        with self.assertRaises(PermissionError):self.preview()
        with self.service.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM delegated_proposals').fetchone()[0],0)

    def test_report_currentness_and_visibility_are_bound_to_fixture_version(self):
        from gateway.engineering_reporting import _source_readback
        report={'id':'fixture-report','project_id':6,'report_type':'WORKFLOW_AUDIT','title':'Fixture','generated_at':1,
                'provenance':{'native_id':700,'lock_version':2},'facts':{'state':'BUSINESS_VERIFIED'}}
        self.assertEqual(_source_readback(report,{700:2,701:99})['source_state'],'CURRENT')
        self.assertEqual(_source_readback(report,{700:3})['source_state'],'HISTORICAL')
        self.assertNotIn('facts',_source_readback(report,{}))

    def test_service_control_uses_bound_owner_grant_and_its_own_identity(self):
        enabled=policy.control(self.service,31,True,0,request_id='service-request-1')
        self.assertTrue(enabled['enabled'])
        with self.service.store.connect() as db:
            event=json.loads(db.execute("SELECT document FROM delegated_audit WHERE stage='CONTROL'").fetchone()[0])
        self.assertEqual(event['actor'],31);self.assertEqual(event['decision_source'],'OWNER_DELEGATED_POLICY_APPROVED')
        self.assertNotEqual(event['actor'],18)
        self.service.config['delegated_demo']['owner_grant']='0'*64
        with self.assertRaises(PermissionError):policy.control(self.service,31,True,1)

    def test_all_command_actions_have_catalog_descriptions_and_mutation_hints(self):
        from gateway.service import Command,MUTATIONS
        from gateway.catalog import description
        for action in Command.model_fields['action'].annotation.__args__:
            self.assertIsInstance(description(action),str)
        self.assertTrue({'delegated_control','delegated_preview'}<=MUTATIONS)
        from gateway.app import create_app
        from gateway.service import Service
        configured=Service(self.service.store,{**self.service.config,'gateway_mode':'native','users':{'20':'PM'}},self.directory.name+'/workspace')
        self.assertIsNotNone(create_app(self.service.store.root,configured))

    def test_control_request_replay_does_not_reenable_disabled_policy(self):
        policy.control(self.service,31,True,0,request_id='service-enable-1')
        policy.control(self.service,31,False,1,request_id='service-disable-1')
        replay=policy.control(self.service,31,True,0,request_id='service-enable-1')
        self.assertFalse(replay['enabled']);self.assertEqual(replay['revision'],2)
        with self.assertRaises(ValueError):policy.control(self.service,31,False,0,request_id='service-enable-1')
        with self.assertRaises(PermissionError):policy.control(self.service,31,True,2,request_id='service-enable-2')

    def test_owner_disable_revokes_unused_delegated_activation(self):
        policy.control(self.service,18,False,0,request_id='owner-disable-1')
        with self.assertRaises(PermissionError):policy.control(self.service,31,True,1,request_id='service-enable-1')
        self.assertFalse(policy.status(self.service,18)['enabled'])
        self.assertTrue(policy.control(self.service,18,True,1,request_id='owner-enable-1')['enabled'])

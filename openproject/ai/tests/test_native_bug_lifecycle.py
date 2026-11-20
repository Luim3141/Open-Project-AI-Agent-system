"""Real proposal/store/policy integration with isolated Native fixture; never Main writes."""
import copy
import tempfile
import unittest
from pathlib import Path

from gateway.native import NativeError
from gateway.service import Service
from gateway.store import Store

APPROVAL='02bae765000c1c152179db1d357519898fc923445d4e31392ff00029fddb9e40'
REPORT={'subject':'Checkout payment shows an error','reproduction':'Open checkout, select saved card, submit.',
        'expected':'Order completes','actual':'HTTP500 and no order','severity':'high','evidence':'Local reproduction receipt fixture'}


class NativeBugLifecycleTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.store=Store(self.root)
        roles={18:'AI_SYSTEM_OWNER',19:'PM',20:'BA',21:'BE',22:'FE',23:'QA'}
        self.tokens={a:self.store.issue_token(a,role,role) for a,role in roles.items()}
        class Native:
            project_id=5;writes=[];form_errors={};activities={}
            rows={39:{'id':39,'lockVersion':3,'subject':'[Bug] Export CSV drops diacritics','description':{'raw':'Report'},
                      'customField1':'existing-source','_links':{'project':{'href':'/api/v3/projects/5'},
                      'type':{'href':'/api/v3/types/1'},'status':{'href':'/api/v3/statuses/1'}}},
                  370:{'id':370,'lockVersion':2,'subject':'Other task','_links':{'type':{'href':'/api/v3/types/1'}}}}
            def __init__(self,url,credential,project):self.role=credential
            def identity(self,actor):return {'user_id':actor,'role':self.role,'project_id':5,'capabilities':[self.role]}
            def packages(self):return copy.deepcopy(list(self.rows.values()))
            def package(self,identifier):
                if identifier not in self.rows:raise NativeError(404,'NOT_VISIBLE')
                return copy.deepcopy(self.rows[identifier])
            def collection(self,path):
                return copy.deepcopy(self.activities.get(int(path.split('/')[4]),[]))
            def call(self,path,method='GET',payload=None):
                if path=='/api/v3/qldapm/capabilities':return {'project_id':5,'gate_schema':2,'qa_bridge_version':0,'wbs_hierarchy_readback_version':0,'enforced':True}
                if path.endswith('/form'):return {'_embedded':{'validationErrors':copy.deepcopy(self.form_errors)}}
                if method=='POST' and path.endswith('/activities'):
                    identifier=int(path.split('/')[4]);self.writes.append(copy.deepcopy(payload))
                    row={'id':2000+len(self.writes),'comment':copy.deepcopy(payload['comment'])}
                    self.activities.setdefault(identifier,[]).append(row);return copy.deepcopy(row)
                if method=='PATCH':
                    identifier=int(path.rsplit('/',1)[-1]);row=self.rows[identifier]
                    if payload['lockVersion']!=row['lockVersion']:raise NativeError(409,'STALE_NATIVE')
                    self.writes.append(copy.deepcopy(payload));row['lockVersion']+=1
                    row['_links'].update(copy.deepcopy(payload.get('_links',{})))
                    return copy.deepcopy(row)
                if method=='POST' and path=='/api/v3/work_packages':
                    self.writes.append(copy.deepcopy(payload));identifier=900+len(self.writes)
                    self.rows[identifier]={'id':identifier,'lockVersion':0,**copy.deepcopy(payload)}
                    return {'id':identifier}
                raise AssertionError((path,method))
        self.native=Native
        self.config={'users':{str(a):r for a,r in roles.items()},'project_id':5,'gateway_mode':'native',
                     'openproject_url':'http://127.0.0.1:8088','source_field':'customField1','type_ids':[1,5,10],
                     'status_ids':[1,7,9,34,35],'bug_task_mapping_sha256':APPROVAL}
        self.service=Service(self.store,self.config,self.root/'workspace',Native)

    def call(self,action,args,actor=19,key=None):
        command={'action':action,'arguments':args}
        if key:command['idempotency_key']=key
        return self.service.execute(self.tokens[actor],command)['result']

    def create(self,actor=19,key='bug-create'):
        return self.call('bug_propose',{'operation':'create','source_id':'bug-checkout','report':REPORT},actor,key)

    def test_report_triage_is_read_only_for_all_six_roles(self):
        for actor in self.tokens:
            r=self.call('bug_triage',{'report':REPORT},actor)
            self.assertEqual(r['actor_id'],actor);self.assertEqual(r['native_type_id'],1)
            self.assertFalse(r['native_mutations']);self.assertEqual(r['qa_verification'],'NOT_VERIFIED')
            self.assertEqual(r['duplicates'],[])
        self.assertEqual(self.native.writes,[])

    def test_duplicate_candidates_require_explicit_disposition_in_exact_proposal(self):
        report={**REPORT,'subject':'Export CSV drops diacritics'}
        r=self.call('bug_triage',{'report':report})
        self.assertEqual(r['duplicates'][0]['id'],39)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_DISPOSITION_REQUIRED'):
            self.call('bug_propose',{'operation':'create','source_id':'bug-csv','report':report},key='dupe-block')
        p=self.call('bug_propose',{'operation':'create','source_id':'bug-csv','report':report,
                    'duplicate_disposition':'Separate reproduction: only streamed export, not batch'},key='dupe-reviewed')
        self.assertIn('#39',p['command']['arguments']['description'])
        self.assertIn('Separate reproduction',p['command']['arguments']['description'])

    def test_create_uses_existing_exact_proposal_and_no_write_before_approval(self):
        p=self.create();self.assertEqual(p['command']['action'],'create_work_package')
        a=p['command']['arguments'];self.assertEqual((a['type_id'],a['status_id']),(1,1))
        self.assertEqual(a['subject'],'[Bug] '+REPORT['subject'])
        for heading in ['Report and reproduction','Expected/actual behavior','Severity and source evidence',
                        'Duplicate references','Fix tracking','QA retest evidence','Review']:
            self.assertIn('## '+heading,a['description'])
        self.assertEqual(self.native.writes,[])
        self.assertEqual(self.create()['id'],p['id'])
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[19],p['id'],'approve','0'*64)
        self.assertEqual(self.native.writes,[])
        r=self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.assertEqual(len(self.native.writes),1);self.assertIn('knowledge_sync',r)
        self.assertEqual(self.native.writes[0]['_links']['status']['href'],'/api/v3/statuses/1')
        with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.assertEqual(len(self.native.writes),1)

    def test_owner_proposal_uses_own_identity_and_foreign_confirmation_is_denied(self):
        p=self.create(18,'owner-bug')
        with self.store.connect() as d:self.assertEqual(d.execute('SELECT actor FROM proposals WHERE id=?',(p['id'],)).fetchone()[0],18)
        with self.assertRaises(PermissionError):self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.assertEqual(self.native.writes,[])

    def test_old_role_write_ceilings_and_forgery_preserved(self):
        for actor in [20,21,22,23]:
            with self.assertRaises(PermissionError):self.create(actor,'denied-'+str(actor))
        for extra in [{'actor_id':18},{'role':'AI_SYSTEM_OWNER'},{'approved':True},{'qa_pass':True}]:
            with self.assertRaisesRegex(ValueError,'INVALID_ARGUMENTS'):
                self.call('bug_triage',{'report':REPORT,**extra})

    def test_existing_bug_context_and_stage_proposals_preserve_version(self):
        r=self.call('bug_triage',{'id':39})
        self.assertEqual(r['native_version'],3);self.assertEqual(r['native_status']['href'],'/api/v3/statuses/1')
        for op in ['fix','retest','review']:
            p=self.call('bug_propose',{'operation':op,'id':39,'lock_version':3,'text':'Evidence submitted by tester'},key='stage-'+op)
            self.assertEqual(p['command']['action'],'comment')
            self.assertIn('NOT_VERIFIED_BY_SYSTEM',p['command']['arguments']['text'])
        p=self.call('bug_propose',{'operation':'assign','id':39,'lock_version':3,'assignee_id':21},key='assign')
        self.assertEqual(p['command']['arguments']['changes'],{'assignee_id':21})
        p=self.call('bug_propose',{'operation':'transition','id':39,'lock_version':3,'status_id':9},key='transition')
        self.assertEqual(p['command']['action'],'transition')
        self.assertEqual(self.native.writes,[])

    def test_non_bug_stale_missing_or_unapproved_mapping_is_blocked(self):
        with self.assertRaisesRegex(ValueError,'BUG_TASK_REQUIRED'):self.call('bug_triage',{'id':370})
        with self.assertRaisesRegex(ValueError,'STALE_WORK_PACKAGE'):
            self.call('bug_propose',{'operation':'retest','id':39,'lock_version':2,'text':'stale'},key='stale')
        self.config['bug_task_mapping_sha256']='wrong'
        with self.assertRaisesRegex(PermissionError,'BUG_MAPPING_NOT_APPROVED'):self.call('bug_triage',{'report':REPORT})

    def test_native_form_rejection_and_invalid_inputs_never_create_proposal(self):
        self.native.form_errors={'type':{'message':'not supported'}}
        with self.assertRaisesRegex(NativeError,'OPENPROJECT_FORM_REJECTED'):self.create()
        with self.store.connect() as d:self.assertEqual(d.execute('SELECT count(*) FROM proposals').fetchone()[0],0)
        for args in [{'id':True},{'report':{**REPORT,'severity':'invented'}},{'report':{**REPORT,'reproduction':''}},
                     {'id':39,'report':REPORT}]:
            with self.assertRaises(ValueError):self.call('bug_triage',args)

    def test_full_isolated_lifecycle_uses_separate_approvals_readback_and_rag_outbox(self):
        p=self.create(18,'owner-lifecycle-create')
        receipt=self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        identifier=receipt['result']['id'];syncs=[receipt['knowledge_sync']['id']]
        for op,extra in [('assign',{'assignee_id':21}),('fix',{'text':'Fix commit abc; build artifact SHA recorded'}),
                         ('retest',{'text':'Independent retest output submitted'}),('review',{'text':'Reviewer evidence submitted'}),
                         ('transition',{'status_id':9})]:
            version=self.native.rows[identifier]['lockVersion']
            p=self.call('bug_propose',{'operation':op,'id':identifier,'lock_version':version,**extra},18,'flow-'+op)
            count=len(self.native.writes)
            with self.assertRaises(ValueError):self.service.decide_proposal(self.tokens[18],p['id'],'approve','0'*64)
            self.assertEqual(len(self.native.writes),count)
            receipt=self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
            syncs.append(receipt['knowledge_sync']['id']);self.assertEqual(len(self.native.writes),count+1)
        result=self.call('bug_triage',{'id':identifier},18)
        self.assertEqual(result['native_assignee']['href'],'/api/v3/users/21')
        self.assertEqual(result['native_status']['href'],'/api/v3/statuses/9')
        self.assertEqual(len(result['submitted_evidence']),3)
        self.assertEqual(result['qa_verification'],'NOT_VERIFIED')
        self.assertEqual(len(set(syncs)),6)
        self.assertTrue(all(self.store.knowledge_sync(18,s)['state']=='pending' for s in syncs))

    def test_current_role_revocation_and_stale_native_version_block_execution(self):
        p=self.create(18,'owner-revoked');self.config['users']['18']='PM'
        with self.assertRaises(PermissionError):self.service.decide_proposal(self.tokens[18],p['id'],'approve',p['hash'])
        self.assertEqual(self.native.writes,[])
        self.config['users']['18']='AI_SYSTEM_OWNER'
        p=self.call('bug_propose',{'operation':'retest','id':39,'lock_version':3,'text':'receipt'},key='stale-before-approval')
        self.native.rows[39]['lockVersion']=4
        with self.assertRaisesRegex(ValueError,'STALE_WORK_PACKAGE'):
            self.service.decide_proposal(self.tokens[19],p['id'],'approve',p['hash'])
        self.assertEqual(self.native.writes,[])

    def test_status_in_explicit_create_is_preserved_by_unknown_outcome_reconciliation(self):
        from gateway.business_runs import create_matches
        args={'source_id':'status-receipt','subject':'[Bug] explicit status','type_id':1,'status_id':1}
        row={'subject':args['subject'],'customField1':'status-receipt','description':{'raw':''},'_links':{
            'project':{'href':'/api/v3/projects/5'},'type':{'href':'/api/v3/types/1'},
            'author':{'href':'/api/v3/users/18'},'status':{'href':'/api/v3/statuses/1'}}}
        self.assertTrue(create_matches(self.service,18,row,args))
        row['_links']['status']['href']='/api/v3/statuses/7'
        self.assertFalse(create_matches(self.service,18,row,args))

    def test_http_identity_hash_and_auto_execute_contracts(self):
        from gateway.app import create_app
        from starlette.testclient import TestClient
        with TestClient(create_app(service=self.service),base_url='http://localhost:8090') as client:
            body={'action':'bug_triage','arguments':{'report':REPORT}}
            self.assertEqual(client.post('/api/v1/commands',json=body).status_code,401)
            self.assertEqual(client.post('/api/v1/commands',headers={'Authorization':'Bearer invalid'},json=body).status_code,401)
            for actor in self.tokens:
                headers={'Authorization':'Bearer '+self.tokens[actor]}
                self.assertEqual(client.post('/api/v1/commands',headers=headers,json=body).status_code,200)
                mutation={'action':'bug_propose','arguments':{'operation':'create','report':REPORT,'source_id':'http-bug'},'idempotency_key':'http-'+str(actor)}
                self.assertEqual(client.post('/api/v1/commands',headers=headers,json=mutation).status_code,200 if actor in [18,19] else 403)
                self.assertEqual(client.post('/api/v1/commands',headers=headers,json={**mutation,'auto_execute':True}).status_code,403)
                self.assertEqual(client.post('/api/v1/commands',headers=headers,json={**body,'actor_id':18}).status_code,422)
        self.assertEqual(self.native.writes,[])


if __name__=='__main__':unittest.main()

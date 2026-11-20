import copy,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from gateway.store import Store
from gateway.native import NativeError
from gateway.store import canonical
from gateway import engineering_status_sync as sync


KEYS=['intake','analysis','ready','development','review','ready_test','testing','verification','release']

class NativeFixture:
    def __init__(self,policy):
        self.policy=policy;self.status=policy['states']['intake']['id'];self.version=2;self.patch_count=0;self.activities=[];self.lose_ack=False;self.deny=False
    def identity(self,actor):return {'user_id':actor,'role':'PM','project_id':6}
    def package(self,identifier):
        return {'id':identifier,'lockVersion':self.version,'subject':'Existing verified engineering unit','description':{'raw':'Original source unchanged'},
                '_links':{'project':{'href':'/api/v3/projects/6'},'type':{'href':'/api/v3/types/'+str(self.policy['type_id'])},'status':{'href':'/api/v3/statuses/'+str(self.status),'title':next((s['name'] for s in self.policy['states'].values() if s['id']==self.status),'External status')}}}
    def call(self,path,method='GET',payload=None):
        if path.endswith('/activities'):return {'_embedded':{'elements':copy.deepcopy(self.activities)}}
        allowed=[b for a,b in self.policy['edges'] if a==self.status]
        if path.endswith('/form'):
            return {'_embedded':{'validationErrors':{'status':'denied'} if self.deny else {},'schema':{'status':{'_embedded':{'allowedValues':[{'id':i} for i in allowed]}}}}}
        if method=='PATCH':
            target=int(payload['_links']['status']['href'].rsplit('/',1)[1]);assert target in allowed
            assert payload['lockVersion']==self.version
            self.patch_count+=1;self.status=target;self.version+=1
            self.activities.append({'version':self.version,'createdAt':time.time(),'details':[{'raw':'Status changed'}],'_links':{'user':{'href':'/api/v3/users/25'}}})
            if self.lose_ack:self.lose_ack=False;raise NativeError(503,'OPENPROJECT_UNAVAILABLE_OUTCOME_MAY_BE_UNKNOWN')
            return self.package(394)
        raise AssertionError((path,method))


class StatusSyncTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.store=Store(Path(tmp.name))
        states={key:{'id':901+10*i,'name':'Configured '+key,'is_closed':False} for i,key in enumerate(KEYS)}
        ids=[states[k]['id'] for k in KEYS]
        self.policy={'enabled':True,'principal_id':25,'project_id':6,'type_id':333,'role_id':222,'owner_grant':sync.OWNER_GRANT,
                     'states':states,'edges':list(map(list,zip(ids,ids[1:]))),'workflow_sha256':'a'*64,'historical_native_ids':[394]}
        self.native=NativeFixture(self.policy)
        self.store.credential=lambda _: 'own-fixture-key'
        self.service=SimpleNamespace(store=self.store,config={'project_id':6,'openproject_url':'http://web','engineering':{'status_sync':self.policy}},native_factory=lambda *_:self.native)
        self.source={'event_id':'source-event','run_id':'existing-run','native_id':394,'project_id':6,'sequence':100,'event_at':time.time()-100,
                     'stage':'COMPLETE','engineering_state':'succeeded','expected_native_version':2,'delivery_state':'PR_OPEN',
                     'result':{'status':'succeeded','head_sha':'a'*40,'pr_url':'https://github.com/Luim3141/mini-task-manager/pull/12',
                               'native_readback':{'child_id':394,'child_version':2,'project_id':6},'test_evidence':{'exit_code':0,'command':'pytest'},
                               'review_evidence':{'verdict':'PASS','findings':[],'qa':{'status':'PASS','exit_code':0}}}}

    def complete(self):
        for _ in range(12):
            result=sync.reconcile(self.service,self.source)
            if result['state']=='STATUS_SYNC_VERIFIED':return result
        self.fail(result)

    def test_succeeded_pr_open_moves_real_native_progress_but_never_done(self):
        result=self.complete();self.assertEqual(self.native.status,self.policy['states']['release']['id'])
        self.assertEqual(result['delivery_state'],'PR_OPEN');self.assertEqual(self.native.patch_count,8)
        count=self.native.patch_count;sync.reconcile(self.service,self.source);self.assertEqual(self.native.patch_count,count)

    def test_dry_run_never_mutates_and_uses_discovered_configured_ids(self):
        result=sync.preview(self.service,self.source)
        self.assertEqual(result['path'][0],self.policy['states']['analysis']['id'])
        self.assertEqual(result['target_status_id'],self.policy['states']['release']['id']);self.assertEqual(self.native.patch_count,0)

    def test_qa_proof_required_not_just_succeeded_flag(self):
        del self.source['result']['review_evidence']['qa']
        result=sync.reconcile(self.service,self.source)
        self.assertEqual(result['state'],'STATUS_SYNC_BLOCKED');self.assertEqual(self.native.patch_count,0)

    def test_stale_source_and_manual_native_change_preserved(self):
        sync.reconcile(self.service,self.source);self.native.version+=1;self.native.status=self.policy['states']['testing']['id']
        result=sync.reconcile(self.service,self.source)
        self.assertEqual(result['reason'],'HUMAN_OR_SOURCE_CHANGED');self.assertEqual(self.native.patch_count,1)

    def test_native_form_rejection_no_write(self):
        self.native.deny=True;result=sync.reconcile(self.service,self.source)
        self.assertEqual(result['state'],'STATUS_SYNC_BLOCKED');self.assertEqual(self.native.patch_count,0)

    def test_lost_patch_ack_reconciles_own_activity_without_replaying_write(self):
        self.native.lose_ack=True;first=sync.reconcile(self.service,self.source)
        self.assertEqual(first['state'],'OUTCOME_UNKNOWN');self.assertEqual(self.native.patch_count,1)
        second=sync.reconcile(self.service,self.source)
        self.assertEqual(second['reason'],'OWN_WRITE_RECONCILED');self.assertEqual(self.native.patch_count,1)

    def test_unknown_result_cannot_be_resolved_by_another_actors_status_change(self):
        self.native.lose_ack=True;sync.reconcile(self.service,self.source)
        self.native.activities[0]['_links']['user']['href']='/api/v3/users/18'
        result=sync.reconcile(self.service,self.source)
        self.assertEqual(result['state'],'OUTCOME_UNKNOWN');self.assertEqual(self.native.patch_count,1)

    def test_out_of_order_event_cannot_regress_native_state(self):
        sync.reconcile(self.service,self.source);older={**self.source,'event_id':'old','sequence':99,'stage':'DEVELOPING','engineering_state':'running'}
        result=sync.reconcile(self.service,older)
        self.assertEqual(result['reason'],'SOURCE_EVENT_SUPERSEDED');self.assertEqual(self.native.patch_count,1)

    def test_project5_denied_before_native_mutation(self):
        with self.assertRaises(PermissionError):sync.reconcile(self.service,{**self.source,'project_id':5})
        self.assertEqual(self.native.patch_count,0)

    def test_worker_source_guard_accepts_only_contiguous_owned_status_chain(self):
        sync.reconcile(self.service,self.source);sync.reconcile(self.service,self.source)
        item=self.native.package(394)
        self.assertTrue(sync.owned_source_matches(self.store,'existing-run',2,item))
        item['subject']='Human changed requirements'
        self.assertFalse(sync.owned_source_matches(self.store,'existing-run',2,item))
        item=self.native.package(394);item['lockVersion']+=1
        self.assertFalse(sync.owned_source_matches(self.store,'existing-run',2,item))

    def test_status_from_a_closed_or_foreign_workflow_node_cannot_reenter(self):
        self.native.status=999;self.policy['edges'].insert(0,[999,self.policy['states']['analysis']['id']])
        result=sync.reconcile(self.service,self.source)
        self.assertEqual(result['state'],'STATUS_SYNC_BLOCKED');self.assertEqual(self.native.patch_count,0)

    def test_source_uses_actual_github_html_url_and_merge_fields(self):
        from gateway.engineering_github_sync import save_projection
        contract={'engine':'openclaw','project_id':6,'native_id':394,'source_version':2,'kind':'development'}
        with self.store.connect() as db:
            db.execute("INSERT INTO ai_runs VALUES('existing-run',20,'done',?,?)",(canonical(self.source['result']),time.time()-100))
            db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES('existing-run',20,?,'finished',?,'agent')",(canonical(contract),time.time()-100))
        save_projection(self.service,[{'html_url':self.source['result']['pr_url'],'head_sha':'a'*40,'is_merged':True,'state':'closed'}],{'state':'NOT_VERIFIED'},time.time())
        source=sync.sources(self.service)[0]
        self.assertEqual(source['delivery_state'],'MERGED_PENDING_DEPLOYMENT')
        save_projection(self.service,[{'html_url':self.source['result']['pr_url'],'head_sha':'a'*40,'is_merged':True,'state':'closed','deployment_state':'DEPLOYED_TO_DEMO'}],{'state':'DEPLOYED_TO_DEMO'},time.time()+1)
        self.assertEqual(sync.sources(self.service)[0]['delivery_state'],'DEPLOYED_PENDING_ACCEPTANCE')


if __name__=='__main__':unittest.main()

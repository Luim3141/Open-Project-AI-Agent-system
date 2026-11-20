import copy
import json
from pathlib import Path
import tempfile
import time
import threading
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from gateway.store import Store,canonical,digest
from gateway import integration_events as events
from gateway.n8n_lifecycle_outbox import sign_envelope
from automation.n8n_integration_adapter import attach


class IntegrationEventsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.key='a'*64
        self.service=SimpleNamespace(store=self.store,config={'project_id':6,'engineering':{'enabled':True},'n8n_integration':{'enabled':True,'base_url':'http://n8n:5678','signing_key':self.key}})
        (self.store.root/'webhook_secret.json').write_text(json.dumps({'webhook_token':'x'*32}))

    def event(self,kind='GITHUB_PR_CHANGED',version=None,payload=None):
        identifier=events.enqueue(self.store,kind,'github:fixture:pr:10',version or 'a'*64,payload=payload or {'pr_number':10,'head_sha':'b'*40,'work_package_id':391})
        with self.store.connect() as db:return json.loads(db.execute('SELECT document FROM integration_event_outbox WHERE id=?',(identifier,)).fetchone()[0])

    def test_source_identity_deduplicates_and_rejects_arbitrary_payload(self):
        first=self.event();second=self.event()
        self.assertEqual(first,second)
        self.assertEqual(first['project_id'],6)
        for payload in [{'project_id':5},{'raw_prompt':'private'},{'head_sha':{'token':'private'}}]:
            with self.assertRaises(ValueError):self.event(payload=payload)

    def test_exact_signed_stored_event_required_and_effect_replayed_once(self):
        event=self.event();envelope=sign_envelope(event,self.key)
        with patch('gateway.integration_events._business',return_value={'state':'DELIVERY_OBSERVED'}) as effect:
            first=events.observe(self.service,envelope,'123');self.assertEqual(events.observe(self.service,envelope,'124'),first)
            effect.assert_called_once()
        changed=copy.deepcopy(event);changed['payload']['pr_number']=11
        with self.assertRaisesRegex(PermissionError,'SOURCE_DENIED'):events.observe(self.service,sign_envelope(changed,self.key),'125')
        with self.assertRaises(PermissionError):events.observe(self.service,envelope,'not-an-execution')
        old={**envelope,'published_at':int(time.time())-61}
        with self.assertRaises(PermissionError):events.observe(self.service,old,'123')

    def test_dispatch_requires_business_ack_and_retries_are_bounded(self):
        event=self.event()
        for attempt in range(5):
            result=events.deliver_pending(self.service,transport=lambda *a,**k:{'status':'ok'},now=time.time()+attempt*600)
        self.assertEqual(result,'DEAD')
        with self.store.connect() as db:row=db.execute('SELECT attempts,error FROM integration_event_outbox').fetchone()
        self.assertEqual(row['attempts'],5);self.assertEqual(row['error'],'INTEGRATION_DELIVERY_FAILED')
        self.assertEqual(events.deliver_pending(self.service,transport=lambda *a,**k:self.fail('No infinite retries'),now=time.time()+9999),'IDLE')

    def test_concurrent_duplicate_has_one_business_effect_and_durable_replay(self):
        event=self.event();envelope=sign_envelope(event,self.key);entered=threading.Event();release=threading.Event();results=[]
        def business(*args):
            entered.set();self.assertTrue(release.wait(5));return {'state':'DELIVERY_OBSERVED'}
        with patch('gateway.integration_events._business',side_effect=business) as effect:
            worker=threading.Thread(target=lambda:results.append(events.observe(self.service,envelope,'101')))
            worker.start();self.assertTrue(entered.wait(5))
            with self.assertRaisesRegex(ValueError,'OBSERVATION_BUSY'):events.observe(self.service,envelope,'102')
            release.set();worker.join(5);self.assertFalse(worker.is_alive())
            self.assertEqual(events.observe(self.service,envelope,'103'),results[0]);effect.assert_called_once()

    def test_reconcile_crash_replay_never_resets_a_verified_cache_job(self):
        event=self.event('RECONCILE_REQUESTED',100,{});native=SimpleNamespace(packages=lambda:[{'id':391,'lockVersion':2}])
        scoped=SimpleNamespace(store=self.store,native_actor=lambda actor:(native,{}),perform=lambda *a:{'status':'DRIFT_DETECTED','missing_native_ids':[391]})
        with patch('gateway.engineering.scoped_service',return_value=scoped):
            first=events._business(self.service,event)
            with self.store.connect() as db:
                row=db.execute('SELECT id FROM knowledge_sync').fetchone();identifier=row[0]
                db.execute("UPDATE knowledge_sync SET state='verified',attempts=1 WHERE id=?",(identifier,))
            second=events._business(self.service,event)
        self.assertEqual(first['queued_jobs'],1);self.assertEqual(second['queued_jobs'],0)
        self.assertEqual(second['state'],'DRIFT_OBSERVED')
        with self.store.connect() as db:
            rows=db.execute('SELECT id,state,attempts FROM knowledge_sync').fetchall()
        self.assertEqual(len(rows),1);self.assertEqual(tuple(rows[0]),(identifier,'verified',1))

    def test_dispatch_exact_callback_receipt_and_no_bearer(self):
        event=self.event();captured=[]
        def send(url,envelope,timeout,headers):
            captured.append((url,headers))
            return events.observe(self.service,envelope,'998')
        self.assertEqual(events.deliver_pending(self.service,transport=send),'ACKED')
        self.assertEqual(captured[0][0],'http://n8n:5678/webhook/qldapm-integration-wf04')
        self.assertNotIn('Authorization',captured[0][1])
        self.assertEqual(events.snapshot(self.store)[0]['execution_id'],'998')

    def test_github_source_state_cannot_overwrite_business_result(self):
        receipt=events._business(self.service,self.event(payload={'state':'open','pr_number':10}))
        self.assertEqual(receipt['state'],'DELIVERY_OBSERVED');self.assertEqual(receipt['github_state'],'open')

    def test_matching_http_ack_without_durable_business_receipt_is_retried(self):
        event=self.event()
        fake={'status':'OBSERVED','event_id':event['event_id'],'workflow':'WF04','project_id':6,'correlation_id':event['correlation_id'],'business_result':{}}
        self.assertEqual(events.deliver_pending(self.service,transport=lambda *a,**k:fake),'RETRY')
        fake['business_result']={'state':'DELIVERY_OBSERVED'}
        self.assertEqual(events.deliver_pending(self.service,transport=lambda *a,**k:fake,now=time.time()+100),'RETRY')

    def test_repair_prioritizes_actual_missing_source_outside_first_fifty(self):
        selected,scope=events._repair_targets(self.store,{'missing_native_ids':[99],'missing_point_ids':['unknown-vector']},[{'id':i,'lockVersion':1} for i in range(1,101)])
        self.assertEqual([r['id'] for r in selected],[99]);self.assertEqual(scope['unmapped_drift'],1)
        self.assertFalse(scope['repair_scope_complete'])
        selected,scope=events._repair_targets(self.store,{'missing_native_ids':list(range(1,61))},[{'id':i,'lockVersion':1} for i in range(1,101)])
        self.assertEqual(len(selected),50);self.assertEqual(scope['remaining_sources'],10);self.assertFalse(scope['repair_scope_complete'])

    def test_background_delivery_never_overlaps_or_blocks_worker(self):
        entered=threading.Event();release=threading.Event()
        def slow(service):
            entered.set();self.assertTrue(release.wait(5))
        with patch('gateway.integration_events.tick',side_effect=slow) as tick:
            events.dispatch(self.service);self.assertTrue(entered.wait(5))
            events.dispatch(self.service);tick.assert_called_once()
            release.set();self.service._n8n_integration_thread.join(5)
            self.assertFalse(self.service._n8n_integration_thread.is_alive())

    def test_withdrawn_source_never_claims_physical_delete_or_indexes(self):
        with self.store.connect() as db:db.execute('INSERT INTO native_index_cursor VALUES(20,6,391,2,?,0,?)',('a'*64,time.time()))
        event=self.event('NATIVE_WITHDRAWN',2,{'native_id':391,'source_hash':'a'*64})
        result=events._business(self.service,event)
        self.assertEqual(result['state'],'TOMBSTONED_VISIBILITY');self.assertFalse(result['physical_deletion'])
        event['source_version']=1
        self.assertEqual(events._business(self.service,event)['state'],'SUPERSEDED')

    def test_engineering_qa_never_grants_native_approval(self):
        run=str(uuid.uuid4());result={'status':'succeeded','head_sha':'b'*40,'test_evidence':{'command':'pytest','exit_code':0},'review_evidence':{'verdict':'PASS','qa':{'status':'PASS','exit_code':0}}}
        with self.store.connect() as db:
            db.execute('INSERT INTO ai_queue VALUES(?,?,?, ?,?,?,?,?)',(run,20,canonical({'project_id':6,'native_id':391}),'finished',time.time(),None,1,'agent'))
            db.execute('INSERT INTO ai_runs VALUES(?,?,?,?,?)',(run,20,'done',canonical(result),time.time()))
        event=self.event('ENGINEERING_QA_RESULT',digest(canonical(result)),{'run_id':run,'native_id':391,'head_sha':'b'*40})
        receipt=events._business(self.service,event)
        self.assertEqual(receipt['state'],'QA_VERIFIED');self.assertFalse(receipt['native_approval'])
        result['review_evidence']['qa']['exit_code']=1
        with self.store.connect() as db:db.execute('UPDATE ai_runs SET result=? WHERE id=?',(canonical(result),run))
        event['source_version']=digest(canonical(result))
        self.assertEqual(events._business(self.service,event)['state'],'QA_BLOCKED')

    def test_planning_publish_uses_actual_scoped_admission_and_plan_once(self):
        from gateway.engineering_lifecycle import setup
        setup(self.store)
        run=str(uuid.uuid4());contract={'engine':'openclaw','project_id':6,'kind':'planning','native_id':379,
            'source_version':4,'unit':'requirements-planning-v1','request_key':'intake-one','stage':'ADMITTED'}
        plan={'id':run,'project_id':6,'native_id':379,'state':'PUBLISHED','ba':{'summary':'BA'},
            'pm':{'assignments':[{'unit':'new-unit'}]},'native_units':{'new-unit':{'id':401}}}
        with self.store.connect() as db:
            db.execute('INSERT INTO ai_queue VALUES(?,?,?,?,?,?,?,?)',(run,20,canonical(contract),'finished',time.time(),None,1,'agent'))
            db.execute('INSERT INTO engineering_plans VALUES(?,?,?)',(run,20,canonical(plan)))
        events.publish(self.store)
        contract['stage']='COMPLETED'
        with self.store.connect() as db:db.execute('UPDATE ai_queue SET payload=? WHERE id=?',(canonical(contract),run))
        events.publish(self.store)
        with self.store.connect() as db:
            rows=[json.loads(r[0]) for r in db.execute("SELECT document FROM integration_event_outbox WHERE workflow IN ('WF03','WF10')")]
        self.assertEqual(len(rows),2)
        native=SimpleNamespace(package=lambda identifier:{'id':identifier,'lockVersion':4})
        scoped=SimpleNamespace(store=self.store,native_actor=lambda actor:(native,{}))
        with patch('gateway.engineering.scoped_service',return_value=scoped):
            receipts={r['workflow']:events._business(self.service,r) for r in rows}
            self.assertEqual(receipts['WF03']['state'],'PLANNING_ACCEPTED')
            self.assertEqual(receipts['WF10']['state'],'PLAN_NATIVE_UNITS_VERIFIED')
            self.assertEqual(receipts['WF10']['native_unit_ids'],[401])
            changed=next(copy.deepcopy(r) for r in rows if r['workflow']=='WF10');changed['payload']['native_id']=5
            with self.assertRaisesRegex(PermissionError,'NATIVE_SCOPE_DENIED'):events._business(self.service,changed)
            with self.store.connect() as db:db.execute('UPDATE engineering_plans SET document=? WHERE id=?',(canonical({**plan,'state':'PLANNING'}),run))
            self.assertEqual(events._business(self.service,next(r for r in rows if r['workflow']=='WF10'))['state'],'SUPERSEDED')
            with self.store.connect() as db:db.execute('UPDATE ai_queue SET actor=19 WHERE id=?',(run,))
            with self.assertRaisesRegex(PermissionError,'PLANNING_SOURCE_REQUIRED'):events._business(self.service,next(r for r in rows if r['workflow']=='WF03'))
        self.assertFalse(receipts['WF10']['native_write'])

    def test_machine_route_forbids_human_bearer_origin_and_query(self):
        event=self.event();envelope=sign_envelope(event,self.key);scope={'method':'POST','query_string':b''}
        for headers in [{'authorization':'Bearer private'},{'origin':'http://localhost'},{'x-qldapm-n8n-execution':'bad'}]:
            self.assertEqual(events.response(self.service,scope,headers,json.dumps(envelope).encode()).status_code,403)

    def test_adapter_keeps_human_approval_graph_and_deduplicates_branch(self):
        original={'id':'fixture','name':'WF11: QA','nodes':[{'id':'human','name':'Human Decision','parameters':{}}],'connections':{'Human Decision':{'main':[]}},'settings':{}}
        candidate=attach(original);second=attach(candidate)
        self.assertEqual(candidate,second);self.assertEqual(original['nodes'][0],candidate['nodes'][0])
        self.assertEqual(len(candidate['nodes']),5)
        self.assertFalse(any('Authorization' in json.dumps(n) for n in candidate['nodes'][1:]))
        callback=next(n for n in candidate['nodes'] if n['id']=='integration-callback')
        self.assertEqual(callback['parameters']['jsonBody'],'={{ $json.body }}')

    def test_delegated_adapters_preserve_human_branches_without_bearer_or_identity_claim(self):
        for code in ('WF05','WF06'):
            original={'id':'fixture','name':code+': approval','nodes':[{'id':'human','name':'Human Decision','parameters':{}}],
                      'connections':{'Human Decision':{'main':[]}},'settings':{'timezone':'Asia/Bangkok'}}
            candidate=attach(original)
            self.assertEqual(candidate,attach(candidate));self.assertEqual(candidate['nodes'][0],original['nodes'][0])
            self.assertEqual(candidate['connections']['Human Decision'],original['connections']['Human Decision'])
            self.assertEqual(candidate['settings'],original['settings'])
            machine=json.dumps(candidate['nodes'][1:]);self.assertNotIn('Bearer',machine);self.assertNotIn('actor18',machine)


if __name__=='__main__':unittest.main()

import tempfile,time,unittest,json
from pathlib import Path
from types import SimpleNamespace
from gateway.store import Store,canonical
from gateway import engineering
from gateway.engineering_observability import describe_run,policy,persist_notifications,enrich_profiles

class OwnerRecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name));engineering.setup(self.store)
  self.service=SimpleNamespace(store=self.store,config={'engineering':{'enabled':True}})
  self.run={'id':'fixture-run','native_id':391,'unit':'csv','queue_state':'finished','created_at':10,'result':{'status':'blocked','error':'OPENCLAW_STEP_NOT_COMPLETED'},'checkpoint':{'version':1,'resumable':True,'terminal_known':True,'stage':'dev-0','session_id':'last','completed_steps':['context']}}
  with self.store.connect() as db:
   db.execute('INSERT INTO ai_queue VALUES(?,?,?,?,?,?,?,?)',('fixture-run',20,canonical({'engine':'openclaw','project_id':6,'native_id':391,'unit':'csv','definition':{'title':'CSV export'}}),'finished',10,None,1,'engineering'))
   db.execute('INSERT INTO ai_runs VALUES(?,?,?,?,?)',('fixture-run',20,'failed_or_unknown',canonical(self.run['result']),10))
 def receipt(self,n,session='last',http=200):
  self.store.provider_receipt({'id':session+str(n),'actor':20,'run_id':'fixture-run','project':'billing','agent':'dev','provider':'google','phase':'generateContent','session_id':session,'at':n+(100 if session=='last' else 0),'http_status':http,'usage':{'totalTokenCount':5}})
 def describe(self):return describe_run(self.service,self.run)
 def test_classifies_internal_cap_only_with_complete_successful_evidence(self):
  for n in range(12):self.receipt(n)
  d=self.describe();self.assertEqual(d['failure']['category'],'DEV_BUDGET_EXHAUSTED');self.assertEqual(d['budget']['calls_used'],12);self.assertEqual(d['budget']['provider_response_count'],12)
 def test_latest_session_quota_overrides_old_internal_exhaustion(self):
  for n in range(12):self.receipt(n,'old')
  self.receipt(1,http=429)
  d=self.describe();self.assertEqual(d['failure']['category'],'PROVIDER_QUOTA_EXHAUSTED');self.assertEqual(d['budget']['cumulative_calls'],13);self.assertFalse(d['resume']['eligible'])
 def test_insufficient_evidence_stays_unknown(self):
  self.receipt(1);self.assertEqual(self.describe()['failure']['category'],'UNKNOWN_FAILURE')
 def test_unknown_write_fences_resume(self):
  self.store.begin(20,'engineering-fixture-run-progress',{'action':'write'})
  d=self.describe();self.assertFalse(d['resume']['eligible']);self.assertEqual(d['resume']['reason'],'EXTERNAL_WRITE_RECONCILIATION_REQUIRED')
 def test_policy_validated_and_auto_opt_in(self):
  self.assertFalse(policy(self.service)['auto_continue']);self.service.config['engineering']['continuation']={'attempt_calls':100};self.assertRaises(ValueError,policy,self.service)
 def test_durable_notification_dedup_and_dismissal(self):
  from gateway.engineering_reporting import dismiss_notification,list_notifications
  d=self.describe();persist_notifications(self.service,[d]);persist_notifications(self.service,[d]);rows=list_notifications(self.service,18);self.assertEqual(len(rows),2);self.assertEqual(rows[0]['native_id'],391);self.assertEqual(rows[0]['run_id'],'fixture-run')
  dismiss_notification(self.service,18,rows[0]['id']);persist_notifications(self.service,[d]);self.assertFalse(next(row for row in list_notifications(self.service,18) if row['id']==rows[0]['id'])['unread'])
 def test_unchanged_poll_does_not_open_one_write_transaction_per_historical_notification(self):
  from unittest.mock import patch
  d=self.describe();persist_notifications(self.service,[d])
  with patch.object(self.store,'connect',wraps=self.store.connect) as connect:
   persist_notifications(self.service,[d]*50)
  self.assertLessEqual(connect.call_count,3,'unchanged UI polling repeats schema/writes for every old event')
 def test_last_activity_not_current_running(self):
  self.receipt(1)
  d=self.describe();p=[{'agent':'dev','status':'STANDBY'}];enrich_profiles(p,[d]);self.assertEqual(p[0]['current_state'],'STANDBY');self.assertEqual(p[0]['last_activity']['native_id'],391)
 def test_provider_success_does_not_complete_task(self):
  self.receipt(1);self.assertEqual(self.describe()['task_status'],'BLOCKED')
 def test_failed_agent_event_is_not_successful_last_activity(self):
  self.receipt(1)
  with self.store.connect() as db:
   db.execute('INSERT INTO execution_events(event_id,run_id,actor,project,document) VALUES(?,?,?,?,?)',('failed','fixture-run',20,6,canonical({'agent_id':'dev','event_type':'AGENT_FAILED','timestamp':200})))
  self.assertEqual(self.describe()['agent_activities']['dev']['result'],'blocked')
 def test_failed_rework_not_overridden_by_old_completed_dev_step(self):
  self.receipt(1)
  self.run['checkpoint'].update(stage='rework-1',completed_steps=['dev-0','review-0'])
  self.assertEqual(self.describe()['agent_activities']['dev']['result'],'blocked')
 def test_previous_dev_activity_survives_reviewer_handoff(self):
  self.receipt(1)
  with self.store.connect() as db:
   for i,(role,kind) in enumerate([('dev','AGENT_STARTED'),('dev','AGENT_COMPLETED'),('reviewer','AGENT_STARTED')]):
    db.execute('INSERT INTO execution_events(event_id,run_id,actor,project,document) VALUES(?,?,?,?,?)',(str(i),'fixture-run',20,6,canonical({'agent_id':role,'event_type':kind,'timestamp':200+i})))
  self.run.update(queue_state='executing',result={'status':'running','agent':'reviewer'})
  d=self.describe();profiles=[{'agent':r,'status':'STANDBY'} for r in ['dev','reviewer']];enrich_profiles(profiles,[d])
  self.assertEqual(profiles[0]['current_state'],'STANDBY');self.assertEqual(profiles[0]['last_activity']['result'],'succeeded');self.assertEqual(profiles[1]['current_run']['native_id'],391)
 def test_session_receipt_cap_overrides_default(self):
  self.store.provider_receipt({'id':'cap','actor':20,'run_id':'fixture-run','project':'billing','agent':'dev','phase':'generateContent','session_id':'last','at':100,'http_status':200,'call_cap':3})
  d=self.describe();self.assertEqual(d['budget']['call_cap'],3);self.assertEqual(d['budget']['remaining'],2)
 def test_recovered_429_does_not_override_later_success_and_spent_internal_cap(self):
  self.receipt(0,http=429)
  for n in range(1,12):self.receipt(n)
  self.assertEqual(self.describe()['failure']['category'],'DEV_BUDGET_EXHAUSTED')
 def test_authorization_failure_distinct_from_quota(self):
  self.receipt(1,http=401);self.assertEqual(self.describe()['failure']['category'],'PROVIDER_AUTH_FAILED')
 def test_missing_checkpoint_time_is_unknown(self):
  self.assertIsNone(self.describe()['resume']['checkpoint_saved_at'])

class OwnerContinuationPolicyTests(unittest.TestCase):
 def setUp(self):
  from test_engineering_continuation import Native
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name));self.native=Native()
  self.service=SimpleNamespace(store=self.store,config={'project_id':6,'engineering':{'enabled':True,'continuation':{'cooldown_seconds':0}}},native_actor=lambda actor:(self.native,{'user_id':actor,'role':'PM'}))
 def failed(self,auto=False):
  from gateway import engineering_lifecycle as lifecycle
  rid=engineering.admit(self.service,20,{'native_id':379,'lock_version':0,'unit':engineering.UNIT},'policy')['id'];engineering.claim(self.service,20)
  saved=lifecycle.save(self.service,20,rid,{'stage':'dev-0','completed_steps':['context'],'terminal_known':True,'resumable':True,'revision':None,'session_id':'fixture','error':'OPENCLAW_STEP_NOT_COMPLETED'})
  for n in range(12):self.store.provider_receipt({'id':str(n),'run_id':rid,'actor':20,'project':'billing','agent':'dev','phase':'generateContent','session_id':'fixture','at':time.time(),'http_status':200})
  if auto:
   with self.store.connect() as db:db.execute("UPDATE engineering_control SET mode='AUTO' WHERE project=6")
  engineering.finish(self.service,20,rid,{'status':'blocked','error':'OPENCLAW_STEP_NOT_COMPLETED'})
  return rid,saved
 def test_manual_continuation_policy_cooldown_and_recovery_limit(self):
  from gateway import engineering_lifecycle as lifecycle
  rid,saved=self.failed();self.service.config['engineering']['continuation']['cooldown_seconds']=60
  with self.assertRaisesRegex(ValueError,'COOLDOWN'):lifecycle.resume(self.service,20,rid,saved['version'])
  self.service.config['engineering']['continuation'].update(cooldown_seconds=0,max_continuations=0)
  with self.assertRaisesRegex(ValueError,'RECOVERY_BUDGET'):lifecycle.resume(self.service,20,rid,saved['version'])
 def test_auto_opt_in_only_safe_same_run_and_duplicate_prevention(self):
  from gateway.engineering_auto import schedule_next_auto_unit
  self.service.config['engineering']['continuation']['auto_continue']=True
  rid,saved=self.failed(auto=True);res=schedule_next_auto_unit(self.service,20)
  self.assertTrue(res['continuation']);self.assertEqual(res['run_id'],rid);self.assertEqual(res['mode'],'AUTO')
  self.assertEqual(schedule_next_auto_unit(self.service,20)['reason'],'CONCURRENCY_LOCKED')
  with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM ai_queue').fetchone()[0],1)
 def test_default_auto_blocked_shutoff_is_explicit(self):
  rid,saved=self.failed(auto=True)
  with self.store.connect() as db:
   self.assertEqual(db.execute('SELECT mode FROM engineering_control').fetchone()[0],'OFF')
   self.assertEqual(db.execute("SELECT outcome FROM audit WHERE action='engineering_auto_shutoff'").fetchone()[0],'RUN_BLOCKED_REQUIRES_OWNER')
 def test_pending_resume_after_owner_off_does_not_spend_another_continuation(self):
  from gateway import engineering_lifecycle as lifecycle
  rid,saved=self.failed()
  first=lifecycle.resume(self.service,20,rid,saved['version'])
  engineering.control(self.service,20,'OFF')
  again=lifecycle.resume(self.service,20,rid,saved['version'])
  self.assertEqual(again['recovery_count'],first['recovery_count'])
 def test_provider_recovery_requires_newer_verified_readiness_and_preserves_error(self):
  from gateway import engineering_lifecycle as lifecycle
  rid,saved=self.failed()
  failed_at=time.time()
  self.store.provider_receipt({'id':'quota','run_id':rid,'actor':20,'project':'billing','agent':'dev','phase':'generateContent','session_id':'quota-session','at':failed_at,'http_status':429})
  self.service.gemini=SimpleNamespace(settings=lambda:{'project':'billing'},readiness=lambda p:{'state':'READY','last_successful_check':failed_at-10})
  with self.assertRaisesRegex(ValueError,'PROVIDER_RECOVERY_REQUIRED'):lifecycle.resume(self.service,20,rid,saved['version'])
  self.service.gemini.readiness=lambda p:{'state':'READY','last_successful_check':time.time()}
  self.assertEqual(lifecycle.resume(self.service,20,rid,saved['version'])['id'],rid)
 def test_delivery_note_targets_child_wp_and_keeps_child_run_reference(self):
  from gateway import engineering_operator as operator
  from unittest.mock import patch
  rid=engineering.admit(self.service,20,{'native_id':379,'lock_version':0,'unit':engineering.UNIT},'child-note')['id']
  engineering.claim(self.service,20)
  with self.store.connect() as db:
   payload=json.loads(db.execute('SELECT payload FROM ai_queue WHERE id=?',(rid,)).fetchone()[0]);payload['native_id']=391
   db.execute('UPDATE ai_queue SET payload=? WHERE id=?',(canonical(payload),rid))
  with patch.object(operator,'native_once') as write:
   result=operator._operation(self.service,'delivery_note',{'run_id':rid,'error':'OPENCLAW_STEP_NOT_COMPLETED'})
  self.assertEqual(write.call_args.args[4],'/api/v3/work_packages/391/activities')
  self.assertIn('WP #391',write.call_args.args[6]['comment']['raw'])
  self.assertEqual(result['native_id'],391)
 def test_status_execution_rows_receive_resume_summary_without_losing_result_document(self):
  from unittest.mock import patch
  rid,saved=self.failed()
  with patch('gateway.engineering_github_sync.fetch_pull_requests',return_value=[]),patch('gateway.engineering_health.integration_health',return_value=[]):
   row=next(r for r in engineering.status(self.service,20)['runs'] if r['id']==rid)
  self.assertTrue(row['resume']['eligible'])
  self.assertIsInstance(row['result'],dict)
 def test_provider_readiness_does_not_deadlock_inside_resume_write_transaction(self):
  from gateway import engineering_lifecycle as lifecycle
  import sqlite3
  rid,saved=self.failed();failed_at=time.time()
  self.store.provider_receipt({'id':'quota-lock','run_id':rid,'actor':20,'project':'billing','agent':'dev','phase':'generateContent','session_id':'quota-session','at':failed_at,'http_status':429})
  def readiness(policy):
   db=sqlite3.connect(self.store.root/'gateway.sqlite',timeout=.02)
   try:db.execute('BEGIN IMMEDIATE')
   finally:db.close()
   return {'state':'READY','last_successful_check':time.time()}
  self.service.gemini=SimpleNamespace(settings=lambda:{'project':'billing'},readiness=readiness)
  self.assertEqual(lifecycle.resume(self.service,20,rid,saved['version'])['id'],rid)
 def test_auto_429_waits_for_fresh_readiness_then_same_run_once(self):
  from gateway.engineering_auto import schedule_next_auto_unit
  self.service.config['engineering']['continuation']['auto_continue']=True
  self.service.gemini=SimpleNamespace(settings=lambda:{'model':'gemini-3.5-flash-lite'},readiness=lambda policy:{'state':'WAITING_QUOTA'})
  rid,saved=self.failed(auto=True)
  self.store.provider_receipt({'id':'11','run_id':rid,'actor':20,'project':'billing','agent':'dev','phase':'generateContent','session_id':'fixture','at':time.time(),'http_status':429})
  waiting=schedule_next_auto_unit(self.service,20);self.assertEqual(waiting['reason'],'WAITING_FOR_QUOTA');self.assertEqual(waiting['mode'],'AUTO')
  self.service.gemini.readiness=lambda policy:{'state':'READY','last_successful_check':time.time()}
  resumed=schedule_next_auto_unit(self.service,20);self.assertEqual(resumed['run_id'],rid);self.assertTrue(resumed['continuation'])
  self.assertEqual(schedule_next_auto_unit(self.service,20)['reason'],'CONCURRENCY_LOCKED')
 def test_auto_429_respects_off_and_exhausted_policy(self):
  from gateway.engineering_auto import schedule_next_auto_unit
  self.service.config['engineering']['continuation']['auto_continue']=True
  self.service.gemini=SimpleNamespace(settings=lambda:{'model':'gemini-3.5-flash-lite'},readiness=lambda policy:{'state':'READY','last_successful_check':time.time()})
  rid,saved=self.failed(auto=True)
  self.store.provider_receipt({'id':'11','run_id':rid,'actor':20,'project':'billing','agent':'dev','phase':'generateContent','session_id':'fixture','at':time.time(),'http_status':429})
  with self.store.connect() as db:db.execute("UPDATE engineering_control SET mode='OFF' WHERE project=6")
  self.assertEqual(schedule_next_auto_unit(self.service,20)['reason'],'MODE_NOT_AUTO')
  self.service.config['engineering']['continuation']['max_continuations']=0
  with self.store.connect() as db:db.execute("UPDATE engineering_control SET mode='AUTO' WHERE project=6")
  stopped=schedule_next_auto_unit(self.service,20);self.assertEqual(stopped['reason'],'CONTINUATION_LIMIT_REACHED');self.assertEqual(stopped['mode'],'OFF')
 def test_internal_auto_resume_requires_owner_opt_in(self):
  from gateway import engineering_lifecycle as lifecycle
  rid,saved=self.failed()
  with self.store.connect() as db:db.execute("UPDATE engineering_control SET mode='AUTO' WHERE project=6")
  with self.assertRaisesRegex(ValueError,'AUTO_CONTINUATION_DISABLED'):lifecycle.resume(self.service,20,rid,saved['version'],preserve_auto=True)
if __name__=='__main__':unittest.main()

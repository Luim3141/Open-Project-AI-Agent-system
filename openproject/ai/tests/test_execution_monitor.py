"""Monitor projections, scope, telemetry and read-only replay. No Google network."""
import json
import time
import unittest
import uuid
from unittest.mock import patch

from pydantic import ValidationError

from gateway.agent_models import AgentTask,AgentRun,AgentResult,RunScope,ExecutionPlan,PlanStep,PlanBudget
from gateway.execution_monitor import project_execution,layers,observed
from gateway.execution_events import append,ExecutionEvent
from gateway.store import canonical,digest


class ExecutionMonitorTests(unittest.TestCase):
    def setUp(self):
        from tests.test_local_queries import LocalQueryTests
        self.fixture=LocalQueryTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.s=self.fixture.service;self.store=self.fixture.store;now=time.time()
        self.scope=RunScope(run_id=str(uuid.uuid4()),task_id=str(uuid.uuid4()),actor_id=7,project_id=3,trace_id=str(uuid.uuid4()))
        self.task=AgentTask(task_id=self.scope.task_id,actor_id=7,project_id=3,conversation_id=str(uuid.uuid4()),agent='supervisor',instruction='BA Developer QA phân tích #1, chỉ đọc.',created_at=now,expires_at=now+600)
        self.agent=AgentResult(**self.scope.model_dump(),state='COMPLETED',summary='BA:\nRequirement draft.\n\nDEV:\nTechnical draft.\n\nQA:\nTest draft.\n\nReviewer local: references checked.')
        self.run=AgentRun(**self.scope.model_dump(),state='COMPLETED',created_at=now,updated_at=now+1,result=self.agent)
        self.plan=ExecutionPlan(plan_id=self.scope.task_id,task_id=self.scope.task_id,actor_id=7,project_id=3,operation_type='READ_ONLY',budget=PlanBudget(),steps=[PlanStep(step_id=i+1,agent=a,action='analyze',dependencies=[i] if i else []) for i,a in enumerate(['ba','dev','qa','reviewer'])])
        self.result={'status':'succeeded','engine':'gemini_supervisor','plan':self.plan.model_dump(),'agent_result':self.agent.model_dump(),'text':'Stored aggregate',
                     'source_ids':[1],'source_fingerprint':digest(canonical([(1,1)])),'tools':[]}
        self.receipts=[{'id':str(uuid.uuid4()),'actor':7,'project':'offline-fixture','run_id':self.scope.run_id,'agent':a,'phase':'generateContent','state':'LIVE_SUCCESS','model':'gemini-3.5-flash-lite','at':now+i,'duration_seconds':.5,'attempt':0,'usage':{'promptTokenCount':10,'totalTokenCount':20}} for i,a in enumerate(['supervisor','ba','dev','qa'])]

    def project(self,result=None,events=None,receipts=None):
        return project_execution({'id':self.scope.run_id,'state':'done','result':result or self.result},self.task,self.run,'PM',self.receipts if receipts is None else receipts,events or [])

    def save(self,result=None):
        self.store.create_agent_task(7,3,self.task)
        queued=self.run.model_copy(update={'state':'QUEUED','result':None,'updated_at':self.run.created_at})
        self.store.create_agent_run(7,3,queued)
        self.store.transition_agent_run(7,3,self.scope.run_id,'QUEUED','RUNNING')
        with self.store.connect() as db:db.execute('INSERT INTO ai_runs VALUES(?,?,?,?,?)',(self.scope.run_id,7,'running',canonical(result or self.result),time.time()))
        self.store.finish_run(7,self.scope.run_id,result or self.result,'done')
        for r in self.receipts:self.store.provider_receipt(r)

    def test_graph_has_distinct_assignment_and_dependency_edges(self):
        view=self.project();self.assertEqual(len(view.nodes),6)
        self.assertIn({'from':'supervisor','to':'3','kind':'ASSIGNMENT'},view.edges)
        self.assertIn({'from':'1','to':'2','kind':'DEPENDENCY'},view.edges)
        self.assertNotIn({'from':'1','to':'2','kind':'ASSIGNMENT'},view.edges)

    def test_six_role_projection_keeps_fe_be_outputs_and_local_reviewer_distinct(self):
        agents=['ba','fe','be','qa','reviewer']
        plan=self.plan.model_copy(update={'steps':[PlanStep(step_id=i+1,agent=a,action='analyze',dependencies=[i] if i else []) for i,a in enumerate(agents)]})
        result={**self.result,'plan':plan.model_dump(),'agent_outputs':[{'step_id':i+1,'agent':a,
            'result':self.agent.model_copy(update={'summary':a+' synthetic advisory; no tests executed'}).model_dump()} for i,a in enumerate(agents)]}
        receipts=[{**self.receipts[0],'id':str(uuid.uuid4()),'agent':a,'state':'MOCK_SUCCESS'} for a in ['supervisor','ba','fe','be','qa']]
        view=self.project(result,receipts=receipts)
        self.assertEqual(view.metrics['agents'],6)
        self.assertEqual(view.metrics['calls'],5)
        self.assertEqual(view.mode,'MOCK_TEST')
        for agent in ['fe','be']:
            node=next(n for n in view.nodes if n.agent==agent)
            self.assertEqual(node.name,agent.upper()+' Agent')
            self.assertIn(agent+' synthetic advisory',node.output)
            self.assertEqual(node.calls,1)
        reviewer=next(n for n in view.nodes if n.agent=='reviewer')
        self.assertEqual(reviewer.calls,0)
        self.assertEqual(reviewer.mode,'LOCAL_DETERMINISTIC')

    def test_actual_execution_client_javascript_syntax_accepts_fe_be_roles(self):
        import re,shutil,subprocess
        from pathlib import Path
        node=shutil.which('node')
        if not node:self.skipTest('Node.js required for actual ERB client syntax validation')
        source=(Path(__file__).resolve().parents[1]/'core/overlay/app/views/qldapm_ai/_execution_client.html.erb').read_text(encoding='utf-8')
        self.assertIn("label: 'FE'",source);self.assertIn("label: 'BE'",source)
        checked=subprocess.run([node,'--check'],input=re.sub(r'<%.*?%>','',source,flags=re.S),text=True,capture_output=True)
        self.assertEqual(checked.returncode,0,checked.stderr)

    def test_actual_client_report_separates_fe_be_from_ba(self):
        import re, shutil, subprocess
        from pathlib import Path
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js required for actual client report parser')
        source = (Path(__file__).resolve().parents[1] / 'core/overlay/app/views/qldapm_ai/_execution_client.html.erb').read_text(encoding='utf-8')
        parser = source[source.index('  function parseFinalReport('):source.index('  function snapshot()')]
        harness = r"""
const assert = require('node:assert/strict');
function el(tag, text, className) {
  return {tag, text, className, children: [], append(...children) {this.children.push(...children);}};
}
const container = el('div');
container.replaceChildren = () => { container.children = []; };
const $ = () => container;
"""
        checks = r"""
parseFinalReport('Summary\nBA:\nBA output\nFE:\n<script>FE output</script>\nBE:\nBE output\nQA:\nQA output');
assert.equal(container.children.length, 5);
assert.match(container.children[2].children[0].children[0].text, /FE Agent/);
assert.equal(container.children[2].children[1].text, '<script>FE output</script>');
assert.match(container.children[3].children[0].children[0].text, /BE Agent/);
assert.equal(container.children[3].children[1].text, 'BE output');
parseFinalReport(null);
assert.equal(container.children.length, 1);
"""
        checked = subprocess.run([node, '-'], input=harness + parser + checks, text=True, capture_output=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_single_specialist_only_has_real_plan_nodes(self):
        r={**self.result,'plan':self.plan.model_copy(update={'steps':self.plan.steps[:1]}).model_dump()}
        self.assertEqual([n.agent for n in self.project(r).nodes],['supervisor','ba','final'])

    def test_parallel_branches_have_same_level_and_reviewer_join(self):
        steps=[PlanStep(step_id=1,agent='ba',action='read'),PlanStep(step_id=2,agent='dev',action='read'),PlanStep(step_id=3,agent='reviewer',action='review',dependencies=[1,2])]
        self.assertEqual(layers(steps),{1:1,2:1,3:2})

    def test_invalid_dag_cycles_duplicates_and_missing_dependencies_rejected(self):
        for steps in ([PlanStep(step_id=1,agent='ba',action='x',dependencies=[2]),PlanStep(step_id=2,agent='qa',action='x',dependencies=[1])],[PlanStep(step_id=1,agent='ba',action='x',dependencies=[9])],[PlanStep(step_id=1,agent='ba',action='x')]*2):
            with self.assertRaises(ValueError):layers(steps)

    def test_legacy_outputs_are_only_exact_stored_segments_and_missing_times_are_null(self):
        v=self.project();ba=next(n for n in v.nodes if n.agent=='ba')
        self.assertEqual(ba.output,'Requirement draft.');self.assertEqual(ba.output_origin,'LEGACY_AGGREGATE_SEGMENT')
        self.assertIsNone(ba.started_at);self.assertIsNone(ba.duration_seconds)
        self.assertIsNone(next(n for n in v.nodes if n.agent=='reviewer').output)
        self.assertTrue(v.warnings)

    def test_ambiguous_legacy_labels_do_not_invent_output(self):
        r={**self.result,'agent_result':{**self.agent.model_dump(),'summary':'BA:\nOne\nBA:\nUnexpected second marker'}}
        self.assertIsNone(next(n for n in self.project(r).nodes if n.agent=='ba').output)

    def test_receipts_not_configuration_determine_mode_usage_and_retry(self):
        self.assertEqual(self.project().metrics['calls'],4);self.assertEqual(self.project().metrics['tokens'],80)
        self.assertIsNone(self.project(receipts=[]).mode)
        rs=[{**self.receipts[0],'state':'MOCK_SUCCESS','attempt':1}]
        self.assertEqual(self.project(receipts=rs).mode,'MOCK_TEST');self.assertEqual(observed(rs)['retries'],1)
        self.assertIsNone(observed([{**rs[0],'usage':None}])['tokens'])
        self.assertEqual(observed([{**rs[0],'state':'INVALID_RESPONSE'}])['errors'],1)
        pending={k:v for k,v in rs[0].items() if k!='duration_seconds'}
        self.assertIsNone(observed([{**pending,'state':'ATTEMPTING'}])['model_duration_seconds'])

    def test_stored_event_order_dedup_and_code_only_schema(self):
        self.save()
        with self.store.connect() as db:
            for _ in range(2):append(db,self.scope,'AGENT_STARTED',agent='ba',step_id=1,status='RUNNING',key='one-start')
        events,_=self.store.execution_records(7,3,self.scope.run_id)
        self.assertEqual(sum(e['event_type']=='AGENT_STARTED' for e in events),1)
        self.assertEqual([e['sequence'] for e in events],sorted(e['sequence'] for e in events))
        with self.assertRaises(ValidationError):ExecutionEvent(event_id='x',run_id='x',trace_id='x',event_type='SECRET',timestamp=1.,sequence=1)

    def test_detail_and_replay_do_not_enqueue_or_call_model(self):
        self.save()
        with patch.object(self.s.gemini,'structured',side_effect=AssertionError('Never call provider on read')):
            for _ in range(3):
                v=self.s.execute_actor(7,{'action':'get_execution_monitor','arguments':{'id':self.scope.run_id}})['result']
                self.assertEqual(v['mode'],'LIVE_GEMINI')
        with self.store.connect() as db:self.assertEqual(db.execute('select count(*) from gemini_usage').fetchone()[0],0)

    def test_cross_actor_and_cross_project_denied(self):
        self.save()
        with self.assertRaises(PermissionError):self.s.execute_actor(8,{'action':'get_execution_monitor','arguments':{'id':self.scope.run_id}})
        self.fixture.config['project_id']=4
        with self.assertRaises(PermissionError):self.s.execute_actor(7,{'action':'get_execution_monitor','arguments':{'id':self.scope.run_id}})

    def test_version_stale_has_no_old_request_outputs_events_sources(self):
        self.save();self.fixture.state.rows[0]['lockVersion']=2
        v=self.s.execute_actor(7,{'action':'get_execution_monitor','arguments':{'id':self.scope.run_id}})['result']
        self.assertEqual(v['state'],'STALE');self.assertIsNone(v['request']);self.assertEqual(v['events'],[]);self.assertEqual(v['nodes'],[]);self.assertIsNone(v['final_output'])

    def test_revoked_item_and_membership_fail_closed(self):
        self.save();self.fixture.state.visible[7]=[2]
        with self.assertRaises(PermissionError):self.s.execute_actor(7,{'action':'get_execution_monitor','arguments':{'id':self.scope.run_id}})
        del self.fixture.state.roles[7]
        with self.assertRaises(PermissionError):self.s.execute_actor(7,{'action':'list_execution_monitors','arguments':{}})

    def test_history_filter_pagination_and_actor_bound_with_no_outputs(self):
        self.save()
        page=self.s.execute_actor(7,{'action':'list_execution_monitors','arguments':{'limit':1,'search':'Developer','state':'COMPLETED'}})['result']
        self.assertEqual(page['total'],1);self.assertEqual(len(page['items']),1);self.assertNotIn('output',page['items'][0]);self.assertEqual(page['items'][0]['calls'],4)
        self.assertEqual(self.store.execution_history(8,3)['total'],0)
        self.assertEqual(self.store.execution_history(7,3,search="' OR 1=1 --")['total'],0)
        self.assertEqual(self.store.execution_history(7,3,offset=1)['items'],[])

    def test_failed_and_running_statuses_use_actual_events_not_old_live_success(self):
        events=[{'event_type':'AGENT_STARTED','step_id':2,'agent_id':'dev','timestamp':1.,'sequence':1,'status':'RUNNING'},
                {'event_type':'AGENT_FAILED','step_id':2,'agent_id':'dev','timestamp':2.,'sequence':2,'status':'FAILED'}]
        node=next(n for n in self.project(events=events).nodes if n.agent=='dev');self.assertEqual(node.state,'FAILED');self.assertEqual(node.duration_seconds,1.)
        self.assertEqual(next(n for n in self.project(events=events[:1]).nodes if n.agent=='dev').state,'INTERRUPTED')
        active=self.run.model_copy(update={'state':'RUNNING','result':None})
        view=project_execution({'id':self.scope.run_id,'state':'running','result':self.result},self.task,active,'PM',self.receipts,events[:1])
        self.assertEqual(next(n for n in view.nodes if n.agent=='dev').state,'RUNNING')

    def test_current_agent_outputs_have_scope_and_validation_not_hidden_prompts(self):
        r={**self.result,'agent_outputs':[{'step_id':1,'agent':'ba','result':{**self.agent.model_dump(),'summary':'<script>danger()</script>'}}]}
        v=self.project(r);self.assertEqual(v.nodes[1].output,'<script>danger()</script>') # Client must use textContent.
        r['agent_outputs'][0]['result']['actor_id']=8
        with self.assertRaises(PermissionError):self.project(r)

    def test_empty_plan_and_missing_telemetry_are_explicit(self):
        r={**self.result,'plan':None,'agent_result':None}
        v=self.project(r,receipts=[]);self.assertEqual([n.agent for n in v.nodes],['supervisor']);self.assertIsNone(v.metrics['tokens'])

    def test_planning_duration_only_uses_recorded_start_and_completion(self):
        events=[{'event_type':'PLANNING_STARTED','timestamp':10.},
                {'event_type':'PLAN_CREATED','timestamp':11.5}]
        node=self.project(events=events).nodes[0]
        self.assertEqual(node.duration_seconds,1.5)
        self.assertEqual(node.planning_method,'LOCAL_REGISTERED_ROUTING')
        self.assertIsNone(self.project().nodes[0].duration_seconds)

    def test_event_error_codes_reject_raw_exception_text(self):
        self.save()
        with self.store.connect() as db:
            with self.assertRaises(ValidationError):
                append(db,self.scope,'AGENT_FAILED',agent='ba',status='FAILED',error_code='raw password=do-not-store')


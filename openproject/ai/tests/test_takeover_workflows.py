"""Static regression for n8n authentication wiring; not a live n8n acceptance test."""
import unittest

from automation.deploy_real_n8n_workflows import build_workflows, secure_workflows, GATEWAY_URL, GATEWAY_CRED_ID


class WorkflowBoundaryTests(unittest.TestCase):
    def test_gateway_calls_forward_only_the_authenticated_request_header(self):
        workflows = build_workflows()
        self.assertEqual(len(workflows), 16)
        for code, workflow in workflows.items():
            self.assertEqual(workflow["settings"]["saveDataErrorExecution"], "none")
            self.assertEqual(workflow["settings"]["saveDataSuccessExecution"], "none")
            self.assertFalse(workflow["settings"]["saveManualExecutions"])
            for node in workflow["nodes"]:
                self.assertNotIn(GATEWAY_CRED_ID, str(node.get("credentials", {})), code)
                if node["type"] != "n8n-nodes-base.httpRequest" or GATEWAY_URL not in node["parameters"].get("url", ""):
                    continue
                parameters = node["parameters"]
                if code == 'WF04' and node['id'] == 'lifecycle-observe':
                    # Signed lifecycle has its own no-caller-authority contract tests.
                    self.assertNotIn('Authorization', str(parameters))
                    self.assertFalse(node.get('retryOnFail', False))
                    continue
                if code in {'WF07','WF16'} or code=='WF12' and node['id']=='weekly_report':
                    self.assertEqual(parameters['url'],GATEWAY_URL+('/internal/automation/monitor' if code=='WF16' else '/internal/automation/commands'))
                    self.assertEqual(node['credentials']['httpHeaderAuth']['id'],'qldapmMachineStatus')
                    self.assertNotIn('authorization',str(parameters).lower())
                    self.assertFalse(node['retryOnFail'])
                    self.assertFalse(parameters['options']['redirect']['redirect']['followRedirects'])
                    continue
                self.assertNotIn("credentials", node)
                self.assertFalse(node["retryOnFail"])
                self.assertIn(".first().json.headers.authorization", parameters["headerParameters"]["parameters"][0]["value"])
                self.assertFalse(parameters["options"]["redirect"]["redirect"]["followRedirects"])

    def test_execution_uses_exact_proposal_decision_never_raw_mutation(self):
        workflow = build_workflows()["WF06"]
        calls = [n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.httpRequest"]
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0]["parameters"]["url"].endswith("/decision"))
        self.assertNotIn("auto_execute", str(workflow))
        self.assertNotIn("WF06 Verification", str(workflow))
        self.assertNotIn("REJECTED_BY_PM", str(build_workflows()["WF05"]))

    def test_interactive_approval_and_trace_preserve_gateway_http_status(self):
        workflows=build_workflows()
        for code in (f'WF{i:02}' for i in range(1,17) if i not in (7,16)):
            workflow=workflows[code]
            trigger=workflow['nodes'][0]
            self.assertEqual(trigger['parameters']['responseMode'],'responseNode')
            call=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
            response=call['parameters']['options']['response']['response']
            self.assertTrue(response['neverError'])
            self.assertTrue(response['fullResponse'])
            reply=next(n for n in workflow['nodes'] if n['id']=='reply_gateway_status')
            self.assertEqual(reply['type'],'n8n-nodes-base.respondToWebhook')
            self.assertEqual(reply['parameters']['options']['responseCode'],'={{ $json.statusCode }}')

    def test_reapplying_hardening_preserves_graph_and_has_no_dangling_nodes(self):
        import copy
        workflows=build_workflows()
        again=secure_workflows(copy.deepcopy(workflows))
        self.assertEqual(again,workflows)
        for code in (f'WF{i:02}' for i in range(1,17) if i not in (7,16)):
            workflow=workflows[code];names={n['name'] for n in workflow['nodes']}
            for source,connections in workflow['connections'].items():
                self.assertIn(source,names)
                for branch in connections['main']:
                    self.assertTrue(all(edge['node'] in names for edge in branch))

    def test_reconciliation_calls_exact_identity_audit_without_static_totals(self):
        import json
        workflow=build_workflows()['WF15']
        calls=[n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.httpRequest']
        self.assertEqual(len(calls),1)
        self.assertEqual(json.loads(calls[0]['parameters']['jsonBody']),{'action':'knowledge_integrity','arguments':{}})
        self.assertFalse(any(n['type']=='n8n-nodes-base.code' for n in workflow['nodes']))

    def test_weekly_summary_retains_weekly_purpose_and_caller_context(self):
        workflow=build_workflows()['WF12']
        self.assertEqual(workflow['name'],'WF12: Weekly Summary')
        self.assertEqual(workflow['nodes'][0]['parameters']['path'],'qldapm-weekly-summary')
        prepare=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.code')
        self.assertIn("action:'weekly_summary'",prepare['parameters']['jsCode'])
        self.assertNotIn('workload',str(workflow).lower())
        schedule=next(n for n in workflow['nodes'] if n['id']=='weekly_schedule')
        self.assertEqual(schedule['parameters']['rule']['interval'],[{'field':'cronExpression','expression':'0 0 17 * * 5'}])
        self.assertNotIn('disabled',schedule)
        self.assertIn("kind: 'weekly_summary'",next(n for n in workflow['nodes'] if n['id']=='weekly_metadata')['parameters']['jsonOutput'])
        self.assertIn("startOf('week')",str(workflow))

    def test_scheduled_weekly_rejects_transport_success_with_incomplete_business_result(self):
        import json,shutil,subprocess
        node=shutil.which('node')
        if node is None:self.skipTest('Node runtime unavailable')
        code=next(n for n in build_workflows()['WF12']['nodes'] if n['id']=='weekly_business_result')['parameters']['jsCode']
        for state,status,success in [('COMPLETED','READY',True),('COMPLETED','PARTIAL',False),('RUNNING','COLLECTING',False),('FAILED','INTERRUPTED_NO_REPLAY',False)]:
            script='const $json='+json.dumps({'result':{'state':state,'status':status}})+'; const $input={all:()=>[$json]}; new Function("$json","$input",'+json.dumps(code)+')($json,$input);'
            result=subprocess.run([node,'-e',script],capture_output=True)
            self.assertEqual(result.returncode==0,success,(state,status))

    def test_sprint_risk_uses_persisted_native_analysis_and_no_default_work_package(self):
        workflow=build_workflows()['WF08']
        self.assertEqual(workflow['name'],'WF08: Sprint Risk')
        self.assertEqual(workflow['nodes'][0]['parameters']['path'],'qldapm-sprint-risk')
        self.assertIn("action:'sprint_risks'",str(workflow))
        self.assertNotIn('work_package_id',str(workflow))

    def test_qa_gate_reads_real_evidence_without_asserting_approval(self):
        workflow = build_workflows()['WF11']
        self.assertEqual(len(workflow['nodes']), 4)
        self.assertIn("action:'qa_evidence_list'", str(workflow))
        self.assertNotIn('acceptance_criteria_verified', str(workflow))
        self.assertNotIn('transition_permitted', str(workflow))
        self.assertNotIn("|| 38", str(workflow))
        self.assertNotIn('auto_execute', str(workflow))

    def test_legacy_adapters_return_actual_results_without_default_targets(self):
        for code in ('WF01','WF02','WF09','WF10','WF13'):
            workflow = build_workflows()[code]
            self.assertEqual(len(workflow['nodes']), 4)
            self.assertNotIn('Date.now()', str(workflow))
            self.assertNotIn('|| 38', str(workflow))
            self.assertNotIn('COMPLETED', str(workflow))
            self.assertEqual(workflow['nodes'][-1]['parameters']['responseBody'], '={{ $json.body }}')

    def test_orchestrator_preserves_request_identity_and_polls_stored_runs(self):
        workflow=build_workflows()['WF03']
        self.assertEqual(workflow['nodes'][0]['parameters']['responseMode'],'responseNode')
        call=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
        self.assertTrue(call['parameters']['url'].endswith('/api/v1/commands'))
        code=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.code')['parameters']['jsCode']
        self.assertIn('request_id',code)
        self.assertIn("action:'get_ai_run'",code)
        self.assertNotIn('Date.now()',code)
        self.assertNotIn("engine:'supervisor'",code)

    def test_recovery_routes_only_durable_rag_job_operations(self):
        workflow=build_workflows()['WF14']
        self.assertEqual(workflow['nodes'][0]['parameters']['responseMode'],'responseNode')
        self.assertIn('knowledge_sync_status',str(workflow))
        self.assertIn('knowledge_sync_retry',str(workflow))
        self.assertNotIn('SCHEDULE_RETRY',str(workflow))
        self.assertNotIn('audit_logged',str(workflow))

    def test_daily_schedule_uses_fixed_signed_machine_operation_without_caller_inputs(self):
        workflow=build_workflows()['WF07']
        schedule=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.scheduleTrigger')
        self.assertFalse(schedule.get('disabled',False))
        self.assertEqual(schedule['parameters']['rule']['interval'][0]['expression'],'0 0 8 * * *')
        self.assertEqual(workflow['settings']['timezone'],'Asia/Bangkok')
        metadata=next(n for n in workflow['nodes'] if n['id']=='metadata')['parameters']['jsonOutput']
        self.assertIn("kind: 'daily_brief'",metadata)
        self.assertIn("request_key: 'daily:'",metadata)
        self.assertNotIn('body',metadata)
        signer=next(n for n in workflow['nodes'] if n['id']=='signature')
        self.assertEqual(signer['credentials']['crypto']['id'],'qldapmCommandHmac')
        self.assertNotIn('DAILY_BRIEF_GENERATED',str(workflow))
        names={n['name'] for n in workflow['nodes']}
        for source,connections in workflow['connections'].items():
            self.assertIn(source,names)
            for branch in connections['main']:
                self.assertTrue(all(edge['node'] in names for edge in branch))

    def test_monitor_schedule_uses_fixed_machine_probe_without_fabricated_kpis(self):
        workflow=build_workflows()['WF16']
        self.assertEqual(workflow['name'],'WF16: Main Health Monitoring')
        self.assertEqual(workflow['nodes'][0]['parameters']['path'],'qldapm-monitoring')
        schedule=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.scheduleTrigger')
        self.assertFalse(schedule.get('disabled',False))
        self.assertEqual(schedule['parameters']['rule']['interval'][0]['expression'],'0 */15 * * * *')
        self.assertNotIn('system_health',str(workflow))
        self.assertNotIn('ON_SCHEDULE',str(workflow))
        call=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
        self.assertEqual(call['parameters']['method'],'GET')
        self.assertNotIn('sendBody',call['parameters'])

    def test_javascript_formatters_propagate_denial_and_actual_proposal_lifecycle(self):
        import json,shutil,subprocess
        node=shutil.which('node')
        if not node:
            self.skipTest('Node.js required for formatter execution; static checks still run')
        script=r'''
const assert=require('node:assert/strict');
const workflows=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
for(const code of ['WF04','WF05']) {
  const source=workflows[code].nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
  const fn=new Function('$input','$',source);
  const run=(response,body={})=>fn({first:()=>({json:response})},()=>({first:()=>({json:{body}})}))[0].json;
  const denied=run({statusCode:403,body:{error:'PM_REQUIRED'}});
  assert.equal(denied.statusCode,403);assert.equal(denied.body.error,'PM_REQUIRED');
  if(code==='WF04') {
    const result=run({statusCode:200,body:{result:{items:[{event_id:'actual-fixture-event'}]}}});
    assert.equal(result.body.total_events,1);assert.equal(result.body.events[0].event_id,'actual-fixture-event');
  } else {
    const result=run({statusCode:200,body:{result:{id:'fixture',hash:'a'.repeat(64),state:'done',lifecycle:'NATIVE_CONFIRMED_RAG_PENDING'}}});
    assert.equal(result.body.status,'NATIVE_CONFIRMED_RAG_PENDING');assert.equal(result.body.human_confirmation_required,false);
    assert.equal(run({statusCode:200,body:{result:{}}},{decision:'approve'}).statusCode,400);
  }
}
const weeklyCode=workflows.WF12.nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
const weekly=new Function('$input',weeklyCode)({first:()=>({json:{body:{as_of_date:'2026-10-23',actor_id:19,role:'PM',with_ai_summary:true}}})})[0].json;
assert.deepEqual(weekly,{action:'weekly_summary',arguments:{as_of_date:'2026-10-23'}});
const riskCode=workflows.WF08.nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
const risk=new Function('$input',riskCode)({first:()=>({json:{body:{actor_id:19,role:'PM',as_of_date:'2026-10-23',auto_execute:true}}})})[0].json;
assert.deepEqual(risk,{action:'sprint_risks',arguments:{as_of_date:'2026-10-23'}});
const selectedRisk=new Function('$input',riskCode)({first:()=>({json:{body:{sprint_id:11,actor_id:18,role:'AI_SYSTEM_OWNER',approved:true}}})})[0].json;
assert.deepEqual(selectedRisk,{action:'sprint_risks',arguments:{sprint_id:11}});
const source=workflows.WF03.nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
const orchestrate=body=>new Function('$input',source)({first:()=>({json:{body}})})[0].json;
const request='aabbccdd-1111-2222-3333-eeeeffff0000';
for (const code of ['WF01','WF02','WF13']) {
  const source=workflows[code].nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
  const run=body=>new Function('$input',source)({first:()=>({json:{body}})})[0].json;
  assert.deepEqual(run({id:370,request_id:request,actor_id:1,role:'PM',approved:true}),
    {action:'knowledge_ingest',arguments:{id:370},idempotency_key:code.toLowerCase()+'-'+request});
  for(const body of [{},{id:true},{id:370},{id:370,request_id:request,path:'secret.env'},
      {id:370,request_id:request,operation:'delete'}]) assert.notEqual(run(body).action,'knowledge_ingest');
  if (code==='WF01') {
    assert.deepEqual(run({source_key:'workflow-contract',request_id:request,actor_id:18,role:'AI_SYSTEM_OWNER'}),
      {action:'knowledge_file_ingest',arguments:{source_key:'workflow-contract'},idempotency_key:'wf01-file-'+request});
    assert.deepEqual(run({source_key:'workflow-contract',operation:'search',query:'workflow',limit:4}),
      {action:'knowledge_file_search',arguments:{source_key:'workflow-contract',query:'workflow',limit:4}});
    assert.equal(run({source_key:'workflow-contract',operation:'read',document_id:'a'.repeat(64)}).action,'knowledge_file_read');
    for(const extra of [{path:'secret.env'},{file_path:'secret.env'},{content:'unverified'},{id:370},{operation:'delete'}])
      assert.ok(run({source_key:'workflow-contract',request_id:request,...extra}).action.startsWith('INVALID_'));
  }
  if (code==='WF02') {
    assert.deepEqual(run({operation:'sync',request_id:request,actor_id:18,role:'AI_SYSTEM_OWNER'}),
      {action:'knowledge_incremental_sync',arguments:{},idempotency_key:'wf02-sync-'+request});
    assert.deepEqual(run({operation:'status',actor_id:19}),{action:'knowledge_incremental_status',arguments:{}});
    assert.ok(run({operation:'sync',request_id:request,file_path:'secret.env'}).action.startsWith('INVALID_'));
  }
  if (code==='WF13') {
    assert.deepEqual(run({operation:'feedback_submit',native_id:370,note:'citation review',request_id:request,actor_id:18,approved:true}),
      {action:'knowledge_feedback_submit',arguments:{native_id:370,note:'citation review'},idempotency_key:'wf13-feedback-'+request});
    const decision=run({operation:'feedback_decision',feedback_id:request,decision:'accept',hash:'a'.repeat(64),role:'PM'});
    assert.deepEqual(decision,{feedback_decision:true,feedback_id:request,payload:{decision:'accept',hash:'a'.repeat(64)}});
    assert.ok(run({operation:'feedback_decision',feedback_id:'http://forbidden.example/decision'}).action.startsWith('INVALID_'));
    assert.ok(run({operation:'feedback_submit',source_key:'workflow-contract',note:'note',request_id:request,file_path:'secret.env'}).action.startsWith('INVALID_'));
  }
}
const optionsSource=workflows.WF10.nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
assert.deepEqual(new Function('$input',optionsSource)({first:()=>({json:{body:{approved:true,operation:'create'}}})})[0].json,
  {action:'get_project_options',arguments:{}});
const qaSource=workflows.WF11.nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
const qa=body=>new Function('$input',qaSource)({first:()=>({json:{body}})})[0].json;
assert.deepEqual(qa({id:370,actor_id:19,role:'PM',approved:true,target_status:'Tested'}),{action:'qa_evidence_list',arguments:{native_id:370}});
for(const id of [undefined,null,true,0,-1,1.5,'370',Number.MAX_SAFE_INTEGER+1]) assert.equal(qa({id}).action,'INVALID_QA_TARGET');
const start=orchestrate({request_id:request,prompt:'fixture',role:'PM',actor_id:19,engine:'supervisor',allow_routine_writes:true});
assert.deepEqual(start,{action:'start_ai_run',arguments:{prompt:'fixture',engine:'gemini',run_class:'agent',allow_routine_writes:false},idempotency_key:'wf03-'+request});
assert.deepEqual(orchestrate({operation:'plan',request_id:request,prompt:'proposal',engine:'gemini',allow_routine_writes:true}).arguments,
  {prompt:'proposal',engine:'supervisor_gemini',run_class:'agent',allow_routine_writes:false});
assert.deepEqual(orchestrate({request_id:request.toUpperCase(),prompt:'fixture'}),start);
assert.equal(orchestrate({request_id:[request],prompt:'fixture'}).idempotency_key,'');
assert.equal(orchestrate({prompt:'fixture'}).idempotency_key,'');
assert.equal(orchestrate({operation:'unexpected'}).action,'INVALID_ORCHESTRATION_OPERATION');
assert.deepEqual(orchestrate({operation:'status',run_id:request}),{action:'get_ai_run',arguments:{id:request}});
const recoverCode=workflows.WF14.nodes.find(n=>n.type==='n8n-nodes-base.code').parameters.jsCode;
const recover=body=>new Function('$input',recoverCode)({first:()=>({json:{body}})})[0].json;
assert.deepEqual(recover({job_id:request,actor_id:19,role:'PM'}),{action:'knowledge_sync_status',arguments:{id:request}});
assert.deepEqual(recover({operation:'retry',job_id:request,request_id:request}),{action:'knowledge_sync_retry',arguments:{id:request},idempotency_key:'wf14-'+request});
assert.equal(recover({operation:'retry',job_id:request}).idempotency_key,'');
assert.equal(recover({retry_count:99,audit_logged:true}).action,'INVALID_RECOVERY_JOB_ID');
assert.equal(recover({operation:'native_retry',job_id:request}).action,'INVALID_RECOVERY_OPERATION');
'''
        result=subprocess.run([node,'-e',script],input=json.dumps(build_workflows()),text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == "__main__":
    unittest.main()

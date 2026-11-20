"""Changed Project6 routes only, executed inside qualify_business's disposable services."""


def final_paths_case():
    fixture=py("n6=Native('http://web:8080',keys['20'],6);item=n6.call('/api/v3/work_packages','POST',{'subject':'[Bug] Final scope fixture '+str(uuid.uuid4()),c['source_field']:'FINAL-P6-'+str(uuid.uuid4()),'description':{'raw':'Fixture reproduction and expected behavior, not verified QA.'},'_links':{'project':{'href':'/api/v3/projects/6'},'type':{'href':'/api/v3/types/1'}}});print(json.dumps({'id':item['id'],'version':item['lockVersion']}))")
    risk=ok(request('WF08',{'project_id':6,'as_of_date':datetime.date.today().isoformat()},actor='20'))
    assert risk['project_id']==6 and risk['report_id']
    report=py("from gateway.service import Service;s=Service(Store(root),c,'/tmp/final-workspaces');r=s.execute_actor(20,{\"action\":\"get_report\",\"arguments\":{\"id\":"+repr(risk['report_id'])+"},\"project_id\":6});print(json.dumps(r['result']))")
    assert report['sha256']==risk['report_sha256']
    bug=ok(request('WF09',{'operation':'triage','id':fixture['id'],'project_id':6},actor='20'))
    assert bug['project_id']==6 and bug['native_id']==fixture['id'] and bug['native_mutations'] is False
    request_id=str(uuid.uuid4());payload={'operation':'draft','project_id':6,'request_id':request_id,
        'requirements':[{'id':'R1','text':'Isolated Project6 scope and exact WBS read-back'}],
        'nodes':[{'key':'epic','kind':'Epic','subject':'P6 acceptance epic','requirement_ids':['R1']},
                 {'key':'task','kind':'Task','parent':'epic','subject':'P6 acceptance task','requirement_ids':['R1']}]}
    draft=ok(request('WF10',payload,actor='20'))
    assert ok(request('WF10',payload,actor='20'))==draft
    readback=ok(request('WF10',{'operation':'get','id':draft['id'],'project_id':6},actor='20'))
    assert readback['hash']==draft['hash'] and readback['project_id']==6
    file_payload={'project_id':6,'source_key':'clone-local-p6','request_id':str(uuid.uuid4()),'operation':'ingest'}
    ingest=ok(request('WF01',file_payload,actor='20'))
    assert ingest['vector_indexed'] is True
    # Source-bound callbacks run actual n8n graphs and re-read the earlier successful command.
    deliveries=py("from gateway.service import Service\nfrom gateway.integration_events import deliver_pending\ns=Service(Store(root),c,'/tmp/final-workspaces');states=[]\nfor _ in range(12):\n state=deliver_pending(s);states.append(state)\n if state=='IDLE':break\n time.sleep(5)\nwith s.store.connect() as d:\n rows=[dict(r) for r in d.execute('SELECT o.workflow,o.state,r.execution_id,r.document FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id ORDER BY o.rowid')]\nprint(json.dumps({'states':states,'receipts':[{'workflow':r['workflow'],'state':r['state'],'execution_id':r['execution_id'],'business':json.loads(r['document'])['business_result'] if r['document'] else None} for r in rows]}))")
    assert {r['workflow'] for r in deliveries['receipts'] if r['state']=='ACKED' and r['business']['state']=='COMMAND_RESULT_VERIFIED'}>={'WF01','WF08','WF09','WF10'}
    denied=request('WF09',{'operation':'triage','id':fixture['id'],'project_id':6},actor='19')
    assert denied['status']==403
    before=py("n6=Native('http://web:8080',keys['20'],6);print(json.dumps({'count':len(n6.packages())}))")
    blocked=request('WF10',{'operation':'next','project_id':6,'id':draft['id'],'hash':draft['hash'],'request_id':str(uuid.uuid4())},actor='20')
    assert blocked['status']!=200
    after=py("n6=Native('http://web:8080',keys['20'],6);print(json.dumps({'count':len(n6.packages())}))")
    assert before==after
    return {'risk_report_id':risk['report_id'],'risk_report_sha256':risk['report_sha256'],'bug_native_id':fixture['id'],
        'wbs_draft_id':draft['id'],'wbs_hash':draft['hash'],'wbs_replay_identical':True,'file_document_id':ingest['document_id'],
        'receipts':deliveries['receipts'],'actor19_denied':True,'materialization_denied_without_native_write':True,
        'provider_calls':0}


def planning_observation_case():
    # Read an actual historical MAIN admission/plan; reproduce only its observation in the Native clone.
    reader="import json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row;r=d.execute(\"SELECT q.id,q.actor,q.payload,q.state,q.created,p.document FROM ai_queue q JOIN engineering_plans p ON p.id=q.id AND p.actor=q.actor WHERE q.actor=20 AND json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.kind')='planning' AND json_extract(p.document,'$.state')='PUBLISHED' ORDER BY q.created DESC LIMIT 1\").fetchone();assert r;print(json.dumps(dict(r)))"
    source=json.loads(run('exec','qldapm-ai-gateway-1','python','-c',reader))
    payload=json.dumps(source)
    loaded=py("from gateway.engineering_lifecycle import setup\nfrom gateway.integration_events import publish\ns=Store(root);setup(s);row=json.loads("+repr(payload)+")\nwith s.connect() as d:\n d.execute('INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,?,?,?)',(row['id'],row['actor'],row['payload'],row['state'],row['created'],'agent'))\n d.execute('INSERT INTO engineering_plans VALUES(?,?,?)',(row['id'],row['actor'],row['document']))\npublish(s)\nprint(json.dumps({'run_id':row['id']}))")
    delivered=py("from gateway.service import Service\nfrom gateway.integration_events import deliver_pending\ns=Service(Store(root),c,'/tmp/final-workspaces')\nfor _ in range(8):\n state=deliver_pending(s)\n if state=='IDLE':break\n time.sleep(5)\nwith s.store.connect() as d:rows=[dict(r) for r in d.execute(\"SELECT o.workflow,o.state,r.execution_id,r.document FROM integration_event_outbox o JOIN integration_event_receipts r ON r.id=o.id WHERE json_extract(o.document,'$.kind') IN ('PLANNING_ACCEPTED','PLANNING_PUBLISHED')\")]\nprint(json.dumps({'receipts':[{'workflow':r['workflow'],'state':r['state'],'execution_id':r['execution_id'],'business':json.loads(r['document'])['business_result']} for r in rows]}))")
    assert len(delivered['receipts'])==2 and all(r['state']=='ACKED' for r in delivered['receipts'])
    assert {r['business']['state'] for r in delivered['receipts']}=={'PLANNING_ACCEPTED','PLAN_NATIVE_UNITS_VERIFIED'}
    return {'source':'actual historical MAIN admission/PUBLISHED plan observed against restored Native clone; not fresh provider generation',
        'run_id':loaded['run_id'],'receipts':delivered['receipts'],'new_agent_runs_started':0,'native_writes':0}


record('FINAL_P6_BUSINESS','Actual P6 risk/report, Bug triage, immutable WBS and file → real n8n observer receipts',final_paths_case)
record('FINAL_PLANNING_OBSERVERS','Real stored PM/BA planning/source/Native unit read-back through WF03/WF10 observers',planning_observation_case)

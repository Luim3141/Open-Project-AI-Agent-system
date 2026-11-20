"""Bounded allowlist projection from persisted execution events and receipts only."""
import json
import re


def code(value):
    return value if isinstance(value, str) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}', value) else None


def identifier(value):
    return value if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.:/-]{1,200}', value) else None


def sha(value, length=64):
    return value if isinstance(value,str) and re.fullmatch('[a-f0-9]{'+str(length)+'}',value) else None


def snapshot(store, runs):
    with store.connect() as db:
        rows = db.execute("SELECT e.sequence,e.document FROM execution_events e JOIN ai_queue q ON q.id=e.run_id "
                          "AND q.actor=e.actor WHERE e.project=6 AND json_extract(q.payload,'$.project_id')=6 "
                          "AND json_extract(q.payload,'$.engine')='openclaw' ORDER BY e.sequence DESC LIMIT 100").fetchall()
        events = []
        for row in reversed(rows):
            document = json.loads(row['document'])
            event = {key: identifier(document.get(key)) for key in
                     ['event_id','run_id','trace_id','event_type','agent_id','status','receipt_id','error_code']}
            event.update(sequence=row['sequence'], timestamp=document.get('timestamp'))
            events.append(event)
        observed = []
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for run in runs:
            result = run.get('result') or {}
            checkpoint = run.get('checkpoint') or {}
            own = [event for event in events if event['run_id']==run['id']]
            last = own[-1] if own else None
            receipts = []
            for row in db.execute('SELECT id,document FROM gemini_call_receipts WHERE run_id=? ORDER BY rowid DESC LIMIT 20', (run['id'],)):
                document = json.loads(row['document'])
                receipts.append({'id': identifier(row['id']), **{key: identifier(document.get(key)) for key in
                    ['agent','provider','model','state']}, 'at': document.get('at'),
                    'http_status': document.get('http_status'), 'error_code': code(document.get('error'))})
            pipeline = []
            # Completion events prove a step ended, never that Reviewer/QA passed.
            for agent in ['pm','ba','dev','reviewer','qa']:
                evidence = next((event for event in reversed(own) if event['agent_id']==agent and
                    event['event_type'] in {'AGENT_STARTED','AGENT_COMPLETED','AGENT_FAILED','REVIEW_STARTED','REVIEW_COMPLETED'}), None)
                state = ('RUNNING' if evidence['event_type'] in {'AGENT_STARTED','REVIEW_STARTED'} else
                         'FAIL' if evidence['event_type']=='AGENT_FAILED' else 'UNKNOWN') if evidence else 'NOT_STARTED'
                if run['queue_state']=='finished' and state=='RUNNING':
                    state='UNKNOWN'
                pipeline.append({'agent': agent, 'status': state, 'evidence_id': evidence['event_id'] if evidence else None})
            n8n = []
            if 'n8n_lifecycle_outbox' in tables:
                for row in db.execute("SELECT event_id,state,attempts FROM n8n_lifecycle_outbox WHERE json_extract(document,'$.run_id')=? ORDER BY rowid DESC LIMIT 20", (run['id'],)):
                    item = dict(row)
                    execution = db.execute('SELECT execution_id FROM n8n_lifecycle_execution_metadata WHERE event_id=?', (row['event_id'],)).fetchone() if 'n8n_lifecycle_execution_metadata' in tables else None
                    item['execution_id'] = identifier(execution[0]) if execution else None
                    n8n.append(item)
            review=result.get('review_evidence') if isinstance(result.get('review_evidence'),dict) else {}
            test=result.get('test_evidence') if isinstance(result.get('test_evidence'),dict) else {}
            qa=review.get('qa') if isinstance(review.get('qa'),dict) else {}
            revision=sha(review.get('revision'))
            current_revision=sha(checkpoint.get('revision'))
            matching=bool(revision and (not current_revision or revision==current_revision))
            head=sha(result.get('head_sha'),40)
            test_log=sha(test.get('log_sha256'))
            verified=result.get('status')=='succeeded'
            states={}
            if verified and matching and head and test.get('exit_code')==0 and test_log:
                states['dev']=('PASS',head)
            if verified and matching and review.get('verdict')=='PASS' and review.get('findings')==[]:
                states['reviewer']=('PASS',revision)
            if verified and matching and qa.get('status')=='PASS' and qa.get('exit_code')==0 and test_log:
                states['qa']=('PASS',test_log)
            queue=db.execute('SELECT payload FROM ai_queue WHERE id=?',(run['id'],)).fetchone()
            payload=json.loads(queue[0]) if queue else {}
            plan_id=result.get('plan_id') or (payload.get('definition') or {}).get('plan_id') or (run['id'] if payload.get('kind')=='planning' else None)
            plan_row=db.execute('SELECT document FROM engineering_plans WHERE id=?',(plan_id,)).fetchone() if plan_id else None
            plan=json.loads(plan_row[0]) if plan_row else {}
            if plan.get('state')=='PUBLISHED' and plan.get('project_id')==6:
                for role in ['pm','ba']:
                    if isinstance(plan.get(role),dict) and plan[role]:
                        states[role]=('PASS',identifier(plan_id))
            for step in pipeline:
                if step['agent'] in states:
                    step.update(status=states[step['agent']][0],evidence_id=states[step['agent']][1])
            pr=result.get('pr_url')
            pr=pr if isinstance(pr,str) and re.fullmatch(r'https://github\.com/Luim3141/mini-task-manager/pull/[1-9][0-9]*',pr) else None
            native=result.get('native_readback') if isinstance(result.get('native_readback'),dict) else {}
            knowledge=result.get('knowledge_readback') if isinstance(result.get('knowledge_readback'),dict) else {}
            child=native.get('child_id')
            native_ok=verified and native.get('project_id')==6 and type(child) is int and child>0 and type(native.get('child_version')) is int
            rag_ok=(verified and knowledge.get('project_id')==6 and knowledge.get('child_id')==child and
                type(knowledge.get('retrieval_count')) is int and knowledge['retrieval_count']>0 and
                any(isinstance(ref,dict) and ref.get('native_id')==child and ref.get('citation')==f'/work_packages/{child}'
                    for ref in knowledge.get('references',[])))
            ack=next((item for item in n8n if item['state']=='ACKED'),None)
            pipeline.extend([
                {'agent':'github','status':'PASS' if verified and pr and head else 'UNKNOWN','evidence_id':pr},
                {'agent':'native','status':'PASS' if native_ok else 'UNKNOWN','evidence_id':f'wp:{child}:v{native.get("child_version")}' if native_ok else None},
                {'agent':'n8n','status':'PASS' if ack else 'BLOCKED' if any(item['state']=='DEAD' for item in n8n) else 'QUEUED' if n8n else 'NOT_STARTED','evidence_id':ack['event_id'] if ack else None},
                {'agent':'rag','status':'PASS' if rag_ok else 'UNKNOWN','evidence_id':f'/work_packages/{child}' if rag_ok else None},
                {'agent':'reports','status':'UNKNOWN','evidence_id':None}])
            projected = {key: checkpoint.get(key) for key in ['version','terminal_known','resumable']}
            projected.update(stage=code(checkpoint.get('stage')),revision=identifier(checkpoint.get('revision')),
                             completed_steps=[identifier(step) for step in checkpoint.get('completed_steps', [])[:20]])
            observed.append({'id': run['id'], 'native_id': run['native_id'], 'unit': run['unit'],
                'queue_state': run['queue_state'], 'status': identifier(result.get('status')),
                'stage': code(result.get('stage')) or projected['stage'],
                'agent': identifier(result.get('agent')) or (last or {}).get('agent_id'),
                'created_at': run['created_at'], 'updated_at': (last or {}).get('timestamp', run['created_at']),
                'last_event': last, 'checkpoint': projected, 'receipts': receipts, 'pipeline': pipeline, 'n8n': n8n,
                'plan_id':identifier(plan_id),
                'review':{'kind':'INTERNAL','verdict':review.get('verdict') if review.get('verdict') in {'PASS','FAIL'} else 'UNKNOWN','revision':revision,'matches_checkpoint':matching},
                'qa':{'kind':'INTERNAL','verdict':qa.get('status') if qa.get('status') in {'PASS','FAIL'} else 'UNKNOWN','exit_code':qa.get('exit_code') if type(qa.get('exit_code')) is int else None},
                'artifacts':{'commit':head,'diff_sha256':revision,'test_log_sha256':test_log,'worktree_ref':run['id']},
                'blocked_reason': code(result.get('error')),
                'head_sha':head,'pr_url':pr})
    return {'cursor': events[-1]['sequence'] if events else 0, 'events': events, 'runs': observed,
            'limit': 100, 'source': 'PERSISTED_GATEWAY_EVENTS_AND_RECEIPTS'}

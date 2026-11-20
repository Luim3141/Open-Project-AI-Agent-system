"""Actual GitHub -> isolated Native journal/outbox -> published n8n WF04.

Executed only by the disposable n8n clone harness with its `py` callable. The
clone must have actor-18 Native credentials, an existing read-only GitHub token,
network access to GitHub and an active WF04 integration adapter. No MAIN writes.
"""

def github_chain():
    code=r'''
from unittest.mock import patch
from gateway.service import Service
from gateway.engineering import scoped_service,authorized
from gateway import engineering_github_sync as gh,integration_events as ie

assert c.get('n8n_integration',{}).get('enabled') is True
assert c.get('engineering',{}).get('github_token') or c.get('github_token')
c.setdefault('engineering',{})['github_sync']={'enabled':True,'actor':18,'interval_seconds':300}
s=Service(Store(root),c,'/tmp/github-clone-workspace');sc=scoped_service(s,6);native,_=authorized(sc,18)
actual_fetch=gh.fetch_pull_requests
prs=actual_fetch('Luim3141/mini-task-manager',force=True,include_details=True)
selected=[p for p in prs if p.get('number')==6]
assert len(selected)==1 and not selected[0].get('details_error')
wp=gh.get_pr_wp_map(sc)[6];assert wp==386
package=native.package(wp)
assert package['_links']['project']['href']=='/api/v3/projects/6'
assert package['_links']['parent']['href']=='/api/v3/work_packages/379'
with patch.object(gh,'fetch_pull_requests',return_value=selected):
    first=gh.reconcile_github_with_openproject(sc,native,actor=18,request_id='clone-github-first')
    assert first['status']=='SUCCESS' and first['items'][0]['status'] in {'UPDATED','RECONCILED','UNCHANGED'}
    with sc.store.connect() as db:
        rows=db.execute("SELECT id,document FROM integration_event_outbox WHERE json_extract(document,'$.kind')='GITHUB_PR_CHANGED' AND json_extract(document,'$.payload.pr_number')=6").fetchall()
        assert len(rows)==1
        event_id=rows[0]['id'];event=json.loads(rows[0]['document'])
        journal=db.execute('SELECT operation_key,state FROM engineering_github_sync_journal WHERE wp_id=?',(wp,)).fetchall()
        done=[r['operation_key'] for r in journal if r['state']=='DONE']
        assert done
    activities=native.collection(f'/api/v3/work_packages/{wp}/activities')
    markers=[r['id'] for r in activities if any('[qldapm-github-sync:'+key+']' in str((r.get('comment') or {}).get('raw','')) for key in done)]
    assert markers
    second=gh.reconcile_github_with_openproject(sc,native,actor=18,request_id='clone-github-repeat')
    assert second['status']=='SUCCESS' and second['items'][0]['changed'] is False
    activities2=native.collection(f'/api/v3/work_packages/{wp}/activities')
    assert len(activities2)==len(activities)
    with sc.store.connect() as db:
        assert db.execute("SELECT count(*) FROM integration_event_outbox WHERE json_extract(document,'$.kind')='GITHUB_PR_CHANGED' AND json_extract(document,'$.payload.pr_number')=6").fetchone()[0]==1
        delayed=[(r['id'],r['next_at']) for r in db.execute("SELECT id,next_at FROM integration_event_outbox WHERE id!=? AND state IN ('PENDING','RETRY','SENDING')",(event_id,))]
        db.executemany('UPDATE integration_event_outbox SET next_at=? WHERE id=?',[(time.time()+3600,i) for i,_ in delayed])
    try: delivery=ie.deliver_pending(sc)
    finally:
        with sc.store.connect() as db:db.executemany('UPDATE integration_event_outbox SET next_at=? WHERE id=?',[(at,i) for i,at in delayed])
    assert delivery=='ACKED'
    with sc.store.connect() as db:
        receipt=db.execute('SELECT document,execution_id FROM integration_event_receipts WHERE id=?',(event_id,)).fetchone()
        outbox=db.execute('SELECT state,attempts FROM integration_event_outbox WHERE id=?',(event_id,)).fetchone()
    ack=json.loads(receipt['document'])
    assert outbox['state']=='ACKED' and ack['business_result']['state']=='DELIVERY_OBSERVED'
    assert ack['workflow']=='WF04' and ack['event_id']==event_id and ack['correlation_id']==event['correlation_id']
    assert str(receipt['execution_id']).isdigit()
    from gateway.engineering_github_poll import tick
    with patch.object(gh,'fetch_pull_requests',new=actual_fetch):
        poll=tick(s);repeat_poll=tick(s)
    assert poll['scheduled'] is True and poll['status']=='SUCCESS'
    assert repeat_poll=={'scheduled':False,'reason':'NOT_DUE'}
    sync_meta=gh.get_sync_meta(sc)
    assert sync_meta['status']=='SUCCESS' and sync_meta['last_synced_at']>0
    with sc.store.connect() as db:
        lease=db.execute('SELECT lease,lease_until,error FROM engineering_github_poll WHERE project=6').fetchone()
    assert lease and lease['lease'] is None and lease['lease_until']==0 and lease['error'] is None
    print(json.dumps({'pr_number':6,'head_sha':selected[0]['head_sha'],'github_state':selected[0]['state'],
      'reviews_state':selected[0]['reviews_state'],'checks_state':selected[0]['checks_state'],
      'native_wp':wp,'first_sync':first['items'][0]['status'],'repeat_sync':second['items'][0]['status'],
      'native_marker_ids':markers,'journal_done':len(done),'event_id':event_id,'correlation_id':event['correlation_id'],
      'outbox_state':outbox['state'],'n8n_execution_id':receipt['execution_id'],'business_state':ack['business_result']['state'],
      'automatic_poll':poll['status'],'poll_checked_prs':sync_meta['total_checked'],'poll_changed':sync_meta['total_changed'],
      'repeat_poll':repeat_poll['reason'],'poll_lease_cleared':True,
      'fixture_note':'Other clone-only pending rows were temporarily delayed and restored to select this event.'}))
'''
    return py(code)


record('GITHUB_PRODUCER','Read-only real GitHub PR6 -> isolated Native journal -> durable outbox -> published n8n WF04 receipt; replay idempotent',github_chain)

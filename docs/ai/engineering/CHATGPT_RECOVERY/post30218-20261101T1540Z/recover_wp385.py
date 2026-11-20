"""Audited Native replacement; safe receipts prevent replay of unknown outcomes."""
import json
from pathlib import Path
from gateway import engineering
from gateway.engineering_operator import native_once
from gateway.native import NativeError
from gateway.service import Service
from gateway.store import Store

root=Path('/state'); store=Store(root)
service=engineering.scoped_service(Service(store,json.loads((root/'config.json').read_text()),'/workspaces'),6)
native,who=engineering.authorized(service,20)
assert who['user_id']==20
marker='[Recovery WP385] Category, filter and CSV export (AC10–AC12)'
run='ea554d7a-8f45-46a0-8c1a-d18aa3000385'
with store.connect() as db:
    unsafe=db.execute("SELECT state FROM requests WHERE actor=20 AND key LIKE ? AND state NOT IN ('done','rejected')",('engineering-'+run+'-%',)).fetchall()
assert not unsafe,'OUTCOME_UNKNOWN_RECONCILE_FIRST'
items=native.packages()
matches=[p for p in items if p.get('subject')==marker]
assert len(matches)<=1,'AMBIGUOUS_DUPLICATE'
try:
    native.package(385)
except NativeError as e:
    assert e.status==404,'ORIGINAL_UNCONFIRMED'
else:
    raise RuntimeError('ORIGINAL_385_PRESENT')
base=native.package(384); parent=native.package(379)
assert base['_links']['project']['href']=='/api/v3/projects/6' and parent['_links']['project']['href']=='/api/v3/projects/6'
payload={'subject':marker,'description':{'format':'markdown','raw':
    'Replacement for deleted WP385; NEW record, not restoration of Native history.\n'
    'Forensics: CHATGPT_RECOVERY/WP385_FORENSICS.md; old plan b1cca031-81f5-4df1-870b-cbeb23d51e66; unit feedback-b1c22888cba835bb.\n'
    'AC10: category on task POST/PATCH.\nAC11: GET /tasks?category=… filters tasks.\nAC12: GET /tasks/export/csv returns CSV.\n'
    'Dependency: health-check-v1 / WP384. Old mapping and historical result are preserved.'},
    '_links':{'project':{'href':'/api/v3/projects/6'},'parent':{'href':'/api/v3/work_packages/379'},
              'status':{'href':'/api/v3/statuses/1'},'type':{'href':base['_links']['type']['href']}}}
if matches:
    with store.connect() as db: receipt=db.execute('SELECT state FROM requests WHERE actor=20 AND key=?',('engineering-'+run+'-child',)).fetchone()
    assert receipt and receipt['state']=='done','EXISTING_REPLACEMENT_NEEDS_RECONCILIATION'
created=native_once(service,native,run,'child','/api/v3/work_packages','POST',payload)
identifier=created['id']; assert identifier!=385
child=native.package(identifier)
assert child['subject']==marker and child['_links']['parent']['href']=='/api/v3/work_packages/379'
relations=native.relations(native.packages())
related=[r for r in relations if {r.get('_links',{}).get(k,{}).get('href') for k in ('from','to')}=={f'/api/v3/work_packages/{identifier}','/api/v3/work_packages/384'}]
assert len(related)<=1,'AMBIGUOUS_DEPENDENCY'
if not related:
    result=native_once(service,native,run,'dependency',f'/api/v3/work_packages/{identifier}/relations','POST',{'type':'follows','_links':{'from':{'href':f'/api/v3/work_packages/{identifier}'},'to':{'href':'/api/v3/work_packages/384'}}})
    relation=native.call(result['_links']['self']['href'])
else: relation=related[0]
assert {relation['_links'][k]['href'] for k in ('from','to')}=={f'/api/v3/work_packages/{identifier}','/api/v3/work_packages/384'}
assert relation['type'] in ('follows','precedes')
print(json.dumps({'status':'REPLACEMENT_READ_BACK','original_385_absent':True,'new_id':identifier,'parent':379,'dependency':384,'relation_id':relation['id'],'project':6}))

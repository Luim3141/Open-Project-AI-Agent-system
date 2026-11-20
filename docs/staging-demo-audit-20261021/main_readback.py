"""Independent, read-only Main schedule verification while Staging stays frozen."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
from read_only_audit import command, OUT

def sql(query):
    statement="BEGIN READ ONLY; SELECT coalesce(json_agg(x),'[]'::json) FROM ("+query+") x; ROLLBACK;"
    return json.loads(command(['docker','exec','-i','qldapm-openproject-db-1','psql','-v','ON_ERROR_STOP=1','-U','postgres','-d','openproject','-Atq'],statement).strip())

proposal=Path('docs/ai-multi-agent-upgrade/run_20261021_final_delivery/FINAL_7_SPRINT_NATIVE_PROPOSAL_V2.csv')
rows=list(csv.DictReader(proposal.open(encoding='utf-8-sig',newline='')))
current=sql("SELECT w.id,w.start_date,w.due_date,w.parent_id,w.assigned_to_id,w.status_id,w.schedule_manually,w.ignore_non_working_days,s.name AS sprint,v.name AS version FROM work_packages w LEFT JOIN sprints s ON s.id=w.sprint_id LEFT JOIN versions v ON v.id=w.version_id WHERE w.project_id=5 ORDER BY w.id")
by_id={r['id']:r for r in current}
errors=[]
for row in rows:
    w=by_id.get(int(row['ID']))
    if not w:
        errors.append({'id':row['ID'],'field':'missing'});continue
    pairs={'start_date':row['Proposed Start Date'],'due_date':row['Proposed Due Date'],
           'assigned_to_id':int(row['Actor ID Preserved']), 'status_id':int(row['Status ID Preserved']),
           'schedule_manually':row['Schedule Manually Preserved'].lower()=='true',
           'ignore_non_working_days':row['Ignore Non Working Days Preserved'].lower()=='true'}
    for key,expected in pairs.items():
        if w[key]!=expected:errors.append({'id':w['id'],'field':key})
    for key,column in [('sprint','Proposed Native Sprint'),('version','Proposed Roadmap Version')]:
        expected=row[column]
        if expected=='PRESERVE_UNASSIGNED_ROLLUP':expected=None
        if w[key]!=expected:errors.append({'id':w['id'],'field':key,'expected':expected,'actual':w[key]})
rollup=[]
for parent in current:
    children=[w for w in current if w['parent_id']==parent['id']]
    if children and (parent['start_date']!=min(w['start_date'] for w in children) or parent['due_date']!=max(w['due_date'] for w in children)):
        rollup.append(parent['id'])
result={'timestamp':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(),
        'proposal_sha256':hashlib.sha256(proposal.read_bytes()).hexdigest(),'proposal_rows':len(rows),'native_rows':len(current),
        'field_mismatches':errors,'parent_rollup_mismatches':rollup,
        'sprints':sql('SELECT id,name,status,start_date,finish_date FROM sprints WHERE project_id=5 ORDER BY id'),
        'earliest_start':min(w['start_date'] for w in current),'latest_due':max(w['due_date'] for w in current),
        'all_boundaries_weekdays':all(datetime.date.fromisoformat(w[k]).weekday()<5 for w in current for k in ['start_date','due_date']),
        'main_business_writes_by_this_audit':0}
target=OUT/'main-schedule-readback.json';assert not target.exists()
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))

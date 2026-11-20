"""Validate saved UI evidence against read-only Native/state data after Owner completes MFA."""
import datetime
import json
import re
from read_only_audit import OUT, snapshot, postgres, gateway, command

texts={n:(OUT/(n+'-ui.txt')).read_text(encoding='utf-8') for n in ['assistant','second-brain','monitor','backlog','kanban','gantt']}
checks={
    'assistant_authenticated':'Gateway: ok' in texts['assistant'] and 'OpenProject: authenticated' in texts['assistant'],
    'control_center_own_history':'Run history của bạn (9)' in texts['assistant'],
    'second_brain_fresh_citation':'1 kết quả phù hợp và còn quyền đọc' in texts['second-brain'] and 'Nguồn #38' in texts['second-brain'] and 'lockVersion 1' in texts['second-brain'],
    'historical_live_monitor':'38fdb479-5566-4a18-b2da-6a9cf15aad3c' in texts['monitor'] and 'LIVE_GEMINI' in texts['monitor'] and 'Không gọi Gemini' in texts['monitor'],
    'seven_kanban_columns':all(s in texts['kanban'] for s in ['NEW','IN PROGRESS','CODE REVIEW','READY FOR TEST','IN TESTING','READY FOR RELEASE','DONE']),
    'backlog_and_five_sprints':all(s in texts['backlog'] for s in ['17','318','S1','S2','S3','S4','S5']),
    'gantt_wbs_undated':'ngày bắt đầu' in texts['gantt'].lower() and 'ngày kết thúc' in texts['gantt'].lower() and '-\t-\t-' in texts['gantt'],
}
assert all(checks.values()), checks
old=json.loads((OUT/'before.json').read_text(encoding='utf-8'))
pg=postgres('qldapm-ai-stage-db-1')
assert pg['business_fingerprints']==old['stage_postgres']['business_fingerprints']
gw=gateway('qldapm-ai-stage-staging-gateway-1')
kept=['ai_runs','agent_runs','agent_tasks','gemini_usage','gemini_call_receipts','execution_events','proposals','daily_briefs']
counts={n:gw['gateway.sqlite']['tables'][n]['count'] for n in kept}
assert all(counts[n]==old['stage_gateway']['gateway.sqlite']['tables'][n]['count'] for n in kept)
sql="BEGIN READ ONLY; SELECT coalesce(json_agg(x),'[]'::json) FROM (SELECT id,user_id,active FROM two_factor_authentication_devices WHERE user_id=7 ORDER BY id) x; ROLLBACK;"
devices=json.loads(command(['docker','exec','-i','qldapm-ai-stage-db-1','psql','-v','ON_ERROR_STOP=1','-U','postgres','-d','openproject','-Atq'],sql).strip())
assert any(d['active'] for d in devices)
current=snapshot()
old_stage={r['name']:(r['id'],r['image'],r['started']) for r in old['containers'] if r['name'].startswith('qldapm-ai-stage-')}
new_stage={r['name']:(r['id'],r['image'],r['started']) for r in current if r['name'].startswith('qldapm-ai-stage-')}
assert old_stage==new_stage and len(new_stage)==7
result={'timestamp':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(),
        'status':'READY_FOR_READ_ONLY_DEMO_WITH_LIMITS','checks':checks,'pm_totp_devices':devices,
        'kanban_card_ids':len(re.findall(r'^#(\d+)$',texts['kanban'],re.M)),
        'stage_counts':counts,'business_fingerprints_unchanged':True,'container_id_image_start_unchanged':True,
        'new_google_requests':0,'new_ai_runs':0,
        'console_note':'Sampled errors were chrome-extension content-script errors; not exhaustive console certification',
        'remaining_limits':['Gantt dates absent','No fresh Gemini generation','Independent remote Internet probe unavailable','n8n owner UI not authenticated']}
target=OUT/'browser-uat-final.json'
assert not target.exists(), 'Refuse evidence overwrite'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))

"""Snapshot current schemas and semantic assertions; never creates proposals or changes control."""
import json,os,subprocess,urllib.request
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
raw=subprocess.check_output(['docker','exec','qldapm-ai-telegram-ai-1','python','-c',"import json;from app.tools import declarations,WRITES;print(json.dumps({'tools':declarations(),'writes':sorted(WRITES)}))"],text=True)
schemas=json.loads(raw);assert len(schemas['tools'])==29 and len(schemas['writes'])==7
(OUT/'telegram-tool-schemas.json').write_text(json.dumps(schemas,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
token=(Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai/secrets/gateway.token').read_text().strip()
request=urllib.request.Request('http://127.0.0.1:18089/api/v1/openapi.json',headers={'Authorization':'Bearer '+token})
with urllib.request.urlopen(request,timeout=30) as r:api=json.load(r)
(OUT/'gateway-openapi.json').write_text(json.dumps(api,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
live=json.loads((OUT/'main-integrations.json').read_text(encoding='utf-8'));tools={r['tool']:r['result'] for r in live['tools']}
task=tools['get_task_progress'];cp=tools['get_checkpoint_status']['checkpoint'];pending=tools['get_pending_approvals'];active=tools['get_active_agents']
checks={
    '398_business_not_done':task['business_status']=='READY FOR RELEASE' and task['acceptance_status']=='AWAITING_OWNER_APPROVAL',
    '398_no_current_agent':tools['get_current_agent']['current_agent'] is None,
    'global_no_active_agents_OFF':not active['items'] and active['system']['control']['desired_mode']=='OFF' and active['system']['queue']['active']==0,
    'pending_has398_not397':398 in [x['task_id'] for x in pending['items']] and 397 not in [x['task_id'] for x in pending['items']],
    'checkpoint27_is11_steps':cp['version']==27 and len(cp['completed_steps'])==11,
    'completed_run_not_resumable':tools['get_checkpoint_status']['resume']['eligible'] is False,
    'review_historical_PASS':json.loads(tools['get_review_results']['stages'][0]['summary'])['verdict']=='PASS',
    'qa_historical_PASS':json.loads(tools['get_qa_results']['stages'][0]['summary'])['qa']['status']=='PASS',
    'scope_not_omitted':bool(active['scope_notice']) and 'truncated' in active,
}
(OUT/'semantic-read-checks.json').write_text(json.dumps({'scope':'Actual current MAIN DTO semantics; historical reviewer/QA evidence, no new run','checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'tools':29,'writes':7,'routes':len(api.get('paths',{})),'checks':checks}));assert all(checks.values())

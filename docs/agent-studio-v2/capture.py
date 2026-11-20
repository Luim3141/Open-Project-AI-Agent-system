"""Read canonical Observer using the existing local principal; never print bearer."""
import json, os
from pathlib import Path
import urllib.request

OUT=Path(__file__).resolve().parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai'
token=(private/'secrets/gateway.token').read_text().strip()
def read(action, arguments):
    req=urllib.request.Request('http://127.0.0.1:18089/api/v1/commands',data=json.dumps({'action':action,'arguments':arguments,'project_id':6}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)['result']
if __name__=='__main__':
    for task in (391,397):
        snapshot=read('observer_task_progress',{'task_id':task})
        (OUT/f'task-{task}.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        monitor=read('observer_run_details',{'run_id':snapshot['latest_run_id']})
        (OUT/f'run-{task}.json').write_text(json.dumps(monitor,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'task':task,'stages':[s['stage_key'] for s in snapshot['stages']],'edges':monitor.get('edges'),'node_keys':list(monitor['nodes'][1]),'event':monitor.get('events',[])[:1]},ensure_ascii=False))

"""Run inside serving Gateway: Native GET only, no provider calls. Output is metadata only."""
import json,sys
from pathlib import Path
from unittest.mock import patch
from gateway.service import Service
from gateway.store import Store
from gateway.native import Native
root=Path('/state');store=Store(root);service=Service(store,json.loads((root/'config.json').read_text()),'/workspaces')
old='6276720c-d6f8-4c3a-bf64-1e4fca623eb0';ids=[old]+sys.argv[1:];out={'runs':[]};original=Native.call;methods=[]
def reads(self,path,method='GET',payload=None):
    assert method=='GET','CLOSEOUT_NATIVE_WRITE_FORBIDDEN';methods.append([method,path.split('?')[0]])
    return original(self,path,method,payload)
with patch.object(Native,'call',reads):
    for identifier in ids:
        view=service.execute_actor(19,{'action':'get_ai_run','arguments':{'id':identifier}})['result']
        monitor=service.execute_actor(19,{'action':'get_execution_monitor','arguments':{'id':identifier}})['result']
        with store.connect() as db:
            receipts=[json.loads(r[0]) for r in db.execute('select document from gemini_call_receipts where actor=19 and run_id=? order by rowid',(identifier,))]
            lifecycle=[dict(r) for r in db.execute('select id,at,action,outcome from audit where actor=19 and run_id=? order by at',(identifier,))]
        raw=store.run(19,identifier);r=view.get('result',{})
        out['runs'].append({'id':identifier,'worker_state':raw['state'],'original_error':raw.get('result',{}).get('error'),
          'effective_state':view['state'],'completion':r.get('completion'),'heading':r.get('heading'),'model_used':r.get('model_used'),
          'synthesis_origin':r.get('synthesis_origin'),'final_text':r.get('text'),'monitor_state':monitor['state'],'monitor_terminal':monitor['terminal'],
          'monitor_metrics':monitor['metrics'],'receipts':receipts,'lifecycle':lifecycle,
          'tools':[{'action':c['action'],'native_id':c.get('result',{}).get('result',{}).get('id') if isinstance(c.get('result',{}).get('result'),dict) else None,
                    'native_confirmed':c.get('result',{}).get('result',{}).get('native_confirmed') if isinstance(c.get('result',{}).get('result'),dict) else None} for c in r.get('tools',[])]})
with store.connect() as db:
    out['counters']={k:db.execute('select count(*) from '+table).fetchone()[0] for k,table in [('runs','ai_runs'),('receipts','gemini_call_receipts'),('usage','gemini_usage')]}
    out['busy']=db.execute("select count(*) from ai_runs where state='running'").fetchone()[0]
    out['pending']=db.execute("select count(*) from requests where state!='done'").fetchone()[0]
out['native_read_calls']=methods;print(json.dumps(out,ensure_ascii=False))

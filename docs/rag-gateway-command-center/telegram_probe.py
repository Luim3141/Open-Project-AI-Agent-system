"""Read only real Owner turn containing the Phase 4 marker; never synthesizes inbound."""
import json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
script='''import json,sqlite3,time
from app.config import Settings
s=Settings.from_env();d=sqlite3.connect(s.db_path.as_uri()+'?mode=ro',uri=True)
m=d.execute('select document from memories where user_id=? and chat_id=?',(1916909968,1916909968)).fetchone();m=json.loads(m[0]) if m else {}
messages=m.get('recent_messages',[]);start=next((i for i in range(len(messages)-1,-1,-1) if messages[i].get('role')=='user' and 'ORBIT-RECEIPT-20261103' in messages[i].get('text','')),None)
messages=messages[start:] if start is not None else [];since=messages[0]['at']-2 if messages else time.time()
audit=[{'at':r[0],**json.loads(r[1])} for r in d.execute('select created,document from command_audit where created>=? order by created',(since,))]
print(json.dumps({'scope':'ACTUAL Owner Telegram messages + receipts, no simulated input','messages':messages,'audit':audit,'budget':d.execute('select day,calls from model_budget order by day desc limit 2').fetchall(),'model':s.gemini_model,'daily_cap':s.max_daily_model_calls},ensure_ascii=False))'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-telegram-ai-1','python','-'],input=script,text=True,capture_output=True,encoding='utf-8',check=True)
report=json.loads(p.stdout)
if report['messages']:
    citation=json.loads((OUT/'main-file-ui.json').read_text(encoding='utf-8'))['readback']['result']['citation']
    answer='\n'.join(x['text'] for x in report['messages'] if x['role']=='model')
    generations=[x for x in report['audit'] if x.get('event')=='GEMINI_REQUEST']
    report['checks']={'real_input':True,'answer_received':bool(answer),'fresh_rag_tool':any(x.get('event')=='READ_TOOL' and x.get('tool')=='search_knowledge' for x in report['audit']),'no_write':not any(x.get('event')=='WRITE_TOOL' for x in report['audit']),'technical_source_pin_retained':citation in answer,'exact_resolved_model':bool(generations) and all(x.get('resolved_model_version')=='gemini-3.5-flash-lite' and not x.get('error_type') for x in generations)}
else:report['checks']={'real_input':False}
(OUT/'telegram-live-rag.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':report['checks'],'budget':report['budget'],'messages':report['messages']},ensure_ascii=False))
if '--require-pass' in __import__('sys').argv:assert all(report['checks'].values())

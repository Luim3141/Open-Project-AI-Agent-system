import sqlite3,json,sys,hashlib,socket,threading,time
from pathlib import Path
from task_manager.app import create_app
import uvicorn,httpx
source=Path('/home/openclaw/engineering/demo-data/tasks.sqlite');target=Path.cwd()/'compat.sqlite'
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as old,sqlite3.connect(target) as new:old.backup(new)
with sqlite3.connect(target) as db:before=db.execute('SELECT id,title,status FROM tasks ORDER BY id').fetchall();schema=db.execute('PRAGMA table_info(tasks)').fetchall()
app=create_app(str(target));sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False));t=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);t.start()
try:
 for _ in range(50):
  if server.started:break
  time.sleep(.1)
 with httpx.Client(base_url='http://127.0.0.1:'+str(port)) as c:
  assert c.get('/healthz').status_code==200
  baseline=c.get('/tasks/summary').json();assert baseline['total']==len(before)
  task=c.post('/tasks',json={'title':'Phase2 isolated compat probe'});assert task.status_code==201;identifier=task.json()['id']
  assert c.patch('/tasks/'+str(identifier),json={'status':'done'}).status_code==200
  assert any(v['id']==identifier for v in c.get('/tasks',params={'q':'isolated compat'}).json())
  summary=c.get('/tasks/summary').json();assert summary['total']==baseline['total']+1 and summary['active']+summary['completed']==summary['total']
  assert c.delete('/tasks/'+str(identifier)).status_code==204
  assert c.patch('/tasks/99999999',json={'title':'missing'}).status_code==404
  assert c.post('/tasks',json={'title':''}).status_code==422
 with sqlite3.connect(target) as db:after=db.execute('SELECT id,title,status FROM tasks ORDER BY id').fetchall();assert before==after and schema==db.execute('PRAGMA table_info(tasks)').fetchall()
 print(json.dumps({'release_sha':'0498ceeda97cd3e856a975129129e71f6c94a3dd','http_health':200,'http_summary':200,'crud_search_errors':'PASS','preserved_existing_rows':len(before),'schema_preserved':True,'data_fingerprint':hashlib.sha256(repr(before).encode()).hexdigest(),'live_port18791_changed':False}))
finally:server.should_exit=True;t.join(5)

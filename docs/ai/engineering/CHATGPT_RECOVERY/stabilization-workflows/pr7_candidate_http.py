import json,socket,sqlite3,subprocess,tempfile,threading,time
from pathlib import Path
import httpx,uvicorn
from task_manager.app import create_app

tree=Path('/home/openclaw/engineering/feedback-20c2a94109f4e78f')
expected='a150f3d690288ff95451c2667954f09661aa9604'
assert subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD']).decode().strip()==expected
source=Path('/home/openclaw/engineering/demo-data/tasks.sqlite')
with tempfile.TemporaryDirectory(prefix='qldapm-pr7-http-') as temp:
    target=Path(temp)/'tasks.sqlite'
    with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as original,sqlite3.connect(target) as clone:
        original.backup(clone)
    with sqlite3.connect(target) as db:
        before=db.execute('select id,title,status from tasks order by id').fetchall()
        schema=db.execute('pragma table_info(tasks)').fetchall()
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(create_app(str(target)),log_level='critical',access_log=False))
    thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    try:
        for _ in range(50):
            if server.started:break
            time.sleep(.1)
        assert server.started
        with httpx.Client(base_url=f'http://127.0.0.1:{port}') as client:
            assert client.get('/healthz').status_code==200
            assert client.get('/tasks/summary').status_code==200
            created=client.post('/tasks',json={'title':'PR7 isolated retrieval fixture'})
            assert created.status_code==201
            item=created.json();found=client.get('/tasks/'+str(item['id']))
            assert found.status_code==200 and all(found.json()[k]==item[k] for k in ('id','title','status'))
            assert client.get('/tasks/999999999').status_code==404
            assert client.get('/tasks/not-an-integer').status_code==422
            assert client.delete('/tasks/'+str(item['id'])).status_code==204
        with sqlite3.connect(target) as db:
            assert db.execute('select id,title,status from tasks order by id').fetchall()==before
            assert db.execute('pragma table_info(tasks)').fetchall()==schema
        print(json.dumps({'status':'PASS','commit':expected,'isolated_port':port,'get_existing':200,'missing':404,'invalid':422,'health':200,'summary':200,'live_database_written':False,'schema_unchanged':True}))
    finally:
        server.should_exit=True;thread.join(5)

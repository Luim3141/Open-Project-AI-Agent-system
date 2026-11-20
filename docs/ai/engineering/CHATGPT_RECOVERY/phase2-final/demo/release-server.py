import sys
sys.path.insert(0,'/home/openclaw/engineering/releases/0498ceeda97cd3e856a975129129e71f6c94a3dd')
from task_manager.app import create_app
import uvicorn
app=create_app('/home/openclaw/engineering/demo-data/tasks.sqlite')
@app.middleware('http')
async def revision_header(request,call_next):
 response=await call_next(request)
 response.headers['X-QLDAPM-Revision']='0498ceeda97cd3e856a975129129e71f6c94a3dd'
 response.headers['X-QLDAPM-Release-Status']='TEST RELEASE - UNMERGED SOURCE'
 return response
@app.get('/_qldapm/release',include_in_schema=False)
def release_status():
 return {'status':'TEST RELEASE - UNMERGED SOURCE','revision':'0498ceeda97cd3e856a975129129e71f6c94a3dd','pull_request':6,'merged':False}
uvicorn.run(app,host='127.0.0.1',port=18791,access_log=False)

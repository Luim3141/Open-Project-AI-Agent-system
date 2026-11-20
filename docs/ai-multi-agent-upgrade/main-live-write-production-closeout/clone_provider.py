"""Clone-only sitecustomize: SDK MockTransport, synthetic policy. Never included in candidate image."""
import json
import httpx
from gateway.gemini import Gemini
POLICY={'model':'gemini-3.5-flash-lite','data_scope':'project-business-content','project':'offline-closeout-clone',
        'limits':{'rpm':100,'rpd':100,'tpm':1000000}}
Gemini.settings=lambda self,*args,**kwargs:POLICY
original=Gemini.sdk_client
def wire(request):
    body=json.loads(request.content)
    if request.url.path.endswith(':countTokens'):return httpx.Response(200,json={'totalTokens':120})
    responses=[p['functionResponse'] for c in body.get('contents',[]) for p in c.get('parts',[]) if 'functionResponse' in p]
    inputs=json.loads(body['contents'][0]['parts'][0]['text']) if not body.get('tools') else {}
    facts=[{k:item.get(k) for k in ('id','parent_id','assignee_id')} for item in inputs.get('native_items',[])]
    parts=[{'text':json.dumps({'citations':[367,50],'facts':facts,
        'explanation':'SDK MOCK trên clone: #367 thuộc Parent #50; đọc dữ liệu Native thật, không ghi thay đổi.'},ensure_ascii=False)}] if responses or not body.get('tools') else [
          {'functionCall':{'name':'get_work_package','args':{'id':i}}} for i in (367,50)]
    return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':parts}}],
        'usageMetadata':{'promptTokenCount':120,'candidatesTokenCount':40,'totalTokenCount':160}})
Gemini.sdk_client=lambda self,transport=None,timeout=120:original(self,httpx.MockTransport(wire),timeout)

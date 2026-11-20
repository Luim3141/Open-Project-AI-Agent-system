"""Bounded read-only reproduction; bearer stays in memory, responses are never dumped."""
import argparse,json,os,time,urllib.request,urllib.error,statistics
from pathlib import Path
OUT=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=1);parser.add_argument('--timeout',type=float,default=15);parser.add_argument('--output',default='gateway-baseline.json');args=parser.parse_args()
    assert 1<=args.samples<=10 and 1<=args.timeout<=30
    token=(Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai/secrets/gateway.token').read_text().strip()
    scenarios=[('list','observer_active',{'limit':5}),('task397','observer_task_progress',{'task_id':397}),('parent379','observer_task_progress',{'task_id':379})]
    rows=[]
    for sample in range(args.samples):
        for name,action,arguments in scenarios:
            request=urllib.request.Request('http://127.0.0.1:18089/api/v1/commands',data=json.dumps({'action':action,'arguments':arguments,'project_id':6}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
            start=time.perf_counter();status=None;error=None;size=0;ttfb=None;shape={};headers={}
            try:
                with urllib.request.urlopen(request,timeout=args.timeout) as response:
                    ttfb=(time.perf_counter()-start)*1000;status=response.status
                    headers={k:v for k,v in response.headers.items() if k.lower() in {'x-request-id','x-correlation-id','server-timing','retry-after'}}
                    data=response.read();size=len(data);result=json.loads(data).get('result',{})
                    shape={k:len(result[k]) for k in ['items','runs','stages','events','artifacts'] if isinstance(result.get(k),list)}
            except urllib.error.HTTPError as e:
                status=e.code
                try:error=json.load(e).get('error','HTTP_ERROR')
                except Exception:error='HTTP_ERROR'
            except Exception as e:error=type(e).__name__
            row={'scenario':name,'sample':sample,'action':action,'http_status':status,'error':error,'ttfb_ms':ttfb,'total_ms':round((time.perf_counter()-start)*1000,3),'bytes':size,'shape':shape,'headers':headers,'at':time.time()};rows.append(row);print(json.dumps(row),flush=True)
    (OUT/args.output).write_text(json.dumps({'route':'DIRECT_AUTHENTICATED_GATEWAY_READ','samples':rows,'business_writes':0,'model_calls':0},indent=2)+'\n')
    assert all(r['http_status']==200 and r['total_ms']<(2000 if r['scenario']=='list' else 3000) for r in rows),'READ_PATH_LATENCY_OR_AVAILABILITY_REGRESSION'
if __name__=='__main__':main()

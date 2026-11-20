"""Execute inside existing Gateway, read-only Observer; emit timing metadata only."""
import cProfile,json,pstats,time,sys
from pathlib import Path
from gateway.native import Native
from gateway.store import Store
from gateway.service import Service
from gateway.agent_observer import execute

native_calls=[]
class TimedNative(Native):
    def call(self,path,*args,**kwargs):
        start=time.perf_counter();status=200
        try:return super().call(path,*args,**kwargs)
        except Exception as e:status=getattr(e,'status',None);raise
        finally:native_calls.append({'path':path.split('?')[0],'method':args[0] if args else kwargs.get('method','GET'),'status':status,'ms':round((time.perf_counter()-start)*1000,3)})

config=json.loads(Path('/state/config.json').read_text());config['project_id']=6
service=Service(Store('/state'),config,'/workspaces',native_factory=TimedNative)
profiler=cProfile.Profile();profiler.enable();start=time.perf_counter()
native,who=service.native_actor(18)
task_id=int(sys.argv[1]) if len(sys.argv)>1 else 397
result=execute(service,who,native,'observer_task_progress',{'task_id':task_id})
duration=time.perf_counter()-start;profiler.disable()
stats=pstats.Stats(profiler)
top=sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:45]
print(json.dumps({'task_id':task_id,'total_ms':duration*1000,'native_calls':native_calls,'result_bytes':len(json.dumps(result).encode()),'functions':[{'file':Path(k[0]).name,'line':k[1],'function':k[2],'calls':v[1],'self_s':v[2],'cumulative_s':v[3]} for k,v in top]},indent=2))

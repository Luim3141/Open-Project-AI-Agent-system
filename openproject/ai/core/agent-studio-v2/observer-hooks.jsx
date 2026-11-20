import {useEffect,useState} from 'react';
import {readJSON,ReadError,retryDelay} from './request.mjs';

// A request generation belongs to one endpoint/argument key. Cleanup invalidates it.
export function useObserverRead(endpoint,args,{enabled=true,poll=false,refresh=0,debounce=0,validate}={}){
 const key=JSON.stringify(args),[state,setState]=useState({key:null,data:null,phase:'idle',error:null,lastFetch:null});
 useEffect(()=>{
  if(!enabled)return;
  let cancelled=false,timer,controller,inFlight=false,resume=false,stopped=false,failures=0;
  const update=patch=>{if(!cancelled)setState(old=>({...((old.key===key)?old:{key,data:null,error:null,lastFetch:null}),...patch,key}));};
  async function read(){
   if(cancelled||document.hidden||stopped)return;
   if(inFlight){resume=true;return;}
   inFlight=true;controller=new AbortController();
   setState(old=>cancelled?old:{...((old.key===key)?old:{key,data:null,lastFetch:null}),key,phase:old.key===key&&old.data?'refreshing':'loading',error:null});
   try{
    const data=await readJSON(endpoint,args,controller.signal);
    if(cancelled)return;
    if(validate)validate(data);
    failures=0;
    const empty=Array.isArray(data.items)?data.items.length===0:Array.isArray(data.runs)&&data.runs.length===0;
    update({data,phase:data.source_conflicts?.length||data.truncated?'partial':empty?'empty':'loaded',error:null,lastFetch:Date.now()});
    if(poll&&!document.hidden)timer=setTimeout(read,data.workflow_status==='RUNNING'&&data.freshness?.freshness_status==='FRESH'?3000:15000);
   }catch(cause){
    if(cancelled)return;
    if(cause.name==='AbortError'){update({phase:'cancelled',error:null});return;}
    const error=cause instanceof ReadError?cause:new ReadError(502,'INVALID_OBSERVER_DATA',null);
    const delay=retryDelay(error,++failures);stopped=delay===null;
    update({phase:error.status===504?'timeout':'error',error,attempt:failures,nextRetryAt:delay?Date.now()+delay:null,...([401,403,404].includes(error.status)?{data:null}:{})});
    if(delay&&!document.hidden)timer=setTimeout(read,delay);
   }finally{
    inFlight=false;
    if(resume&&!cancelled&&!document.hidden&&!stopped){resume=false;clearTimeout(timer);timer=setTimeout(read,0);}
   }
  }
  const visibility=()=>{clearTimeout(timer);if(document.hidden){controller?.abort();update({phase:'cancelled'});}else if(!stopped)read();};
  document.addEventListener('visibilitychange',visibility);
  timer=setTimeout(read,debounce);
  return()=>{cancelled=true;clearTimeout(timer);controller?.abort();document.removeEventListener('visibilitychange',visibility);};
 },[endpoint,key,enabled,poll,refresh,debounce]);
 const bound=state.key===key?state:{key,data:null,phase:enabled?'loading':'idle',error:null,lastFetch:null};
 return {...bound,busy:['loading','refreshing'].includes(bound.phase)};
}

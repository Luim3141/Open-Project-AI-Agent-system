import test from 'node:test';import assert from 'node:assert/strict';
import * as requests from './request.mjs';
const {readJSON,ReadError,retryDelay,parseRetryAfter}=requests;
test('Retry-After accepts nonnegative seconds and HTTP dates; invalid/missing hints are absent',()=>{
 const now=Date.parse('Thu, 12 Nov 2026 04:00:00 GMT');
 assert.equal(parseRetryAfter('1',now),1);assert.equal(parseRetryAfter('0',now),0);
 assert.equal(parseRetryAfter('Thu, 12 Nov 2026 04:00:12 GMT',now),12);
 for(const value of [null,'','bad','-1','1.5','Infinity'])assert.equal(parseRetryAfter(value,now),null);
});
test('valid Retry-After is honored for both 429 and 503 with bounded positive jitter',()=>{
 for(const status of [429,503])for(const seconds of [1,9,120]){
  const delay=retryDelay(new ReadError(status,'BUSY','rid',seconds),1);
  assert(delay>=seconds*1000&&delay<=seconds*1000+250);
 }
 assert.equal(retryDelay(new ReadError(503,'BUSY','rid',3000000),1),null);
});
test('no retry for revoked permissions, missing record or cancelled request; bounded failures',()=>{
 for(const status of [401,403,404,409,422])assert.equal(retryDelay(new ReadError(status,'ERROR','rid'),1),null);
 assert(retryDelay(new ReadError(503,'MAINTENANCE','rid'),1)>=5000);
 assert.equal(retryDelay(new ReadError(503,'MAINTENANCE','rid'),4),null);
});
test('HTTP errors retain status/correlation and never consume backend text as trusted UI',async()=>{
 const original=globalThis.fetch;globalThis.fetch=async()=>new Response(JSON.stringify({error:'MAINTENANCE',message:'untrusted body'}),{status:503,headers:{'x-qldapm-request-id':'safe-id','retry-after':'9'}});
 try{await assert.rejects(readJSON('/observer',{},new AbortController().signal),e=>e.status===503&&e.requestId==='safe-id'&&e.message!=='untrusted body'&&retryDelay(e,1)>=9000&&retryDelay(e,1)<=9250);}finally{globalThis.fetch=original;}
});
test('timeout resolves as finite error; explicit cancellation remains cancellation',async()=>{
 const original=globalThis.fetch;globalThis.fetch=async(_url,{signal})=>new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(signal.reason),{once:true}));
 try{
  const c=new AbortController();const pending=readJSON('/observer',{},c.signal);c.abort();await assert.rejects(pending,e=>e.name==='AbortError');
  const keepAlive=setTimeout(()=>{},100);await assert.rejects(readJSON('/observer',{},new AbortController().signal,10),e=>e.status===504&&e.code==='TIMEOUT');clearTimeout(keepAlive);
 }finally{globalThis.fetch=original;}
});
test('local bridge backpressure uses its short Retry-After without weakening quota retries',()=>{
 assert(retryDelay(new ReadError(429,'AI_BRIDGE_BUSY','rid',1),1)<=1250);
 assert(retryDelay(new ReadError(429,'RATE_LIMITED','rid',30),1)>=30000);
 assert.equal(retryDelay(new ReadError(429,'AI_BRIDGE_BUSY','rid',1),4),null);
});

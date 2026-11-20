export class ReadError extends Error{
 constructor(status,code,requestId,retryAfter=null){super(status===401?'Phiên đăng nhập đã hết hạn.':status===403?'Không tìm thấy hoặc không có quyền đọc trong project này.':status===404?'Không tìm thấy Task hoặc run.':status===429?'Đã chạm giới hạn đọc; vui lòng thử lại sau.':status===504||code==='TIMEOUT'?'Hết thời gian đọc dữ liệu; hãy Retry.':code==='MAINTENANCE'?'Backend đang bảo trì.':status>=500?'Backend tạm thời chưa sẵn sàng.':'Dữ liệu trả về chưa hợp lệ.');this.status=status;this.code=code;this.requestId=requestId;this.retryAfter=retryAfter;}
}
export function parseRetryAfter(value,now=Date.now()){
 if(value===null||value===undefined||!String(value).trim())return null;
 const text=String(value).trim();
 const seconds=/^\d+$/.test(text)?Number(text):/GMT$/.test(text)?Math.max(0,Math.ceil((Date.parse(text)-now)/1000)):NaN;
 return Number.isFinite(seconds)&&seconds>=0?seconds:null;
}
export function retryDelay(error,failures){
 if(error?.name==='AbortError'||[401,403,404,409,422].includes(error?.status)||failures>3)return null;
 const hint=error?.retryAfter;
 const base=Number.isFinite(hint)&&hint>=0?Math.max(250,hint*1000):error?.code==='AI_BRIDGE_BUSY'?Math.min(3000,1000*2**(failures-1)):Math.min(60000,5000*2**(failures-1));
 // Longer hints stay visible as errors; never overflow the browser timer into an immediate retry.
 return base>2147483397?null:base+Math.floor(Math.random()*251);
}
export async function readJSON(endpoint,args,signal,timeout=10000){
 try{
  const response=await fetch(endpoint+'?'+new URLSearchParams(args),{signal:AbortSignal.any([signal,AbortSignal.timeout(timeout)]),credentials:'same-origin',headers:{Accept:'application/json'},cache:'no-store'});
  const rid=response.headers.get('x-qldapm-request-id')||response.headers.get('x-request-id');
  if(response.redirected&&new URL(response.url).pathname==='/login')throw new ReadError(401,'SESSION_EXPIRED',rid);
  let data;try{data=await response.json();}catch{throw new ReadError(response.status||502,'INVALID_JSON',rid);}
  if(!response.ok)throw new ReadError(response.status,String(data.error||'HTTP_ERROR').match(/^[A-Z0-9_]+$/)?.[0]||'HTTP_ERROR',rid,parseRetryAfter(response.headers.get('retry-after')));
  return data;
 }catch(error){
  if(signal.aborted)throw new DOMException('Read cancelled','AbortError');
  if(error.name==='TimeoutError')throw new ReadError(504,'TIMEOUT',null);
  if(error instanceof ReadError)throw error;
  throw new ReadError(503,'CONNECTION_UNAVAILABLE',null);
 }
}

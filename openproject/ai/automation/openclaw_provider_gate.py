"""Loopback Gemini transport gate. Root-owned admission; no inference while OFF.

The host reserves the bounded request allowance in QLDAPM's existing quota store
before activating this gate. OpenClaw receives only a local token, never the Google key.
"""
import hashlib
import hmac
import json
import re
import random
import math
import threading
import time
import uuid
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path('/root/.qldapm-openclaw')
LOCK=threading.Lock()
MODEL='gemini-3.5-flash-lite'
GATEWAY='http://127.0.0.1:18089/internal/engineering/provider'

def retry_delay(headers,body,attempt,now=None):
    now=time.time() if now is None else now
    value=headers.get('Retry-After')
    try:delay=float(value)
    except (ValueError,TypeError):
        try:delay=parsedate_to_datetime(value).timestamp()-now
        except (ValueError,TypeError,AttributeError):delay=0
    try:
        details=json.loads(body).get('error',{}).get('details',[])
        for item in details:
            raw=item.get('retryDelay','')
            if re.fullmatch(r'\d+(?:\.\d+)?s',raw):delay=max(delay,float(raw[:-1]))
    except (ValueError,TypeError,AttributeError):pass
    if not math.isfinite(delay):delay=0
    return min(86400,max(60*(2**min(attempt,10)),delay)+random.uniform(0,.5))

def control(active,action,request_id,details):
    expected=(ROOT/'client-token').read_text().strip()
    body={'action':action,'claim':active.get('claim'),'session_id':active['session_id'],'step':active['step'],'request_id':request_id,'details':details}
    request=urllib.request.Request(GATEWAY,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Host':'localhost:18089','X-QLDAPM-Provider-Token':expected})
    try:response=urllib.request.urlopen(request,timeout=8)
    except urllib.error.HTTPError as error:response=error
    with response:result=json.loads(response.read(8192))
    if result.get('error'):raise PermissionError(result['error'])
    return result

def wait_for_admission(active,phase,data):
    while True:
        current=json.loads((ROOT/'active.json').read_text())
        if not same_active(current,active) or current.get('deadline',0)<=time.time()+45:raise PermissionError('ENGINEERING_PROVIDER_OFF')
        request_id=str(uuid.uuid4())
        result=control(active,'reserve',request_id,{'phase':phase,'request_sha256':hashlib.sha256(data).hexdigest(),'input_token_bound':len(data)+3000})
        if result['state']=='RESERVED':return request_id
        if result['state'] not in {'WAITING_FOR_QUOTA','WAITING_FOR_PROVIDER'}:raise PermissionError(result.get('reason') or 'ENGINEERING_PROVIDER_UNAVAILABLE')
        retry=result.get('retry_at')
        if type(retry) not in (int,float) or retry>=active['deadline']-45:raise PermissionError('ENGINEERING_PROVIDER_WAITING_QUOTA')
        while time.time()<retry:
            if time.time()>=active['deadline']-45:raise PermissionError('ENGINEERING_PROVIDER_DEADLINE')
            current=json.loads((ROOT/'active.json').read_text())
            if not same_active(current,active):raise PermissionError('ENGINEERING_PROVIDER_OFF')
            time.sleep(min(1,max(.05,retry-time.time())))


def same_active(current,expected):
    return current.get('active') is True and all(current.get(key)==expected.get(key) for key in ['run_id','session_id','step','claim'])


def admit(document, model, size, now):
    if document.get('active') is not True or document.get('deadline',0)<=now:
        raise PermissionError('ENGINEERING_PROVIDER_OFF')
    if model!=MODEL or size>262144 or size<=0:
        raise PermissionError('ENGINEERING_PROVIDER_SCOPE')
    if type(document.get('remaining')) is not int or document['remaining']<=0:
        raise PermissionError('ENGINEERING_PROVIDER_BUDGET')
    document['remaining']-=1


def save(document):
    path=ROOT/'active.json';tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(document));tmp.chmod(0o600);tmp.replace(path)


class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'

    def log_message(self,*args):
        pass  # Request paths may contain the local client token; never access-log them.

    def reject(self,message,status=403):
        body=json.dumps({'error':{'code':status,'status':'PERMISSION_DENIED','message':message}}).encode()
        self.response_started=True;self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.send_header('Connection','close');self.end_headers();self.close_connection=True;self.wfile.write(body)

    def do_POST(self):
        self.response_started=False
        try:
            url=urllib.parse.urlsplit(self.path)
            match=re.fullmatch(r'/v1beta/models/([^/:]+):(generateContent|streamGenerateContent|countTokens)',url.path)
            token=self.headers.get('x-goog-api-key') or urllib.parse.parse_qs(url.query).get('key',[''])[0]
            expected=(ROOT/'client-token').read_text().strip()
            if not match or len(expected)<32 or not hmac.compare_digest(token,expected):
                raise PermissionError('ENGINEERING_PROVIDER_AUTH_OR_PATH')
            size=int(self.headers.get('Content-Length','0'))
            if match[1]!=MODEL or not 0<size<=262144 or self.headers.get('Transfer-Encoding'):raise PermissionError('ENGINEERING_PROVIDER_SCOPE')
            with LOCK:
                active=json.loads((ROOT/'active.json').read_text())
                if active.get('active') is not True or active.get('deadline',0)<=time.time()+45:raise PermissionError('ENGINEERING_PROVIDER_OFF')
                run_id=active['run_id']
            self.connection.settimeout(10)
            data=self.rfile.read(size)
            if len(data)!=size:raise ValueError('ENGINEERING_PROVIDER_BODY_INCOMPLETE')
            request_body=json.loads(data)
            if not isinstance(request_body,dict) or not isinstance(request_body.get('generationConfig',{}),dict):raise ValueError('ENGINEERING_PROVIDER_INPUT_INVALID')
            output=request_body.get('generationConfig',{}).get('maxOutputTokens',3000)
            if type(output) is not int or not 1<=output<=3000:raise PermissionError('ENGINEERING_OUTPUT_BUDGET')
            if match[2]!='countTokens' and 'maxOutputTokens' not in request_body.get('generationConfig',{}):
                request_body.setdefault('generationConfig',{})['maxOutputTokens']=3000
                data=json.dumps(request_body,separators=(',',':'),ensure_ascii=False).encode('utf-8');size=len(data)
                if size>262144:raise PermissionError('ENGINEERING_PROVIDER_SCOPE')
            query='?alt=sse' if match[2]=='streamGenerateContent' else ''
            key=(ROOT/'google-key').read_text().strip()
            if not key:raise PermissionError('ENGINEERING_PROVIDER_KEY_MISSING')
            request=urllib.request.Request('https://generativelanguage.googleapis.com'+url.path+query,
                data=data,headers={'x-goog-api-key':key,'Content-Type':'application/json'})
            for attempt in range(2):
                request_id=wait_for_admission(active,match[2],data)
                with LOCK:
                    current=json.loads((ROOT/'active.json').read_text())
                    if not same_active(current,active):raise PermissionError('ENGINEERING_PROVIDER_OFF')
                    active=current;admit(active,match[1],size,time.time());save(active)
                    sequence=len(active.get('receipts',[]))+1
                started=time.time();upstream_status=0;response_data=bytearray();usage=None;delay=None
                try:
                    try:response=urllib.request.urlopen(request,timeout=45)
                    except urllib.error.HTTPError as error:response=error
                    with response:
                        upstream_status=response.status
                        if upstream_status in {429,503}:
                            response_data.extend(response.read(1048577))
                            if len(response_data)>1048576:raise ValueError('PROVIDER_RESPONSE_TOO_LARGE')
                            delay=retry_delay(response.headers,response_data,attempt)
                        if upstream_status not in {429,503} or attempt==1 or active.get('remaining',0)<=0 or time.time()+(delay or 0)+45>=active['deadline']:
                            self.response_started=True;self.send_response(upstream_status);self.send_header('Content-Type',response.headers.get('Content-Type','application/json'))
                            self.send_header('Connection','close');self.end_headers();self.close_connection=True
                            if response_data:self.wfile.write(response_data)
                            else:
                                while chunk:=response.read1(16384):
                                    response_data.extend(chunk)
                                    if len(response_data)>1048576:raise ValueError('PROVIDER_RESPONSE_TOO_LARGE')
                                    self.wfile.write(chunk);self.wfile.flush()
                finally:
                    for line in bytes(response_data).splitlines():
                        try:
                            event=json.loads(line[5:].strip() if line.startswith(b'data:') else line)
                            if isinstance(event,dict) and event.get('usageMetadata'):usage=event['usageMetadata']
                        except (ValueError,TypeError):pass
                    control(active,'settle',request_id,{'http_status':upstream_status,'usage':usage,'started':started,'finished':time.time(),'retry_after':delay,'call_cap':active['call_cap']})
                    with LOCK:
                        active=json.loads((ROOT/'active.json').read_text())
                        if active.get('run_id')==run_id:
                            active.setdefault('receipts',[]).append({'id':request_id,'sequence':sequence,'started':started,'finished':time.time(),'phase':match[2],
                                'http_status':upstream_status,'request_sha256':hashlib.sha256(data).hexdigest(),'usage':usage,'retry_after_seconds':delay})
                            save(active)
                if self.response_started:break
        except PermissionError as error:
            if not self.response_started:self.reject(str(error))
        except (ValueError,OSError,KeyError,TypeError):
            if not self.response_started:self.reject('ENGINEERING_PROVIDER_FAILED',502)
        finally:self.close_connection=True


if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',18890),Handler).serve_forever()

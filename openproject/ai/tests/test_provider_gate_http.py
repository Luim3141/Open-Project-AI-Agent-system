"""Actual loopback HTTP gate against a synthetic upstream; no Google or real credentials."""
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from automation import openclaw_provider_gate as gate

class GateHTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.now=time.time();self.calls=[];self.settled=[];self.waiting=False;self.off_during_wait=False;self.statuses=[429,200]
  self.active={'active':True,'run_id':'fixture-session-step','remaining':3,'call_cap':3,'deadline':self.now+450,'session_id':'session','step':'dev-0','claim':{'run_id':'fixture','worker_id':'worker','claim_token':'synthetic'}}
  (self.root/'active.json').write_text(json.dumps(self.active));(self.root/'client-token').write_text('synthetic-client-token-01234567890123456789');(self.root/'google-key').write_text('synthetic-upstream-key')
  fixture=self
  class Upstream(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    fixture.calls.append(self.rfile.read(int(self.headers['Content-Length'])))
    status=fixture.statuses[min(len(fixture.calls)-1,len(fixture.statuses)-1)]
    body=json.dumps({'error':{'code':status}} if status!=200 else {'usageMetadata':{'totalTokenCount':42},'candidates':[]}).encode()
    self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  self.upstream=ThreadingHTTPServer(('127.0.0.1',0),Upstream);self.server=ThreadingHTTPServer(('127.0.0.1',0),gate.Handler)
  for server in [self.upstream,self.server]:
   threading.Thread(target=server.serve_forever,daemon=True).start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
  real_urlopen=urllib.request.urlopen
  def route(request,*args,**kwargs):
   if request.full_url.startswith('https://generativelanguage.googleapis.com/'):
    request=urllib.request.Request('http://127.0.0.1:'+str(self.upstream.server_port)+'/provider',data=request.data,headers={'Content-Type':'application/json'})
   return real_urlopen(request,*args,**kwargs)
  self.real_urlopen=real_urlopen
  for patcher in [patch.object(gate,'ROOT',self.root),patch.object(gate,'control',self.control),patch.object(gate,'time',SimpleNamespace(time=lambda:self.now,sleep=self.sleep)),patch.object(gate,'retry_delay',return_value=0),patch.object(gate.urllib.request,'urlopen',side_effect=route)]:
   patcher.start();self.addCleanup(patcher.stop)
 def control(self,active,action,request_id,details):
  if action=='reserve':
   if self.waiting:self.waiting=False;return {'state':'WAITING_FOR_QUOTA','retry_at':self.now+1}
   return {'state':'RESERVED'}
  self.settled.append(details)
  if details['http_status']==429:self.waiting=True
  return {'state':'SETTLED'}
 def sleep(self,seconds):
  self.now+=seconds
  if self.off_during_wait:
   d=json.loads((self.root/'active.json').read_text());d['active']=False;(self.root/'active.json').write_text(json.dumps(d))
 def post(self,model=gate.MODEL,declared=None):
  data=b'{"contents":[]}'
  headers={'x-goog-api-key':'synthetic-client-token-01234567890123456789','Content-Type':'application/json'}
  if declared is not None:headers['Content-Length']=str(declared)
  request=urllib.request.Request('http://127.0.0.1:'+str(self.server.server_port)+'/v1beta/models/'+model+':generateContent',data=data,headers=headers)
  try:response=self.real_urlopen(request,timeout=3)
  except urllib.error.HTTPError as error:response=error
  with response:return response.status,response.read()
 def test_429_waits_and_retries_once_then_returns_real_success(self):
  status,body=self.post();self.assertEqual(status,200);self.assertEqual(len(self.calls),2);self.assertEqual([d['http_status'] for d in self.settled],[429,200]);self.assertGreaterEqual(self.now-self.active['deadline']+450,1)
 def test_persistent_429_is_bounded_to_two_actual_requests(self):
  self.statuses=[429,429];status,body=self.post();self.assertEqual(status,429);self.assertEqual(len(self.calls),2)
 def test_owner_off_during_quota_wait_stops_second_request(self):
  self.off_during_wait=True;status,body=self.post();self.assertEqual(status,403);self.assertIn(b'ENGINEERING_PROVIDER_OFF',body);self.assertEqual(len(self.calls),1);self.assertEqual(len(self.settled),1)
 def test_invalid_model_or_huge_length_never_reads_body_or_reserves(self):
  for model,declared in [('other-model',None),(gate.MODEL,262145)]:
   status,body=self.post(model,declared);self.assertEqual(status,403)
  self.assertEqual(self.calls,[]);self.assertEqual(self.settled,[])
if __name__=='__main__':unittest.main()

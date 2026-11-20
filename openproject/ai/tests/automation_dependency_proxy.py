"""Clone-only dependency proxy: fixed Ollama routes and explicit HTTP-200 partial contract fixture."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT=Path('/qualification')
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,status,body):
        self.send_response(status);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
    def do_GET(self):self.forward()
    def do_POST(self):self.forward()
    def forward(self):
        if self.path=='/partial-daily':
            self.reply(200,json.dumps({'result':{'state':'COMPLETED','status':'PARTIAL','ready':4,'targets':5,'fixture':'HTTP_CONTRACT_ONLY'}}).encode());return
        if self.path not in {'/api/tags','/api/embed'}:self.reply(404,b'{}');return
        mode=(ROOT/'dependency-mode').read_text().strip()
        if mode=='offline':self.reply(503,b'{"error":"ISOLATED_OLLAMA_UNAVAILABLE"}');return
        if mode=='hold' and self.path=='/api/embed':time.sleep(60)
        length=int(self.headers.get('Content-Length','0'))
        if length>262144:self.reply(413,b'{}');return
        data=self.rfile.read(length) if self.command=='POST' else None
        try:
            request=urllib.request.Request('http://host.docker.internal:11434'+self.path,data=data,headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(request,timeout=90) as response:self.reply(response.status,response.read(4194304))
        except (OSError,urllib.error.URLError):
            try:self.reply(503,b'{"error":"ISOLATED_PROXY_FORWARD_FAILED"}')
            except OSError:pass
ThreadingHTTPServer(('0.0.0.0',11434),Handler).serve_forever()

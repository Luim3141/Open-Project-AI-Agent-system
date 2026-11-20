"""Existing runtime code, temporary Store, real read-only Native identity. No queue or Google call."""
import json
from pathlib import Path
from inspect_runtime import OUT, run

program = r'''
import hashlib,hmac,json,pathlib,tempfile,time,secrets
from unittest.mock import patch
from starlette.testclient import TestClient
from gateway.service import Service
from gateway.store import Store
from gateway.app import create_app
from gateway.gemini import Gemini
c=json.loads(pathlib.Path('/state/config.json').read_text());creds=json.loads(pathlib.Path('/state/credentials.json').read_text())
with tempfile.TemporaryDirectory() as folder:
 root=pathlib.Path(folder);store=Store(root);(root/'credentials.json').write_text(json.dumps(creds));(root/'ui.key').write_bytes(secrets.token_bytes(32))
 c['hosts']=['testserver'];service=Service(store,c,root/'workspaces');service.gemini=Gemini(pathlib.Path('/state'))
 native,identity=service.native_actor(19);parent=native.package(50)
 rows=native.packages();duplicates=[p['id'] for p in rows if p['subject'].casefold()=='test' and p.get('_links',{}).get('parent',{}).get('href')=='/api/v3/work_packages/50']
 payload={'actor':19,'project':5,'audience':'qldapm-ai-ui','at':int(time.time()),'nonce':secrets.token_hex(16),'operation':'command',
 'command':{'action':'start_ai_run','arguments':{'prompt':'Tạo 1 subtask mới tên là test cho task 50, giao cho QA, tự sử dụng các agent thích hợp để làm.',
 'engine':'gemini','allow_routine_writes':True,'write_scope_ids':[]},'idempotency_key':'incident-reproduction'}}
 body=json.dumps(payload).encode();signature=hmac.new((root/'ui.key').read_bytes(),body,hashlib.sha256).hexdigest()
 with patch.object(service,'start_dispatcher'),patch.object(Gemini,'sdk_client',side_effect=AssertionError('GOOGLE_FORBIDDEN')):
  response=TestClient(create_app(root,service)).post('/internal/ui',content=body,headers={'content-type':'application/json','X-Qldapm-Signature':signature})
 with store.connect() as db:count=db.execute('select count(*) from ai_runs').fetchone()[0]
 print(json.dumps({'identity':identity,'parent':{'id':parent['id'],'type':parent['_links']['type'],'native_create_link':parent['_links'].get('addChild')},
 'qa_user':service.role_assignee('QA'),'existing_test_child_ids':duplicates,'main_wp_count':len(rows),'method':'POST','endpoint':'/internal/ui','status':response.status_code,
 'response':response.json(),'temporary_runs_created':count,'native_business_mutations':0,'google_calls':0}))
'''
if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--after',action='store_true');args=parser.parse_args()
    result=json.loads(run('docker','exec','-i','qldapm-ai-gateway-1','python','-',data=program.encode()))
    (OUT/('runtime-after-admission.json' if args.after else 'runtime-reproduction.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

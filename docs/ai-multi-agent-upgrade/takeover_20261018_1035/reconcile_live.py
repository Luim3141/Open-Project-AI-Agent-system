"""Read original n8n history and runtime hashes; no workflow execution or enrollment."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote
from inspect_takeover import ROOT, OUT, run, save

sys.path.insert(0, str(ROOT/'openproject/ai'))
from n8n_status_workflow import LocalWorkflow

def main():
    private = Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
    owner = json.loads((private/'operator/n8n-owner/owner.json').read_text())
    client = LocalWorkflow('http://localhost:5678')
    client.request('/rest/login', {'emailOrLdapLoginId': owner['email'], 'password': owner['password']})
    listing = client._request('/rest/executions?filter='+quote(json.dumps({'workflowId':'qldapmDailyBrief'}))+'&limit=50')
    result = []
    for e in listing['results']:
        identifier = str(e['id'])
        doc = client.execution(identifier)
        data = doc['data']
        if isinstance(data, str):
            js="const r=require('module').createRequire('/usr/local/lib/node_modules/n8n/package.json');const d=r('flatted').parse(require('fs').readFileSync(0,'utf8'));const n=d.resultData.runData;const out={node_names:Object.keys(n),metadata:n['Command metadata']?.at(-1)?.data?.main?.[0]?.[0]?.json,receipt:n['Gateway status']?.at(-1)?.data?.main?.[0]?.[0]?.json};process.stdout.write(JSON.stringify(out))"
            safe = json.loads(run('docker','exec','-i','qldapm-ai-stage-n8n-1','node','-e',js,data=data))
        else:
            n=data['resultData']['runData']
            safe={'node_names':list(n), 'metadata':n.get('Command metadata',[{}])[-1].get('data',{}).get('main',[[{}]])[0][0].get('json'),
                  'receipt':n.get('Gateway status',[{}])[-1].get('data',{}).get('main',[[{}]])[0][0].get('json')}
        metadata = safe.get('metadata') or {}
        receipt = safe.get('receipt') or {}
        result.append({**{k:doc.get(k) for k in ['id','mode','status','startedAt','stoppedAt','workflowId']},
                       'trigger_nodes':[x for x in safe['node_names'] if x in ['Daily 09:00','After startup','Manual status']],
                       'request_key':metadata.get('request_key'), 'issued_at':metadata.get('issued_at'),
                       'gateway_result':{k:(receipt.get('result') or {}).get(k) for k in ['run_id','request_key','state','ready','model_calls','status']},
                       'created_response':receipt.get('created', (receipt.get('result') or {}).get('created'))})
    save('n8n-history.json',result)
    workflows=[]
    for wid in ['qldapmManualStatus','qldapmDailyBrief','qldapmWorkflowErrors']:
        client.workflow_id=wid
        w=client.workflow()
        workflows.append({'id':wid,'active':w.get('active'),'versionId':w.get('versionId'), 'activeVersionId':w.get('activeVersionId'),
                          'settings':w.get('settings'), 'nodes':[{'name':x['name'],'type':x['type']} for x in w['nodes']]})
    save('n8n-workflows.json', workflows)
    # Hash only application overlay code inside running Core, never credentials or environment values.
    ruby="require 'json';require 'digest';a=Dir['/app/app/{controllers,views,services,models,helpers}/**/*qldapm*','/app/app/views/qldapm_ai/**/*','/app/app/controllers/qldapm_ai_controller.rb','/app/lib/api/v3/qldapm/gates_api.rb'].select{|p|File.file?(p)};puts JSON.generate(a.to_h{|p|[p.delete_prefix('/app/'),Digest::SHA256.file(p).hexdigest]})"
    hashes=json.loads(run('docker','exec','qldapm-ai-stage-staging-web-1','ruby','-e',ruby))
    local={str(p.relative_to(ROOT/'openproject/ai/core/overlay')).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'openproject/ai/core/overlay').rglob('*') if p.is_file()}
    save('core-parity.json', {'runtime_hashes':hashes,'different':[k for k,v in hashes.items() if k in local and local[k]!=v],
                             'control_center_runtime_present':'app/views/qldapm_ai/_control_center.html.erb' in hashes})
    logs = run('docker','logs','--since','2026-10-17T22:19:00Z','--tail','250','qldapm-ai-stage-quick-tunnel-1')
    # docker logs normally emits stderr; separately capture allowed supervisor lines only.
    p=subprocess.run(['docker','logs','--since','2026-10-17T22:19:00Z','qldapm-ai-stage-quick-tunnel-1'],capture_output=True,text=True,encoding='utf-8',timeout=30)
    lines=[line for line in (p.stdout+p.stderr).splitlines() if 'Supervisor' in line or 'trycloudflare.com' in line]
    (OUT/'quick-tunnel-events.log').write_text('\n'.join(lines),encoding='utf-8')
    a=(private/'secrets/staging_totp_secrets.json')
    creds=json.loads(a.read_text())
    save('credentials-shape.json', {'accounts':{k:{'fields':sorted(v),'has_password':bool(v.get('pass')),'has_totp':bool(v.get('totp_secret'))} for k,v in creds.items() if isinstance(v,dict)}})
    print(json.dumps({'executions':len(result),'core_control_center': 'app/views/qldapm_ai/_control_center.html.erb' in hashes,'core_different':[k for k,v in hashes.items() if k in local and local[k]!=v]}))

if __name__=='__main__': main()

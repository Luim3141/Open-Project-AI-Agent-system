"""Arm exact Owner request only; no Google request or business write. Refuses any repeat."""
import hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.native import Native
from gateway.store import digest

PROMPT="Tạo đúng một Subtask mới tên 'test' thuộc Work Package #50 trong Project 5, giao cho QA qa-tester (User ID 23). Trước khi thực hiện phải kiểm tra Subtask trùng, quyền Native và giới hạn parent. Tôi đã phê duyệt chính xác thao tác này. Hãy sử dụng Business Tools hiện có để thực thi, không thay đổi các công việc khác. Sau khi thực thi, đọc lại Subtask từ Native API và báo ID, parent, assignee, trạng thái."

def main():
    assert not (OUT/'armed.json').exists(),'ALREADY_ARMED_RECONCILE_NO_RETRY'
    deployed=json.loads((OUT/'deployment.json').read_text());assert deployed['phase']=='MAIN_GATEWAY_DEPLOYED_HEALTH_PARITY_PASS'
    state=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway'
    assert not (state/'business-acceptance.json').exists()
    n=Native('http://localhost:8088',json.loads((state/'credentials.json').read_text())['19'],5)
    assert n.identity(19)['role']=='PM'
    assert not any(' '.join(p['subject'].split()).casefold()=='test' and p.get('_links',{}).get('parent',{}).get('href')=='/api/v3/work_packages/50' for p in n.packages()),'DUPLICATE_STOP'
    code="""from gateway.gemini import Gemini;from pathlib import Path;import sqlite3,json
g=Gemini(Path('/state'));p=g.settings();assert p['model']=='gemini-3.5-flash-lite' and p['tier']=='Free' and p['billing_enabled'] is False
assert g.readiness(p)['state']=='READY'
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
assert d.execute("select count(*) from ai_runs where state in ('running','queued')").fetchone()[0]==0
assert d.execute("select count(*) from requests where state!='done'").fetchone()[0]==0
print(json.dumps({'runs':d.execute('select count(*) from ai_runs').fetchone()[0],'receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0],'usage':d.execute('select count(*) from gemini_usage').fetchone()[0]}));d.close()"""
    p=subprocess.run(['docker','exec','qldapm-ai-gateway-1','python','-c',code],capture_output=True,timeout=30)
    assert p.returncode==0,'NOT_READY_NO_LIVE_REQUEST';baseline=json.loads(p.stdout)
    consent={'id':str(uuid.uuid4()),'actor':19,'project':5,'prompt_sha256':digest(PROMPT),'scope':[50],
        'create':{'subject':'test','type_id':10,'parent_id':50,'assignee_id':23},'expires':time.time()+900}
    with (state/'business-acceptance.json').open('x',encoding='utf-8') as f:json.dump(consent,f,ensure_ascii=False)
    receipt={'consent':consent,'baseline':baseline,'prompt':PROMPT,'at':time.time(),
        'owner_request_sha256':hashlib.sha256(Path(r'C:\Users\LUIM\.codex\attachments\b7741b80-a076-4d82-af7c-a798f1d0eddb\Pasted text.txt').read_bytes()).hexdigest(),
        'instruction':'ONE_UI_REQUEST_ONLY_NO_AUTOMATIC_REPLAY'}
    (OUT/'armed.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()

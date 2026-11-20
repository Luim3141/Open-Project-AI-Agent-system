"""Real Gemini/tool feedback, real Gateway reads; no Telegram sends or business mutations."""
import asyncio,json,sqlite3,tempfile,time
from pathlib import Path
from app.config import Settings
from app.engine import Commander,GeminiBrain
from app.gateway import GatewayClient
from app.storage import Repository
from app.tools import ToolExecutor,WRITES

async def main():
    s=Settings.from_env();production=Repository(s.db_path);gateway=GatewayClient(s);brain=GeminiBrain(s,production)
    real_generate=brain.generate;calls=0
    async def bounded(*args):
        nonlocal calls
        if calls>=10:raise ValueError('AUDIT_INFERENCE_BOUND')
        calls+=1;return await real_generate(*args)
    brain.generate=bounded
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'conversation.sqlite'
        with sqlite3.connect(s.db_path.as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(path) as target:source.backup(target)
        repo=Repository(path)
        class ReadsOnly(ToolExecutor):
            async def execute(self,name,args,*scope):
                if name in WRITES:raise PermissionError('AUDIT_READS_ONLY')
                return await super().execute(name,args,*scope)
        tools=ReadsOnly(gateway,repo,s);commander=Commander(s,repo,tools,brain)
        cases=[('TG-R01','QLDAPM đang hoạt động bình thường không? Gọi get_system_health để kiểm tra mới.'),('TG-R06','Agent nào đang chạy?'),('TG-R07','Có Task nào đang BLOCKED không?'),('TG-R08','BA đã phân tích những gì ở Task #379?'),('TG-R09','Xem GitHub PR của Task #398 và trạng thái OPEN hay MERGED.'),('TG-R10','Task nào đang chờ tôi phê duyệt?')]
        report={'scope':'REAL GEMINI SDK + REAL Gateway/Native; isolated conversation; live shared budget/audit; no Telegram transport','at':time.time(),'cases':[]}
        for identifier,question in cases:
            if calls>=10:break
            if identifier in ['TG-R01','TG-R06','TG-R07','TG-R10']:repo.save_memory(1916909968,1916909968,{'current_project_id':6,'recent_messages':[]})
            started=time.time();answer=await commander.answer(1916909968,1916909968,question,6)
            with repo.connect() as db:
                audit=[json.loads(row[0]) for row in db.execute('SELECT document FROM command_audit WHERE created>=? ORDER BY created',(started,))]
            with production.connect() as db:receipts=[json.loads(row[0]) for row in db.execute('SELECT document FROM command_audit WHERE user_id=0 AND created>=? ORDER BY created',(started,))]
            report['cases'].append({'id':identifier,'question':question,'answer':answer,'read_tools':[x for x in audit if x.get('event')=='READ_TOOL'],'gemini_receipts':receipts,'seconds':time.time()-started})
        report['generate_rounds']=calls;await brain.close();await gateway.close();return report
if __name__=='__main__':print(json.dumps(asyncio.run(main()),ensure_ascii=False))

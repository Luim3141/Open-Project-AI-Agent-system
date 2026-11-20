"""Retry the actual received read question after deployment maintenance; never replay writes."""
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
target = OUT / 'real-reply-context.json'
assert not target.exists(), 'EXISTING_REPLY_RECEIPT_PRESERVED'
code = '''import asyncio,json
from aiogram import Bot
from app.config import Settings
from app.storage import Repository
from app.gateway import GatewayClient
from app.tools import ToolExecutor
from app.engine import GeminiBrain,Commander
async def main():
 s=Settings.from_env();r=Repository(s.db_path);user=1916909968
 m=r.memory(user,user);q=next(v['text'] for v in reversed(m['recent_messages']) if v['role']=='user')
 assert q.rstrip('? .').casefold()=='dev đã làm gì ở task này', 'EXACT_RECEIVED_READ_ONLY_QUESTION_REQUIRED'
 context=r.notification_context(user,8)
 assert context and context['task_id']==391 and context['project_id']==6, 'ACTUAL_DELIVERY_REPLY_CONTEXT_REQUIRED'
 g=GatewayClient(s);b=GeminiBrain(s,r)
 try:
  result=await Commander(s,r,ToolExecutor(g,r,s),b).answer(user,user,q,6,reply_context=context)
  assert not result.get('confirmation_id'), 'NO_WRITE_CONFIRMATION_EXPECTED'
  assert 'chưa xác minh được trạng thái này từ hệ thống' not in result['text'], 'CURRENT_READ_FAILED'
  async with Bot(s.bot_token) as bot:
   msg=await bot.send_message(user,'Đã đọc lại câu hỏi sau khi Gateway hết maintenance:\\n\\n'+result['text'])
  r.audit(user,user,{'event':'RECEIVED_READ_RETRIED_AFTER_MAINTENANCE','task_id':391,'project_id':6,'message_id':msg.message_id,'source_notification_message_id':8})
  print(json.dumps({'status':'SENT','message_id':msg.message_id,'source_notification_message_id':8,'context':context,'text':result['text'],'route':'EXACT_RECEIVED_READ_RETRY_AFTER_503_MAINTENANCE'},ensure_ascii=False))
 finally:await g.close();await b.close()
asyncio.run(main())
'''
result = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-telegram-ai-1', 'python', '-'],
    input=code, text=True, capture_output=True, timeout=150)
assert result.returncode == 0, 'RECEIVED_READ_RETRY_FAILED'
data = json.loads(result.stdout)
target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: data[k] for k in ('status', 'message_id', 'source_notification_message_id', 'route')}))

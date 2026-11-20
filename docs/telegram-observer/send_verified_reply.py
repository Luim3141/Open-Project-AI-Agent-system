"""Deliver the owner's retried read-only question once; persist an actual Telegram receipt."""
import json
from pathlib import Path
import subprocess

out = Path(__file__).resolve().parent
receipt = out / 'commander-reply-delivery.json'
if receipt.exists():
    raise RuntimeError('EXISTING_DELIVERY_RECEIPT_PRESERVED')
answer = json.loads((out / 'commander-real-response.json').read_text(encoding='utf-8'))
assert answer['task_id'] == 391 and answer['project_id'] == 6
assert 'AWAITING_OWNER_APPROVAL' in answer['text']
payload = {'text': 'Kết quả kiểm tra lại câu hỏi của bạn sau cập nhật:\n\n' + answer['text'] +
    '\n\nLưu ý: đây là bằng chứng của lượt chạy đã lưu; telemetry lịch sử đang STALE. '
    'COMPLETED của runtime chưa phải Task đã được Owner nghiệm thu.', 'user_id': 1916909968}
code = """import asyncio,json,sys
from aiogram import Bot
from app.config import Settings
from app.storage import Repository
async def main():
 p=json.load(sys.stdin);s=Settings.from_env();r=Repository(s.db_path)
 assert r.authorize(p['user_id'],p['user_id']), 'CURRENT_PAIRING_REQUIRED'
 async with Bot(s.bot_token) as bot:
  m=await bot.send_message(p['user_id'],p['text'])
  r.audit(p['user_id'],p['user_id'],{'event':'OPERATOR_READ_REPLY_DELIVERED','message_id':m.message_id,'task_id':391,'project_id':6})
  print(json.dumps({'status':'SENT','message_id':m.message_id,'task_id':391,'project_id':6,'route':'OPERATOR_RETRY_OF_ACTUAL_OWNER_QUESTION'}))
asyncio.run(main())
"""
result = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-telegram-ai-1', 'python', '-c', code],
    input=json.dumps(payload), text=True, capture_output=True, timeout=60)
if result.returncode:
    raise RuntimeError('TELEGRAM_REPLY_DELIVERY_FAILED')
data = json.loads(result.stdout)
receipt.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
print(json.dumps(data))

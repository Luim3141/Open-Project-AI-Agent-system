"""Paired-recipient outbox. n8n owns outgoing Telegram delivery, never agent execution."""
import asyncio
import hashlib
import html
import hmac
import json
import logging
import math
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

TYPES = {'TASK_COMPLETED', 'TASK_BLOCKED', 'AGENT_FAILED', 'QA_FAILED', 'AWAITING_APPROVAL', 'PR_CREATED', 'DELIVERY_TEST'}
LABELS = {'TASK_COMPLETED': 'TASK HOÀN THÀNH — các gate đã được xác minh',
          'TASK_BLOCKED': 'TASK BỊ CHẶN', 'AGENT_FAILED': 'AGENT THẤT BẠI',
          'QA_FAILED': 'QA THẤT BẠI', 'AWAITING_APPROVAL': 'CHỜ CHỦ SỞ HỮU DUYỆT', 'PR_CREATED': 'ĐÃ TẠO PR',
          'DELIVERY_TEST':'KIỂM THỬ KÊNH THÔNG BÁO — không thay đổi Task hoặc xác nhận nghiệm thu'}
log = logging.getLogger(__name__)


class Outbox:
    def __init__(self, repo):
        self.repo = repo
        with repo.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS telegram_notification_outbox('
                       'id TEXT PRIMARY KEY,event_id TEXT NOT NULL,user_id INTEGER NOT NULL,chat_id INTEGER NOT NULL,'
                       'payload TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,'
                       'next_at REAL NOT NULL DEFAULT 0,lease TEXT,lease_until REAL NOT NULL DEFAULT 0,'
                'created_at REAL NOT NULL,sent_at REAL,message_id INTEGER,error TEXT,authorized INTEGER NOT NULL DEFAULT 0,UNIQUE(event_id,chat_id))')
            if 'authorized' not in {row[1] for row in db.execute('PRAGMA table_info(telegram_notification_outbox)')}:
                db.execute('ALTER TABLE telegram_notification_outbox ADD COLUMN authorized INTEGER NOT NULL DEFAULT 0')
            db.execute('CREATE INDEX IF NOT EXISTS telegram_notification_due ON telegram_notification_outbox(status,next_at)')

    @staticmethod
    def permitted(person, event):
        return (person.get('notifications') is True and type(person.get('user_id')) is int
                and person.get('user_id', 0) > 0 and person.get('chat_id') == person['user_id']
                and event['project_id'] in person.get('project_ids', [])
                and event['event_type'] in person.get('notification_types', TYPES))

    def enqueue(self, event, person, *, now=None):
        now = time.time() if now is None else now
        required = {'event_id', 'event_type', 'task_id', 'project_id', 'workflow_run_id', 'source_record_id', 'timestamp'}
        if (not isinstance(event, dict) or not required <= set(event) or set(event)-required-{'uri'}
                or event.get('event_type') not in TYPES
                or any(type(event.get(k)) is not int or event[k] <= 0 for k in ('task_id', 'project_id'))
                or any(not isinstance(event.get(k), str) or not 1 <= len(event[k]) <= 2048 for k in ('event_id', 'source_record_id'))
                or type(event.get('timestamp')) not in (int, float) or not math.isfinite(event['timestamp'])
                or event['timestamp'] > now + 30
                or (event.get('workflow_run_id') is not None and (not isinstance(event['workflow_run_id'], str) or len(event['workflow_run_id']) > 128))):
            raise ValueError('NOTIFICATION_EVENT_INVALID')
        if 'uri' in event:
            parsed = urlsplit(event['uri'])
            if parsed.scheme != 'https' or parsed.hostname != 'github.com' or parsed.username or parsed.password:
                raise ValueError('NOTIFICATION_ARTIFACT_DENIED')
        if not self.permitted(person, event) or event['timestamp'] < person.get('paired_at', now): return False
        identifier = hashlib.sha256(f"{event['event_id']}:{person['chat_id']}".encode()).hexdigest()
        with self.repo.connect() as db:
            return bool(db.execute('INSERT OR IGNORE INTO telegram_notification_outbox('
                'id,event_id,user_id,chat_id,payload,status,created_at) VALUES(?,?,?,?,?,\'PENDING\',?)',
                (identifier, event['event_id'], person['user_id'], person['chat_id'],
                 json.dumps(event, sort_keys=True, separators=(',', ':')), now)).rowcount)

    def _recipient(self, row):
        event = json.loads(row['payload'])
        return next((p for p in self.repo.recipients() if p['user_id'] == row['user_id']
                     and p['chat_id'] == row['chat_id'] and self.permitted(p, event)), None)

    def claim(self, *, now=None):
        now = time.time() if now is None else now
        with self.repo.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute("SELECT * FROM telegram_notification_outbox WHERE status IN ('PENDING','RETRY','PROCESSING') "
                              'AND next_at<=? AND lease_until<=? ORDER BY created_at,id LIMIT 20', (now, now)).fetchall()
            for row in rows:
                if self._recipient(row) is None:
                    db.execute("UPDATE telegram_notification_outbox SET status='CANCELLED' WHERE id=?", (row['id'],)); continue
                if row['attempts'] >= 6:
                    db.execute("UPDATE telegram_notification_outbox SET status='FAILED',error='DELIVERY_ATTEMPTS_EXHAUSTED' WHERE id=?", (row['id'],)); continue
                lease = uuid.uuid4().hex
                db.execute("UPDATE telegram_notification_outbox SET status='PROCESSING',attempts=attempts+1,authorized=0,lease=?,lease_until=? WHERE id=?",
                           (lease, now+180, row['id']))
                return {'notification_id': row['id'], 'event_id': row['event_id'], 'lease': lease}
        return None

    def _row(self, identifier, lease, now):
        with self.repo.connect() as db:
            row = db.execute('SELECT * FROM telegram_notification_outbox WHERE id=?', (identifier,)).fetchone()
        if (not row or not isinstance(lease, str) or not hmac.compare_digest(row['lease'] or '', lease)
                or row['status'] not in {'PROCESSING', 'SENT'}
                or (row['status'] != 'SENT' and row['lease_until'] <= now) or self._recipient(row) is None):
            raise PermissionError('NOTIFICATION_LEASE_OR_RECIPIENT_DENIED')
        return row

    def validate(self, identifier, lease, *, now=None):
        now = time.time() if now is None else now
        row = self._row(identifier, lease, now)
        if row['status'] == 'SENT': raise PermissionError('NOTIFICATION_ALREADY_SENT')
        with self.repo.connect() as db:
            changed = db.execute("UPDATE telegram_notification_outbox SET authorized=1 WHERE id=? AND lease=? AND authorized=0 AND status='PROCESSING' AND lease_until>?",
                                 (identifier, lease, now)).rowcount
        if not changed: raise PermissionError('NOTIFICATION_SEND_ALREADY_AUTHORIZED')
        event = json.loads(row['payload'])
        text = f"QLDAPM — {LABELS[event['event_type']]}\n\nProject #{event['project_id']}\nTask #{event['task_id']}"
        if event.get('workflow_run_id'): text += '\nRun: '+event['workflow_run_id']
        text += '\nEvidence: '+event['source_record_id'][:400]
        if event.get('uri'): text += '\nPR: '+event['uri']
        text += '\n\nBạn có thể trả lời thông báo này để hỏi tiến độ Task.'
        return {'notification_id': identifier, 'event_id': event['event_id'], 'lease': lease,
                'chat_id': row['chat_id'], 'text': html.escape(text)}

    def ack(self, identifier, lease, message_id, chat_id, *, now=None):
        now = time.time() if now is None else now
        if type(message_id) is not int or message_id <= 0: raise ValueError('TELEGRAM_MESSAGE_ID_REQUIRED')
        row = self._row(identifier, lease, now)
        if not row['authorized']: raise PermissionError('NOTIFICATION_SEND_NOT_AUTHORIZED')
        if type(chat_id) is not int or chat_id != row['chat_id']: raise PermissionError('NOTIFICATION_CHAT_DENIED')
        if row['status'] == 'SENT' and row['message_id'] != message_id: raise PermissionError('NOTIFICATION_ACK_CHANGED')
        event = json.loads(row['payload'])
        self.repo.record_notification(chat_id, message_id, event['task_id'], event['project_id'], event.get('workflow_run_id'))
        with self.repo.connect() as db:
            db.execute("UPDATE telegram_notification_outbox SET status='SENT',message_id=?,sent_at=?,error=NULL WHERE id=? AND lease=?",
                       (message_id, now, identifier, lease))
        return {'status': 'SENT', 'notification_id': identifier, 'telegram_message_id': message_id}

    def fail(self, identifier, lease, *, now=None):
        now = time.time() if now is None else now
        with self.repo.connect() as db:
            db.execute("UPDATE telegram_notification_outbox SET status=CASE WHEN attempts>=6 THEN 'FAILED' ELSE 'RETRY' END,"
                       "next_at=?+MIN(300,1<<attempts),lease=NULL,lease_until=0,error='N8N_DELIVERY_UNCONFIRMED' "
                       "WHERE id=? AND lease=? AND status='PROCESSING'", (now, identifier, lease))

    def status(self):
        with self.repo.connect() as db:
            return dict(db.execute('SELECT status,count(*) FROM telegram_notification_outbox GROUP BY status').fetchall())


def create_app(repo, settings, gateway):
    from aiohttp import ClientSession, ClientTimeout, web
    outbox = Outbox(repo)
    app = web.Application(client_max_size=4096)
    task_key = web.AppKey('notification_task', asyncio.Task)

    def secret():
        try: value = Path(settings.internal_secret_file).read_text(encoding='utf-8').strip()
        except (OSError, TypeError, AttributeError): return ''
        return value if 32 <= len(value) <= 512 and '\n' not in value and '\r' not in value else ''

    async def endpoint(request):
        key = secret()
        if not key or not hmac.compare_digest(request.headers.get('X-QLDAPM-Notification-Key', ''), key):
            return web.json_response({'error': 'NOTIFICATION_AUTH_DENIED'}, status=403)
        try:
            body = await request.json()
            allowed = {'notification_id', 'lease'} | ({'message_id', 'chat_id'} if request.path.endswith('/ack') else set())
            if not isinstance(body, dict) or set(body) != allowed: raise ValueError()
            if request.path.endswith('/ack'):
                result = outbox.ack(body['notification_id'], body['lease'], body['message_id'], body['chat_id'])
            else:
                row = outbox._row(body['notification_id'], body['lease'], time.time())
                event = json.loads(row['payload'])
                snapshot = await gateway.command('observer_task_progress', {'task_id': event['task_id']}, event['project_id'])
                if (snapshot.get('task_id') != event['task_id'] or snapshot.get('project_id') != event['project_id']
                        or event['event_type'] == 'TASK_COMPLETED' and snapshot.get('acceptance_status') != 'COMPLETED'):
                    raise PermissionError('NOTIFICATION_CURRENT_NATIVE_SCOPE_OR_ACCEPTANCE_DENIED')
                result = outbox.validate(body['notification_id'], body['lease'])
            return web.json_response(result)
        except (ValueError, TypeError, KeyError, PermissionError):
            return web.json_response({'error': 'NOTIFICATION_REQUEST_DENIED'}, status=403)

    app.router.add_post('/internal/notifications/validate', endpoint)
    app.router.add_post('/internal/notifications/ack', endpoint)

    async def reconcile():
        people = repo.recipients()
        projects = sorted({p for person in people if person.get('notifications') for p in person.get('project_ids', [])})
        for project in projects:
            try:page = await gateway.command('observer_active', {'limit': 50}, project)
            except asyncio.CancelledError:raise
            except Exception:
                log.warning('NOTIFICATION_PROJECT_UNAVAILABLE project=%s',project);continue
            page = page.get('result', page)
            tasks = page.get('tasks', page.get('items', [])) if isinstance(page, dict) else page
            if isinstance(page, dict) and page.get('truncated'): log.warning('NOTIFICATION_OBSERVER_PAGE_TRUNCATED')
            for task in (tasks or [])[:50]:
                task_id = task.get('task_id') if isinstance(task, dict) else None
                if type(task_id) is not int: continue
                document = task
                if 'notification_events' not in document:
                    document = await gateway.command('observer_task_progress', {'task_id': task_id}, project)
                    document = document.get('result', document)
                for event in document.get('notification_events', []):
                    for person in people: outbox.enqueue(event, person)

    async def dispatch():
        url = getattr(settings, 'n8n_webhook_url', '')
        key = secret()
        if not url or not key: return
        parsed = urlsplit(url)
        if (parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password
                or parsed.path != '/webhook/qldapm-telegram-agent-notifications' or parsed.query or parsed.fragment):
            raise ValueError('NOTIFICATION_WEBHOOK_CONFIG_INVALID')
        delivery = outbox.claim()
        if not delivery: return
        headers = {'X-QLDAPM-Notification-Key': key}
        webhook_secret = getattr(settings, 'notification_webhook_secret_file', None)
        if webhook_secret:
            value = Path(webhook_secret).read_text(encoding='utf-8').strip()
            if not value or len(value) > 512 or '\n' in value or '\r' in value: raise ValueError('N8N_WEBHOOK_SECRET_INVALID')
            headers['X-QLDAPM-Webhook-Token'] = value
        try:
            async with ClientSession(timeout=ClientTimeout(total=30), trust_env=False) as client:
                async with client.post(url, json={'notification_id': delivery['notification_id'], 'lease': delivery['lease']},
                                       headers=headers, allow_redirects=False) as response:
                    if response.status != 200: raise ValueError('N8N_DELIVERY_FAILED')
                    raw = await response.content.read(4097)
                    if len(raw) > 4096: raise ValueError('N8N_ACK_TOO_LARGE')
                    ack = json.loads(raw)
                    if ack.get('status') != 'SENT' or ack.get('notification_id') != delivery['notification_id']:
                        raise ValueError('N8N_BUSINESS_ACK_REQUIRED')
        except Exception:
            # Telegram may have received a message before a response was lost: delivery is at-least-once.
            outbox.fail(delivery['notification_id'], delivery['lease'])

    async def loop():
        while True:
            try:
                if getattr(settings, 'notifications_enabled', True):
                    await reconcile(); await dispatch()
            except asyncio.CancelledError: raise
            except Exception: log.warning('NOTIFICATION_RECONCILIATION_UNAVAILABLE')
            await asyncio.sleep(max(10, min(300, getattr(settings, 'notification_poll_seconds', 30))))

    async def startup(application): application[task_key] = asyncio.create_task(loop())

    async def cleanup(application):
        task = application[task_key]; task.cancel()
        try: await task
        except asyncio.CancelledError: pass

    app.on_startup.append(startup); app.on_cleanup.append(cleanup)
    return app

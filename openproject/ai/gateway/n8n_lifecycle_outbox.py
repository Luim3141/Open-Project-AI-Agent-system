"""Project6 metadata observation only; the existing Gateway worker owns dispatch."""
import asyncio
import hashlib
import hmac
import json
import time
import uuid
from urllib.parse import urlsplit

import httpx

from .store import canonical

PATH = '/internal/automation/lifecycle-observation'
EVENTS = {'REQUEST_RECEIVED', 'PLAN_CREATED', 'AGENT_ASSIGNED', 'AGENT_STARTED',
          'AGENT_COMPLETED', 'AGENT_FAILED', 'REVIEW_COMPLETED', 'RUN_COMPLETED', 'RUN_FAILED'}


def ensure_schema(db):
    # No executescript: it would commit the caller's lifecycle transaction early.
    db.execute('CREATE TABLE IF NOT EXISTS n8n_lifecycle_outbox(event_id TEXT PRIMARY KEY,actor INTEGER NOT NULL,document TEXT NOT NULL,state TEXT NOT NULL DEFAULT \'PENDING\',attempts INTEGER NOT NULL DEFAULT 0,next_at REAL NOT NULL DEFAULT 0,lease TEXT,lease_until REAL NOT NULL DEFAULT 0,error TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS n8n_lifecycle_observations(event_id TEXT PRIMARY KEY,document TEXT NOT NULL,observed_at REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS n8n_lifecycle_execution_metadata(event_id TEXT PRIMARY KEY,execution_id TEXT NOT NULL,observed_at REAL NOT NULL)')


def enqueue(db, scope, event):
    if scope.project_id != 6 or event.event_type not in EVENTS:
        return
    ensure_schema(db)
    payload = {'schema_version': 1, 'event_id': event.event_id, 'event_type': event.event_type,
               'run_id': event.run_id, 'project_id': 6, 'work_package_id': None, 'unit_id': None,
               'timestamp': event.timestamp, 'correlation_id': event.trace_id,
               'status': event.status, 'agent_id': event.agent_id}
    row=db.execute('SELECT payload FROM ai_queue WHERE id=? AND actor=?',(event.run_id,scope.actor_id)).fetchone()
    contract=json.loads(row[0]) if row else {}
    if contract.get('project_id')==6 and type(contract.get('native_id')) is int:
        payload['work_package_id']=contract['native_id']
    if event.error_code:payload['error_code']=event.error_code
    db.execute('INSERT OR IGNORE INTO n8n_lifecycle_outbox(event_id,actor,document) VALUES(?,?,?)',
               (event.event_id, scope.actor_id, canonical(payload)))


def sign_envelope(event, key):
    envelope = {'event': event, 'published_at': int(time.time())}
    envelope['signature'] = hmac.new(key.encode('ascii'), canonical(envelope).encode(), hashlib.sha256).hexdigest()
    return envelope


def observe(store, envelope, key, execution_id=None):
    if not isinstance(envelope, dict) or set(envelope) != {'event', 'published_at', 'signature'}:
        raise PermissionError('LIFECYCLE_ENVELOPE_DENIED')
    unsigned = {k: envelope[k] for k in ('event', 'published_at')}
    signature = hmac.new(key.encode('ascii'), canonical(unsigned).encode(), hashlib.sha256).hexdigest()
    if (not isinstance(envelope['signature'], str) or not hmac.compare_digest(signature, envelope['signature'])
            or type(envelope['published_at']) is not int or not -15 <= time.time()-envelope['published_at'] <= 60):
        raise PermissionError('LIFECYCLE_SIGNATURE_OR_EXPIRY_DENIED')
    event = envelope['event']
    if not isinstance(event, dict) or event.get('project_id') != 6:
        raise PermissionError('LIFECYCLE_SCOPE_DENIED')
    if execution_id is not None and (not isinstance(execution_id, str) or not execution_id.isascii() or not execution_id.isdigit() or len(execution_id) > 20):
        raise PermissionError('LIFECYCLE_EXECUTION_ID_DENIED')
    with store.connect() as db:
        ensure_schema(db)
        row = db.execute('SELECT actor,document FROM n8n_lifecycle_outbox WHERE event_id=?', (event.get('event_id'),)).fetchone()
        if not row or row['document'] != canonical(event):
            raise PermissionError('LIFECYCLE_SOURCE_DENIED')
        source = db.execute('SELECT document FROM execution_events WHERE event_id=? AND actor=? AND project=6 AND run_id=?',
                            (event['event_id'], row['actor'], event['run_id'])).fetchone()
        if not source:
            raise PermissionError('LIFECYCLE_TRACE_DENIED')
        # Retrieve the actual source trace, never caller-provided status or an engine-green verdict.
        trace = json.loads(source['document'])
        ack = {'status': 'OBSERVED', 'event_id': event['event_id'], 'run_id': event['run_id'],
               'project_id': 6, 'correlation_id': event['correlation_id'], 'trace_event_id': trace['event_id']}
        db.execute('INSERT OR IGNORE INTO n8n_lifecycle_observations VALUES(?,?,?)', (event['event_id'], canonical(ack), time.time()))
        if execution_id is not None:
            db.execute('INSERT OR IGNORE INTO n8n_lifecycle_execution_metadata VALUES(?,?,?)', (event['event_id'], execution_id, time.time()))
        return json.loads(db.execute('SELECT document FROM n8n_lifecycle_observations WHERE event_id=?', (event['event_id'],)).fetchone()[0])


def http_transport(url, envelope, timeout, *, headers=None):
    async def request():
        try:
            # Includes connect/headers/body; drip-fed headers must not reset the deadline.
            async with asyncio.timeout(timeout):
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, trust_env=False) as client:
                    async with client.stream('POST', url, json=envelope, headers=headers) as response:
                        response.raise_for_status()
                        content = bytearray()
                        async for chunk in response.aiter_bytes():
                            if len(content) + len(chunk) > 8192:
                                raise ValueError('ACK_TOO_LARGE')
                            content.extend(chunk)
                        return json.loads(content)
        except TimeoutError:
            raise TimeoutError('ACK_DEADLINE') from None
    # Called by the existing synchronous background worker, never the ASGI request loop.
    return asyncio.run(request())


def deliver_pending(store, config, *, transport=http_transport, now=None):
    if config.get('enabled') is not True:
        return 'DISABLED'
    url, key = config.get('webhook_url', ''), config.get('signing_key', '')
    parsed = urlsplit(url)
    if (parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path != '/webhook/qldapm-lifecycle'
            or len(key) != 64 or any(c not in '0123456789abcdef' for c in key)):
        raise ValueError('LIFECYCLE_CONFIG_INVALID')
    headers=None
    if config.get('authenticated_webhook') is True:
        try:
            secret=json.loads((store.root/'webhook_secret.json').read_text())
            token=secret.get('webhook_token') or secret.get('secret')
            if not isinstance(token,str) or not 16<=len(token)<=512 or any(c in token for c in '\r\n'):raise ValueError()
            headers={'X-QLDAPM-Webhook-Token':token}
        except (OSError,ValueError,TypeError):raise ValueError('LIFECYCLE_WEBHOOK_CREDENTIAL_UNAVAILABLE') from None
    now = time.time() if now is None else now
    lease = str(uuid.uuid4())
    with store.connect() as db:
        ensure_schema(db)
        db.execute('BEGIN IMMEDIATE')
        row = db.execute("SELECT * FROM n8n_lifecycle_outbox WHERE state IN ('PENDING','RETRY','SENDING') AND next_at<=? AND lease_until<=? ORDER BY rowid LIMIT 1", (now, now)).fetchone()
        if not row:
            return 'IDLE'
        db.execute("UPDATE n8n_lifecycle_outbox SET state='SENDING',lease=?,lease_until=?,attempts=attempts+1 WHERE event_id=?", (lease, now+30, row['event_id']))
    event = json.loads(row['document'])
    state, error = 'ACKED', None
    try:
        envelope=sign_envelope(event,key)
        ack = transport(url,envelope,3.0,headers=headers) if headers else transport(url,envelope,3.0)
        expected = {'status': 'OBSERVED', 'event_id': event['event_id'], 'run_id': event['run_id'],
                    'project_id': 6, 'correlation_id': event['correlation_id'], 'trace_event_id': event['event_id']}
        if ack != expected:
            raise ValueError('BUSINESS_ACK_REQUIRED')
    except Exception:
        # Persist a fixed code, never remote response bodies, URLs, headers or exception text.
        state = 'DEAD' if row['attempts']+1 >= 5 else 'RETRY'
        error = 'LIFECYCLE_DELIVERY_FAILED'
    with store.connect() as db:
        db.execute('UPDATE n8n_lifecycle_outbox SET state=?,error=?,next_at=?,lease=NULL,lease_until=0 WHERE event_id=? AND lease=?',
                   (state, error, now+min(300, 2**(row['attempts']+1)), event['event_id'], lease))
    return state


def observation_response(store, config, scope, headers, body):
    from starlette.responses import JSONResponse
    settings = config.get('n8n_lifecycle', {})
    if (settings.get('enabled') is not True or scope.get('query_string') or headers.get('authorization')
            or scope['method'] != 'POST' or scope['path'] != PATH):
        return JSONResponse({'error': 'LIFECYCLE_SCOPE_DENIED'}, status_code=403)
    try:
        key = settings['signing_key']
        if len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
            raise PermissionError('LIFECYCLE_KEY_UNAVAILABLE')
        return JSONResponse(observe(store, json.loads(body), key, headers.get('x-qldapm-n8n-execution')))
    except (KeyError, ValueError, TypeError, PermissionError):
        return JSONResponse({'error': 'LIFECYCLE_OBSERVATION_DENIED'}, status_code=403)

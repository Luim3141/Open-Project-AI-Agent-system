"""Bind trusted operator work to the current durable queue claim."""
from contextvars import ContextVar
from contextlib import contextmanager
import json
import time

CURRENT = ContextVar('engineering_claim', default=None)
CURRENT_STORE = ContextVar('engineering_claim_store', default=None)


def validate(db, claim, *, completing=False):
    row=db.execute('SELECT state,payload,lease_until FROM ai_queue WHERE id=? AND actor=20',(claim.get('run_id'),)).fetchone()
    payload=json.loads(row['payload']) if row else {}
    if (not row or row['state'] not in ({'executing','finished'} if completing else {'executing'}) or not row['lease_until'] or row['lease_until']<=time.time()
            or not claim.get('claim_token') or not claim.get('worker_id')
            or payload.get('claim_token')!=claim['claim_token'] or payload.get('worker_id')!=claim['worker_id']):
        raise ValueError('ENGINEERING_CLAIM_LOST')


@contextmanager
def bound(claim,store=None):
    token=CURRENT.set(claim)
    store_token=CURRENT_STORE.set(store)
    try:yield
    finally:
        CURRENT_STORE.reset(store_token)
        CURRENT.reset(token)


def check(store, claim):
    with store.connect() as db:validate(db,claim)
    return {'claim_valid':True}


def ensure_current():
    """Check at cross-store/network write boundaries; ordinary ingestion has no claim."""
    claim=CURRENT.get()
    if claim is None:return
    store=CURRENT_STORE.get()
    if store is None:raise ValueError('ENGINEERING_CLAIM_STORE_REQUIRED')
    check(store,claim)
    from .engineering_lifecycle import signal
    state=signal(store,20,claim['run_id'])
    if state['cancel_requested']:raise ValueError('ENGINEERING_CANCELLED')
    if state['mode'] not in {'RUN_ONCE','AUTO'}:raise ValueError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
    if time.time()>=state['deadline']:raise ValueError('ENGINEERING_DEADLINE_EXCEEDED')

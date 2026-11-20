"""Read-only readiness, separate from agent/business state; never performs inference."""
from concurrent.futures import ThreadPoolExecutor, wait
import os
import json
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit, urlunsplit

import httpx

from .vector_client import _resolve_url

_HEALTH_CACHE=None
_HEALTH_LOCK=threading.Lock()


def _base(value, *, strip_path=False):
    try:
        url = urlsplit(value or '')
        if (url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password
                or url.query or url.fragment or (not strip_path and url.path not in {'', '/'})):
            return None
        # Accessing port also validates malformed/out-of-range configuration.
        url.port
        return urlunsplit((url.scheme, url.netloc, '', '', '')).rstrip('/')
    except (ValueError, TypeError):
        return None


def _http_status(url, headers):
    # Only readiness reads a bounded JSON body; no credentials or redirects.
    with httpx.stream('GET', url, headers=headers, timeout=1.5, follow_redirects=False, trust_env=False) as response:
        if url.endswith('/readyz'):
            data=bytearray()
            for chunk in response.iter_bytes():
                if len(data)+len(chunk)>16384:raise ValueError('HEALTH_RESPONSE_TOO_LARGE')
                data.extend(chunk)
            return response.status_code,json.loads(data)
        return response.status_code


def openclaw_snapshot(service):
    """Worker owns CLI probes; polling reads only a small, recent projection."""
    try:
        path=Path(service.store.root)/'openclaw-health.json'
        if path.stat().st_size>8192:return None
        value=json.loads(path.read_text())
        checked=value.get('checked_at')
        if type(checked) not in (int,float) or not 0<=time.time()-checked<=150:return None
        return {k:value.get(k) for k in ('checked_at','check_type','health','wsl_distro','wsl_running',
            'gateway_rpc_ok','process_state','child_runtime_available','last_error','latency_ms')}
    except (AttributeError,OSError,ValueError,TypeError):return None


def integration_health(service, *, transport=_http_status):
    global _HEALTH_CACHE
    configured = service.config.get('integration_health_urls') or {}
    lifecycle = service.config.get('n8n_lifecycle') or {}
    targets = [
        ('openproject', 'OpenProject Community', _base(service.config.get('openproject_url')), '/health_check'),
        ('gateway', 'QLDAPM AI Gateway', _base(configured.get('gateway', 'http://127.0.0.1:8090')), '/health'),
        ('openclaw', 'OpenClaw Gateway', _base(configured.get('openclaw')), '/readyz'),
        ('n8n', 'n8n Orchestration', _base(configured.get('n8n') or lifecycle.get('webhook_url'), strip_path=True), '/healthz/readiness'),
        ('qdrant', 'Qdrant Vector Database', _base(_resolve_url('QLDAPM_QDRANT_URL', 'http://127.0.0.1:6333', 'http://qldapm-qdrant:6333')), '/collections'),
        ('ollama', 'Ollama Local Models', _base(_resolve_url('QLDAPM_OLLAMA_URL', 'http://127.0.0.1:11434', 'http://host.docker.internal:11434')), '/api/tags'),
        ('demo', 'Demo App', _base(configured.get('demo') or os.environ.get('QLDAPM_DEMO_HEALTH_BASE_URL')), '/healthz'),
    ]
    fingerprint = (str(getattr(getattr(service,'store',None),'root','')),tuple(targets),transport)
    cached = _HEALTH_CACHE
    if cached and cached[0] == fingerprint and time.monotonic() - cached[1] < 60:
        return cached[2]
    with _HEALTH_LOCK:
        cached = _HEALTH_CACHE
        if cached and cached[0] == fingerprint and time.monotonic() - cached[1] < 60:
            return cached[2]

        def check(target):
            key, name, base, path = target
            row = {'key': key, 'name': name, 'url': base, 'health': 'UNKNOWN', 'checked_at': None,
                   'check_type': 'NOT CHECKED', 'latency_ms': None, 'last_error': None,
                   'process_health': 'NOT CHECKED', 'api_readiness': 'UNKNOWN',
                   'authentication': 'NOT CHECKED', 'business_status': 'NOT CHECKED'}
            if key == 'n8n':
                row['business_status'] = 'NOT CHECKED — API readiness không chứng minh workflows PASS'
            if key == 'openclaw':
                row['business_status'] = 'NOT CHECKED — Gateway availability không chứng minh Dev đang chạy'
                row['cli_status']=openclaw_snapshot(service)
            if not base or not path:
                row['last_error'] = 'SAFE_ENDPOINT_NOT_CONFIGURED' if not base else 'SAFE_HEALTH_ENDPOINT_NOT_VERIFIED'
                return row
            row.update(checked_at=time.time(), check_type='HTTP GET ' + path)
            started = time.monotonic()
            headers = {'Host': 'localhost:8088', 'X-Forwarded-Proto': 'https'} if key == 'openproject' else {}
            try:
                observed = transport(base + path, headers)
                status,body=observed if isinstance(observed,tuple) else (observed,{})
                row['health'] = 'UP' if status == 200 else 'DEGRADED' if status in {401, 403, 429} else 'DOWN'
                if key=='openclaw' and status==200:
                    row['health']='READY' if body.get('ready') is True and body.get('coreReady') is True else 'DEGRADED'
                    row['process_health']='HTTP_READY; CLI process details checked separately' if row['health']=='READY' else 'NOT CHECKED'
                    cli=row.get('cli_status')
                    if cli:
                        row['process_health']=cli.get('process_state') or 'UNKNOWN'
                        if cli.get('health')!='READY' or cli.get('gateway_rpc_ok') is not True:
                            row.update(health='DEGRADED',last_error=cli.get('last_error') or 'CLI_NOT_READY')
                row['api_readiness'] = 'HTTP_' + str(status)
                if status!=200:row['last_error']='HTTP_' + str(status)
            except (TimeoutError, httpx.TimeoutException):
                row.update(health='DOWN', last_error='TIMEOUT')
            except Exception:
                # Exception/remote text can contain credentials; expose a fixed code only.
                row.update(health='DOWN', last_error='CONNECTIVITY_CHECK_FAILED')
            row['latency_ms'] = round((time.monotonic() - started) * 1000, 1)
            return row

        pool = ThreadPoolExecutor(max_workers=7, thread_name_prefix='readiness')
        futures = [pool.submit(check, target) for target in targets]
        wait(futures, timeout=2.2)
        rows = []
        for target, future in zip(targets, futures):
            if future.done():
                rows.append(future.result())
            else:
                key, name, base, path = target
                rows.append({'key': key, 'name': name, 'url': base, 'health': 'UNKNOWN', 'checked_at': time.time(),
                             'check_type': 'HTTP GET ' + str(path), 'latency_ms': None, 'last_error': 'AGGREGATION_DEADLINE',
                             'process_health': 'NOT CHECKED', 'api_readiness': 'UNKNOWN',
                             'authentication': 'NOT CHECKED', 'business_status': 'NOT CHECKED'})
                future.cancel()
        pool.shutdown(wait=False, cancel_futures=True)
        _HEALTH_CACHE = (fingerprint, time.monotonic(), rows)
        return rows

def provider_status(service):
    """Local policy/receipts only; READY is a fresh successful probe, not a model call."""
    try:
        from .engineering_provider import effective_policy
        policy=effective_policy(service)
        observed=service.gemini.readiness(service.gemini.settings())
        with service.store.connect() as db:
            row=db.execute("SELECT document FROM gemini_call_receipts WHERE json_extract(document,'$.phase')='generateContent' ORDER BY json_extract(document,'$.at') DESC LIMIT 1").fetchone()
        import json
        last=json.loads(row[0]) if row else {}
        checked=observed.get('last_successful_check') or 0
        latest=last.get('completed_at') or last.get('at') or 0
        if last.get('http_status')==429 and checked<=latest:state='RATE_LIMITED'
        elif last.get('http_status') in {401,403} and checked<=latest:state='AUTH_FAILED'
        elif observed.get('state')=='READY' and ((checked>=latest and time.time()-checked<=300) or
                (last.get('http_status')==200 and 0<=time.time()-latest<=300)):state='AVAILABLE'
        else:state='READINESS_STALE' if observed.get('state')=='READY' else observed.get('state','UNKNOWN')
        return {'state':state,'model':policy['model'],'project_limits':policy.get('quota',policy['limits']),'engineering_limits':policy['limits'],'last_successful_probe':checked or None,'retry_at':observed.get('retry_at'),
                'last_provider_http':last.get('http_status'),'network_checked_now':False,'source':'PERSISTED_PROJECT_QUOTA_AND_PROVIDER_RECEIPTS'}
    except Exception:return {'state':'UNKNOWN','source':'PROVIDER_POLICY_UNAVAILABLE','network_checked_now':False}


def demo_observability(service):
    """Persisted metadata only; no outbound probes or retention/business PASS inference."""
    result={'n8n':{'state':'NOT_OBSERVED'},'rag':{'state':'NOT_OBSERVED'},'dr':{'state':'NOT_OBSERVED'}}
    with service.store.connect() as db:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if {'n8n_lifecycle_outbox','n8n_lifecycle_execution_metadata'}<=tables:
            result['n8n']={'state':'OBSERVED','outbox':{r[0]:r[1] for r in db.execute('SELECT state,count(*) FROM n8n_lifecycle_outbox GROUP BY state')}}
            row=db.execute('SELECT execution_id,observed_at FROM n8n_lifecycle_execution_metadata ORDER BY observed_at DESC LIMIT 1').fetchone()
            if row:result['n8n'].update(execution_id=row[0],observed_at=row[1])
            result['n8n']['meaning']='Gateway-correlated execution; retained n8n history verified separately'
        if 'native_index_scans' in tables:
            rows=db.execute('SELECT actor,generation,document FROM native_index_scans WHERE project=6').fetchall()
            result['rag']={'state':'OBSERVED' if rows else 'NOT_OBSERVED','scans':[{'actor':r[0],'generation':r[1],
                **{k:v for k,v in json.loads(r[2]).items() if k in {'observed_at','visible','changed','state'}}} for r in rows],
                'meaning':'Inventory observation age; semantic relevance and vector integrity are separate checks'}
    try:
        path=Path(service.store.root)/'demo-dr-status.json'
        if path.stat().st_size<=8192:
            saved=json.loads(path.read_text())
            result['dr']={k:saved.get(k) for k in ('state','checked_at','backup_at','manifest_sha256','off_host','scope')}
    except (OSError,ValueError,TypeError,AttributeError):pass
    return result

"""Fixed Main probes, persisted once per fifteen-minute bucket; no human authority or writes."""
from contextlib import closing
import json
import shutil
import time
from pathlib import Path

import httpx

from .knowledge_lock import lease
from .store import canonical, digest
from .vector_client import VectorClient

MONITOR_PATH = '/internal/automation/monitor'


def json_get(client, url):
    deadline = time.monotonic()+3
    with client.stream('GET',url) as response:
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_bytes():
            body.extend(chunk)
            if len(body)>131072 or time.monotonic()>deadline:
                raise ValueError('MONITOR_RESPONSE_BOUND_EXCEEDED')
        return response.status_code,json.loads(body)


def resources(root):
    values = {}
    for key, name in [('memory_bytes','memory.current'),('memory_limit_bytes','memory.max'),('pids','pids.current')]:
        raw = (Path('/sys/fs/cgroup') / name).read_text().strip()
        values[key] = None if raw == 'max' else int(raw)
    values['cpu_cumulative'] = {k:int(v) for k,v in (line.split() for line in Path('/sys/fs/cgroup/cpu.stat').read_text().splitlines())}
    values['state_storage_free_bytes'] = shutil.disk_usage(root).free
    values['scope'] = 'Gateway cgroup and mounted state filesystem; CPU cumulative counters, not utilization'
    limit = values['memory_limit_bytes']
    values['state'] = 'PRESSURE' if limit and values['memory_bytes'] >= limit * .9 else 'OK'
    return values


def collect(service):
    if service.config.get('project_id') != 5 or service.config.get('openproject_url') != 'http://web:8080':
        raise PermissionError('MAIN_MONITOR_TARGET_REQUIRED')
    checks = {}
    def probe(name, operation):
        started = time.monotonic()
        try:
            details = operation()
            checks[name] = {'state':'OK',**details}
        except Exception as error:
            checks[name] = {'state':'ERROR','error_type':type(error).__name__}
        checks[name]['latency_ms'] = round((time.monotonic()-started)*1000,1)

    with httpx.Client(timeout=3,trust_env=False,follow_redirects=False) as client, closing(VectorClient(timeout=8)) as vector:
        if vector.qdrant_url != 'http://qldapm-qdrant:6333' or vector.ollama_url != 'http://host.docker.internal:11434':
            raise PermissionError('MAIN_MONITOR_TARGET_REQUIRED')
        def native_health():
            with client.stream('GET','http://web:8080/health_check',headers={'Host':'localhost:8088','X-Forwarded-Proto':'https'}) as response:
                response.raise_for_status()
                return {'http_status':response.status_code,'scope':'OpenProject web health; not full Native permission check'}
        def qdrant():
            status,body = json_get(client,vector.qdrant_url+'/collections/'+vector.collection_name)
            data = body['result']
            if (data['status'] != 'green' or data['config']['params']['vectors']['size'] != 1024
                    or type(data['points_count']) is not int or data['points_count'] < 0):
                raise ValueError('QDRANT_NOT_GREEN_OR_INVALID_DIMENSIONS')
            return {'http_status':status,'collection_status':data['status'],'points':data['points_count'],'dimensions':1024}
        def ollama():
            status,body = json_get(client,vector.ollama_url+'/api/tags')
            if not any(m.get('name')=='bge-m3' or m.get('name','').startswith('bge-m3:') for m in body['models']):
                raise ValueError('BGE_M3_MISSING')
            return {'http_status':status,'model':'bge-m3'}
        probe('openproject',native_health)
        probe('qdrant',qdrant)
        probe('ollama',ollama)
    # Readiness must not allocate or infer with a model just to test health.
    from .engineering_health import integration_health,provider_status
    for item in integration_health(service):
        if item['key'] in {'gateway','openclaw','n8n','demo'}:
            checks[item['key']]={'state':'OK' if item['health'] in {'UP','READY'} else 'NOT_CHECKED' if item['health']=='UNKNOWN' else 'ERROR',
                'health':item['health'],'checked_at':item['checked_at'],'latency_ms':item['latency_ms'],'last_error':item['last_error']}
    provider=provider_status(service);readiness=provider['state']
    checks['provider']={**provider,'state':'ATTENTION' if readiness in {'RATE_LIMITED','AUTH_FAILED'} else 'OK' if readiness=='AVAILABLE' else 'NOT_CHECKED',
        'health':'PROVIDER_'+readiness,'scope':'Persisted provider evidence; no inference health probe'}
    probe('resources',lambda:resources(service.store.root))
    with service.store.connect() as db:
        backlog = {table:{state:count for state,count in db.execute('SELECT state,count(*) FROM '+table+' GROUP BY state')}
            for table in ('ai_queue','knowledge_sync')}
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_worker_state'").fetchone():
            worker=db.execute('SELECT seen,run_id FROM engineering_worker_state WHERE project=6').fetchone()
            checks['worker']={'state':'OK' if worker and time.time()-worker['seen']<30 else 'ERROR','health':'WORKER_ALIVE' if worker and time.time()-worker['seen']<30 else 'WORKER_STALE',
                'seen':worker['seen'] if worker else None,'run_id':worker['run_id'] if worker else None}
    checks['backlog'] = {'state':'ATTENTION' if backlog['knowledge_sync'].get('dlq',0) else 'OK','counts':backlog}
    from .integration_events import snapshot as integration_snapshot
    integrations=integration_snapshot(service.store)
    failed=[row['workflow'] for row in integrations if row['integration_state']=='DEAD' or (row.get('business_result') or {}).get('state') in {'QA_BLOCKED','BLOCKED_DLQ'}]
    checks['business_integration']={'state':'ATTENTION' if failed else 'OK' if integrations else 'NOT_CHECKED',
        'health':'BUSINESS_INTEGRATION_FAILED' if failed else 'NO_FAILED_OBSERVATIONS' if integrations else 'NOT_OBSERVED','workflows':failed}
    return {'observed_at':time.time(),'project_id':5,'state':'HEALTHY' if all(c['state'] not in {'ERROR','ATTENTION'} for c in checks.values()) else 'DEGRADED',
        'checks':checks,'authority':'machine','actor_id':None,'model_calls':0,'native_write_allowed':False,
        'scope':'Main HTTP readiness, resources, queues, Worker and persisted provider evidence; zero embedding/model inference'}


def snapshot(service):
    if service.config.get('project_id') != 5 or service.config.get('openproject_url') != 'http://web:8080':
        raise PermissionError('MAIN_MONITOR_TARGET_REQUIRED')
    bucket = str(int(time.time())//900)
    with lease(service.store.root/'main-monitor.lock'):
        with service.store.connect() as db:
            row = db.execute("SELECT id,outcome,version FROM audit WHERE actor IS NULL AND action='health_monitor' AND target=? ORDER BY at DESC LIMIT 1",(bucket,)).fetchone()
        if row:
            identifier,body,sha256 = row
            if digest(body) != sha256:
                raise ValueError('MONITOR_RECEIPT_HASH_CHANGED')
            from .notification_delivery import enqueue_monitor
            enqueue_monitor(service.store,identifier)
            return {'result':json.loads(body),'sha256':sha256,'correlation_id':identifier,'cached':True}
        report = collect(service)
        body = canonical(report)
        sha256 = digest(body)
        identifier = service.store.record(None,'health_monitor',bucket,body,version=sha256)
        from .notification_delivery import enqueue_monitor
        enqueue_monitor(service.store,identifier)
        return {'result':report,'sha256':sha256,'correlation_id':identifier,'cached':False}

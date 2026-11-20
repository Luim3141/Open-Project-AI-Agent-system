"""GitHub REST API Two-Way Reconciliation Module (Milestone 3 & Phase 2.6 Enhancement).

Safely reconciles GitHub Pull Requests, Commits, and Branch Stack state with OpenProject
without external webhooks, public tunnels, or autonomous merging.
Features:
- Stacked PR chain awareness (merged-to-main vs merged-to-feature-branch).
- Durable SQLite journal and Native marker readback; unknown POSTs are never replayed.
- Out-of-order and idempotency protection.
"""
import hashlib
import json
import logging
import os
import re
import subprocess
import time
import threading
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CACHED_TOKEN: Optional[str] = None
_SYNC_CACHE: Dict[str, str] = {}
_CACHED_PRS: List[Dict[str, Any]] = []
_CACHED_PRS_TIME: float = 0.0
_CACHED_PRS_REPO: Optional[str] = None
_CACHED_PRS_STARTED: float = 0.0
_CACHED_PRS_DETAILS = False
_CACHE_LOCK = threading.Lock()
_PRS_TTL: float = 60.0

PR_WP_MAP = {
    1: 380,
    2: 381,
    3: 382,
    4: 383,
    5: 384,
    6: 386,
}


def get_pr_wp_map(service: Any = None) -> Dict[int, int]:
    """Return PR-to-WP mapping dynamically enriched from active plans and runs."""
    mapping = dict(PR_WP_MAP)
    store = getattr(service, "store", None)
    if store and hasattr(store, "connect"):
        try:
            with store.connect() as db:
                rows = db.execute(
                    "SELECT q.payload, r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id "
                    "WHERE json_extract(q.payload,'$.project_id')=6 "
                    "AND json_extract(q.payload,'$.engine')='openclaw' "
                    "AND json_extract(q.payload,'$.repository')='Luim3141/mini-task-manager' "
                    "AND r.result IS NOT NULL ORDER BY r.created, r.id"
                ).fetchall()
                for p_str, r_str in rows:
                    try:
                        p = json.loads(p_str or "{}")
                        r = json.loads(r_str or "{}")
                        pr_url = r.get("pr_url", "")
                        wp_id = (r.get('native_readback') or {}).get('child_id') or p.get('native_id')
                        match = re.fullmatch(r'https://github\.com/Luim3141/mini-task-manager/pull/([1-9][0-9]*)', pr_url)
                        if r.get('status') == 'succeeded' and match and type(wp_id) is int and wp_id > 0 and wp_id != 379:
                            mapping[int(match[1])] = wp_id
                    except (ValueError, TypeError, AttributeError):
                        logger.warning('Malformed engineering PR receipt ignored')
        except Exception as exc:
            logger.warning('Could not read dynamic engineering PR mapping: %s', exc)
    return mapping


def get_github_token() -> Optional[str]:
    """Retrieve GitHub token from environment, config.json, or git credential helper."""
    global _CACHED_TOKEN
    if _CACHED_TOKEN:
        return _CACHED_TOKEN

    env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env_token:
        _CACHED_TOKEN = env_token.strip()
        return _CACHED_TOKEN

    from pathlib import Path
    for cfg_candidate in [
        Path("/state/config.json"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "QLDAPM/openproject-ai/gateway/config.json",
    ]:
        if cfg_candidate.is_file():
            try:
                cfg = json.loads(cfg_candidate.read_text(encoding="utf-8"))
                cfg_token = cfg.get("engineering", {}).get("github_token") or cfg.get("github_token")
                if cfg_token:
                    _CACHED_TOKEN = str(cfg_token).strip()
                    return _CACHED_TOKEN
            except Exception:
                pass

    try:
        proc = subprocess.run(
            ["git", "-c", "core.hooksPath=NUL", "credential", "fill"],
            input="protocol=https\nhost=github.com\n",
            text=True,
            capture_output=True,
            timeout=5,
        )
        for line in proc.stdout.splitlines():
            if line.startswith("password="):
                _CACHED_TOKEN = line.split("=", 1)[1].strip()
                return _CACHED_TOKEN
    except Exception as exc:
        logger.warning(f"Could not retrieve token from git credential helper: {exc}")

    return None


def fetch_pull_requests(
    repo: str = "Luim3141/mini-task-manager",
    token: Optional[str] = None,
    force: bool = False,
    include_details: bool = False,
) -> List[Dict[str, Any]]:
    """Fetch all pull requests from GitHub REST API with stacked branch awareness."""
    global _CACHED_PRS, _CACHED_PRS_TIME, _CACHED_PRS_REPO, _CACHED_PRS_STARTED, _CACHED_PRS_DETAILS
    now = time.time()
    with _CACHE_LOCK:
        if not force and _CACHED_PRS_REPO == repo and _CACHED_PRS_DETAILS==include_details and _CACHED_PRS_TIME > 0 and (now - _CACHED_PRS_TIME < _PRS_TTL):
            return _CACHED_PRS

    if token is None:
        token = get_github_token()

    headers = {
        "User-Agent": "QLDAPM-Sync/1.0",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    raw_prs = []
    deadline = time.monotonic() + 20
    for page in range(1, 101):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('GITHUB_SYNC_DEADLINE_EXCEEDED')
        url = f"https://api.github.com/repos/{repo}/pulls?state=all&per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=min(15, remaining)) as resp:
            batch = json.loads(resp.read().decode("utf-8"))
        if not isinstance(batch, list):
            raise ValueError('GITHUB_PULLS_RESPONSE_INVALID')
        raw_prs.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError('GITHUB_PULLS_COLLECTION_INCOMPLETE')

    prs = []
    for pr in raw_prs:
        is_merged = pr.get("merged_at") is not None
        base_ref = pr.get("base", {}).get("ref", "")
        if is_merged:
            merge_target = "MAIN" if base_ref == "main" else f"FEATURE_BRANCH ({base_ref})"
        else:
            merge_target = "UNMERGED"

        prs.append({
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "is_merged": is_merged,
            "merge_target": merge_target,
            "merged_at": pr.get("merged_at"),
            "head_sha": pr.get("head", {}).get("sha", ""),
            "base_ref": base_ref,
            "head_ref": pr.get("head", {}).get("ref", ""),
            "html_url": pr.get("html_url", ""),
            "draft": pr.get("draft", False),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "reviews_state": 'NOT_CHECKED',
            "checks_state": 'NOT_CHECKED',
        })

    if include_details:
        from .engineering_github_details import enrich
        prs=enrich(prs,repo,headers,deadline)
    # A slower earlier fetch must not overwrite a newer remote observation.
    with _CACHE_LOCK:
        if now >= _CACHED_PRS_STARTED:
            _CACHED_PRS = prs
            _CACHED_PRS_REPO = repo
            _CACHED_PRS_TIME = time.time()
            _CACHED_PRS_STARTED = now
            _CACHED_PRS_DETAILS = include_details
    return prs


def _get_cached_hash(service: Any, wp_id: int) -> Optional[str]:
    """Read sync hash from SQLite store if available, falling back to in-memory cache."""
    store = getattr(service, "store", None)
    if store and hasattr(store, "connect"):
        try:
            with store.connect() as db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS engineering_github_sync_cache "
                    "(wp_id INTEGER PRIMARY KEY, pr_hash TEXT, updated REAL)"
                )
                row = db.execute(
                    "SELECT pr_hash FROM engineering_github_sync_cache WHERE wp_id=?",
                    (wp_id,),
                ).fetchone()
                if row:
                    return row[0]
        except Exception as exc:
            logger.warning(f"Failed to read from persistent sync cache: {exc}")

    return _SYNC_CACHE.get(str(wp_id))


def _set_cached_hash(service: Any, wp_id: int, pr_hash: str) -> None:
    """Save sync hash to SQLite store and in-memory cache."""
    _SYNC_CACHE[str(wp_id)] = pr_hash
    store = getattr(service, "store", None)
    if store and hasattr(store, "connect"):
        try:
            with store.connect() as db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS engineering_github_sync_cache "
                    "(wp_id INTEGER PRIMARY KEY, pr_hash TEXT, updated REAL)"
                )
                db.execute(
                    "INSERT OR REPLACE INTO engineering_github_sync_cache (wp_id, pr_hash, updated) "
                    "VALUES (?, ?, ?)",
                    (wp_id, pr_hash, time.time()),
                )
        except Exception as exc:
            logger.warning(f"Failed to write to persistent sync cache: {exc}")


def _journal_reserve(service: Any, key: str, wp_id: int) -> tuple[str, bool]:
    store = getattr(service, 'store', None)
    if store is None or not hasattr(store, 'connect'):
        raise RuntimeError('GITHUB_SYNC_DURABLE_STORE_REQUIRED')
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS engineering_github_sync_journal '
                   '(operation_key TEXT PRIMARY KEY, wp_id INTEGER NOT NULL, state TEXT NOT NULL, '
                   'updated REAL NOT NULL, error TEXT)')
        row = db.execute('SELECT state FROM engineering_github_sync_journal WHERE operation_key=?',
                         (key,)).fetchone()
        if row and row[0] != 'REJECTED':
            return row[0], False
        db.execute('INSERT INTO engineering_github_sync_journal VALUES(?,?,\'RESERVED\',?,NULL) '
                   'ON CONFLICT(operation_key) DO UPDATE SET state=\'RESERVED\',updated=excluded.updated,error=NULL',
                   (key, wp_id, time.time()))
    return 'RESERVED', True


def _journal_finish(service: Any, key: str, state: str, error: Optional[str] = None) -> None:
    with service.store.connect() as db:
        # A concurrent readback can confirm success while the original POST is returning.
        db.execute('UPDATE engineering_github_sync_journal SET state=?,updated=?,error=? '
                   'WHERE operation_key=? AND state!=\'DONE\'', (state, time.time(), error, key))


def _has_activity_marker(native: Any, wp_id: int, marker: str, legacy_comment: str) -> bool:
    activities = native.collection(f'/api/v3/work_packages/{wp_id}/activities')
    if not isinstance(activities, list):
        raise ValueError('GITHUB_SYNC_ACTIVITY_COLLECTION_INVALID')
    for activity in activities:
        if not isinstance(activity, dict) or not isinstance(activity.get('comment', {}), dict):
            raise ValueError('GITHUB_SYNC_ACTIVITY_INVALID')
        raw = str(activity.get('comment', {}).get('raw', ''))
        if marker in raw or raw.strip() == legacy_comment.strip():
            return True
    return False


def _sync_activity(service: Any, native: Any, wp_id: int, key: str, comment: str) -> str:
    state, owned = _journal_reserve(service, key, wp_id)
    if state == 'DONE':
        return 'UNCHANGED'
    marker = f'[qldapm-github-sync:{key}]'
    attempted = False
    try:
        package = native.package(wp_id)
        if (package.get('id') != wp_id
                or package.get('_links', {}).get('project', {}).get('href') != '/api/v3/projects/6'
                or package.get('_links', {}).get('parent', {}).get('href') != '/api/v3/work_packages/379'):
            raise PermissionError('ENGINEERING_CHILD_SCOPE_MISMATCH')
        if _has_activity_marker(native, wp_id, marker, comment):
            _journal_finish(service, key, 'DONE')
            return 'RECONCILED'
        if not owned:
            return 'UNKNOWN'
        # Commit uncertainty before the network call: even a process exit cannot permit a second POST.
        _journal_finish(service, key, 'UNKNOWN')
        attempted = True
        native.call(f'/api/v3/work_packages/{wp_id}/activities', 'POST',
                    {'comment': {'format': 'markdown', 'raw': comment + '\n\n' + marker}})
        if not _has_activity_marker(native, wp_id, marker, comment):
            return 'UNKNOWN'
        _journal_finish(service, key, 'DONE')
        return 'UPDATED'
    except Exception as exc:
        from .native import NativeError
        # Only explicit origin rejections prove no activity was created; transport/5xx stay unknown.
        rejected = (not attempted or (isinstance(exc, NativeError)
                    and exc.status in {400, 401, 403, 404, 405, 409, 410, 422, 429}
                    and str(exc).startswith(f'OPENPROJECT_{exc.status}:')))
        if owned:
            _journal_finish(service, key, 'REJECTED' if rejected else 'UNKNOWN', type(exc).__name__)
        if attempted and not rejected:
            return 'UNKNOWN'
        raise


def reconcile_github_with_openproject(
    service: Any,
    native: Any,
    actor: int = 20,
    repo: str = "Luim3141/mini-task-manager",
    token: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Reconcile GitHub Pull Requests with OpenProject child work packages idempotently."""
    if repo != 'Luim3141/mini-task-manager':
        raise PermissionError('ENGINEERING_REPOSITORY_MISMATCH')
    started_at=time.time()
    correlation_id=str(uuid.uuid4())
    try:
        include_details=getattr(service,'config',{}).get('engineering',{}).get('github_sync',{}).get('enabled') is True
        prs = fetch_pull_requests(repo, token=token, force=True,include_details=include_details)
    except Exception as exc:
        error=_error_code(exc)
        logger.error('GitHub sync fetch failed: %s',error)
        meta = {'last_synced_at': time.time(), 'total_checked': 0, 'total_changed': 0,
                'status': 'SYNC_FAILED', 'error': error,'started_at':started_at,'correlation_id':correlation_id,'request_id':request_id}
        _save_sync_meta(service, meta)
        return {
            "timestamp": time.time(),
            "repo": repo,
            "status": "SYNC_FAILED",
            "error": error,
            "correlation_id": correlation_id,
            "changed": False,
            "total_prs_synced": 0,
            "items": [],
            "sync_meta": meta,
        }

    changed_any = False
    changed_count = 0
    errors = []
    synced_items = []

    pr_mapping = get_pr_wp_map(service)
    if include_details:
        from .engineering_github_details import deployment_projection
        deployment_projection(service,prs,verify_ancestry=True)
    for pr in prs:
        pr_num = pr.get("number")
        wp_id = pr_mapping.get(pr_num)
        pr_hash = hashlib.sha256(json.dumps({key:pr.get(key) for key in ['number','state','is_merged','merge_target','head_sha','base_ref','draft','title','updated_at','reviews_state','checks_state','details_hash']},sort_keys=True).encode()).hexdigest()
        if include_details and pr.get('details_error'):
            errors.append(f"PR #{pr_num}: {pr['details_error']}")
            synced_items.append({'pr_number':pr_num,'work_package_id':wp_id,'status':'FAILED','changed':False,'error':pr['details_error']})
            continue
        if not wp_id:
            _enqueue_pr_event(service,repo,pr,pr_hash,correlation_id,None)
            continue

        base_ref = pr.get("base_ref", "")
        is_merged = pr.get("is_merged", False)
        merge_target = pr.get("merge_target", "UNMERGED")

        # Include destination in the logical identity; the key is shared across actors/processes.
        operation_key = hashlib.sha256(f'{repo}:6:379:{wp_id}:{pr_hash}'.encode()).hexdigest()
        item_status = 'UNCHANGED'
        item_error = None

        status_desc = pr.get("state", "").upper()
        if is_merged:
            if merge_target == "MAIN":
                status_desc = "ĐÃ MERGE VÀO MAIN (Sẵn sàng phát hành)"
            else:
                status_desc = f"ĐÃ MERGE VÀO FEATURE BRANCH (`{base_ref}`) — CHƯA VÀO MAIN"
        elif pr.get("draft"):
            status_desc = "DRAFT PR (Đang hoàn thiện)"

        comment = (
            f"**[QLDAPM GitHub Sync]** Đồng bộ trạng thái Pull Request:\n"
            f"- PR: [#{pr_num} {pr.get('title')}]({pr.get('html_url')})\n"
            f"- Trạng thái GitHub: **`{status_desc}`**\n"
            f"- Base Branch: `{base_ref}` | Head Commit: `{pr.get('head_sha', '')[:8]}`\n"
            f"- Phân loại nhánh: `{merge_target}`\n"
            f"- GitHub reviews / CI cho commit này: `{pr.get('reviews_state','NOT_CHECKED')}` / `{pr.get('checks_state','NOT_CHECKED')}`"
        )
        try:
            item_status = _sync_activity(service, native, wp_id, operation_key, comment)
            if item_status in {'UPDATED', 'RECONCILED', 'UNCHANGED'}:
                _set_cached_hash(service, wp_id, pr_hash)
                _enqueue_pr_event(service,repo,pr,pr_hash,correlation_id,wp_id)
            if item_status == 'UPDATED':
                changed_any = True
                changed_count += 1
            elif item_status == 'UNKNOWN':
                item_error = 'OUTCOME_UNKNOWN_RECONCILE_FIRST'
                errors.append(f'WP #{wp_id}: {item_error}')
        except Exception as e:
            logger.warning('Failed GitHub sync activity WP %s: %s',wp_id,_error_code(e))
            item_status = 'FAILED'
            item_error = _error_code(e)
            errors.append(f'WP #{wp_id}: {item_error}')

        synced_items.append({
            "pr_number": pr_num,
            "work_package_id": wp_id,
            "state": pr.get("state"),
            "is_merged": is_merged,
            "merge_target": merge_target,
            "base_ref": base_ref,
            "head_sha": pr.get("head_sha"),
            "changed": item_status == 'UPDATED',
            "status": item_status,
            "error": item_error,
        })

    synced_count = len(synced_items) - len(errors)
    status = ('PARTIAL' if synced_count else 'SYNC_FAILED') if errors else 'SUCCESS'
    sync_meta = {
        "last_synced_at": time.time(),
        "total_checked": len(prs),
        "total_changed": changed_count,
        "status": status,
        "error": '; '.join(errors) or None,
        "started_at": started_at,
        "correlation_id": correlation_id,
        "request_id": request_id,
    }
    _save_sync_meta(service, sync_meta)
    return {
        "timestamp": time.time(),
        "correlation_id": correlation_id,
        "repo": repo,
        "status": status,
        "error": sync_meta['error'],
        "total_prs_synced": synced_count,
        "changed": changed_any,
        "items": synced_items,
        "sync_meta": sync_meta,
    }


def _enqueue_pr_event(service,repo,pr,version,correlation_id,wp_id):
    from .integration_events import enqueue
    enqueue(service.store,'GITHUB_PR_CHANGED',f"{repo}:pr:{pr['number']}",version,correlation_id=correlation_id,
        payload={'pr_number':pr['number'],'work_package_id':wp_id,'head_sha':pr.get('head_sha'),'merge_target':pr.get('merge_target','UNMERGED'),
                 'state':pr.get('state'),'reviews_state':pr.get('reviews_state','NOT_CHECKED'),'checks_state':pr.get('checks_state','NOT_CHECKED')})


def _error_code(error):
    if isinstance(error, TimeoutError):
        return 'GITHUB_SYNC_TIMEOUT'
    if isinstance(error, urllib.error.HTTPError):
        error_code='GITHUB_HTTP_'+str(error.code)
        error.close()
        return error_code
    from .native import NativeError
    if isinstance(error, NativeError):
        return 'OPENPROJECT_'+str(error.status)
    if isinstance(error, urllib.error.URLError):
        return 'GITHUB_SYNC_NETWORK_ERROR'
    text=str(error)
    return text if re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}',text) else 'GITHUB_SYNC_FAILED'


def _setup_sync_meta(db):
    db.execute('CREATE TABLE IF NOT EXISTS engineering_github_sync_meta '
               '(id INTEGER PRIMARY KEY CHECK(id=1),last_synced_at REAL,total_checked INTEGER,'
               'total_changed INTEGER,status TEXT,error_message TEXT)')
    columns={row[1] for row in db.execute('PRAGMA table_info(engineering_github_sync_meta)')}
    for name,kind in [('correlation_id','TEXT'),('started_at','REAL'),('last_success_at','REAL'),('request_id','TEXT')]:
        if name not in columns:
            db.execute('ALTER TABLE engineering_github_sync_meta ADD COLUMN '+name+' '+kind)


def _save_sync_meta(service: Any, sync_meta: Dict[str, Any]) -> None:
    store = getattr(service, "store", None)
    if store and hasattr(store, "connect"):
        try:
            with store.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                _setup_sync_meta(db)
                db.execute(
                    "INSERT INTO engineering_github_sync_meta (id,last_synced_at,total_checked,total_changed,status,error_message,correlation_id,started_at,last_success_at,request_id) "
                    "VALUES(1,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_synced_at=excluded.last_synced_at,"
                    "total_checked=excluded.total_checked,total_changed=excluded.total_changed,status=excluded.status,error_message=excluded.error_message,"
                    "correlation_id=excluded.correlation_id,started_at=excluded.started_at,last_success_at=COALESCE(excluded.last_success_at,engineering_github_sync_meta.last_success_at),request_id=excluded.request_id "
                    "WHERE excluded.started_at>=COALESCE(engineering_github_sync_meta.started_at,0)",
                    (sync_meta["last_synced_at"],sync_meta["total_checked"],sync_meta["total_changed"],sync_meta["status"],sync_meta["error"],
                     sync_meta.get('correlation_id'),sync_meta.get('started_at',sync_meta['last_synced_at']),
                     sync_meta['last_synced_at'] if sync_meta['status']=='SUCCESS' else None,sync_meta.get('request_id')),
                )
        except Exception as exc:
            logger.warning(f"Failed to persist sync meta: {exc}")

def get_sync_meta(service: Any) -> Dict[str, Any]:
    """Read last recorded sync meta from persistent SQLite store."""
    store = getattr(service, "store", None)
    if store and hasattr(store, "connect"):
        try:
            with store.connect() as db:
                _setup_sync_meta(db)
                row = db.execute(
                    "SELECT last_synced_at,total_checked,total_changed,status,error_message,correlation_id,started_at,last_success_at,request_id FROM engineering_github_sync_meta WHERE id=1"
                ).fetchone()
                if row:
                    return {
                        "last_synced_at": row[0],
                        "total_checked": row[1],
                        "total_changed": row[2],
                        "status": row[3],
                        "error": row[4],
                        "correlation_id":row[5],"started_at":row[6],"last_success_at":row[7],"request_id":row[8],
                    }
        except Exception as exc:
            logger.warning(f"Failed to read sync meta: {exc}")
    return {
        "last_synced_at": None,
        "total_checked": 0,
        "total_changed": 0,
        "status": "NOT_SYNCED",
        "error": None,
        "correlation_id":None,"started_at":None,"last_success_at":None,"request_id":None,
    }

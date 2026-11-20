"""Automated Engineering Progress Reporting System (Milestone 7).

Generates Daily, Weekly, and On-Demand reports combining:
1. Deterministic factual metrics (WPs, transitions, PRs, commits, AI runs, tokens).
2. Optional Gemini narrative for risk analysis and next-step recommendations.
3. Persistent SQLite storage for auditability and history tracking.
"""
import hashlib
import json
import logging
import math
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field

from .store import canonical

DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"


class ReportNarrative(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    text: str = Field(min_length=1, max_length=1200)


def get_tz(name: Optional[str] = None) -> ZoneInfo:
    try:
        return ZoneInfo(name or DEFAULT_TIMEZONE)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def format_iso(timestamp: Optional[float], tz_name: Optional[str] = None) -> Optional[str]:
    if timestamp is None:
        return None
    dt = datetime.fromtimestamp(timestamp, tz=get_tz(tz_name))
    return dt.isoformat(timespec='seconds')

logger = logging.getLogger(__name__)

PROJECT = 6


def setup_reporting(store: Any) -> None:
    """Ensure engineering_reports, schedules, and notifications tables exist."""
    if getattr(store,'_reporting_ready',False):return
    with store.connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS engineering_reports ("
            "id TEXT PRIMARY KEY, "
            "project INTEGER NOT NULL, "
            "report_type TEXT NOT NULL, "
            "title TEXT NOT NULL, "
            "document TEXT NOT NULL, "
            "created REAL NOT NULL"
            ")"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS engineering_report_schedules ("
            "project INTEGER PRIMARY KEY, "
            "daily_enabled BOOLEAN NOT NULL DEFAULT 1, "
            "daily_hour INTEGER NOT NULL DEFAULT 8, "
            "daily_minute INTEGER NOT NULL DEFAULT 0, "
            "weekly_enabled BOOLEAN NOT NULL DEFAULT 1, "
            "weekly_day INTEGER NOT NULL DEFAULT 1, "
            "weekly_hour INTEGER NOT NULL DEFAULT 9, "
            "weekly_minute INTEGER NOT NULL DEFAULT 0, "
            "last_daily_run REAL, "
            "last_weekly_run REAL, "
            "timezone TEXT NOT NULL DEFAULT 'Asia/Ho_Chi_Minh', "
            "updated REAL NOT NULL"
            ")"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS engineering_notifications ("
            "id TEXT PRIMARY KEY, "
            "project INTEGER NOT NULL, "
            "actor INTEGER, "
            "level TEXT NOT NULL, "
            "title TEXT NOT NULL, "
            "message TEXT NOT NULL, "
            "link TEXT, "
            "unread BOOLEAN NOT NULL DEFAULT 1, "
            "created REAL NOT NULL"
            ")"
        )
        if "metadata" not in {r[1] for r in db.execute("PRAGMA table_info(engineering_notifications)")}:
            db.execute("ALTER TABLE engineering_notifications ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'")
        db.execute(
            "INSERT OR IGNORE INTO engineering_report_schedules "
            "(project, daily_enabled, daily_hour, daily_minute, weekly_enabled, weekly_day, weekly_hour, weekly_minute, updated) "
            "VALUES (6, 1, 8, 0, 1, 1, 9, 0, ?)",
            (time.time(),)
        )
    store._reporting_ready=True


def collect_factual_metrics(service: Any, native: Any) -> Dict[str, Any]:
    """Collect deterministic facts from SQLite DB, OpenProject Native, and GitHub."""
    now = time.time()
    store = service.store

    # 1. AI Queue and Runs metrics from SQLite
    with store.connect() as db:
        rows = db.execute(
            "SELECT q.id, q.state, q.payload, r.result, q.created "
            "FROM ai_queue q JOIN ai_runs r ON r.id=q.id "
            "WHERE json_extract(q.payload,'$.project_id')=6 "
            "ORDER BY q.created DESC"
        ).fetchall()

        worker_row = db.execute(
            "SELECT worker_id, seen, run_id FROM engineering_worker_state WHERE project=6"
        ).fetchone()

        control_row = db.execute(
            "SELECT mode, updated FROM engineering_control WHERE project=6"
        ).fetchone()
        generations = db.execute(
            "SELECT c.run_id,c.document FROM gemini_call_receipts c "
            "JOIN ai_queue q ON q.id=c.run_id JOIN ai_runs r ON r.id=q.id "
            "WHERE json_extract(q.payload,'$.project_id')=6 "
            "AND json_extract(c.document,'$.phase')='generateContent'"
        ).fetchall()

    total_runs = len(rows)
    succeeded_runs = 0
    failed_runs = 0
    usage = [json.loads(r['document']).get('usage') or {} for r in generations]
    known_tokens = [u['totalTokenCount'] for u in usage
                    if type(u.get('totalTokenCount')) is int and u['totalTokenCount'] >= 0]
    runs_without_receipts = len({r['id'] for r in rows} - {r['run_id'] for r in generations})
    total_tokens = sum(known_tokens) if known_tokens or not rows else None
    usage_missing = len(generations) - len(known_tokens)

    for r in rows:
        res = json.loads(r["result"] or "{}")
        if res.get("status") == "succeeded":
            succeeded_runs += 1
        elif res.get("status") in {"failed", "cancelled", "blocked"}:
            failed_runs += 1

    worker_state = "NOT_SEEN"
    if worker_row:
        seen_elapsed = now - worker_row["seen"]
        worker_state = "ALIVE" if seen_elapsed < 30 else f"STALE ({int(seen_elapsed)}s ago)"

    mode = control_row["mode"] if control_row else "OFF"

    # 2. GitHub PR metrics
    github_metrics = {"status": "UNKNOWN", "total_prs": None, "open_prs": None, "merged_prs": None, "prs": []}
    try:
        from .engineering_github_sync import fetch_pull_requests
        prs = fetch_pull_requests("Luim3141/mini-task-manager")
        github_metrics["status"] = "ONLINE"
        github_metrics["total_prs"] = len(prs)
        github_metrics["open_prs"] = sum(1 for p in prs if p.get("state") == "open")
        github_metrics["merged_prs"] = sum(1 for p in prs if p.get("is_merged"))
        github_metrics["prs"] = [
            {
                "number": p.get("number"),
                "title": p.get("title"),
                "state": p.get("state"),
                "is_merged": p.get("is_merged"),
                "merge_target": p.get("merge_target"),
                "head_sha": p.get("head_sha", "")[:8],
                "base_ref": p.get("base_ref"),
            }
            for p in prs
        ]
    except Exception as exc:
        github_metrics["status"] = "OFFLINE"
        github_metrics["error"] = type(exc).__name__

    # 3. OpenProject Work Packages
    wp_list = []
    native_status = 'UNAVAILABLE'
    try:
        wp_list = [
                {
                    "id": p.get("id"),
                    "subject": p.get("subject"),
                    "status": p.get("status", {}).get("name") if isinstance(p.get("status"), dict) else p.get("_links", {}).get("status", {}).get("title"),
                    "lock_version": p.get("lockVersion"),
                    "url": f"/work_packages/{p['id']}/activity",
                }
                for p in native.packages()
        ]
        native_status = 'ONLINE'
    except Exception as exc:
        logger.warning('Native report source unavailable: %s', type(exc).__name__)

    return {
        "timestamp": now,
        "project_id": PROJECT,
        "mode": mode,
        "worker": {"state": worker_state, "worker_id": worker_row["worker_id"] if worker_row else None},
        "runs": {
            "total": total_runs,
            "succeeded": succeeded_runs,
            "failed_or_cancelled": failed_runs,
            "estimated_tokens_consumed": total_tokens,
            "usage_complete": not usage_missing and not runs_without_receipts,
            "usage_missing_calls": usage_missing,
            "runs_without_usage_receipts": runs_without_receipts,
            "usage_source": "gemini_call_receipts.generateContent",
        },
        "github": github_metrics,
        "work_packages": {
            "status": native_status,
            "parent_379": next((p for p in wp_list if p['id'] == 379), None),
            "total_items": len(wp_list) if native_status == 'ONLINE' else None,
            "items": wp_list,
        },
    }


def generate_report(
    service: Any,
    actor: int,
    report_type: str = "ON_DEMAND",
    include_narrative: bool = False,
) -> Dict[str, Any]:
    """Generate and persist an engineering progress report."""
    from .engineering import authorized
    native, who = authorized(service, actor)
    setup_reporting(service.store)

    report_type = report_type.upper()
    if report_type not in {"DAILY", "WEEKLY", "ON_DEMAND"}:
        raise ValueError("REPORT_TYPE_INVALID")

    metrics = collect_factual_metrics(service, native)
    report_id = str(uuid.uuid4())
    tz = get_tz("Asia/Ho_Chi_Minh")
    now_dt = datetime.fromtimestamp(metrics["timestamp"], tz=tz)
    now_iso = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    title_map = {
        "DAILY": f"Báo cáo tiến độ hằng ngày (Daily Report) — {now_dt.strftime('%Y-%m-%d')}",
        "WEEKLY": f"Báo cáo tiến độ hằng tuần (Weekly Report) — Tuần {now_dt.strftime('%W/%Y')}",
        "ON_DEMAND": f"Báo cáo tiến độ tức thời (On-Demand Snapshot) — {now_iso}",
    }
    title = title_map.get(report_type, f"Báo cáo tiến độ {report_type}")

    # Build comprehensive factual narrative
    runs_info = metrics["runs"]
    gh_info = metrics["github"]
    wp_data = metrics.get("work_packages", {})
    wps = wp_data.get("items", []) if isinstance(wp_data, dict) else (wp_data or [])
    parent_wp_info = (wp_data.get("parent_379") or {}) if isinstance(wp_data, dict) else metrics.get("parent_wp", {})
    missing = 'Chưa có dữ liệu'
    source_status = 'READY' if wp_data.get('status') == 'ONLINE' and gh_info['status'] == 'ONLINE' else 'PARTIAL'
    
    narrative = (
        f"# BÁO CÁO TIẾN ĐỘ AI ENGINEERING — QLDAPM MAIN\n\n"
        f"**Thời điểm tạo:** {now_iso} (UTC+07:00) | **Loại báo cáo:** `{report_type}` | **Người tạo:** User {actor} ({who.get('role', 'PM')})\n"
        f"**Nguồn số liệu:** Snapshot từ SQLite, OpenProject và GitHub; không xác minh chi phí provider. | **OpenClaw Worker:** `{metrics['worker']['state']}`\n\n"
        f"---\n\n"
        f"### 1. Tổng Quan Vận Hành & Trạng Thái Hệ Thống\n"
        f"- **Chế độ kiểm soát:** `{metrics['mode']}`\n"
        f"- **Delivery Worker:** `{metrics['worker']['state']}`\n"
        f"- **Phạm vi:** OpenProject Project {PROJECT}; trạng thái là snapshot tại thời điểm tạo báo cáo.\n\n"
        f"### 2. Tiến Độ Backlog & Work Packages (OpenProject Project 6)\n"
        f"- **Trạng thái nguồn:** `{source_status}`; OpenProject: `{wp_data.get('status', 'UNKNOWN')}`.\n"
        f"- **Parent Work Package:** {parent_wp_info.get('subject') or missing}\n"
        f"- **Tổng số Work Packages:** {wp_data.get('total_items') if wp_data.get('total_items') is not None else missing}.\n"
    )
    for wp in sorted(wps,key=lambda p:p['id'],reverse=True)[:10]:
        narrative += f"  - [WP #{wp.get('id')}]({wp['url']}) {wp.get('subject')} (Trạng thái: `{wp.get('status')}` | Lock: v{wp.get('lock_version')})\n"
    
    narrative += (
        f"\n### 3. Hoạt Động Của Tác Nhân AI Workforce (Supervisor, BA, PM, Dev, Reviewer, QA)\n"
        f"- **Tổng số lượt chạy (Runs):** `{runs_info['total']}` lượt chạy.\n"
        f"- **Lượt chạy thành công:** `{runs_info['succeeded']}` lượt.\n"
        f"- **Lượt chạy thất bại / Hủy / Blocked:** `{runs_info['failed_or_cancelled']}` lượt.\n"
        f"- **Token ghi nhận trong generation receipts:** `{runs_info['estimated_tokens_consumed'] if runs_info['estimated_tokens_consumed'] is not None else missing}`; usage complete: `{runs_info['usage_complete']}`; không phải chứng nhận billing hoặc tổng chi phí.\n\n"
        f"### 4. Quản Lý Mã Nguồn & GitHub Delivery (Luim3141/mini-task-manager)\n"
        f"- **Trạng thái kết nối GitHub:** `{gh_info.get('status', 'ONLINE')}`\n"
        f"- **Tổng số Pull Requests:** `{gh_info.get('total_prs') if gh_info.get('total_prs') is not None else missing}`.\n"
        f"- **Pull Requests đã merge:** `{gh_info.get('merged_prs') if gh_info.get('merged_prs') is not None else missing}`.\n"
        f"- **Pull Requests đang mở / Chờ review:** `{gh_info.get('open_prs') if gh_info.get('open_prs') is not None else missing}`.\n"
    )
    for pr in gh_info.get('prs', []):
        m_state = "MERGED" if pr.get('is_merged') else pr.get('state', 'OPEN').upper()
        narrative += f"  - [PR #{pr.get('number')}](https://github.com/Luim3141/mini-task-manager/pull/{pr.get('number')}): {pr.get('title')} (`{m_state}` -> `{pr.get('merge_target') or pr.get('base_ref')}`)\n"
    
    narrative += (
        f"\n### 5. Chất Lượng Mã Nguồn & Kiểm Thử QA\n"
        f"- Snapshot này chưa tổng hợp test receipts hoặc đối soát tính toàn vẹn dữ liệu dự án khác.\n\n"
        f"### 6. Đánh Giá Kỹ Thuật & Khuyến Nghị Tiếp Theo\n"
        f"- Cần kiểm tra test receipts, blocker và trạng thái PR trước khi nghiệm thu hoặc giao thêm task.\n"
    )

    ai_narrative_status = 'NOT_REQUESTED'
    if include_narrative:
        try:
            from .live_agents import LiveBudget, LiveConfig
            prompt = (f"Mode={metrics['mode']}; runs={runs_info['total']}; succeeded={runs_info['succeeded']}; "
                      f"open PRs={gh_info.get('open_prs')}; merged PRs={gh_info.get('merged_prs')}.")
            budget=LiveBudget(LiveConfig(max_model_calls=1,max_http_attempts=2,retry_limit=0,
                                         timeout_seconds=90,call_timeout_seconds=45,max_output_tokens=1800))
            ai=service.gemini.structured(prompt,ReportNarrative,
                system='Give brief Vietnamese risk suggestions based only on supplied aggregate values. Do not invent facts or claim verification.',
                agent='supervisor',scope=SimpleNamespace(actor_id=actor,run_id=report_id),budget=budget)
            narrative += f"\n### Nhận Xét & Khuyến Nghị Của AI Architect (chưa xác minh):\n{ai.text}\n"
            ai_narrative_status = 'GENERATED'
        except Exception:
            ai_narrative_status = 'UNAVAILABLE'
            narrative += '\n*(Nhận xét AI không khả dụng; phần số liệu xác định vẫn được giữ.)*\n'

    report_document = {
        "id": report_id,
        "project_id": PROJECT,
        "report_type": report_type,
        "title": title,
        "generated_by": actor,
        "generated_by_role": who["role"],
        "generated_at": metrics["timestamp"],
        "generated_at_iso": format_iso(metrics['timestamp']),
        "metrics": metrics,
        "source_status": source_status,
        "narrative": narrative,
        "ai_narrative_status": ai_narrative_status,
    }

    doc_json = canonical(report_document)
    with service.store.connect() as db:
        db.execute(
            "INSERT INTO engineering_reports (id, project, report_type, title, document, created) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (report_id, PROJECT, report_type, title, doc_json, metrics["timestamp"]),
        )

    service.store.record(actor, "engineering_report_generated", report_type, report_id)
    return report_document


def list_reports(service: Any, actor: int, limit: int = 10, offset: int = 0, *, verified_native=None, versions=None) -> Dict[str, Any]:
    """List historical engineering reports."""
    from .engineering import authorized
    native = verified_native if verified_native is not None else authorized(service, actor)[0]
    setup_reporting(service.store)

    with service.store.connect() as db:
        total = db.execute("SELECT count(*) FROM engineering_reports WHERE project=6").fetchone()[0]
        rows = db.execute(
            "SELECT id, report_type, title, created, document FROM engineering_reports "
            "WHERE project=6 ORDER BY created DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()

    current = versions if versions is not None else _native_versions(native) if rows else None
    items = []
    for r in rows:
        doc = json.loads(r["document"]) if r["document"] else {}
        doc = _source_readback(doc, current)
        items.append({
            "id": r["id"],
            "report_type": r["report_type"],
            "title": r["title"],
            "created": r["created"],
            "created_iso": format_iso(r["created"]),
            "narrative": doc.get("narrative", ""),
            "metrics": doc.get("metrics", {}),
            "summary": doc.get("summary", ""),
            "source_versions_current": doc.get('source_versions_current'),
            "source_state": doc.get('source_state', 'UNKNOWN'),
            "data_hidden": doc.get('data_hidden', False),
        })

    return {
        "project_id": PROJECT,
        "total": total,
        "limit": limit,
        "offset": offset,
        "reports": items,
    }


def get_report(service: Any, actor: int, report_id: str) -> Dict[str, Any]:
    """Retrieve full content of a specific engineering report."""
    from .engineering import authorized
    native, _ = authorized(service, actor)
    setup_reporting(service.store)

    with service.store.connect() as db:
        row = db.execute(
            "SELECT document FROM engineering_reports WHERE id=? AND project=6",
            (report_id,),
        ).fetchone()

    if not row:
        raise KeyError("ENGINEERING_REPORT_NOT_FOUND")

    report = json.loads(row["document"])
    return _source_readback(report, _native_versions(native))


def _native_versions(native):
    try:
        return {p['id']: p.get('lockVersion') for p in native.packages()}
    except Exception:
        return None


def _source_readback(report, current):
    if report.get('report_type')=='WORKFLOW_AUDIT':
        source=report.get('provenance',{});identifier=source.get('native_id');version=source.get('lock_version')
        if current is None:return {**report,'source_versions_current':None,'source_state':'UNAVAILABLE'}
        if type(identifier) is not int or identifier not in current:
            return {key:report[key] for key in ('id','project_id','report_type','title','generated_at')} | {'data_hidden':True,'source_versions_current':False,'source_state':'SOURCE_UNAVAILABLE'}
        same=current[identifier]==version
        return {**report,'source_versions_current':same,'source_state':'CURRENT' if same else 'HISTORICAL'}
    sources = report.get('metrics', {}).get('work_packages', {})
    if sources.get('status') != 'ONLINE':
        return {**report, 'source_versions_current': None, 'source_state': 'UNKNOWN'}
    if current is None:
        return {**report, 'source_versions_current': None, 'source_state': 'UNAVAILABLE'}
    original = {p['id']: p.get('lock_version') for p in sources['items']}
    if not original.keys() <= current.keys():
        return {key: report[key] for key in ('id', 'project_id', 'report_type', 'title', 'generated_at')} | {
            'data_hidden': True, 'source_versions_current': False, 'source_state': 'SOURCE_UNAVAILABLE'}
    same = original == current
    return {**report, 'source_versions_current': same, 'source_state': 'CURRENT' if same else 'HISTORICAL'}

def get_schedule(service: Any, actor: int, *, verified_native=None) -> Dict[str, Any]:
    from .engineering import authorized
    if verified_native is None:authorized(service, actor)
    setup_reporting(service.store)
    with service.store.connect() as db:
        row = db.execute("SELECT * FROM engineering_report_schedules WHERE project=6").fetchone()
    if not row:
        return {
            "project": 6,
            "daily_enabled": True,
            "daily_hour": 8,
            "daily_minute": 0,
            "weekly_enabled": True,
            "weekly_day": 1,
            "weekly_hour": 9,
            "weekly_minute": 0,
            "timezone": DEFAULT_TIMEZONE,
            "last_daily_run": None,
            "last_weekly_run": None,
            "last_daily_run_iso": None,
            "last_weekly_run_iso": None,
        }
    data = dict(row)
    data["last_daily_run_iso"] = format_iso(data.get("last_daily_run"), data.get("timezone"))
    data["last_weekly_run_iso"] = format_iso(data.get("last_weekly_run"), data.get("timezone"))
    return data


def update_schedule(service: Any, actor: int, config: Dict[str, Any]) -> Dict[str, Any]:
    from .engineering import authorized
    authorized(service, actor)
    setup_reporting(service.store)
    now = time.time()
    allowed={'daily_enabled','daily_hour','daily_minute','weekly_enabled','weekly_day','weekly_hour','weekly_minute','timezone','expected_updated'}
    if not isinstance(config,dict) or set(config)-allowed:raise ValueError('ENGINEERING_REPORT_SCHEDULE_INVALID')
    changes=dict(config)
    expected=changes.pop('expected_updated',None)
    if expected is not None and (type(expected) not in (int,float) or not math.isfinite(expected)):
        raise ValueError('ENGINEERING_REPORT_SCHEDULE_INVALID')
    current=get_schedule(service,actor)
    if expected is not None and expected!=current['updated']:raise ValueError('ENGINEERING_REPORT_SCHEDULE_CONFLICT')
    config={**current,**changes}
    for key,upper in [('daily_hour',23),('weekly_hour',23),('daily_minute',59),('weekly_minute',59),('weekly_day',7)]:
        if type(config[key]) is not int or not (1 if key=='weekly_day' else 0)<=config[key]<=upper:
            raise ValueError('ENGINEERING_REPORT_SCHEDULE_INVALID')
    for key in ['daily_enabled','weekly_enabled']:
        if type(config[key]) not in (bool,int) or config[key] not in (0,1):raise ValueError('ENGINEERING_REPORT_SCHEDULE_INVALID')
    tz_val = config.get("timezone", DEFAULT_TIMEZONE)
    try:
        ZoneInfo(tz_val)
    except Exception:
        raise ValueError('ENGINEERING_REPORT_SCHEDULE_INVALID') from None

    with service.store.connect() as db:
        db.execute(
            "UPDATE engineering_report_schedules SET "
            "daily_enabled=?, daily_hour=?, daily_minute=?, weekly_enabled=?, weekly_day=?, weekly_hour=?, weekly_minute=?, timezone=?, updated=? "
            "WHERE project=6 AND updated=?",
            (
                int(bool(config.get("daily_enabled", True))),
                int(config.get("daily_hour", 8)),
                int(config.get("daily_minute", 0)),
                int(bool(config.get("weekly_enabled", True))),
                int(config.get("weekly_day", 1)),
                int(config.get("weekly_hour", 9)),
                int(config.get("weekly_minute", 0)),
                tz_val,
                now,
                current['updated'],
            )
        )
        if db.execute('SELECT changes()').fetchone()[0]!=1:
            raise ValueError('ENGINEERING_REPORT_SCHEDULE_CONFLICT')
    service.store.record(actor, "engineering_report_schedule_updated", "project6", "ok")
    return get_schedule(service, actor)


def list_notifications(service: Any, actor: int, limit: int = 10, unread_only: bool = False) -> List[Dict[str, Any]]:
    setup_reporting(service.store)
    with service.store.connect() as db:
        query = "SELECT * FROM engineering_notifications WHERE project=6"
        params = []
        if unread_only:
            query += " AND unread=1"
        query += " ORDER BY created DESC LIMIT ?"
        params.append(limit)
        rows = db.execute(query, tuple(params)).fetchall()
    return [{**dict(r), **json.loads(r["metadata"] or "{}")} for r in rows]


def dismiss_notification(service: Any, actor: int, notification_id: str) -> Dict[str, Any]:
    setup_reporting(service.store)
    with service.store.connect() as db:
        count = db.execute("UPDATE engineering_notifications SET unread=0 WHERE id=? AND project=6", (notification_id,)).rowcount
    return {"id": notification_id, "dismissed": count > 0}


def check_and_run_scheduled_reports(service: Any, actor: int = 20, now: Optional[float] = None) -> Dict[str, Any]:
    """Autonomous reporting check independent of Engineering AUTO mode.

    Adheres to P07-08/P07-09 requirements:
    - Timezone-aware (Asia/Ho_Chi_Minh).
    - Idempotent: strictly runs at most once per day for Daily, once per week for Weekly.
    - Zero duplicate run upon restart.
    - Independent background execution.
    """
    setup_reporting(service.store)
    now = time.time() if now is None else now
    with service.store.connect() as db:
        sched = db.execute("SELECT * FROM engineering_report_schedules WHERE project=6").fetchone()
    if not sched:
        return {"checked": False, "reason": "NO_SCHEDULE"}

    tz = get_tz(sched["timezone"] if "timezone" in sched.keys() else None)
    now_dt = datetime.fromtimestamp(now, tz=tz)
    reports_generated = []

    # 1. DAILY REPORT CHECK
    if bool(sched["daily_enabled"]):
        sched_hour = sched["daily_hour"]
        sched_min = sched["daily_minute"]
        current_minute = now_dt.hour * 60 + now_dt.minute
        target_minute = sched_hour * 60 + sched_min

        # Has current time in Asia/Ho_Chi_Minh reached or passed target time today?
        time_reached = current_minute >= target_minute

        # Has it already run today in Asia/Ho_Chi_Minh?
        last_daily = sched["last_daily_run"]
        already_run_today = False
        if last_daily:
            last_daily_dt = datetime.fromtimestamp(last_daily, tz=tz)
            if last_daily_dt.date() == now_dt.date():
                already_run_today = True

        if time_reached and not already_run_today:
            try:
                doc = generate_report(service, actor, "DAILY", include_narrative=False)
                with service.store.connect() as db:
                    db.execute("UPDATE engineering_report_schedules SET last_daily_run=? WHERE project=6", (now,))
                    db.execute(
                        "INSERT INTO engineering_notifications (id, project, actor, level, title, message, link, created) "
                        "VALUES (?, 6, ?, 'SUCCESS', 'Báo cáo Tiến độ Hằng ngày', ?, ?, ?)",
                        (
                            str(uuid.uuid4()),
                            actor,
                            f"Báo cáo tiến độ hằng ngày ({doc['title']}) đã được tự động tạo theo lịch.",
                            "/projects/ai-dev-demo/qldapm_ai/engineering",
                            now,
                        )
                    )
                reports_generated.append({"type": "DAILY", "id": doc["id"]})
                logger.info(f"Auto daily report generated: {doc['id']}")
            except Exception as exc:
                logger.warning(f"Auto daily report generation failed: {exc}")

    # 2. WEEKLY REPORT CHECK
    if bool(sched["weekly_enabled"]):
        sched_day = sched["weekly_day"]  # 1 = Monday, 7 = Sunday
        sched_w_hour = sched["weekly_hour"]
        sched_w_min = sched["weekly_minute"]

        current_year, current_week, current_isoday = now_dt.isocalendar()
        target_minute = sched_w_hour * 60 + sched_w_min
        current_minute = now_dt.hour * 60 + now_dt.minute

        # Has schedule day/time arrived this week?
        if current_isoday > sched_day:
            day_reached = True
        elif current_isoday == sched_day:
            day_reached = current_minute >= target_minute
        else:
            day_reached = False

        # Has it already run in this ISO week?
        last_weekly = sched["last_weekly_run"]
        already_run_this_week = False
        if last_weekly:
            last_weekly_dt = datetime.fromtimestamp(last_weekly, tz=tz)
            if last_weekly_dt.isocalendar()[:2] == (current_year, current_week):
                already_run_this_week = True

        if day_reached and not already_run_this_week:
            try:
                doc = generate_report(service, actor, "WEEKLY", include_narrative=False)
                with service.store.connect() as db:
                    db.execute("UPDATE engineering_report_schedules SET last_weekly_run=? WHERE project=6", (now,))
                    db.execute(
                        "INSERT INTO engineering_notifications (id, project, actor, level, title, message, link, created) "
                        "VALUES (?, 6, ?, 'SUCCESS', 'Báo cáo Tiến độ Hằng tuần', ?, ?, ?)",
                        (
                            str(uuid.uuid4()),
                            actor,
                            f"Báo cáo tiến độ tuần ({doc['title']}) đã được tự động tạo theo lịch.",
                            "/projects/ai-dev-demo/qldapm_ai/engineering",
                            now,
                        )
                    )
                reports_generated.append({"type": "WEEKLY", "id": doc["id"]})
                logger.info(f"Auto weekly report generated: {doc['id']}")
            except Exception as exc:
                logger.warning(f"Auto weekly report generation failed: {exc}")

    return {"checked": True, "generated": reports_generated}

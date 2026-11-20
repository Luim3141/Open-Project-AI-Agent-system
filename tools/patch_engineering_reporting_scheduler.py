"""Script to patch engineering_reporting.py with timezone-aware autonomous scheduler."""
import re
from pathlib import Path

path = Path("openproject/ai/gateway/engineering_reporting.py")
content = path.read_text(encoding="utf-8")

# 1. Update imports
old_import = """from typing import Any, Dict, List, Optional

from .store import canonical"""

new_import = """from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from .store import canonical

DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"


def get_tz(name: Optional[str] = None) -> ZoneInfo:
    try:
        return ZoneInfo(name or DEFAULT_TIMEZONE)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def format_iso(timestamp: Optional[float], tz_name: Optional[str] = None) -> Optional[str]:
    if not timestamp:
        return None
    dt = datetime.fromtimestamp(timestamp, tz=get_tz(tz_name))
    return dt.strftime("%Y-%m-%d %H:%M:%S")"""

assert old_import in content, "old_import not found"
content = content.replace(old_import, new_import, 1)

# 2. Update generate_report title and now_iso
old_gen_now = """    metrics = collect_factual_metrics(service, native)
    report_id = str(uuid.uuid4())
    now_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metrics["timestamp"]))

    title_map = {
        "DAILY": f"Báo cáo tiến độ hằng ngày (Daily Report) — {time.strftime('%Y-%m-%d')}",
        "WEEKLY": f"Báo cáo tiến độ hằng tuần (Weekly Report) — Tuần {time.strftime('%W/%Y')}",
        "ON_DEMAND": f"Báo cáo tiến độ tức thời (On-Demand Snapshot) — {now_iso}",
    }"""

new_gen_now = """    metrics = collect_factual_metrics(service, native)
    report_id = str(uuid.uuid4())
    tz = get_tz("Asia/Ho_Chi_Minh")
    now_dt = datetime.fromtimestamp(metrics["timestamp"], tz=tz)
    now_iso = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    title_map = {
        "DAILY": f"Báo cáo tiến độ hằng ngày (Daily Report) — {now_dt.strftime('%Y-%m-%d')}",
        "WEEKLY": f"Báo cáo tiến độ hằng tuần (Weekly Report) — Tuần {now_dt.strftime('%W/%Y')}",
        "ON_DEMAND": f"Báo cáo tiến độ tức thời (On-Demand Snapshot) — {now_iso}",
    }"""

assert old_gen_now in content, "old_gen_now not found"
content = content.replace(old_gen_now, new_gen_now, 1)

# 3. Update list_reports created_iso
old_list_items = """"created_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["created"])),"""
new_list_items = """"created_iso": format_iso(r["created"]),"""
assert old_list_items in content, "old_list_items not found"
content = content.replace(old_list_items, new_list_items, 1)

# 4. Update get_schedule & update_schedule
old_sched = """def get_schedule(service: Any, actor: int) -> Dict[str, Any]:
    from .engineering import authorized
    authorized(service, actor)
    setup_reporting(service.store)
    with service.store.connect() as db:
        row = db.execute("SELECT * FROM engineering_report_schedules WHERE project=6").fetchone()
    if not row:
        return {"project": 6, "daily_enabled": True, "daily_hour": 8, "daily_minute": 0, "weekly_enabled": True, "weekly_day": 1, "weekly_hour": 9, "weekly_minute": 0}
    return dict(row)


def update_schedule(service: Any, actor: int, config: Dict[str, Any]) -> Dict[str, Any]:
    from .engineering import authorized
    authorized(service, actor)
    setup_reporting(service.store)
    now = time.time()
    with service.store.connect() as db:
        db.execute(
            "UPDATE engineering_report_schedules SET "
            "daily_enabled=?, daily_hour=?, daily_minute=?, weekly_enabled=?, weekly_day=?, weekly_hour=?, weekly_minute=?, updated=? "
            "WHERE project=6",
            (
                int(bool(config.get("daily_enabled", True))),
                int(config.get("daily_hour", 8)),
                int(config.get("daily_minute", 0)),
                int(bool(config.get("weekly_enabled", True))),
                int(config.get("weekly_day", 1)),
                int(config.get("weekly_hour", 9)),
                int(config.get("weekly_minute", 0)),
                now,
            )
        )
    service.store.record(actor, "engineering_report_schedule_updated", "project6", "ok")
    return get_schedule(service, actor)"""

new_sched = """def get_schedule(service: Any, actor: int) -> Dict[str, Any]:
    from .engineering import authorized
    authorized(service, actor)
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
    tz_val = config.get("timezone", DEFAULT_TIMEZONE)
    try:
        ZoneInfo(tz_val)
    except Exception:
        tz_val = DEFAULT_TIMEZONE

    with service.store.connect() as db:
        db.execute(
            "UPDATE engineering_report_schedules SET "
            "daily_enabled=?, daily_hour=?, daily_minute=?, weekly_enabled=?, weekly_day=?, weekly_hour=?, weekly_minute=?, timezone=?, updated=? "
            "WHERE project=6",
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
            )
        )
    service.store.record(actor, "engineering_report_schedule_updated", "project6", "ok")
    return get_schedule(service, actor)"""

assert old_sched in content, "old_sched not found"
content = content.replace(old_sched, new_sched, 1)

# 5. Update check_and_run_scheduled_reports
old_check = """def check_and_run_scheduled_reports(service: Any, actor: int = 20, now: Optional[float] = None) -> Dict[str, Any]:
    \"\"\"Autonomous reporting check independent of Engineering AUTO mode.\"\"\"
    setup_reporting(service.store)
    now = time.time() if now is None else now
    with service.store.connect() as db:
        sched = db.execute("SELECT * FROM engineering_report_schedules WHERE project=6").fetchone()
    if not sched:
        return {"checked": False, "reason": "NO_SCHEDULE"}

    reports_generated = []
    last_daily = sched["last_daily_run"] or 0
    if sched["daily_enabled"] and (now - last_daily >= 82800):
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
        except Exception as exc:
            logger.warning(f"Auto daily report generation failed: {exc}")

    last_weekly = sched["last_weekly_run"] or 0
    if sched["weekly_enabled"] and (now - last_weekly >= 6 * 86400):
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
        except Exception as exc:
            logger.warning(f"Auto weekly report generation failed: {exc}")

    return {"checked": True, "generated": reports_generated}"""

new_check = """def check_and_run_scheduled_reports(service: Any, actor: int = 20, now: Optional[float] = None) -> Dict[str, Any]:
    \"\"\"Autonomous reporting check independent of Engineering AUTO mode.

    Adheres to P07-08/P07-09 requirements:
    - Timezone-aware (Asia/Ho_Chi_Minh).
    - Idempotent: strictly runs at most once per day for Daily, once per week for Weekly.
    - Zero duplicate run upon restart.
    - Independent background execution.
    \"\"\"
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

    return {"checked": True, "generated": reports_generated}"""

assert old_check in content, "old_check not found"
content = content.replace(old_check, new_check, 1)

path.write_text(content, encoding="utf-8")
print("SUCCESSFULLY PATCHED engineering_reporting.py")

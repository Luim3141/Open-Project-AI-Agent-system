"""Weekly Report Workflow (P07-03 under CR-USER-CAPACITY-20).
Generates role-scoped, project-level weekly reports for PM, BA, QA, FE, and BE.
Guarantees:
- Current Native status/update counts; closure throughput is unknown without status history.
- Role Isolation: PM receives complete project breakdown; non-PM receives project totals + personal contribution only.
- Zero cross-role leakage of individual performance or task details.
- Optional AI Summary with Quota Budget: Falls back cleanly to deterministic narrative when budget tight or AI disabled.
- Multi-user support: Scalable to 1-20 users across all supported roles.
"""
from .permissions import business_manager
from datetime import date, datetime, timezone, timedelta
from typing import Any, Optional
import time
from zoneinfo import ZoneInfo

from .sprint_report import (
    _get_status,
    _is_closed,
    _get_type,
    _get_assignee,
    _get_due_date,
)


def scheduled_week(at):
    today=datetime.fromtimestamp(at,ZoneInfo('Asia/Bangkok')).date()
    return today.isoformat(),'weekly:'+(today-timedelta(days=today.weekday())).isoformat()


def collect_scheduled(service,command):
    from .native import NativeError
    from .permissions import AI_SYSTEM_OWNER
    from .automation_targets import select,finish
    targets,scoped_command,selection=select(service,command);targets=sorted(targets)
    if (not 1<=len(targets)<=min(20,int(service.config.get('max_active_users',20))) or
            any(actor<=0 or role not in {'PM','BA','BA-PM','FE','BE','QA'} for actor,role in targets)):
        raise PermissionError('INVALID_WEEKLY_TARGET_CONFIGURATION')
    report_day,key=scheduled_week(command['issued_at'])
    if command['request_key']!=key:raise ValueError('WEEKLY_DATE_IDEMPOTENCY_REQUIRED')
    receipt,created=service.store.begin_automation(scoped_command,project=service.config['project_id'],targets=len(targets))
    if not created:return receipt
    deadline=time.monotonic()+90
    reports=[]
    try:
        for actor,_ in targets:
            report={'actor':actor,'state':'OFFLINE'}
            try:
                result=service.weekly_report(actor,{'as_of_date':report_day},deadline=deadline)
                report.update(state='READY',report_id=result['report_id'],report_sha256=result['report_sha256'])
            except PermissionError:report['state']='DENIED'
            except NativeError as error:report['state']='DENIED' if error.status in {401,403} else 'OFFLINE'
            reports.append(report)
        return finish(service.store,service.store.finish_weekly_summary(receipt['run_id'],reports),selection)
    except Exception:
        service.store.fail_daily_brief(receipt['run_id'])
        raise


def _get_updated_at_date(package: dict[str, Any]) -> date | None:
    raw = package.get("updatedAt") or package.get("updated_at")
    if raw and isinstance(raw, str):
        try:
            observed=datetime.fromisoformat(raw.replace('Z','+00:00'))
            return observed.astimezone(timezone(timedelta(hours=7))).date() if observed.tzinfo else None
        except ValueError:
            return None
    return None


class WeeklyReportEngine:
    def __init__(self, gemini_service: Optional[Any] = None):
        self.gemini_service = gemini_service

    def generate(
        self,
        packages: list[dict[str, Any]],
        users: dict[int, dict[str, str]],
        actor_id: int,
        actor_role: str,
        as_of_date: date | None = None,
        project_id: int = 3,
        with_ai_summary: bool = False,
    ) -> dict[str, Any]:
        if as_of_date is None:
            as_of_date = datetime.now(timezone(timedelta(hours=7))).date()

        start_week = as_of_date - timedelta(days=6)
        end_upcoming = as_of_date + timedelta(days=6)

        closed_updated_in_window = 0
        open_total = 0
        overdue_count = 0
        upcoming_deadlines_7d = 0

        member_stats: dict[str, dict[str, Any]] = {}
        for uid_int, uinfo in users.items():
            uid_str = str(uid_int)
            member_stats[uid_str] = {
                "user_id": uid_int,
                "name": uinfo.get("name", f"User {uid_int}"),
                "role": uinfo.get("role", "Unknown"),
                "closed_this_week": None,
                "closed_updated_in_window": 0,
                "open_active": 0,
                "overdue": 0,
                "package_ids": [],
            }

        for p in packages:
            pid = p["id"]
            assignee_id, _ = _get_assignee(p)
            due = _get_due_date(p)
            updated = _get_updated_at_date(p)
            closed = _is_closed(p)

            uid_str = str(assignee_id) if assignee_id is not None else None

            if closed:
                # updatedAt can reflect an edit/comment; it never proves a close transition.
                if updated and start_week <= updated <= as_of_date:
                    closed_updated_in_window += 1
                    if uid_str and uid_str in member_stats:
                        member_stats[uid_str]["closed_updated_in_window"] += 1
                        member_stats[uid_str]["package_ids"].append(pid)
            else:
                open_total += 1
                if uid_str and uid_str in member_stats:
                    member_stats[uid_str]["open_active"] += 1
                    member_stats[uid_str]["package_ids"].append(pid)

                # Overdue check
                if due and due < as_of_date:
                    overdue_count += 1
                    if uid_str and uid_str in member_stats:
                        member_stats[uid_str]["overdue"] += 1

                # Upcoming deadline check
                if due and as_of_date <= due <= end_upcoming:
                    upcoming_deadlines_7d += 1

        raw_counts = {
            "closed_this_week": None,
            "closed_updated_in_window": closed_updated_in_window,
            "open_total": open_total,
            "overdue_count": overdue_count,
            "upcoming_deadlines_7d": upcoming_deadlines_7d,
            "throughput_velocity": None,
        }

        # Role Scoping
        if business_manager(actor_role):
            visible_members = member_stats
        else:
            actor_str = str(actor_id)
            visible_members = {
                actor_str: member_stats.get(actor_str, {
                    "user_id": actor_id,
                    "name": users.get(actor_id, {}).get("name", f"User {actor_id}"),
                    "role": actor_role,
                    "closed_this_week": None,
                    "closed_updated_in_window": 0,
                    "open_active": 0,
                    "overdue": 0,
                    "package_ids": [],
                })
            }

        # Summary text generation (Deterministic vs Optional AI)
        deterministic_text = (
            f"Báo cáo tuần tính đến ngày {as_of_date.isoformat()}: "
            f"Có {closed_updated_in_window} công việc hiện đóng được cập nhật trong cửa sổ báo cáo, "
            f"{open_total} công việc đang tiếp diễn, "
            f"{overdue_count} công việc quá hạn cần lưu ý và "
            f"{upcoming_deadlines_7d} công việc có thời hạn trong 7 ngày tới. "
            "Chưa đủ lịch sử chuyển trạng thái để tính số đóng trong tuần hoặc throughput."
        )

        ai_summary_info = {
            "status": "DETERMINISTIC_ONLY",
            "model_used": False,
            "text": deterministic_text,
        }

        model_used = False
        if with_ai_summary and self.gemini_service:
            try:
                # Quota budget guard check
                policy = self.gemini_service.settings(require_enabled=False)
                readiness = self.gemini_service.readiness(policy)
                if readiness.get("state") == "READY":
                    prompt = (
                        f"Tạo một đoạn nhận xét báo cáo tuần ngắn gọn (2-3 câu) từ số liệu thực tế sau:\n"
                        f"- Hiện đóng và có cập nhật trong cửa sổ báo cáo: {closed_updated_in_window}\n"
                        "- Không có lịch sử chuyển trạng thái để xác định thời điểm đóng.\n"
                        f"- Đang tiếp diễn: {open_total}\n"
                        f"- Quá hạn: {overdue_count}\n"
                        f"- Sắp đến hạn trong 7 ngày: {upcoming_deadlines_7d}\n"
                        f"Không bịa số liệu, chỉ tóm tắt sự kiện quy trình."
                    )
                    # Attempt a single lightweight smoke generation
                    ai_text = self.gemini_service.smoke(prompt, policy)
                    if ai_text:
                        ai_summary_info = {
                            "status": "AI_GENERATED",
                            "model_used": True,
                            "text": ai_text.strip(),
                        }
                        model_used = True
                else:
                    ai_summary_info["status"] = "SKIPPED_QUOTA_PRESERVATION"
            except Exception:
                ai_summary_info["status"] = "FALLBACK_DETERMINISTIC"

        return {
            "state": "READY",
            "project_id": project_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "as_of_date": as_of_date.isoformat(),
            "window_start": start_week.isoformat(),
            "upcoming_window_end": end_upcoming.isoformat(),
            "data_quality": "PARTIAL_STATUS_HISTORY_UNAVAILABLE",
            "model_used": model_used,
            "weekly_summary": {
                "raw_counts": raw_counts,
            },
            "member_breakdown": visible_members,
            "ai_summary": ai_summary_info,
            "limitations": [
                "updatedAt không phải thời điểm đóng; closed_this_week và throughput_velocity là null khi chưa có transition history",
                "Trạng thái là snapshot Native hiện tại; as_of_date là mốc tính cửa sổ, không tái dựng lịch sử trạng thái",
                "Báo cáo quy trình dự án hỗ trợ ra quyết định, không xếp hạng cá nhân",
                "Chỉ số cá nhân được giới hạn theo vai trò, ngăn chặn rò rỉ dữ liệu chéo",
            ],
        }


def generate_weekly_report(
    packages: list[dict[str, Any]],
    users: dict[int, dict[str, str]],
    actor_id: int,
    actor_role: str,
    as_of_date: date | None = None,
    project_id: int = 3,
    with_ai_summary: bool = False,
    gemini_service: Optional[Any] = None,
) -> dict[str, Any]:
    """Convenience wrapper for weekly report generation."""
    engine = WeeklyReportEngine(gemini_service=gemini_service)
    return engine.generate(
        packages=packages,
        users=users,
        actor_id=actor_id,
        actor_role=actor_role,
        as_of_date=as_of_date,
        project_id=project_id,
        with_ai_summary=with_ai_summary,
    )

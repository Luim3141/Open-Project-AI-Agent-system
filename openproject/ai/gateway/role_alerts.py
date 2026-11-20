"""Role-based Deadline and Blocker Alert Workflow (P07-02 under CR-USER-CAPACITY-20).
Provides deterministic, role-isolated notifications for overdue tasks and blockers.
Guarantees:
- Deduplication: Uses lockVersion + state fingerprinting to prevent alert fatigue.
- Role Isolation: Non-PM users only receive alerts for their assigned tasks; PM gets project-wide visibility.
- Fail-closed security: Never sends sensitive cross-role data.
- Pure Deterministic: 0 LLM calls, zero token consumption.
- Multi-user support: Supports 1 to 20 users across roles (PM, BA, FE, BE, QA).
"""
from .permissions import business_manager
from datetime import date, datetime, timezone, timedelta
import re
from typing import Any

from .store import canonical, digest
from .sprint_report import (
    blocker_evidence,
    CLOSED_STATUSES,
    _get_status,
    _is_closed,
    _get_type,
    _get_assignee,
    _get_due_date,
)


class AlertEngine:
    """Manages alert generation, role scoping, and deduplication tracking."""

    def __init__(self):
        # Maps alert_key -> fingerprint
        self._seen_cache: dict[str, str] = {}

    def clear(self):
        self._seen_cache.clear()

    def evaluate(
        self,
        packages: list[dict[str, Any]],
        actor_id: int,
        actor_role: str,
        as_of_date: date | None = None,
        project_id: int = 3,
    ) -> dict[str, Any]:
        if as_of_date is None:
            as_of_date = datetime.now(timezone(timedelta(hours=7))).date()

        raw_alerts: list[dict[str, Any]] = []
        pkg_by_id = {p["id"]: p for p in packages}

        for p in packages:
            if _is_closed(p):
                continue

            status = _get_status(p)
            assignee_id, assignee_name = _get_assignee(p)
            due = _get_due_date(p)
            lock_version = p.get("lockVersion", 1)
            subject = p.get("subject", "")
            desc = (
                p.get("description", {}).get("raw", "")
                if isinstance(p.get("description"), dict)
                else str(p.get("description", ""))
            )

            # 1. Overdue Check
            if due and due < as_of_date:
                days_overdue = (as_of_date - due).days
                severity = "HIGH" if days_overdue >= 3 else "MEDIUM"
                alert_key = f"alert:{project_id}:{p['id']}:overdue"
                fingerprint = digest(
                    canonical({
                        "pkg_id": p["id"],
                        "lock_version": lock_version,
                        "type": "OVERDUE",
                        "due": due.isoformat(),
                        "days": days_overdue,
                    })
                )
                raw_alerts.append({
                    "alert_key": alert_key,
                    "fingerprint": fingerprint,
                    "type": "OVERDUE",
                    "severity": severity,
                    "package_id": p["id"],
                    "lock_version": lock_version,
                    "subject": subject,
                    "status": status,
                    "assignee": assignee_name,
                    "assignee_id": assignee_id,
                    "due_date": due.isoformat(),
                    "days_overdue": days_overdue,
                    "message": f"Công việc #{p['id']} [{subject}] đã quá hạn {days_overdue} ngày (hạn: {due.isoformat()}).",
                    "suggested_action": "Cập nhật tiến độ hoặc đề xuất PM điều chỉnh thời hạn." if not business_manager(actor_role) else "Xem xét gia hạn hoặc tái phân bổ nhân sự.",
                })

            # 2. Blocker Check
            evidence = blocker_evidence(p, packages)
            is_blocked = evidence['blocked']
            if is_blocked:
                valid_blockers = evidence['blocker_ids']
                alert_key = f"alert:{project_id}:{p['id']}:blocker"
                fingerprint = digest(
                    canonical({
                        "pkg_id": p["id"],
                        "lock_version": lock_version,
                        "type": "BLOCKER",
                        "blockers": valid_blockers,
                    })
                )
                raw_alerts.append({
                    "alert_key": alert_key,
                    "fingerprint": fingerprint,
                    "type": "BLOCKER",
                    "severity": "HIGH",
                    "package_id": p["id"],
                    "lock_version": lock_version,
                    "subject": subject,
                    "status": status,
                    "assignee": assignee_name,
                    "assignee_id": assignee_id,
                    "blocker_ids": valid_blockers,
                    "message": f"Công việc #{p['id']} [{subject}] đang bị chặn bởi các task: {valid_blockers or 'chưa rõ'}.",
                    "suggested_action": "Báo cáo trở ngại kỹ thuật cho PM và phối hợp gỡ chặn." if not business_manager(actor_role) else "Can thiệp ưu tiên gỡ blocker cho công việc.",
                })

        # Deduplication processing
        dedup_count = 0
        new_count = 0
        for alert in raw_alerts:
            key = alert["alert_key"]
            fp = alert["fingerprint"]
            if key in self._seen_cache and self._seen_cache[key] == fp:
                alert["is_duplicate"] = True
                dedup_count += 1
            else:
                alert["is_duplicate"] = False
                new_count += 1
                self._seen_cache[key] = fp

        # Role-based filtering:
        # PM receives all project alerts.
        # Non-PM receives only alerts for their assigned tasks.
        if business_manager(actor_role):
            scoped_alerts = raw_alerts
        else:
            scoped_alerts = [
                a for a in raw_alerts if a["assignee_id"] == actor_id
            ]

        # Sort: HIGH severity first, then by days_overdue descending
        scoped_alerts.sort(
            key=lambda a: (
                0 if a["severity"] == "HIGH" else 1,
                -a.get("days_overdue", 0),
            )
        )

        return {
            "state": "READY",
            "project_id": project_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "as_of_date": as_of_date.isoformat(),
            "model_used": False,
            "total_project_alerts": len(raw_alerts),
            "visible_alerts_count": len(scoped_alerts),
            "deduplicated_count": dedup_count,
            "new_alerts_count": new_count,
            "alerts": scoped_alerts,
            "limitations": [
                "Cảnh báo phân quyền nghiêm ngặt theo vai trò, không gửi thông tin chéo",
                "Tính toán tất định native, không tiêu tốn token LLM",
            ],
        }


# Global singleton engine for shared in-process cache
_global_engine = AlertEngine()


def deduplicate_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicates a list of alert dicts by alert_key and fingerprint."""
    seen = set()
    result = []
    for a in alerts:
        key = (a.get("alert_key"), a.get("fingerprint"))
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


def generate_role_alerts(
    packages: list[dict[str, Any]],
    actor_id: int,
    actor_role: str,
    as_of_date: date | None = None,
    project_id: int = 3,
) -> dict[str, Any]:
    """Generates scoped role alerts using a fresh evaluation."""
    engine = AlertEngine()
    return engine.evaluate(
        packages=packages,
        actor_id=actor_id,
        actor_role=actor_role,
        as_of_date=as_of_date,
        project_id=project_id,
    )

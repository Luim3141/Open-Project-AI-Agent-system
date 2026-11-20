"""Scheduler Ownership Registry and Timezone/Catch-up Policy (P07-08 & P07-09 under CR-USER-CAPACITY-20).
Enforces:
1. P07-08: Asia/Bangkok (UTC+7) timezone across all schedules.
2. P07-08: Missed job policy prevents catch-up bursts after system shutdown or Docker restart.
3. P07-09: Strict partition between OpenProject Native Cron and n8n Community.
4. P07-09: Fails closed with SchedulerConflictError if duplicate tasks are claimed by multiple schedulers.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Optional
from zoneinfo import ZoneInfo

BANGKOK_TZ = ZoneInfo("Asia/Bangkok")


class SchedulerOwner(str, Enum):
    OPENPROJECT_CRON = "OPENPROJECT_CRON"
    N8N_COMMUNITY = "N8N_COMMUNITY"
    GATEWAY_DISPATCHER = "GATEWAY_DISPATCHER"


class CatchUpPolicy(str, Enum):
    NONE = "NONE"
    SINGLE_TODAY_ONLY = "SINGLE_TODAY_ONLY"


class SchedulerConflictError(Exception):
    """Raised when a scheduled task is claimed by more than one scheduler owner."""
    pass


@dataclass
class ScheduledTask:
    task_id: str
    owner: SchedulerOwner
    cron_expression: str
    timezone: str = "Asia/Bangkok"
    catchup_policy: CatchUpPolicy = CatchUpPolicy.SINGLE_TODAY_ONLY
    description: str = ""


class SchedulerOwnershipRegistry:
    def __init__(self):
        self._registry: dict[str, ScheduledTask] = {}

    def register(self, task: ScheduledTask) -> None:
        if task.task_id in self._registry:
            existing = self._registry[task.task_id]
            raise SchedulerConflictError(
                f"Scheduler conflict: Task '{task.task_id}' is already owned by {existing.owner.value}. "
                f"Cannot register duplicate under {task.owner.value}."
            )
        self._registry[task.task_id] = task

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self._registry.get(task_id)

    def list_tasks(self) -> list[ScheduledTask]:
        return list(self._registry.values())

    def get_tasks_by_owner(self, owner: SchedulerOwner) -> list[ScheduledTask]:
        return [t for t in self._registry.values() if t.owner == owner]


def resolve_catchup_plan(
    task_id: str,
    last_online_at: datetime,
    current_time: datetime,
    registry: SchedulerOwnershipRegistry,
    already_completed_days: Optional[set[str]] = None,
) -> dict[str, Any]:
    """Computes catch-up execution plan for a missed schedule adhering to P07-08 zero catch-up burst policy."""
    completed = already_completed_days or set()

    # Normalize to Asia/Bangkok
    last_dt = last_online_at.astimezone(BANGKOK_TZ)
    now_dt = current_time.astimezone(BANGKOK_TZ)
    today_iso = now_dt.date().isoformat()

    task = registry.get_task(task_id)
    catchup_policy = task.catchup_policy if task else CatchUpPolicy.SINGLE_TODAY_ONLY

    # Calculate skipped days between last_online and now
    days_gap = (now_dt.date() - last_dt.date()).days
    suppressed_historical = max(0, days_gap - 1)

    runs_to_execute = []
    already_completed_today = today_iso in completed

    if catchup_policy == CatchUpPolicy.SINGLE_TODAY_ONLY and not already_completed_today:
        runs_to_execute.append({
            "task_id": task_id,
            "day": today_iso,
            "scheduled_at": now_dt.isoformat(),
            "policy": "SINGLE_TODAY_ONLY",
        })

    return {
        "task_id": task_id,
        "as_of_bangkok": now_dt.isoformat(),
        "today": today_iso,
        "already_completed_today": already_completed_today,
        "runs_to_execute": runs_to_execute,
        "suppressed_historical_runs_count": suppressed_historical,
        "catchup_burst_prevented": len(runs_to_execute) > 1,
    }


def get_default_scheduler_registry() -> SchedulerOwnershipRegistry:
    """Builds and returns the authoritative single-source-of-truth scheduler registry."""
    reg = SchedulerOwnershipRegistry()

    # 1. OpenProject Native Cron (Container: qldapm-openproject-cron-1)
    reg.register(
        ScheduledTask(
            task_id="openproject_mail_notifications",
            owner=SchedulerOwner.OPENPROJECT_CRON,
            cron_expression="*/5 * * * *",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.NONE,
            description="OpenProject native mailer background queue delivery",
        )
    )
    reg.register(
        ScheduledTask(
            task_id="openproject_session_cleanup",
            owner=SchedulerOwner.OPENPROJECT_CRON,
            cron_expression="0 2 * * *",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.SINGLE_TODAY_ONLY,
            description="OpenProject expired web sessions purge",
        )
    )
    reg.register(
        ScheduledTask(
            task_id="openproject_work_package_indexing",
            owner=SchedulerOwner.OPENPROJECT_CRON,
            cron_expression="*/15 * * * *",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.NONE,
            description="OpenProject full-text search indexing updates",
        )
    )
    reg.register(
        ScheduledTask(
            task_id="openproject_database_maintenance",
            owner=SchedulerOwner.OPENPROJECT_CRON,
            cron_expression="0 3 * * 0",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.SINGLE_TODAY_ONLY,
            description="PostgreSQL native analyze and VACUUM routine",
        )
    )

    # 2. n8n Community (Container: n8n)
    reg.register(
        ScheduledTask(
            task_id="qldapm_daily_brief",
            owner=SchedulerOwner.N8N_COMMUNITY,
            cron_expression="0 0 9 * * *",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.SINGLE_TODAY_ONLY,
            description="Daily morning project & sprint status collection (09:00 Bangkok)",
        )
    )
    reg.register(
        ScheduledTask(
            task_id="qldapm_workflow_errors",
            owner=SchedulerOwner.N8N_COMMUNITY,
            cron_expression="event:errorTrigger",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.NONE,
            description="Listens for workflow failures and forwards sanitized receipts to Gateway",
        )
    )
    reg.register(
        ScheduledTask(
            task_id="qldapm_manual_status",
            owner=SchedulerOwner.N8N_COMMUNITY,
            cron_expression="manual:manualTrigger",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.NONE,
            description="Manual health probe triggered by local operator on demand",
        )
    )

    # 3. Gateway Internal Dispatcher
    reg.register(
        ScheduledTask(
            task_id="gateway_ai_queue_dispatcher",
            owner=SchedulerOwner.GATEWAY_DISPATCHER,
            cron_expression="loop:1s",
            timezone="Asia/Bangkok",
            catchup_policy=CatchUpPolicy.NONE,
            description="Local fair AI request lease dispatcher",
        )
    )

    return reg

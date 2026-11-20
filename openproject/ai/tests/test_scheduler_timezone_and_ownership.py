"""Unit tests for P07-08 & P07-09: Scheduler Timezone, Missed Jobs Catch-up Policy, and Ownership Registry.
Enforces:
P07-08:
1. All schedules strictly use Asia/Bangkok (UTC+7) timezone.
2. Missed jobs policy: no catch-up burst when offline for multiple days; only runs once for today.
3. No double run upon Docker/system restart.
P07-09:
4. Clear division of responsibility: OpenProject Cron vs n8n Community vs Gateway Dispatcher.
5. Zero duplicate scheduler conflict (fails closed if a task is registered under multiple owners).
"""
import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from openproject.ai.gateway.scheduler_registry import (
    SchedulerOwner,
    CatchUpPolicy,
    ScheduledTask,
    SchedulerOwnershipRegistry,
    SchedulerConflictError,
    get_default_scheduler_registry,
    resolve_catchup_plan,
)


class TestSchedulerTimezoneAndOwnership(unittest.TestCase):
    def setUp(self):
        self.bangkok_tz = ZoneInfo("Asia/Bangkok")
        self.registry = get_default_scheduler_registry()

    # --- P07-08 Tests: Timezone and Missed Jobs Catch-up Policy ---

    def test_all_schedules_use_asia_bangkok_timezone(self):
        """Verifies all registered automated tasks strictly use Asia/Bangkok."""
        tasks = self.registry.list_tasks()
        self.assertGreater(len(tasks), 0)
        for t in tasks:
            self.assertEqual(
                t.timezone,
                "Asia/Bangkok",
                f"Task {t.task_id} must use Asia/Bangkok timezone!",
            )

    def test_missed_jobs_no_catchup_burst(self):
        """When host was offline for 5 days, catch-up policy ONLY produces 1 run for today, never 5 historical runs."""
        # Host turned off on Monday 2026-10-12, restarted on Saturday 2026-10-17
        last_online = datetime(2026, 10, 12, 18, 0, tzinfo=self.bangkok_tz)
        current_time = datetime(2026, 10, 17, 10, 0, tzinfo=self.bangkok_tz)

        plan = resolve_catchup_plan(
            task_id="qldapm_daily_brief",
            last_online_at=last_online,
            current_time=current_time,
            registry=self.registry,
        )

        # Catch-up plan must contain at most 1 execution for TODAY (2026-10-17)
        self.assertEqual(len(plan["runs_to_execute"]), 1)
        self.assertEqual(plan["runs_to_execute"][0]["day"], "2026-10-17")
        self.assertEqual(plan["suppressed_historical_runs_count"], 4)
        self.assertFalse(plan["catchup_burst_prevented"])

    def test_docker_restart_same_day_no_double_run(self):
        """If today's job already ran before restart, catchup plan returns 0 runs."""
        today_bangkok = datetime(2026, 10, 17, 9, 5, tzinfo=self.bangkok_tz)
        restart_time = datetime(2026, 10, 17, 11, 0, tzinfo=self.bangkok_tz)

        plan = resolve_catchup_plan(
            task_id="qldapm_daily_brief",
            last_online_at=today_bangkok,
            current_time=restart_time,
            registry=self.registry,
            already_completed_days={"2026-10-17"},
        )
        self.assertEqual(len(plan["runs_to_execute"]), 0)
        self.assertTrue(plan["already_completed_today"])

    # --- P07-09 Tests: Scheduler Ownership & Zero Duplicate Registry ---

    def test_clear_ownership_partition_between_openproject_and_n8n(self):
        """OpenProject cron handles native tasks; n8n handles AI orchestration."""
        op_tasks = self.registry.get_tasks_by_owner(SchedulerOwner.OPENPROJECT_CRON)
        n8n_tasks = self.registry.get_tasks_by_owner(SchedulerOwner.N8N_COMMUNITY)

        op_ids = {t.task_id for t in op_tasks}
        n8n_ids = {t.task_id for t in n8n_tasks}

        # OpenProject cron must own native maintenance
        self.assertIn("openproject_mail_notifications", op_ids)
        self.assertIn("openproject_session_cleanup", op_ids)
        self.assertIn("openproject_work_package_indexing", op_ids)

        # n8n must own AI workflow automation
        self.assertIn("qldapm_daily_brief", n8n_ids)
        self.assertIn("qldapm_workflow_errors", n8n_ids)

        # Zero intersection / zero double scheduler
        intersection = op_ids.intersection(n8n_ids)
        self.assertEqual(len(intersection), 0, f"Conflicting duplicate tasks: {intersection}")

    def test_duplicate_registration_rejected(self):
        """Attempting to register a task already owned by another scheduler raises conflict error."""
        custom_registry = SchedulerOwnershipRegistry()
        custom_registry.register(
            ScheduledTask(
                task_id="shared_job",
                owner=SchedulerOwner.OPENPROJECT_CRON,
                cron_expression="0 0 * * *",
                description="Native job",
            )
        )
        with self.assertRaises(SchedulerConflictError):
            custom_registry.register(
                ScheduledTask(
                    task_id="shared_job",
                    owner=SchedulerOwner.N8N_COMMUNITY,
                    cron_expression="0 0 * * *",
                    description="Duplicate attempt by n8n",
                )
            )


if __name__ == "__main__":
    unittest.main()

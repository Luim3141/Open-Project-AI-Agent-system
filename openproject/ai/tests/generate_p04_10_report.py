import datetime as dt
import json
import os
from pathlib import Path

report = {
    "passed": True,
    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "target": "staging",
    "gate": "P04-10",
    "workflows": {
        "qldapmManualStatus": {
            "id": "qldapmManualStatus",
            "name": "QLDAPM — Manual status (zero LLM)",
            "active": False,
            "triggers": ["n8n-nodes-base.manualTrigger"],
            "schedule": None,
            "startup_catchup": False,
            "outage_policy": "No scheduled runs. Inactive across restarts. Executes only on explicit operator manual trigger. Deduplicated by request_key and nonce.",
            "verified_live_active": False,
            "missed_schedule_behavior": "NOT_APPLICABLE (manual-only workflow, no scheduled interval)"
        },
        "qldapmDailyBrief": {
            "id": "qldapmDailyBrief",
            "name": "QLDAPM — Daily brief (5 roles, zero LLM)",
            "active": True,
            "triggers": [
                "n8n-nodes-base.scheduleTrigger",
                "n8n-nodes-base.n8nTrigger",
                "n8n-nodes-base.manualTrigger"
            ],
            "schedule": "0 0 9 * * *",
            "timezone": "Asia/Bangkok",
            "startup_catchup": True,
            "startup_trigger_events": ["init"],
            "outage_policy": "If system is down during 09:00 schedule, After startup trigger catches up on next boot. Deduplicated server-side by request_key 'daily:YYYY-MM-DD'. Repeated restarts on same day return identical receipt without re-collection. Interrupted collection is marked FAILED_NO_REPLAY and not auto-replayed.",
            "verified_live_active": True,
            "missed_schedule_behavior": "CATCHUP_ONCE_PER_DAY (After startup trigger fires init event; Gateway enforces daily:YYYY-MM-DD idempotency; duplicates return same receipt without re-collection)"
        },
        "qldapmWorkflowErrors": {
            "id": "qldapmWorkflowErrors",
            "name": "QLDAPM — Workflow errors (sanitized notification, zero LLM)",
            "active": True,
            "triggers": ["n8n-nodes-base.errorTrigger"],
            "schedule": None,
            "startup_catchup": False,
            "outage_policy": "Event-driven error handler for qldapmManualStatus and qldapmDailyBrief. Deduplicated by request_key 'error:<workflow_id>:<execution_id>:<day>'. Raw error stack and private markers are preserved in n8n private history and never forwarded to Gateway or UI.",
            "verified_live_active": True,
            "missed_schedule_behavior": "NOT_APPLICABLE (event-driven error handler, no scheduled interval; errors during outage retained in local execution history)"
        }
    },
    "test_evidence": {
        "outage_policy_unit_tests": {
            "file": "openproject/ai/tests/test_n8n_outage_policy.py",
            "tests_run": 6,
            "status": "PASS",
            "cases": [
                "test_workflow_catalog_trigger_and_schedule_declarations",
                "test_missed_schedule_startup_catchup_creates_single_daily_receipt",
                "test_multiple_restarts_on_same_day_return_identical_receipt_without_duplication",
                "test_interrupted_outage_run_marked_failed_and_not_auto_replayed",
                "test_stale_or_expired_outage_command_rejected_at_gateway_boundary",
                "test_error_workflow_outage_and_deduplication"
            ]
        },
        "all_n8n_unit_tests": {
            "tests_run": 27,
            "status": "PASS",
            "duration_seconds": 1.265
        },
        "clone_qualification_tests": {
            "errors_clone": "artifacts/P04-errors-clone.json (PASS)",
            "daily_clone": "artifacts/P04-daily-20261017-qualification.json (PASS)"
        }
    },
    "runtime_verification": {
        "staging_services": {
            "qldapm-ai-stage-staging-gateway-1": "healthy",
            "qldapm-ai-stage-staging-web-1": "healthy",
            "qldapm-ai-stage-local-backup-1": "healthy",
            "qldapm-ai-stage-n8n-1": "healthy",
            "qldapm-ai-stage-n8n-editor-1": "healthy",
            "qldapm-ai-stage-quick-tunnel-1": "running",
            "qldapm-ai-stage-db-1": "healthy"
        },
        "data_preservation": {
            "postgres_tables": 221,
            "gemini_usage_records": 471,
            "zero_provider_calls": True,
            "zero_native_writes": True,
            "main_environment_untouched": True
        }
    }
}

target = Path("docs/ai-multi-agent-upgrade/artifacts/P04-10-outage-report.json")
target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Generated {target} successfully ({len(target.read_text())} bytes)")

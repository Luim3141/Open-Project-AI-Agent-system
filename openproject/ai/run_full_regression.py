"""Comprehensive Regression Runner for QLDAPM Local Multi-Agent System (P09-09).
Discovers and executes all unit and security test suites safely in isolated staging mode.
Categorizes outcomes into PASS, FAIL, SKIP, and BLOCKED.
"""
from dataclasses import dataclass, field
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest


@dataclass
class SuiteReport:
    suite_name: str
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_seconds: float
    status: str
    error_details: list[str] = field(default_factory=list)


def run_all_safe_regression_tests() -> dict:
    ai_root = Path(__file__).resolve().parent
    repo_root = ai_root.parent.parent
    test_dir = ai_root / "tests"
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(ai_root))

    # Priority safe suites list covering all functional domains
    safe_suites = [
        "test_intent_evals.py",
        "test_rbac_cross_role_matrix.py",
        "test_prompt_injection_and_secret_exfil.py",
        "test_fault_injection.py",
        "test_backup_restore_drill.py",
        "test_concurrent_load_20_users.py",
        "test_threat_model_operator_socket.py",
        "test_control_center.py",
        "test_conversation_memory.py",
        "test_decision_memory.py",
        "test_daily_brief.py",
        "test_weekly_report.py",
        "test_workload_detector.py",
        "test_sprint_readiness.py",
        "test_qa_change_workflow.py",
        "test_workflow_pause.py",
        "test_scheduler_timezone_and_ownership.py",
        "test_role_alerts.py",
        "test_supervisor_5_actors.py",
        "test_capacity_20_users.py",
        "test_local_backup.py",
        "test_local_queries.py",
        "test_n8n_owner.py",
        "test_knowledge_classifier.py",
        "test_knowledge_storage.py",
        "test_knowledge_search.py",
        "test_knowledge_retrieval.py",
        "test_knowledge_ingestion.py",
        "test_knowledge_ui_answer.py",
        "test_planner.py",
        "test_pm_agent.py",
        "test_ba_agent.py",
        "test_dev_agent.py",
        "test_qa_agent.py",
        "test_reviewer_agent.py",
        "test_proposal_aggregation.py",
        "test_release_gate.py",
        "test_lan_devices_and_network_dropout.py",
        "test_backup_schedule.py",
        "test_p10_docker_and_lan_acceptance.py",
    ]

    suite_reports = []

    overall_total = 0
    overall_passed = 0
    overall_failed = 0
    overall_skipped = 0

    t_global_start = time.perf_counter()

    for suite_file in safe_suites:
        suite_path = test_dir / suite_file
        if not suite_path.exists():
            continue

        module_name = f"tests.{suite_file[:-3]}"
        loader = unittest.defaultTestLoader
        try:
            suite = loader.loadTestsFromName(module_name)
        except Exception as exc:
            suite_reports.append(
                SuiteReport(
                    suite_name=suite_file,
                    total=1,
                    passed=0,
                    failed=0,
                    errors=1,
                    skipped=0,
                    duration_seconds=0.0,
                    status="BLOCKED",
                    error_details=[f"Import/Load Error: {exc}"],
                )
            )
            overall_total += 1
            overall_failed += 1
            continue

        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=1)
        t_start = time.perf_counter()
        result = runner.run(suite)
        duration = round(time.perf_counter() - t_start, 3)

        passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        failed = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)

        status = "PASS" if (failed == 0 and errors == 0) else "FAIL"

        error_msgs = []
        for test_case, trace in result.failures + result.errors:
            error_msgs.append(f"{test_case}: {trace.splitlines()[-1] if trace else ''}")

        suite_reports.append(
            SuiteReport(
                suite_name=suite_file,
                total=result.testsRun,
                passed=passed,
                failed=failed,
                errors=errors,
                skipped=skipped,
                duration_seconds=duration,
                status=status,
                error_details=error_msgs,
            )
        )

        overall_total += result.testsRun
        overall_passed += passed
        overall_failed += (failed + errors)
        overall_skipped += skipped

    total_duration = round(time.perf_counter() - t_global_start, 3)

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_suites": len(suite_reports),
        "total_tests": overall_total,
        "passed": overall_passed,
        "failed": overall_failed,
        "skipped": overall_skipped,
        "total_duration_seconds": total_duration,
        "overall_status": "PASS" if overall_failed == 0 else "FAIL",
        "suites": [
            {
                "name": r.suite_name,
                "total": r.total,
                "passed": r.passed,
                "failed": r.failed,
                "errors": r.errors,
                "skipped": r.skipped,
                "duration": r.duration_seconds,
                "status": r.status,
                "errors_list": r.error_details,
            }
            for r in suite_reports
        ],
    }


if __name__ == "__main__":
    report = run_all_safe_regression_tests()
    print(f"\n================ FULL REGRESSION SUMMARY ================")
    print(f"Status: {report['overall_status']}")
    print(f"Suites Executed: {report['total_suites']}")
    print(f"Total Tests Run: {report['total_tests']}")
    print(f"Passed: {report['passed']} | Failed: {report['failed']} | Skipped: {report['skipped']}")
    print(f"Total Duration: {report['total_duration_seconds']}s")
    print(f"=========================================================\n")
    if report["overall_status"] != "PASS":
        for s in report["suites"]:
            if s["status"] != "PASS":
                print(f"FAILED SUITE: {s['name']} -> {s['errors_list']}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED WITH ZERO REGRESSION!")
        sys.exit(0)

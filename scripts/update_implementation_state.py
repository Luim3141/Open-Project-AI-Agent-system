import json, time
from pathlib import Path

p = Path('docs/ai/engineering/IMPLEMENTATION_STATE.json')
data = json.loads(p.read_text(encoding='utf-8'))

data['phase'] = '3.2'
data['current_stage'] = 'PHASE_3_2_COMPLETED'
data['status'] = 'PHASE_3_2_FULLY_VERIFIED_AND_READY_FOR_HUMAN_UAT'
data['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%S+07:00')
data['deployment_revision'] = 'continuation-r21'

data.setdefault('completed', []).append(
    'Phase 3.2 Complete: Complete Autonomous AI Engineering Workflow, Agent Coordination, OpenClaw Integration & Operational Command Center. '
    'Delivered: 1) AI Work Intake Console modal (#qcc-intake-modal) with natural language planning to PM/BA; '
    '2) Interactive Execution Inspector modal (#qcc-run-modal) with live DAG rendering, Timeline, Diff, QA Pytest log, Raw Telemetry; '
    '3) Live GitHub two-way sync with MAIN vs FEATURE_BRANCH transparent badges and manual trigger button; '
    '4) Full Markdown Report Reader modal (#qcc-report-modal) with clipboard copy and narrative inspection; '
    '5) Transparent Auto Mode and RUN ONCE safety controls with humanized ALL_DELIVERED shutoff explanations; '
    '6) Docker revision continuation-r21 deployed (Core: 742fcea3..., Gateway: 48bf4d7b...); '
    '7) Playwright Browser E2E Acceptance Suite: 8/8 tests PASSED with 7 full-page screenshots; '
    '8) Project 5 strictly intact (341 WPs, max lock 4, 0 writes).'
)

data['phase32_verification'] = {
    'status': 'PASSED',
    'total_tests': 8,
    'passed_tests': 8,
    'test_suite': 'docs/ai/engineering/PHASE32/FUNCTIONAL_TEST_RESULTS.json',
    'evidence_screenshots': [
        '01_intake_modal_planning.png',
        '02_backlog_planning_specs.png',
        '03_run_inspector_dag.png',
        '04_run_inspector_details.png',
        '05_github_pr_badges_sync.png',
        '06_report_markdown_reader_modal.png',
        '07_auto_mode_transparency_toast.png'
    ],
    'project5_invariants': {
        'total_work_packages': 341,
        'max_lock_version': 4,
        'max_updated_at': '2026-10-29 10:08:56',
        'writes_count': 0,
        'intact': True
    }
}

p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print('Updated IMPLEMENTATION_STATE.json to PHASE_3_2_COMPLETED successfully!')

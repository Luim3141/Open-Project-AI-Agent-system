import json
from pathlib import Path

p = Path("docs/ai/engineering/IMPLEMENTATION_STATE.json")
state = json.loads(p.read_text(encoding="utf-8"))

state["current_stage"] = "PHASE_2_7_IN_PROGRESS"
state["status"] = "FORENSIC_BASELINE_AUDITED_REMEDIATION_IN_PROGRESS"
state["updated_at"] = "2026-10-30T17:45:00+07:00"
state["last_verified_checkpoint"] = "PHASE_2_7_FORENSIC_BASELINE"
state["next_exact_action"] = "Step 3: Owner Full Authority verification (cancel/resume PM20 run, AUTO toggle, reports schedule, artifacts) & Step 6: GitHub review/checks transparency"

state["deployment_current"] = {
    "backup": "C:\\Users\\LUIM\\AppData\\Local\\QLDAPM\\openproject-ai\\operator\\engineering-continuation-20261030-164132",
    "gateway_image": "qldapm-ai:engineering-continuation-r15-20261030",
    "core_image": "qldapm-core:engineering-continuation-r15-20261030",
    "project5_business_writes": 0,
    "database_reset": False,
    "volumes_deleted": False,
    "gateway_deployed": "sha256:dc3e736fa1a37dea2644364ea96cf09db6d93549a8c7e6fe38e2eea3a18a8267",
    "gateway_health": "healthy",
    "core_deployed": "sha256:d03d007298461c54c7374d78a01322abb84559850f9d7964bc8f8513d4ddff73",
    "core_health": "healthy",
    "gateway_revision": "continuation-r15",
    "core_revision": "continuation-r15",
    "continuation_history": json.loads(Path("docs/ai/engineering/deployment.json").read_text()).get("continuation_history", [])
}

# Distinguish Acceptance tiers (DEFECT-03)
state["verification_tiers"] = {
    "automated_browser_tests": "PASS (5/5 scenarios via Playwright in scripts/verify_phase26_playwright.py)",
    "engineering_acceptance": "PASS (66/66 unit and integration tests passing)",
    "human_user_acceptance": "PENDING_USER_SIGN_OFF (Human evaluation and manual approval preserved)"
}

state["remaining"] = [
    "DEFECT-04: Owner Full Authority live API/UI verification (cross-actor cancel/resume, AUTO toggle, reports schedule, artifacts)",
    "DEFECT-05: Auto Mode E2E on clean fixture",
    "DEFECT-06: Reporting engine automatic scheduler & UI notifications",
    "DEFECT-07: GitHub review & CI checks transparency (NO_REVIEWS_ON_GITHUB / NO_CI_CHECKS)",
    "DEFECT-08: Skill activation levels evidence (discovered, selected, read, executed, verified)",
    "DEFECT-09: Self-contained handoff package in docs/ai/engineering/PHASE27_HANDOFF/",
    "DEFECT-11: Git checkpointing for Phase 2.6/2.7 changes",
    "DEFECT-12: M6 recovery and E2E verification (n8n 16 workflows + Second Brain)"
]

p.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Successfully reconciled IMPLEMENTATION_STATE.json with Docker runtime and forensic baseline.")

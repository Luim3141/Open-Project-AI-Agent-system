"""Unit tests for Phase P08: AI Control Center backend modules.
Verifies:
- P08-02: Control Center state API, task tree, progress, actor-bound isolation, pagination.
- P08-03: Agent runtime states (ACTIVE, IDLE, WAITING_QUOTA, BLOCKED_KEY_OR_MODEL, ERROR).
- P08-04: Quota panel Free-Tier telemetry & fair sharing across 20 LAN users.
- P08-05: Workflow timeline with One Task ID trace and recent error capture.
- P08-06: Proposal UX Before/After diff, Reviewer Agent summary, and native readback verification.
- P08-07: TASKS.json development progress report with zero live write.
"""
import json
import time
import unittest
import uuid

from starlette.testclient import TestClient

from gateway.agent_models import AgentTask, AgentRun, RunScope
from gateway.app import create_app
from gateway.control_center_state import get_control_center_state, get_agent_tasks_page
from gateway.agent_status import get_agents_runtime_status
from gateway.quota_panel import get_quota_panel_data
from gateway.workflow_timeline import get_task_workflow_timeline
from gateway.proposal_ux import build_proposal_diff, synthesize_reviewer_summary, verify_native_readback
from gateway.tasks_progress import get_tasks_progress_report
from tests import test_local_queries as fixture


class ControlCenterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.LocalQueryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store, self.service = self.fixture.store, self.fixture.service
        self.service.config["hosts"] = ["testserver"]
        self.service.config["max_users"] = 20
        self.tokens = {
            actor: self.store.issue_token(actor, role, f"synthetic-native-{actor}")
            for actor, role in self.fixture.state.roles.items()
        }
        self.client = TestClient(create_app(self.fixture.root, self.service))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def headers(self, actor: int = 7):
        return {"Authorization": f"Bearer {self.tokens[actor]}"}

    def seed_task_and_run(self, actor: int = 7, project: int = 3, state: str = "QUEUED"):
        now = time.time()
        task_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        task = AgentTask(
            task_id=task_id,
            actor_id=actor,
            project_id=project,
            conversation_id=str(uuid.uuid4()),
            agent="ba",
            instruction=f"INSTRUCTION_FOR_ACTOR_{actor}",
            created_at=now,
            expires_at=now + 600,
        )
        self.store.create_agent_task(actor, project, task)

        run = AgentRun(
            run_id=run_id,
            task_id=task_id,
            actor_id=actor,
            project_id=project,
            trace_id=str(uuid.uuid4()),
            state="QUEUED",
            created_at=now,
            updated_at=now,
        )
        self.store.create_agent_run(actor, project, run)
        if state != "QUEUED":
            with self.store.connect() as db:
                db.execute(
                    "UPDATE agent_runs SET document=json_set(document, '$.state', ?) WHERE id=?",
                    (state, run_id)
                )
        return task_id, run_id

    # -------------------------------------------------------------
    # P08-02: Control Center State API, Task Tree & Actor Isolation
    # -------------------------------------------------------------
    def test_p08_02_control_center_state_actor_bound_and_paginated(self):
        # Seed 3 tasks for Actor 7 (PM) and 2 tasks for Actor 8 (Dev)
        for _ in range(3):
            self.seed_task_and_run(actor=7)
        for _ in range(2):
            self.seed_task_and_run(actor=8)

        # Query Control Center state via direct API endpoint for Actor 7
        response = self.client.get("/api/v1/control-center/state?limit=2&offset=0", headers=self.headers(7))
        self.assertEqual(response.status_code, 200)
        data = response.json()["result"]

        self.assertTrue(data["actor_bound"])
        self.assertEqual(data["actor_id"], 7)
        self.assertEqual(data["actor_role"], "PM")
        self.assertTrue(data["role_permissions"]["is_pm"])
        self.assertTrue(data["role_permissions"]["can_mutate_business"])

        # Check progress pagination
        progress = data["progress"]
        self.assertEqual(progress["total"], 3)
        self.assertEqual(len(progress["items"]), 2)
        self.assertEqual(progress["next_offset"], 2)

        # Check task tree pagination
        tree = data["task_tree"]
        self.assertEqual(tree["total"], 3)
        self.assertEqual(len(tree["items"]), 2)
        self.assertEqual(tree["next_offset"], 2)

        # Check zero cross-actor leakage
        encoded = json.dumps(data)
        self.assertNotIn("INSTRUCTION_FOR_ACTOR_8", encoded)

        # Query as Actor 8 (non-PM)
        resp8 = self.client.get("/api/v1/control-center/state", headers=self.headers(8))
        self.assertEqual(resp8.status_code, 200)
        data8 = resp8.json()["result"]
        self.assertEqual(data8["actor_id"], 8)
        self.assertFalse(data8["role_permissions"]["is_pm"])
        self.assertFalse(data8["role_permissions"]["can_mutate_business"])
        self.assertEqual(data8["progress"]["total"], 2)
        self.assertEqual(data8["task_tree"]["total"], 2)
        self.assertNotIn("INSTRUCTION_FOR_ACTOR_7", json.dumps(data8))

    # -------------------------------------------------------------
    # P08-03: Real Agent Runtime Status Widget (No Fake Online)
    # -------------------------------------------------------------
    def test_p08_03_agent_runtime_states(self):
        project_id = 3
        # Initially all agents should be IDLE
        status = get_agents_runtime_status(self.store, project_id)
        self.assertTrue(status["runtime_healthy"])
        self.assertTrue(status["provider_circuit_closed"])
        self.assertEqual(status["summary"]["total_agents"], 8)
        self.assertEqual(status["summary"]["idle"], 8)
        self.assertEqual(status["summary"]["active"], 0)

        # Seed an ACTIVE run for agent 'ba'
        self.seed_task_and_run(actor=7, project=3, state="RUNNING")
        status_after_run = get_agents_runtime_status(self.store, project_id)
        self.assertEqual(status_after_run["agents"]["ba"]["state"], "ACTIVE")
        self.assertEqual(status_after_run["agents"]["ba"]["active_runs"], 1)
        self.assertEqual(status_after_run["summary"]["active"], 1)
        self.assertEqual(status_after_run["summary"]["idle"], 7)

        # Local handlers remain independent of provider quota; provider circuit is reported separately.
        self.store.block_gemini('provider-project', 'QUOTA_EXHAUSTED', cooldown=60)
        blocked_status=get_agents_runtime_status(self.store,project_id)
        self.assertEqual(blocked_status['agents']['ba']['state'],'ACTIVE')
        self.assertEqual(blocked_status['summary']['blocked'],0)

    def test_current_specialist_status_uses_scoped_execution_events(self):
        from gateway.execution_events import append
        scopes=[]
        for actor,agent in [(7,'fe'),(8,'be')]:
            _,identifier=self.seed_task_and_run(actor=actor,state='RUNNING')
            run=self.store.agent_run(actor,3,identifier)
            scope=RunScope(**{k:getattr(run,k) for k in RunScope.model_fields})
            scopes.append(scope)
            with self.store.connect() as db:
                append(db,scope,'AGENT_STARTED',agent=agent,step_id=2,status='RUNNING')
        status=get_agents_runtime_status(self.store,3,actor_id=7)
        self.assertEqual(status['agents']['fe']['state'],'ACTIVE')
        self.assertEqual(status['agents']['be']['state'],'IDLE')
        with self.store.connect() as db:
            append(db,scopes[0],'AGENT_COMPLETED',agent='fe',step_id=2,status='COMPLETED')
        self.assertEqual(get_agents_runtime_status(self.store,3,actor_id=7)['agents']['fe']['state'],'IDLE')

    def test_quota_panel_uses_validated_policy_and_shared_reservations(self):
        now=time.time()
        with self.store.connect() as db:
            for _ in range(50):db.execute('INSERT INTO gemini_usage VALUES(?,?,?)',('provider-project',now,2400))
        policy={'project':'provider-project','model':'configured-free-model','quota':{'rpm':15,'rpd':500,'tpm':250000},
            'limits':{'rpm':13,'rpd':450,'tpm':225000}}
        data=get_quota_panel_data(self.store,7,3,self.service.config,policy)
        self.assertEqual(data['usage_today']['rpd_used'],50)
        self.assertEqual(data['usage_today']['rpd_remaining'],400)
        self.assertEqual(data['usage_last_60s']['rpm_reserved'],50)
        self.assertIsNone(data['usage_last_60s']['total_tokens_remaining'])
        self.assertEqual(data['provider_details']['active_model'],'configured-free-model')
        self.assertEqual(data['provider_details']['google_status'],'WAITING_QUOTA')
        self.assertEqual(data['multi_user_allocation']['max_active_users'],len(self.service.config['users']))
        self.assertFalse(get_quota_panel_data(self.store,7,3)['available'])

    # -------------------------------------------------------------
    # P08-05: Workflow Timeline with One Task ID Trace
    # -------------------------------------------------------------
    def test_p08_05_workflow_timeline_and_errors(self):
        project_id = 3
        task_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        now = time.time()

        # Insert audit events for this specific task
        with self.store.connect() as db:
            db.execute(
                """INSERT INTO audit(id, at, actor, action, target, outcome, project_id, task_id, run_id, trace_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), now, 7, "task_dispatch", "pm_agent", "ok", project_id, task_id, run_id, trace_id)
            )
            db.execute(
                """INSERT INTO audit(id, at, actor, action, target, outcome, project_id, task_id, run_id, trace_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), now + 1, 7, "agent_step_1", "work_packages/58", "ok", project_id, task_id, run_id, trace_id)
            )
            db.execute(
                """INSERT INTO audit(id, at, actor, action, target, outcome, project_id, task_id, run_id, trace_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), now + 2, 7, "agent_step_2", "work_packages/58", "failed", project_id, task_id, run_id, trace_id)
            )

        timeline = get_task_workflow_timeline(self.store, actor_id=7, project_id=project_id, task_id=task_id)
        self.assertEqual(timeline["task_id"], task_id)
        self.assertEqual(timeline["total_steps"], 3)
        self.assertTrue(timeline["has_active_errors"])
        self.assertEqual(timeline["timeline_trace"][0]["action"], "task_dispatch")
        self.assertEqual(timeline["timeline_trace"][0]["status"], "SUCCESS")
        self.assertEqual(timeline["timeline_trace"][2]["status"], "ERROR")
        self.assertEqual(timeline["timeline_trace"][2]["outcome"], "failed")

    # -------------------------------------------------------------
    # P08-06: Proposal UX Before/After Diff & Native Readback Verification
    # -------------------------------------------------------------
    def test_p08_06_proposal_diff_reviewer_summary_and_readback(self):
        current_wp = {
            "id": 58,
            "subject": "Cũ: Quản lý đăng nhập",
            "description": "Mô tả ban đầu",
            "_links": {
                "status": {"title": "In Progress"},
                "assignee": {"title": "Developer One"},
            },
            "dueDate": "2026-10-20",
        }
        proposed_changes = {
            "subject": "Mới: Quản lý đăng nhập OTP",
            "status": "Ready for QA",
            "dueDate": "2026-10-22",
        }

        # 1. Test Diff Calculation
        diffs = build_proposal_diff(current_wp, proposed_changes)
        self.assertEqual(len(diffs), 3)
        field_map = {d["field"]: d for d in diffs}
        self.assertTrue(field_map["subject"]["is_changed"])
        self.assertEqual(field_map["subject"]["before_value"], "Cũ: Quản lý đăng nhập")
        self.assertEqual(field_map["subject"]["after_value"], "Mới: Quản lý đăng nhập OTP")
        self.assertEqual(field_map["status"]["before_value"], "In Progress")
        self.assertEqual(field_map["status"]["after_value"], "Ready for QA")

        # 2. Test Reviewer Summary
        proposal_meta = {"action": "update_work_package", "arguments": proposed_changes}
        summary_pm = synthesize_reviewer_summary(proposal_meta, actor_role="PM", lock_version_match=True)
        self.assertEqual(summary_pm["verdict"], "APPROVED_FOR_REVIEW")
        self.assertFalse(summary_pm["is_safe_to_execute"])
        self.assertFalse(summary_pm["evidence_verified"])

        # Non-PM review must catch RBAC violation
        summary_dev = synthesize_reviewer_summary(proposal_meta, actor_role="BE", lock_version_match=True)
        self.assertEqual(summary_dev["verdict"], "REJECTED")
        self.assertFalse(summary_dev["is_safe_to_execute"])
        self.assertIn("RBAC_VIOLATION", summary_dev["conflicts"][0])

        # Stale lock version conflict
        summary_stale = synthesize_reviewer_summary(proposal_meta, actor_role="PM", lock_version_match=False)
        self.assertEqual(summary_stale["verdict"], "REJECTED")
        self.assertIn("STALE_VERSION_CONFLICT", summary_stale["conflicts"][0])

        # 3. Test Native Readback Verification
        # Scenario A: Full match -> SUCCEEDED
        native_packages_succeeded = [
            {
                "id": 58,
                "subject": "Mới: Quản lý đăng nhập OTP",
                "_links": {"status": {"title": "Ready for QA"}},
                "dueDate": "2026-10-22",
            }
        ]
        readback_succ = verify_native_readback(native_packages_succeeded, 58, proposed_changes)
        self.assertEqual(readback_succ["status"], "SUCCEEDED")
        self.assertTrue(readback_succ["verified"])

        # Scenario B: Partial match -> PARTIAL_SUCCESS
        native_packages_partial = [
            {
                "id": 58,
                "subject": "Mới: Quản lý đăng nhập OTP",
                "_links": {"status": {"title": "In Progress"}},  # Status did not change!
                "dueDate": "2026-10-22",
            }
        ]
        readback_part = verify_native_readback(native_packages_partial, 58, proposed_changes)
        self.assertEqual(readback_part["status"], "PARTIAL_SUCCESS")
        self.assertFalse(readback_part["verified"])
        self.assertIn("status", readback_part["unmatched_fields"])

        # Scenario C: No native packages available -> PENDING_READBACK (Never marks succeeded early!)
        readback_pending = verify_native_readback(None, 58, proposed_changes)
        self.assertEqual(readback_pending["status"], "PENDING_READBACK")
        self.assertFalse(readback_pending["verified"])

    # -------------------------------------------------------------
    # P08-07: Development Progress from TASKS.json
    # -------------------------------------------------------------
    def test_p08_07_tasks_progress_report(self):
        from pathlib import Path
        path=Path(self.fixture.root)/'isolated-development-progress.json'
        path.write_text(json.dumps({'tasks':[
            {'id':'P00-1','phase':'P00','status':'DONE','evidence':['synthetic-unit-evidence']},
            {'id':'P07-1','phase':'P07','status':'DONE'},
            {'id':'P07-2','phase':'P07','status':'IN_PROGRESS'},
            {'id':'P07-3','phase':'P07','status':'BLOCKED'},
            {'id':'P07-4','phase':'P07','status':'TODO'}]}),encoding='utf-8')
        progress = get_tasks_progress_report(path)
        self.assertTrue(progress["available"])
        self.assertEqual(progress["total_tasks"],5)
        self.assertEqual(progress["done_tasks"],2)
        self.assertEqual(progress["percent_done"],40.0)
        self.assertTrue(progress["read_only"])
        self.assertIn("P00", progress["phases"])
        self.assertIn("P07", progress["phases"])
        self.assertEqual(progress["phases"]["P07"]["status"], "IN_PROGRESS")
        self.assertEqual(progress["phases"]["P07"]["percent"],25.0)
        self.assertEqual([t['id'] for t in progress['blocked_tasks']],['P07-3'])
        self.assertEqual([t['id'] for t in progress['missing_evidence_tasks']],['P07-1'])
        self.assertFalse(get_tasks_progress_report(Path(self.fixture.root)/'absent-progress.json')['available'])


if __name__ == "__main__":
    unittest.main()

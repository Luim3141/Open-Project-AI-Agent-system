"""Tests for Supervisor Planner: read vs write, dependencies, and budget allocation."""
import time
import unittest
import uuid

from gateway.agent_models import AgentTask, ExecutionPlan, NativeReference
from gateway.planner import (
    is_deterministic_intent,
    is_write_intent,
    plan_request,
    resolve_target_agent,
    resolve_target_agents,
)


class SupervisorPlannerTests(unittest.TestCase):
    def test_combined_supervisor_pm_approval_is_not_a_fifth_specialist(self):
        prompt = 'PM/Supervisor điều phối BA FE BE QA cập nhật #370, chờ PM duyệt riêng.'
        self.assertEqual(resolve_target_agents(prompt, 'supervisor'), ['ba', 'fe', 'be', 'qa'])
        self.assertEqual(resolve_target_agents(prompt, 'pm'), ['pm'])
        self.assertEqual(resolve_target_agents('BA và PM phân tích #370', 'supervisor'), ['ba', 'pm'])

    def make_task(self, instruction: str, agent: str = "supervisor", actor_id: int = 7) -> AgentTask:
        now = time.time()
        return AgentTask(
            task_id=str(uuid.uuid4()),
            actor_id=actor_id,
            project_id=3,
            conversation_id=str(uuid.uuid4()),
            agent=agent,
            instruction=instruction,
            references=[],
            run_class="agent",
            created_at=now,
            expires_at=now + 3600,
        )

    # --- 1. Read vs Write Separation ---

    def test_read_instructions_classified_as_read_only(self):
        read_queries = [
            "Liệt kê các work package đang ở trạng thái In Progress",
            "Đếm số lượng công việc quá hạn trong Sprint hiện tại",
            "Xem báo cáo hàng ngày của các thành viên",
            "Tra cứu tiến độ sprint QAG3",
            "List all open tasks for QA role",
        ]
        for query in read_queries:
            task = self.make_task(query)
            plan = plan_request(task, actor_role="PM")
            self.assertEqual(plan.operation_type, "READ_ONLY", f"Failed for: {query}")
            self.assertFalse(plan.requires_pm_approval)
            self.assertFalse(is_write_intent(query))

    def test_write_instructions_classified_as_proposal_write(self):
        write_queries = [
            "Cập nhật trạng thái task #102 sang Done",
            "Gán work package #45 cho thành viên BE",
            "Tạo một subtask mới cho việc viết test",
            "Thay đổi deadline của Epic đăng nhập",
            "Update work package assignee and close task",
        ]
        for query in write_queries:
            task = self.make_task(query)
            plan = plan_request(task, actor_role="PM")
            self.assertEqual(plan.operation_type, "PROPOSAL_WRITE", f"Failed for: {query}")
            self.assertTrue(plan.requires_pm_approval)
            self.assertTrue(is_write_intent(query))

    def test_non_pm_proposing_write_strictly_gated_by_pm_approval(self):
        task = self.make_task("Cập nhật trạng thái task #102", actor_id=9)  # Actor 9 is FE
        plan = plan_request(task, actor_role="FE")
        self.assertEqual(plan.operation_type, "PROPOSAL_WRITE")
        self.assertTrue(plan.requires_pm_approval)
        # Verify the final aggregation step requires PM consent
        pm_step = [s for s in plan.steps if s.requires_pm_consent]
        self.assertTrue(len(pm_step) >= 1)

    def test_explicitly_negated_mutations_do_not_create_phantom_proposals(self):
        for instruction in [
            "Phân tích chỉ đọc và soạn gợi ý cho công việc #38; không ghi thay đổi.",
            "Phân tích yêu cầu, không sửa dữ liệu.",
            "Xem task #38, đừng cập nhật trạng thái.",
            "Analyze task #38; do not update it.",
            "Review task #38, don't modify the data.",
        ]:
            with self.subTest(instruction=instruction):
                self.assertFalse(is_write_intent(instruction))
                plan = plan_request(self.make_task(instruction), actor_role="PM")
                self.assertEqual(plan.operation_type, "READ_ONLY")
                self.assertFalse(plan.requires_pm_approval)

    def test_negation_of_one_mutation_never_suppresses_another_write_request(self):
        for instruction in [
            "Không sửa mô tả, nhưng cập nhật trạng thái task #38.",
            "Do not delete task #38; update its description.",
            "Chỉ đọc task #38 trước, sau đó gán cho BE.",
            "Không ghi thay đổi ở task #38; tạo task mới.",
        ]:
            with self.subTest(instruction=instruction):
                self.assertTrue(is_write_intent(instruction))
                plan = plan_request(self.make_task(instruction), actor_role="FE")
                self.assertTrue(plan.requires_pm_approval)

    # --- 2. Deterministic vs Model Budget Allocation ---

    def test_purely_deterministic_query_allocates_zero_model_budget(self):
        queries = [
            "Đếm số lượng work package quá hạn",
            "Liệt kê danh sách task mở",
            "Xem báo cáo hàng ngày",
            "Count total open bugs in project",
        ]
        for query in queries:
            task = self.make_task(query)
            plan = plan_request(task, actor_role="PM")
            self.assertTrue(plan.budget.deterministic_only, f"Failed for: {query}")
            self.assertFalse(plan.budget.model_needed)
            self.assertEqual(plan.budget.max_turns, 0)
            self.assertEqual(plan.budget.token_estimate, 0)

    def test_complex_analysis_allocates_bounded_model_budget(self):
        queries = [
            "Phân tích mâu thuẫn trong tiêu chí chấp nhận của User Story #12",
            "Đánh giá nguy cơ chậm tiến độ Sprint và đề xuất giải pháp",
            "Phân tích rủi ro kỹ thuật cho kiến trúc database mới",
            "Analyze regression bug trends and suggest missing test cases",
        ]
        for query in queries:
            task = self.make_task(query)
            plan = plan_request(task, actor_role="PM")
            self.assertFalse(plan.budget.deterministic_only, f"Failed for: {query}")
            self.assertTrue(plan.budget.model_needed)
            self.assertTrue(1 <= plan.budget.max_turns <= 2)
            self.assertTrue(800 <= plan.budget.token_estimate <= 1600)

    # --- 3. Role-based Agent Routing ---

    def test_supervisor_routes_to_correct_domain_agent(self):
        cases = [
            ("Phân tích user story và tiêu chí chấp nhận AC cho tính năng thanh toán", "ba"),
            ("Kiểm tra regression test cases và phân loại bug", "qa"),
            ("Đánh giá kiến trúc kỹ thuật backend và schema database", "be"),
            ("Phân tích frontend và accessibility", "fe"),
            ("Tổng hợp nguy cơ trễ hạn sprint và phân bổ workload", "pm"),
        ]
        for query, expected_agent in cases:
            task = self.make_task(query, agent="supervisor")
            plan = plan_request(task, actor_role="PM")
            specialist_step = plan.steps[0]
            self.assertEqual(specialist_step.agent, expected_agent, f"Wrong agent for: {query}")

    def test_explicit_agent_choice_is_respected(self):
        task = self.make_task("Kiểm tra tổng quát hệ thống", agent="qa")
        plan = plan_request(task, actor_role="PM")
        self.assertEqual(plan.steps[0].agent, "qa")

    # --- 4. DAG Step Dependencies Integrity ---

    def test_dag_steps_have_valid_dependencies_and_no_cycles(self):
        task = self.make_task("Cập nhật user story và điều chỉnh AC tính năng giỏ hàng")
        plan = plan_request(task, actor_role="PM")
        self.assertTrue(len(plan.steps) >= 2)
        step_ids = [s.step_id for s in plan.steps]
        self.assertEqual(step_ids, sorted(step_ids))
        for step in plan.steps:
            for dep in step.dependencies:
                self.assertIn(dep, step_ids)
                self.assertTrue(dep < step.step_id, f"Dependency {dep} is not earlier than step {step.step_id}")

    # --- 5. Contract Serialization and Boundedness ---

    def test_plan_serializes_and_deserializes_cleanly_within_size_bounds(self):
        task = self.make_task("Phân tích toàn diện sprint risks và đề xuất cập nhật deadline")
        plan = plan_request(task, actor_role="PM")
        json_data = plan.model_dump_json()
        reconstituted = ExecutionPlan.from_json(json_data)
        self.assertEqual(reconstituted.plan_id, plan.plan_id)
        self.assertEqual(reconstituted.operation_type, plan.operation_type)
        self.assertEqual(len(reconstituted.steps), len(plan.steps))
        self.assertTrue(len(json_data.encode("utf-8")) < 4096)


if __name__ == '__main__':
    unittest.main()

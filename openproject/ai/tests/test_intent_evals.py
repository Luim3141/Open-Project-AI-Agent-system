"""Unit tests and benchmark validation for intent evals (P09-01).
Tests multi-intent decomposition, ambiguity detection, and stale reference resolution.
"""
import unittest

from gateway.conversation_memory import NativeObjectRef
from gateway.intent_evals import (
    GOLDEN_EVALS_SET,
    evaluate_instruction_intent,
    run_intent_evaluations,
)


class IntentEvalsTests(unittest.TestCase):
    def test_golden_evals_benchmark_suite(self):
        summary = run_intent_evaluations()
        print(f"\n[EVALS BENCHMARK] Total: {summary.total}, Passed: {summary.passed}, Failed: {summary.failed}, Accuracy: {summary.accuracy_rate}%")
        self.assertGreaterEqual(summary.accuracy_rate, 95.0, "Accuracy rate must exceed 95% on golden benchmark")
        self.assertEqual(summary.failed, 0, f"Expected 0 failures, got {summary.failed}")

    def test_multi_intent_decomposition_produces_typed_sub_intents(self):
        instruction = "Đếm số bug mở và cập nhật trạng thái của task #45 sang In Progress"
        res = evaluate_instruction_intent(instruction)
        self.assertTrue(res.is_multi_intent)
        self.assertEqual(len(res.sub_intents), 2)
        # Sub-intent 1
        self.assertEqual(res.sub_intents[0].intent_type, "DETERMINISTIC_READ")
        self.assertEqual(res.sub_intents[0].operation_type, "READ_ONLY")
        # Sub-intent 2
        self.assertEqual(res.sub_intents[1].intent_type, "PROPOSAL_WRITE")
        self.assertEqual(res.sub_intents[1].operation_type, "PROPOSAL_WRITE")
        self.assertEqual(res.sub_intents[1].target_id, 45)

    def test_ambiguity_triggers_on_unanchored_mutation(self):
        instruction = "Cập nhật tiến độ sang Done"
        res = evaluate_instruction_intent(instruction)
        self.assertTrue(res.is_ambiguous)
        self.assertIn("MISSING_TARGET_WORK_PACKAGE_ID", res.ambiguity_reason)

    def test_stale_reference_on_lock_version_change(self):
        ref = NativeObjectRef(native_type="work_package", native_id=99, lock_version=1)
        instruction = "Đóng task đó"
        # Current lock version in DB is now 2
        res = evaluate_instruction_intent(instruction, conversation_ref=ref, current_native_lock_version=2)
        self.assertTrue(res.is_stale_reference)
        self.assertTrue(res.is_ambiguous)

    def test_valid_reference_resolves_correctly(self):
        ref = NativeObjectRef(native_type="work_package", native_id=99, lock_version=1)
        instruction = "Cập nhật mô tả của task đó"
        res = evaluate_instruction_intent(instruction, conversation_ref=ref, current_native_lock_version=1)
        self.assertFalse(res.is_stale_reference)
        self.assertFalse(res.is_ambiguous)
        self.assertEqual(res.resolved_ref.native_id, 99)
        self.assertEqual(res.sub_intents[0].intent_type, "PROPOSAL_WRITE")


if __name__ == "__main__":
    unittest.main()

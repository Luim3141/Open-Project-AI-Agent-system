"""Unit tests for Agent Registry (P05-08).
Agent registry specifies role, tool allowlist, model limits per agent,
and guarantees all agents share the single central Gemini project quota limiter.
"""
import unittest

from gateway.agent_registry import (
    AgentDefinition,
    AgentRegistry,
    get_agent_registry,
    AGENT_NAMES,
)


class AgentRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = get_agent_registry()

    def test_required_specialists_and_legacy_pm_dev_registered(self):
        registered_names = set(self.registry.list_agents().keys())
        expected_names = {"supervisor", "pm", "ba", "fe", "be", "dev", "qa", "reviewer"}
        self.assertEqual(registered_names, expected_names)
        self.assertEqual(set(AGENT_NAMES), expected_names)

    def test_live_agents_share_central_quota_and_reviewer_is_local(self):
        """Acceptance: Một Gemini project chạy nhiều agent nhưng tuân thủ quota chung."""
        for name, agent_def in self.registry.list_agents().items():
            if name == 'reviewer':
                self.assertEqual(agent_def.provider,'local-policy')
                self.assertFalse(agent_def.shares_central_quota)
                self.assertEqual(agent_def.max_model_calls_including_retry,0)
                continue
            self.assertEqual(agent_def.provider, "gemini-shared")
            self.assertTrue(agent_def.shares_central_quota)
            # Max turns per agent must be bounded (<= 2) to preserve the shared 15 RPM / 500 RPD quota
            self.assertLessEqual(agent_def.max_turns, 2)
            self.assertLessEqual(agent_def.max_tokens_per_call, 4000)

    def test_strict_tool_allowlists_per_agent(self):
        """Principle of least privilege: Each agent has an explicit, bounded tool/action allowlist."""
        dev = self.registry.get_agent("dev")
        # DEV agent strictly prohibits shell or web research
        self.assertNotIn("shell", dev.allowed_tools)
        self.assertNotIn("git_clone", dev.allowed_tools)
        self.assertNotIn("web_research", dev.allowed_tools)
        self.assertIn("breakdown_fe_be", dev.allowed_tools)

        pm = self.registry.get_agent("pm")
        self.assertIn("analyze_overdue", pm.allowed_tools)
        self.assertIn("analyze_blockers", pm.allowed_tools)
        self.assertIn("analyze_workload", pm.allowed_tools)
        # Cannot mutate tasks directly
        self.assertNotIn("update_work_package", pm.allowed_tools)

        ba = self.registry.get_agent("ba")
        self.assertIn("draft_user_story", ba.allowed_tools)
        self.assertIn("draft_ac", ba.allowed_tools)
        self.assertNotIn("create_work_package", ba.allowed_tools)

        qa = self.registry.get_agent("qa")
        self.assertIn("generate_test_cases", qa.allowed_tools)
        self.assertIn("triage_bug", qa.allowed_tools)
        self.assertNotIn("transition", qa.allowed_tools)

        reviewer = self.registry.get_agent("reviewer")
        self.assertIn("verify_evidence", reviewer.allowed_tools)
        self.assertIn("detect_conflicts", reviewer.allowed_tools)
        # Reviewer cannot auto-approve mutations
        self.assertNotIn("auto_approve", reviewer.allowed_tools)

    def test_instantiate_agent_handler_returns_singleton_or_fresh_handler(self):
        """Registry can create/resolve the executable agent instance."""
        for name in AGENT_NAMES:
            handler = self.registry.get_handler(name)
            self.assertIsNotNone(handler)
            self.assertTrue(hasattr(handler, "run"))

    def test_unknown_agent_lookup_fails_closed(self):
        """Looking up unregistered agent fails closed with KeyError or ValueError."""
        with self.assertRaises(ValueError):
            self.registry.get_agent("unauthorized_hacker_agent")


if __name__ == "__main__":
    unittest.main()

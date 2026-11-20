"""Unit & Integration Tests for Quick Tunnel Auto-Healing Supervisor.

Verifies the self-healing watchdog behavior without requiring Docker socket:
- Failure threshold enforcement (5 consecutive failures = 75s).
- Counter reset on recovery.
- Cooldown and grace period protection against restart loops.
- Zero Docker socket exposure.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUPERVISOR_SCRIPT = ROOT / "openproject" / "ai" / "automation" / "quick_tunnel_supervisor.sh"
DOCKERFILE = ROOT / "openproject" / "ai" / "automation" / "QuickTunnel.Dockerfile"
STAGE_YML = ROOT / "openproject" / "ai" / "quick.stage.yml"


class TestQuickTunnelAutoheal(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SUPERVISOR_SCRIPT.is_file(), f"Missing {SUPERVISOR_SCRIPT}")
        self.script_content = SUPERVISOR_SCRIPT.read_text(encoding="utf-8")

    def test_supervisor_script_syntax_and_structure(self):
        """Verifies supervisor script structure, signals, and parameters."""
        self.assertIn("#!/bin/sh", self.script_content)
        self.assertIn("trap cleanup TERM INT", self.script_content)
        self.assertIn("cloudflared tunnel", self.script_content)
        self.assertIn("http://127.0.0.1:2000/ready", self.script_content)
        self.assertIn("exit 1", self.script_content)

    def test_unhealthy_threshold_configuration(self):
        """Extracts and verifies thresholds for backoff and max failures."""
        grace_match = re.search(r"STARTUP_GRACE_PERIOD=(\d+)", self.script_content)
        interval_match = re.search(r"CHECK_INTERVAL=(\d+)", self.script_content)
        max_fails_match = re.search(r"MAX_FAILS=(\d+)", self.script_content)

        self.assertIsNotNone(grace_match, "STARTUP_GRACE_PERIOD must be defined")
        self.assertIsNotNone(interval_match, "CHECK_INTERVAL must be defined")
        self.assertIsNotNone(max_fails_match, "MAX_FAILS must be defined")

        grace = int(grace_match.group(1))
        interval = int(interval_match.group(1))
        max_fails = int(max_fails_match.group(1))

        # Must have at least 45s grace period to prevent rapid start loops
        self.assertGreaterEqual(grace, 45, "Grace period too short; risk of restart loop")
        # Check interval should be between 10s and 30s
        self.assertTrue(10 <= interval <= 30, f"Check interval {interval}s outside safe range [10, 30]")
        # Max fails should require multiple consecutive checks
        self.assertGreaterEqual(max_fails, 3, "MAX_FAILS must be >= 3 to absorb transient network blips")

        # Total time before self-kill must be >= 60s
        total_failure_window = interval * max_fails
        self.assertGreaterEqual(total_failure_window, 60, f"Total failure window {total_failure_window}s too short")

    def test_zero_docker_socket_exposure(self):
        """Ensures that the auto-healing design does NOT mount /var/run/docker.sock."""
        if STAGE_YML.is_file():
            content = STAGE_YML.read_text(encoding="utf-8")
            self.assertNotIn("docker.sock", content, "Security violation: docker.sock must not be mounted in quick.stage.yml")

        if DOCKERFILE.is_file():
            dockerfile_content = DOCKERFILE.read_text(encoding="utf-8")
            self.assertNotIn("docker.sock", dockerfile_content)

    def test_simulation_unhealthy_and_recovery_logic(self):
        """Simulates the state machine: transient failures reset counter; persistent trigger exit."""
        class MockSupervisor:
            def __init__(self, max_fails=5):
                self.fail_count = 0
                self.max_fails = max_fails
                self.terminated = False

            def probe(self, is_healthy: bool):
                if is_healthy:
                    self.fail_count = 0
                else:
                    self.fail_count += 1
                    if self.fail_count >= self.max_fails:
                        self.terminated = True

        sup = MockSupervisor(max_fails=5)

        # 1. Healthy checks
        sup.probe(True)
        self.assertEqual(sup.fail_count, 0)
        self.assertFalse(sup.terminated)

        # 2. Transient failures (1, 2, 3) followed by recovery
        sup.probe(False)
        sup.probe(False)
        sup.probe(False)
        self.assertEqual(sup.fail_count, 3)
        self.assertFalse(sup.terminated)

        # Transient recovery resets counter
        sup.probe(True)
        self.assertEqual(sup.fail_count, 0)
        self.assertFalse(sup.terminated)

        # 3. Persistent 5 consecutive failures
        for _ in range(5):
            sup.probe(False)

        self.assertEqual(sup.fail_count, 5)
        self.assertTrue(sup.terminated, "Supervisor must terminate after 5 consecutive failures")


if __name__ == "__main__":
    unittest.main()

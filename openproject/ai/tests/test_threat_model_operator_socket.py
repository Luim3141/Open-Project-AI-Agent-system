"""Threat Model Audit & Negative Test Suite for Docker Socket & Machine Operator (P09-08).
Verifies:
1. Docker socket (/var/run/docker.sock) is NEVER mounted into business containers (OpenProject, Gateway, n8n).
2. Business agents (PM, BA, FE, BE, QA) cannot execute Docker or host operator actions.
3. Machine operator private directory (%LOCALAPPDATA%/QLDAPM/openproject-ai/operator) is isolated and inaccessible to business agents.
4. Internal service ports (PostgreSQL 5432, n8n 5678, Gateway internal) are never bound to public/external 0.0.0.0.
"""
from pathlib import Path
import re
import tempfile
import unittest

from gateway.service import Service
from gateway.store import Store


class ThreatModelOperatorSocketTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent

    def test_compose_files_never_mount_docker_socket(self):
        """Audit all compose files: /var/run/docker.sock must NOT be mounted into business containers."""
        compose_paths = [
            self.repo_root / "openproject/compose.yml",
            self.repo_root / "openproject/ai/compose.yml",
            self.repo_root / "openproject/ai/stage.yml",
            self.repo_root / "openproject/ai/deep-ai.stage.yml",
            self.repo_root / "openproject/ai/local-runtime.stage.yml",
        ]
        docker_sock_pattern = re.compile(r"docker\.sock", re.IGNORECASE)

        for compose_file in compose_paths:
            if compose_file.exists():
                with self.subTest(file=compose_file.name):
                    content = compose_file.read_text(encoding="utf-8", errors="ignore")
                    # Check for docker.sock mount
                    self.assertIsNone(
                        docker_sock_pattern.search(content),
                        f"CRITICAL SECURITY HAZARD: docker.sock mounted in {compose_file.name}",
                    )

    def test_compose_files_internal_ports_not_exposed_to_all_interfaces(self):
        """Internal service ports (PostgreSQL 5432, n8n 5678) must bind to 127.0.0.1 or stay in internal network."""
        compose_paths = [
            self.repo_root / "openproject/compose.yml",
            self.repo_root / "openproject/ai/compose.yml",
            self.repo_root / "openproject/ai/stage.yml",
        ]
        # Disallow plain "5432:5432" or "0.0.0.0:5432:5432" or "5678:5678" without 127.0.0.1
        bad_port_patterns = [
            re.compile(r"-\s*[\"']?0\.0\.0\.0:5432", re.IGNORECASE),
            re.compile(r"-\s*[\"']?0\.0\.0\.0:5678", re.IGNORECASE),
            re.compile(r"-\s*[\"']?5432:5432[\"']?", re.IGNORECASE),
            re.compile(r"-\s*[\"']?5678:5678[\"']?", re.IGNORECASE),
        ]

        for compose_file in compose_paths:
            if compose_file.exists():
                content = compose_file.read_text(encoding="utf-8", errors="ignore")
                for pattern in bad_port_patterns:
                    with self.subTest(file=compose_file.name, pattern=pattern.pattern):
                        self.assertIsNone(
                            pattern.search(content),
                            f"Internal port exposed to 0.0.0.0 in {compose_file.name}",
                        )

    def test_business_agent_cannot_access_operator_keys_via_workspace(self):
        """Workspace operations must strictly isolate actor paths and prevent access to operator directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            operator_dir = root / "operator"
            operator_dir.mkdir()
            (operator_dir / "automation.key").write_bytes(b"SUPER_SECRET_MACHINE_KEY")
            (operator_dir / "approval.key").write_bytes(b"SUPER_SECRET_APPROVAL_KEY")

            workspaces_dir = root / "workspaces"
            workspaces_dir.mkdir()

            store = Store(root / "gateway")
            service = Service(
                store,
                {"users": {"10": "PM"}, "project_id": 5, "gateway_mode": "native"},
                workspaces_dir,
            )

            # Attempt to read machine operator key through workspace path traversal
            illegal_paths = [
                "../operator/automation.key",
                "../../operator/approval.key",
                str(operator_dir / "automation.key"),
            ]

            for path in illegal_paths:
                with self.subTest(path=path):
                    with self.assertRaises((PermissionError, ValueError, FileNotFoundError)):
                        service.workspace.read(10, path)

    def test_local_operator_denies_shell_and_raw_sql_execution(self):
        """Local operator execute protocol strictly rejects arbitrary SQL and shell execution packets."""
        from gateway.local_operator import execute

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            malicious_packets = [
                {"operation": "sql", "arguments": {"query": "DROP TABLE requests"}},
                {"operation": "shell", "arguments": {"command": "whoami"}},
                {"operation": "exec", "arguments": {"cmd": "docker ps"}},
                {"operation": "credential", "arguments": {"actor": 10}},
            ]
            for packet in malicious_packets:
                with self.subTest(op=packet["operation"]):
                    with self.assertRaises(ValueError):
                        execute(packet, root)


if __name__ == "__main__":
    unittest.main()

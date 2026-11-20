"""Real local MCP transport smoke; credential-free and no Jira network requests."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class StdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_powershell_launcher(self):
        environment = dict(os.environ)
        environment.pop("QLDAPM_JIRA_ADMIN_TOKEN", None)
        environment.pop("GEMINI_API_KEY", None)
        with tempfile.TemporaryDirectory(prefix="qag3-admin-smoke-") as temporary:
            environment["LOCALAPPDATA"] = temporary
            server = StdioServerParameters(
                command="powershell.exe", env=environment,
                args=["-NoProfile", "-NonInteractive", "-File", str(
                    Path(__file__).resolve().parents[1] / "tools" / "Start-JiraAdminMcp.ps1")],
            )
            async with asyncio.timeout(30):
                async with stdio_client(server) as (reader, writer):
                    async with ClientSession(reader, writer) as client:
                        await client.initialize()
                        status = await client.call_tool("api_status", {})
                        self.assertFalse(status.isError)
                        self.assertFalse(json.loads(status.content[0].text)["credentialPresent"])

    async def test_tools_status_and_missing_token_over_stdio(self):
        environment = dict(os.environ)
        environment.pop("QLDAPM_JIRA_ADMIN_TOKEN", None)
        environment.pop("GEMINI_API_KEY", None)
        server = StdioServerParameters(
            command=sys.executable,
            args=[str(Path(__file__).resolve().parents[1] / "tools" / "jira_admin_mcp.py")],
            env=environment,
        )
        async with asyncio.timeout(30):
            async with stdio_client(server) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    tools = await client.list_tools()
                    self.assertEqual({tool.name for tool in tools.tools}, {
                        "api_status", "api_preflight", "inspect_workflow", "inspect_scheme", "inspect_expression_validation", "inspect_expression_runtime",
                        "inspect_automation", "inspect_gate_fields", "preview_workflow_resolution", "preview_scheme",
                        "preview_automation_state", "preview_subtask_delivery", "preview_epic_forge_gates", "preview_epic_delivery_gates", "preview_task_acceptance_gates", "preview_task_qa_gates", "preview_task_qa_freshness", "preview_subtask_qa_freshness", "preview_subtask_history", "preview_epic_return_reason", "preview_subtask_acceptance_gates", "apply_change", "inspect_publish_result", "preview_scheme_switch", "inspect_scheme_switch_result"})
                    for tool in tools.tools:
                        if tool.name not in ('inspect_publish_result', 'inspect_scheme_switch_result') and (tool.name.startswith('inspect_') or tool.name.startswith('api_')):
                            self.assertTrue(tool.annotations.readOnlyHint)
                        else:
                            self.assertFalse(tool.annotations.readOnlyHint)
                    status = await client.call_tool("api_status", {})
                    self.assertFalse(status.isError)
                    self.assertFalse(json.loads(status.content[0].text)["credentialPresent"])
                    failed = await client.call_tool("api_preflight", {})
                    self.assertTrue(failed.isError)
                    self.assertIn("CREDENTIAL_MISSING", failed.content[0].text)


if __name__ == "__main__":
    unittest.main()

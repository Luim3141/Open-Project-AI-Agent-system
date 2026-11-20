"""Read-only acceptance of the real PowerShell stdio wrapper with existing PM credentials."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    root = Path(__file__).resolve().parents[1]
    args = ["-NoProfile", "-File", str(root / "Start-OpenProjectMCP.ps1"), "-UserId", "20"]
    if "--remote" in sys.argv:
        args.append("-Remote")
    parameters = StdioServerParameters(command="pwsh", args=args, cwd=root)
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            assert len((await session.list_tools()).tools) == 19
            for tool, expected in (("identity", 20), ("analyze", 329)):
                result = await session.call_tool(tool, {"arguments": {}})
                assert not result.isError
                body = result.structuredContent or json.loads(result.content[0].text)
                key = "user_id" if tool == "identity" else "count"
                assert body["result"][key] == expected
    print("Real PM stdio wrapper PASS: initialize, 19 tools, identity20, analyze329; remote=" + str("--remote" in sys.argv) + ". Codex host/TOTP not tested.")


if __name__ == "__main__":
    asyncio.run(main())

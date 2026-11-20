"""Read/deny-only acceptance with existing PM/BA bindings. Does not enroll or rotate tokens."""
import asyncio
import json
import os
import subprocess
import sys
import re
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
url = "http://127.0.0.1:8090"
if "--remote" in sys.argv:
    url = (runtime / "current-url.txt").read_text().strip()
    assert re.fullmatch(r"https://[a-z0-9-]+\.trycloudflare\.com", url), "VERIFIED_QUICK_URL_REQUIRED"
official = "sha256:2beeecac788d4f423c46a95ffbd04e6479491938b9924b610e9f47d81a38303c"


async def main():
    image = subprocess.check_output(["docker", "inspect", "--format", "{{.Image}}", "qldapm-openproject-web-1"], text=True).strip()
    assert image == official, "OFFICIAL_CORE_ONLY_DENY_TEST"
    for actor in (19, 20):
        headers = {"Authorization": "Bearer " + (runtime / "operator" / f"user-{actor}.token").read_text().strip()}
        async with httpx.AsyncClient(headers=headers, timeout=120, trust_env=False, follow_redirects=False) as http:
            schema = await http.get(url + "/api/v1/openapi.json")
            assert schema.status_code == 200 and schema.json()["openapi"] == "3.1.0"
            identity = await http.post(url + "/api/v1/commands", json={"action": "identity"})
            assert identity.status_code == 200 and identity.json()["result"]["user_id"] == actor
            # Invalid payload cannot create a record even if a guard regresses; expect capability refusal before validation.
            blocked = await http.post(url + "/api/v1/commands", json={"action": "create_work_package", "arguments": {},
                "idempotency_key": "official-core-deny-check"})
            assert blocked.status_code == 503 and "CORE_GATES_NOT_ACTIVATED" in blocked.text
            async with streamable_http_client(url + "/mcp", http_client=http) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    result = await session.call_tool("analyze", {"arguments": {}})
                    assert not result.isError
                    data = result.structuredContent or json.loads(result.content[0].text)
                    assert data["result"]["count"] == 329
                    assert len(tools.tools) == 19
            print(json.dumps({"user_id": actor, "actual_identity": True, "openapi": True, "mcp_19_tools_329_items": True,
                              "live_writes_fail_closed": True, "human_totp": "NOT_TESTED"}))


if __name__ == "__main__":
    asyncio.run(main())

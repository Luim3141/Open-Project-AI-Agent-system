"""Real SDK stdio/HTTP MCP against an ephemeral gateway with synthetic staging credentials."""
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from gateway.store import Store, canonical
from gateway.service import Command

root = Path(__file__).resolve().parents[1]
runtime = Path(sys.argv[1])
remote = "--remote" in sys.argv

async def verify(url, token, token_path):
    async with httpx.AsyncClient(headers={"Authorization": "Bearer " + token}, timeout=120, trust_env=False) as http:
        anonymous = await http.get(url + "/api/v1/openapi.json", headers={"Authorization": ""})
        assert anonymous.status_code == 401, "ANONYMOUS_ACCESS_NOT_DENIED"
        async with streamable_http_client(url + "/mcp", http_client=http) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {tool.name for tool in tools.tools} == set(Command.model_fields["action"].annotation.__args__)
                result = await session.call_tool("analyze", {"arguments": {}})
                assert not result.isError, result
                body = result.structuredContent or json.loads(result.content[0].text)
                assert body["result"]["count"] == 329, body
    environment = {**os.environ, "QLDAPM_AI_URL": url, "QLDAPM_AI_TOKEN_FILE": str(token_path)}
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "gateway.stdio"], cwd=root, env=environment)
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            assert len((await session.list_tools()).tools) == len(Command.model_fields["action"].annotation.__args__)
            result = await session.call_tool("identity", {"arguments": {}})
            assert not result.isError, result
            body = result.structuredContent or json.loads(result.content[0].text)
            assert body["result"]["role"] == "BE", body

if "--main" in sys.argv:
    if remote:
        raise SystemExit("Main staging acceptance is loopback only; remote uses the isolated fixture")
    token_path = runtime / "stage/deep-BE.token"
    from operator_state import ContainerState
    be = json.loads((runtime / "stage/test-credentials.json").read_text())["BE"]
    state = ContainerState(runtime / "stage-ai", "qldapm-ai-stage-staging-gateway-1")
    # The owned synthetic fixture needs a fresh 24h token, never an extended token or real-user enrollment.
    token = state.call("issue_token", user_id=be["id"], role="BE", op_token=be["token"])
    token_path.write_text(token, encoding="utf-8")
    asyncio.run(verify("http://127.0.0.1:18092", token, token_path))
    print(json.dumps({"passed": True, "synthetic_only": True, "main_staging": True,
        "http_sdk": True, "stdio_sdk": True, "anonymous_denied": True, "source_count": 329, "google_calls": 0}))
    raise SystemExit(0)

with TemporaryDirectory() as directory:
    directory = Path(directory)
    credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
    bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
    config = {"users": {str(c["id"]): role for role, c in credentials.items()}, "hosts": ["127.0.0.1:18092"],
              "project_id": bootstrap["project_id"], "openproject_url": "http://staging-web:8080"}
    (directory / "config.json").write_text(canonical(config), encoding="utf-8")
    be = credentials["BE"]
    token = Store(directory).issue_token(be["id"], "BE", be["token"])
    token_path = directory / "bearer.token"
    token_path.write_text(token, encoding="utf-8")
    with socket.socket() as check:
        check.bind(("127.0.0.1", 18092))
    images = json.loads((runtime / "image-lock.json").read_text())
    gateway = "qldapm-ai-transport-test-gateway"
    subprocess.run(["docker", "run", "--rm", "-d", "--name", gateway, "--network", "qldapm-ai-stage_stage-front",
                    "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                    "--memory", "384m", "--cpus", "1", "--pids-limit", "128", "--tmpfs", "/tmp:size=32m",
                    "-p", "127.0.0.1:18092:8090", "--mount", f"type=bind,source={directory},target=/state",
                    "-e", "QLDAPM_AI_RUNTIME=/state", "-e", "QLDAPM_AI_WORKSPACES=/workspaces", os.environ.get("AI_IMAGE", images["AI_IMAGE"])],
                   check=True, capture_output=True)
    tunnel = "qldapm-ai-transport-test"
    tunnel_started = False
    try:
        for attempt in range(40):
            try:
                if httpx.get("http://127.0.0.1:18092/health", trust_env=False).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError("TEST_GATEWAY_TIMEOUT")
        url = "http://127.0.0.1:18092"
        if remote:
            subprocess.run(["docker", "run", "--rm", "-d", "--name", tunnel, "--network", "qldapm-ai-stage_stage-front",
                            images["CLOUDFLARED_IMAGE"], "tunnel", "--no-autoupdate", "--url", f"http://{gateway}:8090"],
                           check=True, capture_output=True)
            tunnel_started = True
            import re
            for attempt in range(40):
                logs = subprocess.run(["docker", "logs", tunnel], capture_output=True, text=True, check=True)
                match = re.search(r"https://([a-z0-9-]+\.trycloudflare\.com)", logs.stdout + logs.stderr)
                if match:
                    config["hosts"].append(match[1])
                    (directory / "config.json").write_text(canonical(config), encoding="utf-8")
                    url = match[0]
                    break
                time.sleep(1)
            else:
                raise RuntimeError("TEST_TUNNEL_TIMEOUT")
            observed = set()
            for attempt in range(20):
                try:
                    response = httpx.get(url + "/api/v1/openapi.json", timeout=10, trust_env=False)
                    observed.add(str(response.status_code))
                    if response.status_code == 401:
                        break
                except httpx.HTTPError as error:
                    observed.add(type(error).__name__ + ": " + str(error)[:160])
                time.sleep(1)
            else:
                raise RuntimeError("REMOTE_BEARER_BOUNDARY_NOT_VERIFIED: " + ",".join(sorted(observed)))
        asyncio.run(verify(url, token, token_path))
        print(json.dumps({"passed": True, "synthetic_only": True, "remote": remote, "stdio_sdk": True, "http_sdk": True}))
    finally:
        if tunnel_started:
            subprocess.run(["docker", "stop", tunnel], capture_output=True, timeout=30)
        subprocess.run(["docker", "stop", gateway], capture_output=True, timeout=30)

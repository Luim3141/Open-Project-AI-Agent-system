"""Explicit one-probe Gemini integration on localhost staging; never production."""
import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from gateway.gemini import SMOKE_PROMPT, DEMO_PROMPT
from gateway.service import Command


async def verify(runtime, demo=False, metadata=False):
    url = "http://127.0.0.1:18092"
    token_path = runtime / "stage/deep-BE.token"
    token = token_path.read_text().strip()
    headers = {"Authorization": "Bearer " + token}
    async with httpx.AsyncClient(base_url=url, headers=headers, timeout=40, trust_env=False,
                                 follow_redirects=False) as http:
        for path in ("/api/v1/openapi.json", "/api/v1/insights"):
            response = await http.get(path, headers={"Authorization": ""})
            assert response.status_code == 401, "ANONYMOUS_NOT_DENIED"
        identity = await http.post("/api/v1/commands", json={"action": "identity"})
        assert identity.status_code == 200, "STAGING_BE_TOKEN_OR_NATIVE_IDENTITY_FAILED"
        assert identity.json()["result"]["role"] == "BE", "BE_REQUIRED"
        response = await http.get("/api/v1/openapi.json")
        assert response.status_code == 200 and "/api/v1/ai-runs" in response.json()["paths"], "OPENAPI_FAILED"
        key = "free-stage-" + str(uuid.uuid4())
        payload = {"prompt": "Dự án hiện có bao nhiêu công việc? Dùng analyze để trả lời số lượng." if metadata else DEMO_PROMPT if demo else SMOKE_PROMPT}
        response = await http.post("/api/v1/ai-runs", headers={"Idempotency-Key": key}, json=payload)
        assert response.status_code == 200, "AI_RUN_START_FAILED_NO_RETRY"
        identifier = response.json()["result"]["id"]
        deadline = time.monotonic() + (125 if metadata else 45)
        while True:
            response = await http.get("/api/v1/ai-runs/" + identifier)
            assert response.status_code == 200, "AI_RUN_POLL_FAILED_NO_RETRY"
            result = response.json()["result"]
            if result["state"] != "running":
                break
            assert time.monotonic() < deadline, "AI_RUN_TIMEOUT_NO_RETRY"
            await asyncio.sleep(2)
        if result["state"] != "done":
            raise RuntimeError(result.get("result", {}).get("error", "AI_RUN_FAILED_NO_RETRY"))
        answer = result["result"]["text"]
        if metadata:
            native = await http.post("/api/v1/commands", json={"action": "analyze"})
            assert native.status_code == 200, "NATIVE_READBACK_FAILED"
            count = native.json()["result"]["count"]
            assert any(row["path"] == ["result", "count"] and row["value"] == count for row in result["result"]["claims"]), "METADATA_COUNT_NOT_CITED"
            assert all(row["action"] == "analyze" and {"count", "by_status"} <= set(row["result"]["result"]) <=
                       {"count", "by_status", "overdue_ids", "overdue_count"} for row in result["result"]["tools"]), "PRIVATE_TOOL_DATA_OR_WRITES"
        else:
            assert (bool(answer) if demo else answer == "QLDAPM_OK") and result["result"]["tools"] == [], "INVALID_SMOKE_RESULT"
        assert result["result"]["model"] == "gemini-3.5-flash-lite", "WRONG_SMOKE_MODEL"
        response = await http.post("/api/v1/ai-runs", headers={"Idempotency-Key": key}, json=payload)
        assert response.status_code == 200 and response.json()["result"]["id"] == identifier, "REPLAY_CREATED_NEW_RUN"
        async with streamable_http_client(url + "/mcp", http_client=http) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                assert {tool.name for tool in (await session.list_tools()).tools} == set(Command.model_fields["action"].annotation.__args__), "MCP_CATALOG_FAILED"
                response = await session.call_tool("get_ai_run", {"arguments": {"id": identifier}})
                assert not response.isError, "MCP_READ_RUN_FAILED"
                body = response.structuredContent or json.loads(response.content[0].text)
                assert body["result"]["result"]["text"] == answer, "MCP_RESULT_MISMATCH"
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "gateway.stdio"],
        cwd=Path(__file__).resolve().parents[1], env={**os.environ, "QLDAPM_AI_URL": url,
                                                   "QLDAPM_AI_TOKEN_FILE": str(token_path)})
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            assert {tool.name for tool in (await session.list_tools()).tools} == set(Command.model_fields["action"].annotation.__args__), "STDIO_CATALOG_FAILED"
            response = await session.call_tool("get_ai_run", {"arguments": {"id": identifier}})
            assert not response.isError, "STDIO_READ_RUN_FAILED"
            body = response.structuredContent or json.loads(response.content[0].text)
            assert body["result"]["result"]["text"] == answer, "STDIO_RESULT_MISMATCH"
    print(json.dumps({"passed": True, "model": result["result"]["model"], "run_id": identifier,
        "synthetic_only": not demo and not metadata, "public_demo_only": demo, "project_metadata_only": metadata, "text": answer, "real_probe_count": 1,
        "rest": True, "mcp_http": True, "mcp_stdio": True, "replay_same_run": True,
        "anonymous_denied": True, "production_changed": False}))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ("--real", "--demo", "--metadata"):
        raise SystemExit("Usage: python -m tests.stage_free_smoke <private-runtime> --real|--demo|--metadata; consumes one probe, no automatic retry")
    try:
        asyncio.run(verify(Path(sys.argv[1]), demo=sys.argv[2] == "--demo", metadata=sys.argv[2] == "--metadata"))
    except (AssertionError, RuntimeError) as error:
        print(json.dumps({"passed": False, "error": str(error), "automatic_retry": False}))
        raise SystemExit(1)

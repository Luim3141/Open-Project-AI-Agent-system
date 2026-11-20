"""Local MCP adapter forwards every operation through the authenticated HTTP interface."""
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from mcp.server.fastmcp import FastMCP

from .service import Command, MUTATIONS
from .catalog import description

server = FastMCP("qldapm-openproject")
url = os.environ.get("QLDAPM_AI_URL", "http://127.0.0.1:8090")
parsed = urlsplit(url)
if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname == "127.0.0.1"):
    raise ValueError("HTTPS_OR_LOOPBACK_REQUIRED")

for name in Command.model_fields["action"].annotation.__args__:
    def make_tool(action):
        def tool(arguments: dict, idempotency_key: str | None = None, auto_execute: bool = False) -> dict:
            token = Path(os.environ["QLDAPM_AI_TOKEN_FILE"]).read_text().strip()
            response = httpx.post(url + "/api/v1/commands", json={"action": action, "arguments": arguments,
                                  "idempotency_key": idempotency_key, "auto_execute": auto_execute}, headers={"Authorization": "Bearer " + token},
                                  timeout=60, follow_redirects=False, trust_env=False)
            if response.status_code != 200:
                raise ValueError(f"GATEWAY_HTTP_{response.status_code}")
            return response.json()
        return tool
    server.add_tool(make_tool(name), name=name, description=description(name),
                    annotations={"readOnlyHint": name not in MUTATIONS, "destructiveHint": False})

if __name__ == "__main__":
    server.run(transport="stdio")

"""Call the authenticated Atlassian MCP through the installed Codex client."""

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", help="Exact MCP tool name, e.g. discover or getJiraIssue")
    parser.add_argument("--describe", action="store_true", help="Print the live tool schema")
    parser.add_argument("--server", choices=("atlassian", "qag3-admin"), default="atlassian",
                        help="Use the supplementary QAG3 admin MCP only for authorized admin work")
    options = parser.parse_args()
    executable = shutil.which("codex.exe") or shutil.which("codex")
    if not executable:
        raise RuntimeError("Codex CLI not found in PATH")
    arguments = {} if options.describe else json.loads(sys.stdin.read() or "{}")
    if not isinstance(arguments, dict):
        raise ValueError("MCP arguments must be a JSON object")

    # Use Codex's credential store; no token is copied into this project.
    process = subprocess.Popen(
        [executable, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    messages = queue.Queue()

    def read_responses():
        try:
            for line in process.stdout:
                messages.put(json.loads(line))
        except Exception as error:
            messages.put(error)
        finally:
            messages.put(None)

    threading.Thread(target=read_responses, daemon=True).start()
    request_id = 0

    def request(method, params):
        nonlocal request_id
        request_id += 1
        current_id = request_id
        process.stdin.write(json.dumps({"id": current_id, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        while True:
            message = messages.get(timeout=60)
            if message is None:
                raise RuntimeError("Codex app-server disconnected")
            if isinstance(message, Exception):
                raise message
            if message.get("id") != current_id:
                continue
            if "error" in message:
                raise RuntimeError(json.dumps(message["error"], ensure_ascii=False))
            return message["result"]

    try:
        request("initialize", {
            "clientInfo": {"name": "qldapm_jira_mcp", "version": "1.0.0"},
            "capabilities": {"experimentalApi": True},
        })
        process.stdin.write(json.dumps({"method": "initialized", "params": {}}) + "\n")
        process.stdin.flush()
        session = request("thread/start", {
            "cwd": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ephemeral": True,
        })
        thread_id = session["thread"]["id"]
        status = request("mcpServerStatus/list", {
            "serverName": options.server, "threadId": thread_id, "detail": "toolsAndAuthOnly",
        })
        server = next((item for item in status["data"] if item["name"] == options.server), None)
        if not server or server.get("runtimeStatus") != "connected":
            raise RuntimeError(f"MCP {options.server} is not connected; check the registered server")
        if options.tool not in server["tools"]:
            raise ValueError("Tool is not advertised by selected MCP; inspect live catalog")
        if options.describe:
            result = server["tools"][options.tool]
        else:
            result = request("mcpServer/tool/call", {
                "threadId": thread_id, "server": options.server, "tool": options.tool,
                "arguments": arguments,
            })
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get("isError") else 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

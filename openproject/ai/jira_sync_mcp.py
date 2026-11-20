"""Persistent official MCP read session; no admin connector or Jira REST fallback."""
import json
import os
import queue
import shutil
import subprocess
import threading
from pathlib import Path


def unwrap(value):
    for _ in range(10):
        if not isinstance(value, dict) or value.get("isError") or value.get("error"):
            raise ValueError("OFFICIAL_MCP_READ_FAILED")
        if "content" in value:
            texts = [part["text"] for part in value["content"] if part.get("type") == "text"]
            if len(texts) != 1:
                raise ValueError("MCP_RESPONSE_SHAPE")
            value = json.JSONDecoder().raw_decode(texts[0].lstrip())[0]
        elif "data" in value:
            value = value["data"]
        else:
            return value
    raise ValueError("MCP_RESPONSE_DEPTH")


class OfficialMCP:
    READ_TOOLS = {"atlassianUserInfo", "getAccessibleAtlassianResources", "discover",
                  "executeRead", "getJiraIssue", "searchJiraIssuesUsingJql"}

    def __enter__(self):
        executable = shutil.which("codex.exe") or shutil.which("codex")
        if not executable:
            raise RuntimeError("CODEX_CLI_REQUIRED")
        self.messages, self.identifier, self.allowed = queue.Queue(), 0, set()
        self.process = subprocess.Popen([executable, "app-server", "--stdio"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
            env={k: v for k, v in os.environ.items() if k.upper() not in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}},
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

        def receive():
            try:
                for line in self.process.stdout:
                    if len(line) > 32 * 1024 * 1024:
                        raise ValueError("MCP_RESPONSE_LIMIT")
                    self.messages.put(json.loads(line))
            except Exception:
                self.messages.put({"error": "MCP_READER_FAILED"})
            finally:
                self.messages.put(None)

        threading.Thread(target=receive, daemon=True).start()
        try:
            self.request("initialize", {"clientInfo": {"name": "qldapm_jira_sync_read", "version": "1.0"},
                                        "capabilities": {"experimentalApi": True}})
            self.process.stdin.write(json.dumps({"method": "initialized", "params": {}}) + "\n")
            self.process.stdin.flush()
            root = str(Path(__file__).resolve().parents[2])
            session = self.request("thread/start", {"cwd": root, "ephemeral": True})
            self.thread = session["thread"]["id"]
            state = self.request("mcpServerStatus/list", {"serverName": "atlassian", "threadId": self.thread,
                                                        "detail": "toolsAndAuthOnly"})
            server = next(x for x in state["data"] if x["name"] == "atlassian")
            if server.get("runtimeStatus") != "connected":
                raise ValueError("OFFICIAL_MCP_NOT_CONNECTED")
            self.tools = server["tools"]
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def request(self, method, params):
        self.identifier += 1
        identifier = self.identifier
        self.process.stdin.write(json.dumps({"id": identifier, "method": method, "params": params}) + "\n")
        self.process.stdin.flush()
        while True:
            try:
                value = self.messages.get(timeout=90)
            except queue.Empty:
                raise RuntimeError("OFFICIAL_MCP_RESPONSE_TIMEOUT") from None
            if value is None or "error" in value:
                raise RuntimeError("OFFICIAL_MCP_SESSION_FAILED")
            if value.get("id") == identifier:
                return value["result"]

    def call(self, tool, arguments):
        if tool not in self.READ_TOOLS or tool not in self.tools:
            raise ValueError("JIRA_WRITE_OR_UNADVERTISED_TOOL_DENIED")
        if tool == "executeRead" and arguments.get("name") not in self.allowed:
            raise ValueError("UNDISCOVERED_JIRA_READ_DENIED")
        result = unwrap(self.request("mcpServer/tool/call", {"threadId": self.thread, "server": "atlassian",
                                                             "tool": tool, "arguments": arguments}))
        if tool == "discover":
            self.allowed.update(row["name"] for row in result.get("results", [])
                                if row.get("executeTool") == "executeRead")
        return result

    def __exit__(self, *args):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill(); self.process.wait()

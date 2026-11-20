"""Owner-only enrollment for PM/BA; never expose this script through API/MCP."""
import asyncio
import getpass
import json
import os
import re
from operator_state import ContainerState
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

import manage_local
from gateway.native import Native, NativeError

ROOT = Path(__file__).resolve().parent
RUNTIME = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
MEMBERS = {19: ("ba-pm", "BA-PM"), 20: ("pm", "PM")}
CONTAINER = "qldapm-openproject-web-1"
URL = "http://127.0.0.1:8090"


class BackendNative(Native):
    """Owner CLI only: native auth over the gateway's existing private network."""
    def call(self, path, method="GET", payload=None):
        if method != "GET" or payload is not None:
            raise PermissionError("ENROLLMENT_BACKEND_IS_READ_ONLY")
        program = '''
import json, sys
from gateway.native import Native, NativeError
data = json.load(sys.stdin)
try:
    result = Native("http://web:8080", data["token"], 5).call(data["path"])
    print(json.dumps({"result": result}))
except NativeError as error:
    print(json.dumps({"native_error_status": error.status}))
'''
        output = docker("exec", "-i", "qldapm-ai-gateway-1", "python", "-c", program,
                        input=json.dumps({"token": self.token, "path": path}))
        result = json.loads(output)
        if "native_error_status" in result:
            raise NativeError(result["native_error_status"], "NATIVE_BACKEND_REJECTED")
        return result["result"]


def docker(*args, input=None):
    result = subprocess.run(["docker", *args], input=input, text=True, capture_output=True, timeout=300)
    if result.returncode:
        # Subprocess output may contain secrets; only return the exit status.
        raise RuntimeError(f"DOCKER_OPERATION_FAILED_{result.returncode}")
    return result.stdout


def credentials():
    return json.loads((RUNTIME / "gateway/credentials.json").read_text())


def token_file(actor):
    return RUNTIME / "operator" / f"user-{actor}.token"


def guard_enrollment():
    config = json.loads((RUNTIME / "gateway/config.json").read_text())
    assert config["project_id"] == 5
    for actor, (_, role) in MEMBERS.items():
        assert config["users"][str(actor)] == role
        if str(actor) in credentials() or token_file(actor).exists():
            raise RuntimeError("EXISTING_ENROLLMENT_PRESERVED_USE_VERIFY")
    assert ContainerState(RUNTIME / "gateway").call("token_count", actors=[19, 20]) == 0


def enroll():
    guard_enrollment()
    enrollment = RUNTIME / "operator" / ("enrollment-" + uuid.uuid4().hex)
    enrollment.mkdir()
    container_directory = "/tmp/qldapm-issued-" + uuid.uuid4().hex
    ruby = r'''
Rails.logger = Logger.new(File::NULL)
ActiveRecord::Base.logger = nil
directory = __DIRECTORY__
raise "UNSAFE_OUTPUT" unless directory.match?(%r{\A/tmp/qldapm-issued-[a-f0-9]{32}\z})
Dir.mkdir(directory, 0700)
project = Project.find_by!(identifier: "qldapm-local")
raise "WRONG_INSTANCE" unless project.id == 5 && OpenProject::VERSION.to_s == "17.9.1" && Setting.api_tokens_enabled?
roles = {19 => ["ba-pm", "BA-PM"], 20 => ["pm", "PM"]}
before = Token::API.order(:id).map(&:attributes)
users_before = User.where(id: [19,20,21]).order(:id).map(&:attributes)
devices_before = TwoFactorAuthentication::Device.where(user_id: [19,20,21]).order(:id).map(&:attributes)
created = []
Token::API.transaction do
  roles.keys.sort.each do |id|
    user = User.lock.find(id)
    login, role = roles.fetch(id)
    membership = Member.find_by!(project_id: project.id, user_id: id)
    raise "IDENTITY_OR_ROLE_MISMATCH" unless user.login == login && user.active? && !user.admin? && membership.roles.map(&:name) == ["QLDAPM #{role}"]
    raise "EXISTING_API_TOKEN_PRESERVED" if Token::API.where(user_id: id).exists?
    result = APITokens::CreateService.new(user: user, model: Token::API.new).call(token_name: "QLDAPM AI Gateway #{File.basename(directory)}")
    raise "SERVICE_REJECTED" unless result.success?
    token = result.result
    raise "INVALID_TOKEN" unless token.plain_value.start_with?("opapi-") && Token::API.find_by_plaintext_value(token.plain_value)&.user_id == id
    File.open(File.join(directory, "user-#{id}.api-token"), File::WRONLY | File::CREAT | File::EXCL, 0600) do |file|
      file.write(token.plain_value)
      file.flush
      file.fsync
    end
    created << {user_id: id, token_id: token.id}
  end
  raise "PREVIOUS_TOKENS_CHANGED" unless Token::API.where(id: before.map { |t| t.fetch("id") }).order(:id).map(&:attributes) == before
  raise "ACCOUNT_CHANGED" unless User.where(id: [19,20,21]).order(:id).map(&:attributes) == users_before
  raise "TOTP_CHANGED" unless TwoFactorAuthentication::Device.where(user_id: [19,20,21]).order(:id).map(&:attributes) == devices_before
end
puts JSON.generate({created: created, previous_tokens_preserved: true, account_security_unchanged: true})
'''.replace("__DIRECTORY__", json.dumps(container_directory))
    output = docker("exec", "-i", CONTAINER, "bundle", "exec", "rails", "runner", "-", input=ruby)
    result = json.loads(output.strip().splitlines()[-1])
    assert [item["user_id"] for item in result["created"]] == list(MEMBERS)
    for actor in MEMBERS:
        destination = enrollment / f"user-{actor}.api-token"
        assert not destination.exists()
        docker("cp", f"{CONTAINER}:{container_directory}/user-{actor}.api-token", str(destination))
    register_existing(enrollment)
    # Remove only this invocation's container copies after both host copies are verified.
    cleanup = "require 'fileutils'; FileUtils.remove_entry_secure(" + json.dumps(container_directory) + ")"
    docker("exec", CONTAINER, "ruby", "-e", cleanup)
    print(json.dumps(result))
    print(json.dumps({"private_enrollment_directory": str(enrollment), "registered": list(MEMBERS)}))


def register_existing(enrollment):
    enrollment = Path(enrollment).resolve()
    if enrollment.parent != (RUNTIME / "operator").resolve() or not re.fullmatch(r"enrollment-[a-f0-9]{32}", enrollment.name):
        raise ValueError("UNTRUSTED_PRIVATE_ENROLLMENT_DIRECTORY")
    for actor in MEMBERS:
        credential = (enrollment / f"user-{actor}.api-token").read_text().strip()
        assert re.fullmatch(r"opapi-[a-f0-9]{64}", credential)
        identity = BackendNative("http://web:8080", credential, 5).identity(actor)
        assert identity["role"] == json.loads((RUNTIME / "gateway/config.json").read_text())["users"][str(actor)]
        guard_actor = credentials()
        if str(actor) in guard_actor:
            assert guard_actor[str(actor)] == credential and token_file(actor).exists()
            continue
        assert str(actor) not in guard_actor and not token_file(actor).exists()
        assert ContainerState(RUNTIME / "gateway").call("token_count", actors=[actor]) == 0
        with patch.object(getpass, "getpass", return_value=credential), patch.object(manage_local, "Native", BackendNative):
            manage_local.register(RUNTIME, actor)
        current = credentials()
        assert all(current[key] == value for key, value in guard_actor.items())
        assert current[str(actor)] == credential


def body(result):
    assert not result.isError, "MCP_TOOL_FAILED"
    return result.structuredContent or json.loads(result.content[0].text)


async def verify():
    assert httpx.get(URL + "/api/v1/openapi.json", trust_env=False, timeout=10).status_code == 401
    assert httpx.post(URL + "/mcp", json={}, trust_env=False, timeout=10).status_code == 401
    assert httpx.get(URL + "/api/v1/openapi.json", headers={"Authorization": "Bearer invalid-enrollment-test"},
                     trust_env=False, timeout=10).status_code == 401
    for actor in MEMBERS:
        role = json.loads((RUNTIME / "gateway/config.json").read_text())["users"][str(actor)]
        identity = BackendNative("http://web:8080", credentials()[str(actor)], 5).identity(actor)
        assert identity["user_id"] == actor and identity["role"] == role
        bearer = token_file(actor).read_text().strip()
        headers = {"Authorization": "Bearer " + bearer}
        response = httpx.post(URL + "/api/v1/commands", headers=headers,
                              json={"action": "identity", "arguments": {}}, trust_env=False, timeout=90)
        assert response.status_code == 200, f"REST_IDENTITY_FAILED_{response.status_code}"
        assert response.json()["result"]["user_id"] == actor
        async with httpx.AsyncClient(headers=headers, trust_env=False, timeout=120) as http:
            async with streamable_http_client(URL + "/mcp", http_client=http) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    assert "identity" in [tool.name for tool in (await session.list_tools()).tools]
                    assert body(await session.call_tool("identity", {"arguments": {}}))["result"]["user_id"] == actor
                    assert body(await session.call_tool("analyze", {"arguments": {}}))["result"]["count"] == 329
        env = {**os.environ, "QLDAPM_AI_URL": URL, "QLDAPM_AI_TOKEN_FILE": str(token_file(actor))}
        parameters = StdioServerParameters(command=sys.executable, args=["-m", "gateway.stdio"], cwd=ROOT, env=env)
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                assert "identity" in [tool.name for tool in (await session.list_tools()).tools]
                assert body(await session.call_tool("identity", {"arguments": {}}))["result"]["role"] == role
        print(json.dumps({"user_id": actor, "role": role, "api_v3": "PASS", "rest": "PASS", "mcp_http": "PASS", "mcp_stdio": "PASS", "work_packages": 329}))


def main():
    if not __debug__:
        raise RuntimeError("OPTIMIZED_PYTHON_NOT_ALLOWED")
    if len(sys.argv) < 2 or sys.argv[1] not in {"enroll", "verify", "resume"}:
        raise ValueError("USAGE: provision_member_tokens.py enroll|verify|resume PRIVATE_DIRECTORY")
    if sys.argv[1] in {"enroll", "resume"}:
        # shortcut: only this operator helper honors the lock; do not enroll concurrently with another local command.
        lock = RUNTIME / "operator/member-enrollment.lock"
        lock.open("x", encoding="utf-8").close()
        try:
            if sys.argv[1] == "resume":
                register_existing(sys.argv[2])
            else:
                enroll()
        finally:
            lock.unlink()
    asyncio.run(verify())


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never render exceptions that might contain HTTP headers or credential-bearing objects.
        print(json.dumps({"status": "FAIL", "error_type": type(error).__name__, "secrets_disclosed": False}))
        sys.exit(1)

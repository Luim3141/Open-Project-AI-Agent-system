"""One-time local n8n owner operator. Never a business/model tool; no reset or license activation."""
import argparse
import hashlib
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from free_tier_staging import private_directory

IMAGE = "sha256:dd580fe1ab6e99e85bc66f2acf8bc8c5e9409fbe61b2e2803c5024403ef52833"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("N8N_REDIRECT_DENIED")


class LocalN8n:
    def __init__(self, base="http://localhost:5678"):
        parsed = urllib.parse.urlsplit(base)
        if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"}
                or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
            raise ValueError("N8N_LOOPBACK_ORIGIN_REQUIRED")
        self.base, self.cookie = base.rstrip("/"), ""
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, path, payload=None):
        if path not in {"/rest/settings", "/rest/owner/setup", "/rest/login"}:
            raise ValueError("N8N_OWNER_ENDPOINT_DENIED")
        return self._request(path, payload)

    def _request(self, path, payload=None, *, method=None, allow_null=False):
        if method not in (None, 'PATCH'):
            raise ValueError('N8N_OPERATOR_METHOD_DENIED')
        headers = {"Content-Type": "application/json", "Origin": self.base, "Referer": self.base + "/"}
        if getattr(self, 'push_ref', None):
            headers['push-ref'] = self.push_ref
        if self.cookie:
            headers["Cookie"] = self.cookie
        body = json.dumps(payload).encode() if payload is not None else None
        try:
            with self.opener.open(urllib.request.Request(self.base + path, data=body, headers=headers, method=method), timeout=20) as response:
                data = response.read(1048577)
                for line in response.headers.get_all("Set-Cookie", []):
                    cookie = SimpleCookie(line)
                    if "n8n-auth" in cookie:
                        self.cookie = "n8n-auth=" + cookie["n8n-auth"].value
        except urllib.error.HTTPError as error:
            raise RuntimeError("N8N_HTTP_" + str(error.code) + "; no reset or automatic credential replacement") from None
        if len(data) > 1048576:
            raise ValueError("N8N_RESPONSE_TOO_LARGE")
        document = json.loads(data)
        if not isinstance(document, dict) or 'data' not in document or not (isinstance(document['data'], dict) or (allow_null and document['data'] is None)):
            raise ValueError("N8N_RESPONSE_INVALID")
        return document["data"]


def provision(root, client):
    root = Path(root).resolve()
    operator = (Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/operator").resolve()
    if root == operator or not root.is_relative_to(operator):
        raise ValueError("N8N_CREDENTIAL_DIRECTORY_MUST_BE_PRIVATE_OPERATOR_CHILD")
    settings = client.request("/rest/settings")
    setup = settings.get("userManagement", {}).get("showSetupOnFirstLoad")
    if type(setup) is not bool:
        raise ValueError("N8N_OWNER_SETUP_STATE_UNKNOWN")
    path = root / "owner.json"
    if not path.exists() and not setup:
        raise PermissionError("N8N_OWNER_EXISTS_NO_SAVED_ACCESS; do not reset or replace")
    private_directory(root)
    if not path.exists():
        state = {"schema_version": 1, "endpoint": client.base, "email": "owner@qldapm.local",
            "firstName": "QLDAPM", "lastName": "Owner", "password": "Aa9!" + secrets.token_urlsafe(32)}
        with path.open("x", encoding="utf-8") as stream:
            json.dump(state, stream)
    if path.is_symlink() or path.stat().st_size > 8192:
        raise ValueError("N8N_OWNER_DOCUMENT_INVALID")
    original = path.read_bytes()
    state = json.loads(original)
    if (set(state) != {"schema_version", "endpoint", "email", "firstName", "lastName", "password"}
            or type(state["schema_version"]) is not int or state["schema_version"] != 1 or state["endpoint"] != client.base
            or any(not isinstance(state[name], str) or not state[name] for name in ("email", "firstName", "lastName", "password"))
            or not 8 <= len(state["password"]) <= 64):
        raise ValueError("N8N_OWNER_DOCUMENT_INVALID")
    if setup:
        client.request("/rest/owner/setup", {name: state[name] for name in ("email", "firstName", "lastName", "password")})
    user = client.request("/rest/login", {"emailOrLdapLoginId": state["email"], "password": state["password"]})
    role = user.get("role")
    role = role.get("slug") if isinstance(role, dict) else role
    if role != "global:owner" or user.get("email") != state["email"] or not client.cookie:
        raise PermissionError("N8N_OWNER_LOGIN_NOT_VERIFIED")
    if client.request("/rest/settings").get("userManagement", {}).get("showSetupOnFirstLoad") is not False:
        raise ValueError("N8N_OWNER_STATE_NOT_PERSISTED")
    if path.read_bytes() != original:
        raise ValueError("N8N_OWNER_CREDENTIAL_CHANGED")
    return {"passed": True, "owner_created_now": setup, "owner_role": role,
        "saved_credential_reused": True, "private_credential_persisted": True,
        "editor_endpoint": client.base, "license_activation_requested": False}


def check_primary_backup(path):
    path = Path(path).resolve()
    manifest = json.loads((path / "backup.json").read_text())
    if (manifest.get("target") != "staging" or manifest.get("purpose") != "data-restore-only"
            or not 0 <= time.time() - manifest["at"] < 3600):
        raise ValueError("RECENT_VERIFIED_STAGING_BACKUP_REQUIRED")
    for name in ("config/n8n.sqlite", "config/n8n.key", "config/n8n-files.tar"):
        if hashlib.sha256((path / name).read_bytes()).hexdigest() != manifest["manifest"].get(name):
            raise ValueError("N8N_BACKUP_MANIFEST_MISMATCH")
    info = json.loads(subprocess.check_output(["docker", "inspect", "qldapm-ai-stage-n8n-1"]))[0]
    if info["Image"] != IMAGE or info["Config"]["Labels"].get("com.docker.compose.project") != "qldapm-ai-stage":
        raise ValueError("N8N_PRIMARY_IMAGE_OR_OWNERSHIP_MISMATCH")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", required=True, type=Path)
    args = parser.parse_args()
    try:
        check_primary_backup(args.backup)
        root = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/operator/n8n-owner"
        print(json.dumps(provision(root, LocalN8n())))
    except Exception as error:
        print(json.dumps({"passed": False, "error_type": type(error).__name__, "no_reset_or_automatic_retry": True}))
        raise SystemExit(1)

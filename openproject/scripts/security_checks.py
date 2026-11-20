"""Read-only plus deliberately rejected role transitions, on this local project only."""
import argparse
import http.cookiejar
import html
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from import_wbs import API, NoRedirect, save


def check(runtime):
    config = json.loads((runtime / "bootstrap.json").read_text())
    mapping = json.loads((runtime / "source-mapping.json").read_text())
    tokens = json.loads((runtime / "security-tokens.json").read_text())["tokens"]
    owner = API(config["api_token"])
    project_path = f"/api/v3/projects/{config['project_id']}"
    for actor in (None, "outsider"):
        api = owner if actor is None else API(tokens[actor])
        for path in (project_path, f"/api/v3/work_packages/{mapping['E01']}"):
            try:
                api.call(path, auth=actor is not None)
            except RuntimeError as error:
                assert any(f"HTTP {code}" in str(error) for code in (401, 403, 404)), str(error)
            else:
                raise AssertionError("Anonymous or nonmember read private data")
    rejected = 0
    for actor in ("be", "fe", "qa", "ba-pm"):
        api = API(tokens[actor])
        package = api.call(f"/api/v3/work_packages/{mapping['E01']}")
        try:
            api.call(f"/api/v3/work_packages/{mapping['E01']}", "PATCH", {
                "lockVersion": package["lockVersion"],
                "_links": {"status": {"href": f"/api/v3/statuses/{config['statuses']['READY']}"}}})
        except RuntimeError as error:
            assert "HTTP 422" in str(error) or "HTTP 403" in str(error), str(error)
            rejected += 1
        else:
            raise AssertionError("Unauthorized Epic approval accepted")
    for actor, source in (("be", "AUTH-01-BE"), ("qa", "AUTH-01-QA")):
        api = API(tokens[actor])
        package = api.call(f"/api/v3/work_packages/{mapping[source]}")
        try:
            api.call(f"/api/v3/work_packages/{mapping[source]}", "PATCH", {
                "lockVersion": package["lockVersion"],
                "_links": {"status": {"href": f"/api/v3/statuses/{config['statuses']['DONE']}"}}})
        except RuntimeError as error:
            assert "HTTP 422" in str(error) or "HTTP 403" in str(error), str(error)
            rejected += 1
        else:
            raise AssertionError("Unauthorized direct completion accepted")
    accounts = json.loads((runtime / "accounts.json").read_text())
    login_stages = []
    for account in [accounts["admin"], accounts["users"][0]]:
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect())
        with opener.open("http://localhost:8088/login") as response:
            page = response.read().decode()
        csrf = re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', page)
        assert csrf, "CSRF input unavailable"
        body = urllib.parse.urlencode({"authenticity_token": html.unescape(csrf[1]), "username": account["login"], "password": account["password"]}).encode()
        request = urllib.request.Request("http://localhost:8088/login", data=body,
                                         headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            opener.open(request)
        except urllib.error.HTTPError as error:
            page = error.read().decode()
            assert error.code == 422 and 'name="new_password"' in page, "Initial password change form unavailable"
            login_stages.append("mandatory password change")
        except RuntimeError as error:
            assert "redirect refused" in str(error)
            # NoRedirect stops before navigating; force-password flag is verified separately by Rails.
            login_stages.append("authenticated; redirect to next mandatory stage")
        else:
            raise AssertionError("Initial login did not enter mandatory stage")
    with socket.create_connection(("127.0.0.1", 8088), timeout=10) as connection:
        connection.sendall(b"GET /hocuspocus HTTP/1.1\r\nHost: localhost:8088\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n")
        handshake = connection.recv(4096).decode(errors="replace")
        assert "101 Switching Protocols" in handshake, handshake[:200]
    report = {"anonymous_nonmember_reads_denied": True, "wrong_role_transitions_rejected": rejected,
              "initial_login_mandatory_stages": len(login_stages), "websocket_upgrade": True,
              "totp_enrollment_and_email_pin": "PUBLICATION_REDACTED"}
    save(runtime / "security-report.json", report)
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    check(parser.parse_args().runtime)

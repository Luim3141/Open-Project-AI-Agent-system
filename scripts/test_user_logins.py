import httpx
import re

client = httpx.Client(follow_redirects=True, verify=False, trust_env=False)
r = client.get("http://127.0.0.1:18091/login")
match = re.search(r'name="authenticity_token"\s+value="([^"]+)"', r.text)
if not match:
    print("Could not find authenticity_token")
    exit(1)
token = match.group(1)

accounts = [
    ("stage-owner", "PUBLICATION_REDACTED"),
    ("pm", "PUBLICATION_REDACTED"),
    ("ba-pm", "PUBLICATION_REDACTED"),
    ("fe", "PUBLICATION_REDACTED"),
    ("be", "PUBLICATION_REDACTED"),
    ("qa", "PUBLICATION_REDACTED"),
    ("system-admin", "Aa1!dOX_YZlplbuDL7Cwp_7-jBO9zzjdMK8ho5qV2g"),
]

for username, password in accounts:
    c = httpx.Client(follow_redirects=True, verify=False, trust_env=False)
    resp_get = c.get("http://127.0.0.1:18091/login")
    m = re.search(r'name="authenticity_token"\s+value="([^"]+)"', resp_get.text)
    t = m.group(1)
    resp = c.post(
        "http://127.0.0.1:18091/login",
        data={
            "authenticity_token": t,
            "username": username,
            "password": password,
            "login": "Sign in"
        }
    )
    success = "/login" not in str(resp.url) and resp.status_code == 200
    print(f"User {username:12} -> Success: {success} (URL: {resp.url})")

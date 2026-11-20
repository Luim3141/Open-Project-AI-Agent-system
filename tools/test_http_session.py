import urllib.request

cookie = "_open_project_session=1f116b6d37c7f9ae71c8a30bc52f877f"
url = "http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
req = urllib.request.Request(url, headers={"Cookie": cookie, "User-Agent": "Mozilla/5.0"})

try:
    resp = opener.open(req)
    print("STATUS:", resp.status)
    content = resp.read().decode('utf-8', errors='ignore')
    print("PAGE TITLE:", [line for line in content.splitlines() if '<title>' in line])
    print("HAS AI ENGINEERING:", "AI Engineering Control Center" in content)
    print("BODY PREVIEW:\n", content[:800])
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print("HEADERS:", dict(e.headers))
except Exception as e:
    print("ERROR:", e)

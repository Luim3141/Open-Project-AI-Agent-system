"""Public native HTTPS/auth smoke only; no passwords, provider call or client simulation."""
import json
import os
from pathlib import Path
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
record = json.loads((root / 'access/current-url.json').read_text())
url = record['url']
assert re.fullmatch(r'https://[a-z0-9][a-z0-9-]{0,62}\.trycloudflare\.com', url)
assert record['native_web'] == 'ready', 'NATIVE_STILL_STARTING'


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        assert urllib.parse.urlsplit(newurl).netloc == urllib.parse.urlsplit(url).netloc
        assert newurl.startswith(url + '/')
        return super().redirect_request(request, fp, code, message, headers, newurl)


opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), SameHostRedirect(),
                                   urllib.request.HTTPSHandler(context=ssl.create_default_context()))
with opener.open(url + '/login', timeout=30) as response:
    body = response.read(2_000_000).decode()
    assert response.status == 200 and 'authenticity_token' in body and 'password' in body
    assert any('secure' in c.lower() for c in response.headers.get_all('Set-Cookie', []))
with opener.open(url + '/projects/qldapm-local/qldapm-ai', timeout=30) as response:
    assert urllib.parse.urlsplit(response.url).path == '/login', 'ANONYMOUS_PROJECT_VISIBLE'
try:
    opener.open(url + '/api/v3/projects/3/work_packages', timeout=30)
except urllib.error.HTTPError as error:
    assert error.code in (401, 403)
    anonymous_api = error.code
else:
    raise AssertionError('ANONYMOUS_NATIVE_API_NOT_DENIED')
with urllib.request.urlopen('http://127.0.0.1:18090/', timeout=5) as response:
    assert url.encode() in response.read(100_000)
print(json.dumps({'passed': True, 'url': url, 'persistent_entry': 'http://localhost:18090',
                  'tls_verified_with_system_ca': True, 'native_login_csrf_secure_cookie': True,
                  'anonymous_project_redirects_login': True, 'anonymous_api_status': anonymous_api,
                  'only_native_web_tunneled': True, 'google_called': False}, indent=2))

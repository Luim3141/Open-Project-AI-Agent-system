"""Host-side TLS/bind checks only; never substitutes for five remote clients."""
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import urllib.request

HOST = '26.88.211.101'
ROOT = Path(__file__).resolve().parents[1]
source = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/radmin-caddy/caddy/pki/authorities/local/root.crt'
certificate = source.read_bytes()
public = ROOT / 'certs/QLDAPM-Radmin-Root-CA.crt'
public.parent.mkdir(exist_ok=True)
if public.exists():
    assert public.read_bytes() == certificate, 'CA_CHANGED_REQUIRES_REVIEW'
else:
    with public.open('xb') as stream:
        stream.write(certificate)
context = ssl.create_default_context(cafile=str(public))
with socket.create_connection((HOST, 443), timeout=5) as connection:
    with context.wrap_socket(connection, server_hostname=HOST) as secure:
        protocol = secure.version()
        assert protocol in ('TLSv1.2', 'TLSv1.3')
try:
    with socket.create_connection((HOST, 443), timeout=5) as connection:
        context.wrap_socket(connection, server_hostname='wrong-host.invalid')
except ssl.SSLError:
    pass
else:
    raise AssertionError('WRONG_HOSTNAME_NOT_REJECTED')
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context))
with opener.open('https://' + HOST + '/login', timeout=20) as response:
    body = response.read(2_000_000).decode('utf-8')
    assert response.status == 200 and response.url.startswith('https://' + HOST + '/')
    assert 'authenticity_token' in body and 'password' in body, 'NATIVE_LOGIN_FORM_MISSING'
    cookie_secure = any('secure' in c.lower() for c in response.headers.get_all('Set-Cookie', []))
    assert cookie_secure, 'NATIVE_COOKIE_NOT_SECURE'
blocked = []
for host, port in [('192.168.1.124', 443), ('127.0.0.1', 443), (HOST, 5678), (HOST, 18092), (HOST, 5432)]:
    try:
        with socket.create_connection((host, port), timeout=2):
            raise AssertionError('UNEXPECTED_LISTENER:' + host + ':' + str(port))
    except OSError:
        blocked.append(host + ':' + str(port))
print(json.dumps({'pass': True, 'url': 'https://' + HOST, 'tls': protocol,
                  'native_login_csrf_secure_cookie': True, 'wrong_hostname_rejected': True,
                  'other_interfaces_privileged_ports_not_listening_from_host': blocked,
                  'public_ca': str(public),
                  'ca_der_sha256': hashlib.sha256(ssl.PEM_cert_to_DER_cert(certificate.decode())).hexdigest(),
                  'windows_firewall_or_trust_store_changed': False,
                  'five_remote_clients_tested': False}, indent=2))

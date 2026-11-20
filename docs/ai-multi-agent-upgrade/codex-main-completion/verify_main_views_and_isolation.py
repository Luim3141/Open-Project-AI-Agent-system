"""Actual Main Native reads and service-HMAC negative checks; no forged browser session."""
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path
from native_configure_views import Configuration, Native, OUT

def main():
    assert json.loads((OUT / 'main-native-views-apply-result.json').read_text())['passed']
    state = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/gateway'
    credentials = json.loads((state / 'credentials.json').read_text()); key = (state / 'ui.key').read_bytes()
    manifest = json.loads((OUT / 'main-native-views-configuration.json').read_text(encoding='utf8'))
    boards = [e for e in manifest['events'] if e['kind'] == 'board']; query = next(e for e in manifest['events'] if e['kind'] == 'query')
    result = {'scope': 'ACTUAL_MAIN_NATIVE_AND_SERVICE_HMAC_NOT_BROWSER', 'checks': [], 'business_writes': 0, 'provider_calls': 0}
    def check(name, passed, actual=None):
        result['checks'].append({'id': name, 'passed': passed, 'actual': actual})
        (OUT / 'main-native-views-security-readback.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    for actor in range(19, 24):
        native = Native('http://127.0.0.1:8088', credentials[str(actor)], 5)
        visible = [native.call('/api/v3/grids/' + str(b['id'])) for b in boards]
        check(str(actor) + '-four-board-read', all(b['_links']['project']['href'] == '/api/v3/projects/5' for b in visible))
        saved = native.call('/api/v3/queries/' + str(query['id']))
        check(str(actor) + '-gantt-public-hierarchy', saved['public'] and saved['showHierarchies'] and saved['timelineVisible'])
        check(str(actor) + '-board-column-queries-readable', all(native.call('/api/v3/queries/' + str(widget['options']['queryId']))['_links']['project']['href'] == '/api/v3/projects/5' for b in visible for widget in b['widgets']))
    rows = Configuration('main').collection('/api/v3/projects/5/work_packages')
    result['native_sprint_membership_counts'] = dict(Counter((w['_links'].get('sprint', {}).get('href') or 'UNASSIGNED') for w in rows))
    result['native_version_membership_counts'] = dict(Counter((w['_links'].get('version', {}).get('href') or 'UNASSIGNED') for w in rows))
    check('all-329-business-rows', len(rows) == 329)
    def envelope(actor=19, project=5, action='get_execution_monitor'):
        return json.dumps({'actor': actor, 'project': project, 'audience': 'qldapm-ai-ui', 'at': time.time(), 'nonce': secrets.token_hex(16),
                           'operation': 'command', 'command': {'action': action, 'arguments': {'id': '87803ca8-72a1-4643-b00f-8fda05a06266'} if action != 'identity' else {}, 'idempotency_key': secrets.token_hex(16)}}).encode()
    def request(body, valid=True):
        signature = hmac.new(key, body, hashlib.sha256).hexdigest() if valid else '0' * 64
        req = urllib.request.Request('http://127.0.0.1:8090/internal/ui', data=body, headers={'Content-Type': 'application/json', 'X-Qldapm-Signature': signature})
        try:
            with urllib.request.urlopen(req, timeout=45) as response: return response.status, json.load(response)
        except urllib.error.HTTPError as error: return error.code, json.load(error)
    status, document = request(envelope())
    check('owner-monitor-readable', status == 200, status)
    for actor in range(20, 24):
        status, document = request(envelope(actor=actor))
        check(str(actor) + '-other-actor-monitor-denied', status == 403 and 'result' not in document, status)
    for name, body, valid in [('wrong-project', envelope(project=3), True), ('admin-not-business-member', envelope(actor=18), True), ('invalid-hmac', envelope(), False)]:
        status, document = request(body, valid)
        check(name + '-denied', status == 403 and 'result' not in document, status)
    body = envelope(action='identity'); first, _ = request(body); replay, document = request(body)
    check('hmac-nonce-replay-denied', first == 200 and replay == 403 and 'result' not in document, {'first': first, 'replay': replay})
    result['passed'] = all(c['passed'] for c in result['checks'])
    (OUT / 'main-native-views-security-readback.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result['passed']: raise SystemExit(1)

if __name__ == '__main__': main()

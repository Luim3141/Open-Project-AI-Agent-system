"""Native-authored manual QA attestations; review never replaces Native authorization."""
import hashlib
import json
import re
import time
import uuid
from datetime import datetime

from .agent_trace import current_run
from .native import NativeError
from .permissions import business_manager
from .store import canonical, digest

AUTOMATED_KINDS = {'AUTOMATED_NATIVE_READBACK', 'AUTOMATED_APPLICATION_WBS'}


def application_bridge_supported(native):
    capability = native.call('/api/v3/qldapm/capabilities')
    return (capability.get('project_id') == 5 and capability.get('enforced') is True and
            type(capability.get('qa_bridge_version')) is int and capability['qa_bridge_version'] == 1 and
            type(capability.get('application_qa_bridge_version')) is int and capability['application_qa_bridge_version'] == 1)


def source(native, identifier, activity_id, author):
    item = native.package(identifier)
    activities = native.collection(f'/api/v3/work_packages/{identifier}/activities')
    activity = next((a for a in activities if a.get('id') == activity_id), None)
    if activity is None:
        raise NativeError(409, 'QA_NATIVE_ACTIVITY_MISSING')
    links = activity.get('_links', {})
    if (links.get('user', {}).get('href') != f'/api/v3/users/{author}' or
            links.get('workPackage', {}).get('href') != f'/api/v3/work_packages/{identifier}'):
        raise PermissionError('QA_NATIVE_AUTHOR_REQUIRED')
    raw = activity.get('comment', {}).get('raw', '')
    created = activity.get('createdAt')
    if not isinstance(created, str) or datetime.fromisoformat(created.replace('Z', '+00:00')).tzinfo is None:
        raise ValueError('QA_NATIVE_ACTIVITY_TIMESTAMP_REQUIRED')
    if not isinstance(raw, str) or len(raw.encode()) > 65536:
        raise ValueError('QA_MANIFEST_TOO_LARGE')
    manifest = json.loads(raw)
    if not isinstance(manifest, dict) or set(manifest) != {
            'schema', 'work_package_id', 'source_version', 'criteria', 'tests',
            'attachment_id', 'attachment_sha256', 'related_run_id'}:
        raise ValueError('QA_MANIFEST_SCHEMA_REQUIRED')
    if (manifest['schema'] != 'QLDAPM_QA_EVIDENCE_V1' or
            type(manifest['work_package_id']) is not int or manifest['work_package_id'] != identifier or
            type(manifest['source_version']) is not int or manifest['source_version'] != item['lockVersion']):
        raise NativeError(409, 'QA_NATIVE_SOURCE_VERSION_CHANGED')
    # A caller's run ID is not execution evidence; automated runner receipts need their own trusted producer.
    if manifest['related_run_id'] is not None:
        raise ValueError('QA_AUTOMATED_RUN_PROVENANCE_NOT_IMPLEMENTED')
    criteria, tests = manifest['criteria'], manifest['tests']
    description = item.get('description', {}).get('raw', '')
    if (not isinstance(criteria, dict) or not 1 <= len(criteria) <= 100 or
            any(not isinstance(k, str) or not re.fullmatch(r'AC[1-9][0-9]{0,3}', k) or
                not isinstance(v, str) or not v.strip() or len(v) > 2000 or
                not re.search(r'(?m)^\s*' + re.escape(k) + r': ' + re.escape(v) + r'\s*$', description) for k, v in criteria.items())):
        raise ValueError('QA_CRITERIA_MUST_MATCH_NATIVE_SOURCE')
    native_criteria = re.findall(r'(?m)^\s*(AC[1-9][0-9]{0,3}): ', description)
    if set(criteria) != set(native_criteria) or len(set(native_criteria)) != len(native_criteria):
        raise ValueError('QA_ALL_NATIVE_CRITERIA_REQUIRED')
    if not isinstance(tests, list) or not 1 <= len(tests) <= 500:
        raise ValueError('QA_TEST_CASES_REQUIRED')
    for test in tests:
        if (not isinstance(test, dict) or set(test) != {'criterion_id', 'reference', 'expected', 'actual', 'outcome'} or
                any(not isinstance(test[k], str) or not test[k].strip() or len(test[k]) > 4000 for k in test) or
                test['criterion_id'] not in criteria or test['outcome'] not in {'PASSED', 'FAILED', 'BLOCKED'}):
            raise ValueError('QA_TEST_CASE_INVALID')
    if {t['criterion_id'] for t in tests} != set(criteria) or len({t['reference'] for t in tests}) != len(tests):
        raise ValueError('QA_CRITERIA_COVERAGE_AND_UNIQUE_TESTS_REQUIRED')
    attachment_id = manifest['attachment_id']
    if (type(attachment_id) is not int or attachment_id <= 0 or
            not isinstance(manifest['attachment_sha256'], str) or
            not re.fullmatch('[a-f0-9]{64}', manifest['attachment_sha256'])):
        raise ValueError('QA_ARTIFACT_ID_AND_SHA256_REQUIRED')
    attachment = native.call(f'/api/v3/attachments/{attachment_id}')
    attachment_links = attachment.get('_links', {})
    if (attachment.get('id') != attachment_id or
            attachment_links.get('container', {}).get('href') not in {
                f'/api/v3/work_packages/{identifier}', f'/api/v3/activities/{activity_id}'} or
            attachment_links.get('author', {}).get('href') != f'/api/v3/users/{author}'):
        raise PermissionError('QA_ARTIFACT_NATIVE_SCOPE_DENIED')
    size = attachment.get('fileSize')
    if type(size) is not int or not 1 <= size <= 1048576:
        raise ValueError('QA_ARTIFACT_SIZE_1_1048576_REQUIRED')
    content = native.call(f'/api/v3/attachments/{attachment_id}/content', binary=True)
    if len(content) != size or hashlib.sha256(content).hexdigest() != manifest['attachment_sha256']:
        raise NativeError(409, 'QA_ARTIFACT_CHANGED')
    binding = {'native_id': identifier, 'version': item['lockVersion'], 'activity_id': activity_id, 'activity_created_at': created,
               'activity_sha256': digest(raw), 'artifact_sha256': manifest['attachment_sha256'],
               'criteria_sha256': digest(description), 'assignee': item.get('_links', {}).get('assignee', {}).get('href')}
    return manifest, binding


def reviewer_current(service, actor, roles):
    if type(actor) is not int:
        return False
    try:
        _,identity=service.native_actor(actor)
    except PermissionError:
        return False
    except NativeError as error:
        if error.status in {401,403,404}:
            return False
        raise
    return identity['user_id']==actor and identity['project_id']==service.config['project_id'] and identity['role'] in roles


def read(service, who, native, identifier):
    try:
        if str(uuid.UUID(identifier)) != identifier:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('QA_EVIDENCE_UUID_REQUIRED') from None
    with service.store.connect() as db:
        row = db.execute('SELECT * FROM qa_evidence WHERE id=? AND project=?',
                         (identifier, service.config['project_id'])).fetchone()
    if row is None:
        raise PermissionError('QA_EVIDENCE_SCOPE_DENIED')
    body = json.loads(row['document'])
    automated = body.get('verification_kind') in AUTOMATED_KINDS
    if row['actor'] != who['user_id'] and not (business_manager(who['role']) or automated and who['role'] == 'QA'):
        raise PermissionError('QA_EVIDENCE_SCOPE_DENIED')
    if digest(canonical(body)) != row['hash'] or (body.get('id'), body.get('actor'), body.get('project_id')) != (
            row['id'], row['actor'], row['project']):
        raise ValueError('QA_EVIDENCE_HASH_MISMATCH')
    # A revoked Native read must remain forbidden, even when the ledger is readable.
    native.package(body['binding']['native_id'])
    if body.get('verification_kind') not in AUTOMATED_KINDS | {None, 'MANUAL_ATTESTATION'}:
        if row['actor'] != who['user_id']:
            service.store.record(who['user_id'], 'qa_evidence_oversight', identifier, 'NATIVE_AUTHORIZED_READ')
        return {**body, 'hash': row['hash'], 'state': row['state'], 'reviewer': row['reviewer'],
                'source_current': False, 'ready': False, 'compatibility': 'UNSUPPORTED_EVIDENCE_KIND'}
    if automated:
        from .native_qa_runs import evidence_state
        state = evidence_state(service, who, native, body, row['hash'])
        if row['actor'] != who['user_id']:
            service.store.record(who['user_id'], 'qa_evidence_oversight', identifier, 'NATIVE_AUTHORIZED_READ')
        supported = body['verification_kind'] == 'AUTOMATED_NATIVE_READBACK' or application_bridge_supported(native)
        return {**body, **state, 'hash': row['hash'], 'state': row['state'], 'reviewer': row['reviewer'],
                'native_transition_supported': supported,
                'ready': supported and row['state'] == 'accepted' and state['source_current'] and state['review_chain_complete'] and state['automated_verdict'] == 'PASSED'}
    try:
        manifest, binding = source(native, body['binding']['native_id'], body['binding']['activity_id'], body['actor'])
        current = binding == body['binding'] and manifest == body['manifest']
    except (ValueError, NativeError) as error:
        if isinstance(error, NativeError) and error.status != 409:
            raise
        current = False
    if row['actor'] != who['user_id']:
        service.store.record(who['user_id'], 'qa_evidence_oversight', identifier, 'NATIVE_AUTHORIZED_READ')
    reviewers_current = reviewer_current(service,row['reviewer'],{'PM','AI_SYSTEM_OWNER'}) if row['state']=='accepted' else False
    return {**body, 'hash': row['hash'], 'state': row['state'], 'reviewer': row['reviewer'],
            'reviewers_current': reviewers_current,
            'source_current': current, 'ready': current and reviewers_current and row['state'] == 'accepted' and
            all(t['outcome'] == 'PASSED' for t in body['manifest']['tests'])}


def capture(service, who, native, args, key):
    service.keys(args, {'native_id', 'activity_id'}, {'native_id', 'activity_id'})
    if who['role'] != 'QA' or current_run.get() is not None:
        raise PermissionError('QA_NATIVE_AUTHOR_REQUIRED')
    if any(type(v) is not int or v <= 0 for v in args.values()):
        raise ValueError('QA_NATIVE_POSITIVE_IDS_REQUIRED')
    manifest, binding = source(native, args['native_id'], args['activity_id'], who['user_id'])
    identifier = str(uuid.uuid5(uuid.NAMESPACE_URL,
        f"qldapm.native-qa:{service.config['project_id']}:{who['user_id']}:{args['native_id']}:{args['activity_id']}:{digest(canonical(binding))}"))
    captured = time.time()
    body = {'id': identifier, 'actor': who['user_id'], 'role': 'QA', 'captured_at': captured, 'project_id': service.config['project_id'],
            'verification_kind': 'MANUAL_ATTESTATION', 'binding': binding, 'manifest': manifest}
    with service.store.connect() as db:
        db.execute("INSERT OR IGNORE INTO qa_evidence VALUES(?,?,?,?,?,'pending',?,NULL)",
                   (identifier, who['user_id'], service.config['project_id'], canonical(body), digest(canonical(body)), captured))
    return read(service, who, native, identifier)


def decide(service, bearer, identifier, decision, fingerprint):
    return decide_actor(service, service.store.authenticate(bearer)['user_id'], identifier, decision, fingerprint)


def decide_actor(service, actor, identifier, decision, fingerprint):
    native, who = service.native_actor(actor)
    if not (business_manager(who['role']) or who['role'] == 'QA') or current_run.get() is not None:
        raise PermissionError('INDEPENDENT_AUTHENTICATED_QA_REVIEW_REQUIRED')
    if not isinstance(decision, str) or decision not in {'accept', 'reject'} or not isinstance(fingerprint, str) or not re.fullmatch('[a-f0-9]{64}', fingerprint):
        raise ValueError('QA_EXACT_REVIEW_HASH_REQUIRED')
    evidence = read(service, who, native, identifier)
    if evidence.get('verification_kind') not in AUTOMATED_KINDS | {None, 'MANUAL_ATTESTATION'}:
        raise PermissionError('QA_UNSUPPORTED_EVIDENCE_KIND')
    if evidence['verification_kind'] in AUTOMATED_KINDS:
        from .native_qa_runs import review
        review(service, who, evidence, decision, fingerprint)
        return read(service, who, native, identifier)
    if not business_manager(who['role']):
        raise PermissionError('INDEPENDENT_AUTHENTICATED_QA_REVIEW_REQUIRED')
    if evidence['actor'] == who['user_id'] or evidence['binding']['assignee'] == f"/api/v3/users/{who['user_id']}":
        raise PermissionError('QA_INDEPENDENT_REVIEWER_REQUIRED')
    if (evidence['hash'] != fingerprint or evidence['state'] != 'pending' or
            decision == 'accept' and not evidence['source_current']):
        raise NativeError(409, 'QA_CHANGED_STALE_OR_ALREADY_DECIDED')
    with service.store.connect() as db:
        changed = db.execute("UPDATE qa_evidence SET state=?,reviewer=? WHERE id=? AND project=? AND state='pending' AND hash=?",
            ('accepted' if decision == 'accept' else 'rejected', who['user_id'], identifier, service.config['project_id'], fingerprint)).rowcount
        if changed != 1:
            raise NativeError(409, 'QA_ALREADY_DECIDED')
        service.store.record(who['user_id'], 'qa_evidence_' + decision, identifier, 'EXACT_MANUAL_EVIDENCE_REVIEW',
                             version=fingerprint,connection=db)
    return read(service, who, native, identifier)


def transition_guard(service, who, native, item, args):
    with service.store.connect() as db:
        enrolled = db.execute('SELECT 1 FROM qa_evidence WHERE project=? AND json_extract(document,\'$.binding.native_id\')=? LIMIT 1',
                              (service.config['project_id'], item['id'])).fetchone()
    supplied = 'qa_evidence_id' in args or 'qa_evidence_hash' in args
    if not enrolled and not supplied:
        return
    status = native.call(f"/api/v3/statuses/{int(args['status_id'])}")
    name = re.sub('[^A-Z0-9]', '', status.get('name', '').upper())
    if not supplied and not (status.get('isClosed') or name in {'REVIEW', 'READYFORRELEASE', 'DONE'}):
        return
    if not all(k in args for k in ('qa_evidence_id', 'qa_evidence_hash')):
        raise NativeError(409, 'QA_REVIEWED_EVIDENCE_REQUIRED')
    evidence = read(service, who, native, args['qa_evidence_id'])
    if (not evidence['ready'] or evidence['hash'] != args['qa_evidence_hash'] or
            evidence['binding']['native_id'] != item['id']):
        raise NativeError(409, 'QA_CURRENT_ACCEPTED_EXACT_EVIDENCE_REQUIRED')
    payload = {'lockVersion': item['lockVersion'], '_links': {'status': {'href': f"/api/v3/statuses/{int(args['status_id'])}"}}}
    form = native.call(f"/api/v3/work_packages/{item['id']}/form", 'POST', payload)
    if errors := form.get('_embedded', {}).get('validationErrors'):
        raise NativeError(422, 'OPENPROJECT_FORM_REJECTED', errors)
    if evidence['verification_kind'] in AUTOMATED_KINDS:
        from .native_qa_bridge import preflight
        return preflight(service,who,native,item,args)


def perform(service, who, native, action, args, key):
    if service.mode != 'native' or service.config['project_id'] != 5:
        raise PermissionError('QA_EVIDENCE_NATIVE_MAIN_ONLY')
    if action == 'qa_evidence_capture':
        return capture(service, who, native, args, key)
    if action == 'qa_evidence_list':
        service.keys(args, {'native_id'}, set())
        target=args.get('native_id')
        if 'native_id' in args:
            if type(target) is not int or target<=0:raise ValueError('QA_NATIVE_POSITIVE_ID_REQUIRED')
            native.package(target)
        with service.store.connect() as db:
            rows = db.execute("SELECT id FROM qa_evidence WHERE project=? AND (actor=? OR ? OR (? AND json_extract(document,'$.verification_kind') IN ('AUTOMATED_NATIVE_READBACK','AUTOMATED_APPLICATION_WBS'))) AND (? IS NULL OR json_extract(document,'$.binding.native_id')=?) ORDER BY created DESC LIMIT 20",
                (service.config['project_id'], who['user_id'], business_manager(who['role']), who['role'] == 'QA',target,target)).fetchall()
        items = []
        for row in rows:
            try:
                evidence = read(service, who, native, row['id'])
            except PermissionError:continue
            except NativeError as error:
                if error.status in {403,404}:continue
                raise
            items.append({key: evidence[key] for key in ['id','actor','state','verification_kind','source_current','ready']}
                         | {'native_id': evidence['binding']['native_id'], 'version': evidence['binding']['version']})
        return {'items': items, 'limit': 20, 'scope': 'CURRENT_NATIVE_AUTHORIZED_EVIDENCE'}
    service.keys(args, {'id', 'hash', 'status_id'} if action == 'qa_transition_prepare' else {'id'},
                 {'id', 'hash', 'status_id'} if action == 'qa_transition_prepare' else {'id'})
    evidence = read(service, who, native, args['id'])
    if action == 'qa_evidence_get':
        return evidence
    if evidence['verification_kind'] == 'AUTOMATED_APPLICATION_WBS' and not evidence['native_transition_supported']:
        raise NativeError(422, 'APPLICATION_QA_NATIVE_TRANSITION_NOT_IMPLEMENTED')
    if not evidence['ready'] or evidence['hash'] != args['hash']:
        raise NativeError(409, 'QA_CURRENT_ACCEPTED_EXACT_EVIDENCE_REQUIRED')
    return service.execute_actor(who['user_id'], {'action': 'transition', 'idempotency_key': 'qa-transition-' + key,
        'arguments': {'id': evidence['binding']['native_id'], 'lock_version': evidence['binding']['version'],
                      'status_id': args['status_id'], 'qa_evidence_id': evidence['id'], 'qa_evidence_hash': evidence['hash']}})['result']

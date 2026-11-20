"""Fixed Native readback assertions; signed output is automated evidence, never human approval."""
import hashlib
import hmac
import json
import re
import time
import uuid
from datetime import date
from pathlib import Path

from .native import NativeError
from .presentation import safe_text as redact_secrets
from .permissions import business_manager
from .store import canonical, digest

PRODUCER = 'qldapm-native-readback-v1'
CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DOMAIN = b'qldapm.native-qa-run.v1\0'
REVIEW_DOMAIN = b'qldapm.native-qa-review.v1\0'
FIELDS = {'subject': None, 'startDate': None, 'dueDate': None, 'priority_name': None, 'type_id': 'type', 'status_id': 'status',
          'assignee_id': 'assignee', 'priority_id': 'priority', 'parent_id': 'parent'}
LINKS = {'type': 'types', 'status': 'statuses', 'assignee': 'users', 'priority': 'priorities', 'parent': 'work_packages'}


def snapshot(item):
    return {'id': item['id'], 'version': item['lockVersion'], 'description': item.get('description', {}).get('raw', ''),
            'fields': {field: value(item, field) for field in FIELDS},
            'project': item.get('_links', {}).get('project', {}).get('href')}


def value(item, field):
    if field == 'priority_name':
        return item.get('_links', {}).get('priority', {}).get('title')
    link = FIELDS[field]
    if link is None:
        return item.get(field)
    href = (item.get('_links', {}).get(link) or {}).get('href')
    if href is None:
        return None
    match = re.fullmatch(r'/api/v3/' + LINKS[link] + r'/([1-9][0-9]*)', href)
    if match is None:
        raise ValueError('QA_NATIVE_FIELD_FORMAT_INVALID')
    return int(match[1])


def assignee_identity(service, item):
    actor = value(item, 'assignee_id')
    if actor is None or str(actor) not in service.config['users']:
        return None
    _, identity = service.native_actor(actor)
    return {'actor': actor, 'role': 'BA' if identity['role'] == 'BA-PM' else identity['role']}


def predicates(clause):
    match = re.fullmatch(r'Native startDate is (\d{4}-\d{2}-\d{2}) and dueDate is (\d{4}-\d{2}-\d{2})\.', clause)
    if match:
        for value in match.groups():date.fromisoformat(value)
        return [('startDate', match[1]), ('dueDate', match[2])]
    match = re.fullmatch(r'([A-Za-z][A-Za-z _-]{0,79}) priority([1-9][0-9]*) and (PM|BA|BE|FE|QA)([1-9][0-9]*) assignment are preserved\.', clause)
    if match:
        return [('priority_name', match[1]), ('priority_id', int(match[2])), ('assignee_id', int(match[4])), ('assignee_role', match[3])]
    match = re.fullmatch(r'native\.([A-Za-z_]+) == (.{1,2000})', clause)
    if match is None or match[1] not in FIELDS:
        raise ValueError('QA_AUTOMATED_CRITERION_UNSUPPORTED; fixed Native readback assertions only')
    expected = json.loads(match[2]);field = match[1]
    if (field.endswith('_id') and expected is not None and (type(expected) is not int or expected <= 0) or
            not field.endswith('_id') and expected is not None and not isinstance(expected, str)):
        raise ValueError('QA_NATIVE_EXPECTED_VALUE_TYPE_INVALID')
    return [(field, expected)]


def target(native, identifier):
    if type(identifier) is not int or identifier <= 0:
        raise ValueError('QA_NATIVE_POSITIVE_ID_REQUIRED')
    item = native.package(identifier)
    if item.get('_links', {}).get('project', {}).get('href') != '/api/v3/projects/5':
        raise PermissionError('QA_NATIVE_MAIN_SCOPE_REQUIRED')
    description = item.get('description', {}).get('raw', '')
    if not isinstance(description, str) or len(description.encode()) > 65536:
        raise ValueError('QA_NATIVE_CRITERIA_REQUIRED')
    clauses = re.findall(r'(?m)^\s*(AC[1-9][0-9]{0,3}): ([^\r\n]+)\s*$', description)
    labels = re.findall(r'(?m)^[ \t]*(AC[0-9]+):', description)
    if not 1 <= len(clauses) <= 100 or labels != [c[0] for c in clauses] or len(set(labels)) != len(labels):
        raise ValueError('QA_UNIQUE_NATIVE_CRITERIA_REQUIRED')
    tests = []
    for criterion, clause in clauses:
        for field, expected in predicates(clause):
            tests.append({'criterion_id': criterion, 'clause': clause, 'field': field, 'expected': expected})
    return item, tests


def signing_key(service):
    path = service.store.root / 'ui.key'
    if not path.is_file():
        raise PermissionError('NATIVE_QA_PRODUCER_KEY_REQUIRED')
    return path.read_bytes()


def for_agent(service, bearer, identifier):
    native, who = service.native_actor(service.store.authenticate(bearer)['user_id'])
    return _report(who,read(service, who, native, identifier))


def _report(who,result):
    if not result['source_current']:
        raise NativeError(409, 'QA_RUN_SOURCE_CHANGED')
    from .qa_agent import VerifiedTestReport, _REPORT_ISSUER
    return VerifiedTestReport(_REPORT_ISSUER, who['user_id'], result['project_id'], result['binding']['native_id'],
        result['binding']['version'], result['id'], result['verdict'], result['producer']['id'], result['finished_at'], result['artifact_sha256'])


def latest_report(service,actor,identifier,version):
    native,who=service.native_actor(actor)
    if not (business_manager(who['role']) or who['role']=='QA'):return None
    if type(identifier) is not int or identifier<=0 or type(version) is not int or version<0:
        raise ValueError('QA_NATIVE_SOURCE_BINDING_REQUIRED')
    with service.store.connect() as db:
        row=db.execute("SELECT id FROM qa_test_runs WHERE project=? AND json_extract(document,'$.binding.native_id')=? AND json_extract(document,'$.binding.version')=? ORDER BY created DESC,id DESC LIMIT 1",
            (service.config['project_id'],identifier,version)).fetchone()
    return _report(who,read(service,who,native,row['id'])) if row else None


def read(service, who, native, identifier):
    try:
        if str(uuid.UUID(identifier)) != identifier:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('QA_RUN_UUID_REQUIRED') from None
    with service.store.connect() as db:
        row = db.execute('SELECT * FROM qa_test_runs WHERE id=? AND project=?', (identifier, service.config['project_id'])).fetchone()
    if row is None or row['actor'] != who['user_id'] and not (business_manager(who['role']) or who['role'] == 'QA'):
        raise PermissionError('QA_RUN_SCOPE_DENIED')
    body = json.loads(row['document'])
    signature = body.pop('signature', None)
    expected = hmac.new(signing_key(service), DOMAIN + canonical(body).encode(), hashlib.sha256).hexdigest()
    if (not isinstance(signature, str) or not hmac.compare_digest(signature, expected) or
            (body.get('id'), body.get('actor'), body.get('project_id')) != (row['id'], row['actor'], row['project']) or
            digest(body.get('artifact', '')) != body.get('artifact_sha256')):
        raise ValueError('QA_TRUSTED_RUN_INTEGRITY_FAILED')
    item = native.package(body['binding']['native_id'])
    if body.get('verification_kind') not in {'AUTOMATED_NATIVE_READBACK', 'AUTOMATED_APPLICATION_WBS'}:
        if row['actor'] != who['user_id']:
            service.store.record(who['user_id'], 'qa_run_oversight', identifier, 'NATIVE_AUTHORIZED_READ')
        return {**body, 'signature': signature, 'source_current': False, 'compatibility': 'UNSUPPORTED_RUN_KIND'}
    current = digest(canonical(snapshot(item))) == body['binding']['snapshot_sha256']
    if body.get('verification_kind') == 'AUTOMATED_APPLICATION_WBS':
        from .application_qa_intake import stored_source_current
        current = current and stored_source_current(service, native, body, item)
    if 'assignee_identity' in body['binding']:
        current = current and assignee_identity(service, item) == body['binding']['assignee_identity']
    if row['actor'] != who['user_id']:
        service.store.record(who['user_id'], 'qa_run_oversight', identifier, 'NATIVE_AUTHORIZED_READ')
    return {**body, 'signature': signature, 'source_current': current}


def run(service, who, native, identifier, key):
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != CODE_SHA256:
        raise NativeError(409, 'QA_RUNNER_CODE_CHANGED')
    item, clauses = target(native, identifier)
    initial = snapshot(item)
    started = time.time()
    tests = []
    assignment = None
    for clause in clauses:
        observed = native.package(identifier)
        if clause['field'] == 'assignee_role':
            assignment = assignee_identity(service, observed)
            actual = assignment['role'] if assignment else None
        else:actual = value(observed, clause['field'])
        tests.append({'criterion_id': clause['criterion_id'], 'reference': PRODUCER + ':' + clause['criterion_id'] + ':' + clause['field'],
                      'expected': redact_secrets(canonical(clause['expected'])),
                      'actual': redact_secrets(canonical(actual)), 'observed_at': time.time(),
                      'outcome': 'PASSED' if actual == clause['expected'] else 'FAILED'})
    current = snapshot(native.package(identifier)) == initial
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != CODE_SHA256:
        raise NativeError(409, 'QA_RUNNER_CODE_CHANGED')
    finished = time.time()
    verdict = 'BLOCKED' if not current else 'PASSED' if all(t['outcome'] == 'PASSED' for t in tests) else 'FAILED'
    binding = {'native_id': identifier, 'version': item['lockVersion'], 'snapshot_sha256': digest(canonical(initial)),
               'criteria_sha256': digest(initial['description']), 'assignee': item.get('_links', {}).get('assignee', {}).get('href')}
    if assignment is not None:binding['assignee_identity'] = assignment
    producer = {'id': PRODUCER, 'code_sha256': CODE_SHA256}
    artifact = canonical({'suite': PRODUCER, 'project_id': service.config['project_id'], 'binding': binding,
                          'producer': producer, 'started_at': started, 'finished_at': finished, 'tests': tests, 'verdict': verdict})
    identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, canonical(['qldapm.qa.run', service.config['project_id'], who['user_id'], key])))
    body = {'id': identifier, 'actor': who['user_id'], 'project_id': service.config['project_id'],
            'verification_kind': 'AUTOMATED_NATIVE_READBACK', 'producer': producer, 'binding': binding,
            'criteria': {c['criterion_id']: redact_secrets(c['clause']) for c in clauses}, 'tests': tests,
            'started_at': started, 'finished_at': finished, 'verdict': verdict,
            'artifact': artifact, 'artifact_sha256': digest(artifact)}
    body['signature'] = hmac.new(signing_key(service), DOMAIN + canonical(body).encode(), hashlib.sha256).hexdigest()
    with service.store.connect() as db:
        db.execute('INSERT OR IGNORE INTO qa_test_runs VALUES(?,?,?,?,?)',
                   (identifier, who['user_id'], service.config['project_id'], canonical(body), finished))
    return read(service, who, native, identifier)


def perform(service, who, native, action, args, key):
    if service.mode != 'native' or service.config['project_id'] != 5:
        raise PermissionError('QA_RUN_NATIVE_MAIN_ONLY')
    if action == 'qa_evidence_from_run':
        service.keys(args, {'run_id'}, {'run_id'})
        result_run = read(service, who, native, args['run_id'])
        if result_run['actor'] != who['user_id']:
            raise PermissionError('QA_RUN_PRODUCER_ACTOR_REQUIRED')
        if not result_run['source_current']:
            raise NativeError(409, 'QA_RUN_SOURCE_CHANGED')
        identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, 'qldapm.qa.evidence:' + result_run['id']))
        body = {'id': identifier, 'actor': who['user_id'], 'role': 'AUTOMATED_PRODUCER',
                'captured_at': time.time(), 'project_id': service.config['project_id'],
                'verification_kind': result_run['verification_kind'], 'producer': result_run['producer'], 'run_id': result_run['id'],
                'binding': {**result_run['binding'], 'artifact_sha256': result_run['artifact_sha256']}, 'manifest': manifest(result_run)}
        with service.store.connect() as db:
            db.execute("INSERT OR IGNORE INTO qa_evidence VALUES(?,?,?,?,?,'pending_qa',?,NULL)",
                (identifier, who['user_id'], service.config['project_id'], canonical(body), digest(canonical(body)), body['captured_at']))
        from .native_qa import read as evidence_read
        return evidence_read(service, who, native, identifier)
    service.keys(args, {'native_id'} if action == 'qa_test_run' else {'id'}, {'native_id'} if action == 'qa_test_run' else {'id'})
    return run(service, who, native, args['native_id'], key) if action == 'qa_test_run' else read(service, who, native, args['id'])


def manifest(run):
    schema = 'QLDAPM_AUTOMATED_APPLICATION_QA_V1' if run['verification_kind'] == 'AUTOMATED_APPLICATION_WBS' else 'QLDAPM_AUTOMATED_NATIVE_QA_V1'
    return {'schema': schema, 'work_package_id': run['binding']['native_id'],
            'source_version': run['binding']['version'], 'criteria': run['criteria'], 'tests': run['tests'],
            'artifact_sha256': run['artifact_sha256'], 'started_at': run['started_at'], 'finished_at': run['finished_at']}


def evidence_state(service, who, native, body, fingerprint):
    run = read(service, who, native, body['run_id'])
    if (run['actor'] != body['actor'] or run['producer'] != body.get('producer') or
            {**run['binding'], 'artifact_sha256': run['artifact_sha256']} != body['binding'] or manifest(run) != body['manifest']):
        raise ValueError('QA_AUTOMATED_EVIDENCE_PROVENANCE_INVALID')
    reviews = []
    with service.store.connect() as db:
        rows = {row['stage']: json.loads(row['document']) for row in db.execute(
            'SELECT stage,document FROM qa_evidence_reviews WHERE evidence=?', (body['id'],))}
    for stage in ['qa', 'manager']:
        if stage not in rows:continue
        record = rows[stage];signature = record.pop('signature', None)
        expected = hmac.new(signing_key(service), REVIEW_DOMAIN + canonical(record).encode(), hashlib.sha256).hexdigest()
        if (not isinstance(signature, str) or not hmac.compare_digest(signature, expected) or
                record.get('evidence_id') != body['id'] or record.get('hash') != fingerprint or record.get('stage') != stage or
                record.get('actor') == body['actor'] or body['binding']['assignee'] == f"/api/v3/users/{record.get('actor')}" or
                (record.get('role') != 'QA' if stage == 'qa' else not business_manager(record.get('role')))):
            raise ValueError('QA_REVIEW_PROVENANCE_INVALID')
        reviews.append(record)
    from .native_qa import reviewer_current
    reviewers_current=all(reviewer_current(service,r['actor'],{r['role']}) for r in reviews)
    approved = (len(reviews) == 2 and reviews[0]['actor'] != reviews[1]['actor'] and reviewers_current and
                all(r['decision'] == 'accept' for r in reviews))
    return {'source_current': run['source_current'], 'reviews': reviews, 'artifact': run['artifact'],
            'automated_verdict': run['verdict'], 'review_chain_complete': approved, 'reviewers_current': reviewers_current}


def review(service, who, evidence, decision, fingerprint):
    role = who['role'];stage = 'qa' if role == 'QA' else 'manager'
    if evidence['actor'] == who['user_id'] or evidence['binding']['assignee'] == f"/api/v3/users/{who['user_id']}":
        raise PermissionError('QA_INDEPENDENT_REVIEWER_REQUIRED')
    if stage == 'manager' and evidence['state'] == 'pending_qa':
        raise PermissionError('QA_REVIEW_REQUIRED_BEFORE_MANAGER')
    if stage == 'manager' and decision == 'accept' and evidence.get('reviewers_current') is False:
        raise NativeError(409,'QA_REVIEWER_AUTHORIZATION_CHANGED')
    expected_state = 'pending_qa' if stage == 'qa' else 'qa_accepted'
    if (evidence['hash'] != fingerprint or evidence['state'] != expected_state or
            decision == 'accept' and not evidence['source_current']):
        raise NativeError(409, 'QA_CHANGED_STALE_OR_ALREADY_DECIDED')
    if stage == 'manager' and (not evidence['reviews'] or evidence['reviews'][0]['decision'] != 'accept'):
        raise PermissionError('QA_REVIEW_REQUIRED_BEFORE_MANAGER')
    proof = {'evidence_id': evidence['id'], 'hash': fingerprint, 'stage': stage, 'actor': who['user_id'],
             'role': role, 'decision': decision, 'at': time.time()}
    proof['signature'] = hmac.new(signing_key(service), REVIEW_DOMAIN + canonical(proof).encode(), hashlib.sha256).hexdigest()
    state = ('qa_accepted' if stage == 'qa' else 'accepted') if decision == 'accept' else 'rejected'
    with service.store.connect() as db:
        changed = db.execute('UPDATE qa_evidence SET state=?,reviewer=? WHERE id=? AND project=? AND state=? AND hash=?',
            (state, who['user_id'] if stage == 'manager' else None, evidence['id'], service.config['project_id'], expected_state, fingerprint)).rowcount
        if changed != 1:raise NativeError(409, 'QA_ALREADY_DECIDED')
        db.execute('INSERT INTO qa_evidence_reviews VALUES(?,?,?)', (evidence['id'], stage, canonical(proof)))
        service.store.record(who['user_id'], 'qa_evidence_' + stage + '_' + decision, evidence['id'], 'EXACT_AUTOMATED_EVIDENCE_REVIEW',
                             version=fingerprint,connection=db)

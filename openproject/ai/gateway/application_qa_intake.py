"""Validate an operator-produced application proof without recording a human decision."""
import hashlib
import json
import os
import uuid
from pathlib import Path

from .agent_trace import current_run
from .application_qa_proof import CODE_SHA256, DOMAIN, GATEWAY_SOURCES, PRODUCER, validate
from .native import NativeError
from .native_qa_runs import DOMAIN as RUN_DOMAIN, assignee_identity, signing_key, snapshot
from .store import canonical, digest

KIND = 'AUTOMATED_APPLICATION_WBS'


def gateway_sources():
    directory = Path(__file__).resolve().parent
    return {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in GATEWAY_SOURCES}


def current_sources(native):
    capabilities = native.call('/api/v3/qldapm/capabilities')
    if capabilities.get('project_id') != 5 or capabilities.get('enforced') is not True:
        raise ValueError('APPLICATION_PROOF_NATIVE_CAPABILITY_REQUIRED')
    return {'gateway': gateway_sources(), 'core': capabilities.get('application_qa_source_sha256')}


def load_verified(service, who, native, identifier):
    if (service.mode != 'native' or service.config['project_id'] != 5 or current_run.get() is not None or
            who.get('user_id') != 18 or who.get('role') != 'AI_SYSTEM_OWNER'):
        raise PermissionError('APPLICATION_PROOF_AUTHENTICATED_OWNER_REQUIRED')
    identity = native.identity(18)
    if (identity.get('user_id'), identity.get('role'), identity.get('project_id')) != (18, 'AI_SYSTEM_OWNER', 5):
        raise PermissionError('APPLICATION_PROOF_NATIVE_OWNER_REVOKED')
    try:
        if str(uuid.UUID(identifier)) != identifier:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('APPLICATION_PROOF_UUID_REQUIRED') from None
    directory = service.store.root / 'application-proofs'
    path = directory / (identifier + '.json')
    if directory.is_symlink() or not directory.is_dir() or path.is_symlink():
        raise ValueError('APPLICATION_PROOF_LOCAL_FILE_REQUIRED')
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            content = stream.read(1_100_001)
        if len(content) > 1_100_000:
            raise ValueError('APPLICATION_PROOF_SIZE_INVALID')
        bundle = json.loads(content)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('APPLICATION_PROOF_LOCAL_FILE_INVALID') from error
    body = validate(bundle, signing_key(service), native.package(371), current_sources(native))
    if body['id'] != identifier:
        raise ValueError('APPLICATION_PROOF_ID_MISMATCH')
    return body


def stored_source_current(service, native, run, item):
    key = signing_key(service)
    proof = {'document': run['artifact'], 'signature': run['application_signature']}
    try:
        _, producer = service.native_actor(18)
        if producer['role'] != 'AI_SYSTEM_OWNER':
            return False
        validate(proof, key, item, current_sources(native))
        return True
    except PermissionError:
        return False
    except NativeError as error:
        if error.status in {401, 403, 404}:
            return False
        raise
    except ValueError as error:
        if str(error) in {'APPLICATION_PROOF_NATIVE_SOURCE_CHANGED', 'APPLICATION_PROOF_CODE_CHANGED',
                         'APPLICATION_PROOF_PRODUCER_CODE_CHANGED', 'APPLICATION_PROOF_NATIVE_SCOPE_REQUIRED',
                         'APPLICATION_PROOF_PINNED_CRITERIA_REQUIRED', 'APPLICATION_PROOF_NATIVE_CAPABILITY_REQUIRED'}:
            return False
        raise


def admit(service, who, native, identifier):
    import hmac
    proof = load_verified(service, who, native, identifier)
    item = native.package(371)
    if snapshot(item) != proof['source']:
        raise NativeError(409, 'APPLICATION_PROOF_SOURCE_CHANGED_BEFORE_ADMISSION')
    artifact = canonical(proof)
    key = signing_key(service)
    run_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'qldapm.application.qa.run:' + proof['id']))
    binding = {'native_id': item['id'], 'version': item['lockVersion'], 'snapshot_sha256': digest(canonical(snapshot(item))),
               'criteria_sha256': digest(snapshot(item)['description']),
               'assignee': item.get('_links', {}).get('assignee', {}).get('href'),
               'assignee_identity': assignee_identity(service, item)}
    body = {'id': run_id, 'actor': who['user_id'], 'project_id': 5, 'verification_kind': KIND,
            'producer': {'id': PRODUCER, 'code_sha256': CODE_SHA256}, 'binding': binding,
            'criteria': proof['criteria'], 'tests': proof['tests'], 'started_at': proof['started_at'],
            'finished_at': proof['finished_at'], 'verdict': proof['verdict'],
            'artifact': artifact, 'artifact_sha256': digest(artifact),
            'application_signature': hmac.new(key, DOMAIN + artifact.encode(), hashlib.sha256).hexdigest()}
    body['signature'] = hmac.new(key, RUN_DOMAIN + canonical(body).encode(), hashlib.sha256).hexdigest()
    text = canonical(body)
    with service.store.connect() as db:
        db.execute('INSERT OR IGNORE INTO qa_test_runs VALUES(?,?,?,?,?)', (run_id, who['user_id'], 5, text, proof['finished_at']))
        if db.execute('SELECT document FROM qa_test_runs WHERE id=?', (run_id,)).fetchone()[0] != text:
            raise NativeError(409, 'APPLICATION_PROOF_EXISTING_RUN_CHANGED')
    from .native_qa_runs import perform
    return perform(service, who, native, 'qa_evidence_from_run', {'run_id': run_id}, None)

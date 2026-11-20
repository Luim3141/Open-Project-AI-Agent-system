"""Pinned WBS Bug371 application proof; technical evidence never grants human approval."""
import hashlib
import hmac
import json
import math
import re
import time
import uuid
from pathlib import Path

from .native_qa_runs import snapshot
from .store import canonical, digest

DOMAIN = b'qldapm.wbs-application-proof.v1\0'
PRODUCER = 'qldapm-wbs-application-v1'
QUALIFICATION_FILES = ('gateway/application_qa_proof.py', 'automation/wbs_application_qualification.py',
    'tests/wbs_application_native_client.py', 'tests/test_native_wbs_analysis.py',
    'tests/test_wbs_scheduled_parent_effects.py', 'tests/test_native_wbs.py', 'tests/test_native_bug_lifecycle.py')
MANIFEST_PATH = Path(__file__).with_name('application_qa_producer_manifest.json')


def qualification_manifest():
    root = Path(__file__).resolve().parents[1]
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in QUALIFICATION_FILES}


def producer_code_sha256():
    manifest = json.loads(MANIFEST_PATH.read_text())
    if (not isinstance(manifest, dict) or set(manifest) != set(QUALIFICATION_FILES) or
            any(not isinstance(v, str) or not re.fullmatch('[a-f0-9]{64}', v) for v in manifest.values()) or
            manifest['gateway/application_qa_proof.py'] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
        raise ValueError('APPLICATION_PROOF_PINNED_PRODUCER_MANIFEST_REQUIRED')
    return digest(canonical(manifest))


CODE_SHA256 = producer_code_sha256()
CRITERIA_SHA256 = 'bf84577edd40c07b8215c0e15a182a7d659db2dae3563981fe6cc12cf21057a7'
QUALIFICATION = 'ISOLATED_APPLICATION_AND_NATIVE; synthetic embeddings and isolated decisions; not human QA approval'
GATEWAY_SOURCES = ('native_wbs.py', 'native_wbs_hierarchy.py', 'native_wbs_relations.py', 'wbs_analysis.py')
CORE_SOURCES = ('app/models/concerns/qldapm_gate_write.rb', 'app/models/qldapm/gate_policy.rb',
    'app/services/qldapm/hierarchy_readback.rb', 'app/services/work_packages/create_service.rb',
    'app/services/work_packages/set_attributes_service/derive_progress_values_status_based.rb')
FIELDS = {'version', 'id', 'actor', 'project_id', 'producer', 'producer_sha256', 'source', 'criteria', 'sources',
    'build', 'started_at', 'finished_at', 'tests', 'verdict', 'qualification'}
SHA = re.compile('[a-f0-9]{64}')


def criteria(item):
    if (item.get('id') != 371 or item.get('_links', {}).get('project', {}).get('href') != '/api/v3/projects/5' or
            item.get('_links', {}).get('type', {}).get('href') != '/api/v3/types/1' or
            not str(item.get('subject', '')).startswith('[Bug] [CODEX TEST]') or
            type(item.get('lockVersion')) is not int or item['lockVersion'] < 0):
        raise ValueError('APPLICATION_PROOF_NATIVE_SCOPE_REQUIRED')
    text = item.get('description', {}).get('raw', '')
    if not isinstance(text, str) or len(text.encode()) > 65536:
        raise ValueError('APPLICATION_PROOF_CRITERIA_REQUIRED')
    pairs = re.findall(r'(?m)^[ \t]*(AC[1-9][0-9]{0,3}):[ \t]+([^\r\n]+)$', text)
    labels = re.findall(r'(?m)^[ \t]*(AC[0-9]+):', text)
    result = dict(pairs)
    if (labels != list(result) or len(pairs) != 4 or set(result) != {'AC1', 'AC2', 'AC3', 'AC4'} or
            digest(canonical(result)) != CRITERIA_SHA256):
        raise ValueError('APPLICATION_PROOF_PINNED_CRITERIA_REQUIRED')
    return result


def validate(bundle, key, item, sources, *, now=None):
    if (not isinstance(bundle, dict) or set(bundle) != {'document', 'signature'} or
            not isinstance(bundle['document'], str) or not 1 <= len(bundle['document'].encode()) <= 1048576 or
            not isinstance(key, bytes) or not 16 <= len(key) <= 4096 or
            not isinstance(bundle['signature'], str) or not SHA.fullmatch(bundle['signature'])):
        raise ValueError('APPLICATION_PROOF_SCHEMA_OR_SIZE_INVALID')
    text = bundle['document']
    expected = hmac.new(key, DOMAIN + text.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, bundle['signature']):
        raise ValueError('APPLICATION_PROOF_SIGNATURE_INVALID')
    try:
        body = json.loads(text)
        if canonical(body) != text:
            raise ValueError('APPLICATION_PROOF_CANONICAL_REQUIRED')
    except (TypeError, RecursionError):
        raise ValueError('APPLICATION_PROOF_MALFORMED') from None
    if (not isinstance(body, dict) or set(body) != FIELDS or type(body['version']) is not int or body['version'] != 1 or
            body['actor'] != 18 or body['project_id'] != 5 or body['producer'] != PRODUCER or
            body['qualification'] != QUALIFICATION):
        raise ValueError('APPLICATION_PROOF_SCHEMA_OR_PRODUCER_INVALID')
    try:
        if str(uuid.UUID(body['id'])) != body['id']:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('APPLICATION_PROOF_UUID_REQUIRED') from None
    if body['producer_sha256'] != CODE_SHA256:
        raise ValueError('APPLICATION_PROOF_PRODUCER_CODE_CHANGED')
    actual_criteria = criteria(item)
    if body['source'] != snapshot(item) or body['criteria'] != actual_criteria:
        raise ValueError('APPLICATION_PROOF_NATIVE_SOURCE_CHANGED')
    provided = body['sources']
    if not isinstance(provided, dict) or set(provided) != {'gateway', 'core'}:
        raise ValueError('APPLICATION_PROOF_SOURCE_MANIFEST_INVALID')
    for domain, paths in [('gateway', GATEWAY_SOURCES), ('core', CORE_SOURCES)]:
        group = provided[domain]
        if (not isinstance(group, dict) or set(group) != set(paths) or
                any(not isinstance(v, str) or not SHA.fullmatch(v) for v in group.values())):
            raise ValueError('APPLICATION_PROOF_SOURCE_MANIFEST_INVALID')
    if provided != sources:
        raise ValueError('APPLICATION_PROOF_CODE_CHANGED')
    build = body['build']
    if (not isinstance(build, dict) or set(build) != {'gateway', 'core'} or
            any(not isinstance(v, str) or not re.fullmatch(r'sha256:[a-f0-9]{64}', v) for v in build.values())):
        raise ValueError('APPLICATION_PROOF_IMMUTABLE_BUILD_REQUIRED')
    started, finished = body['started_at'], body['finished_at']
    if (any(type(at) not in (int, float) or not math.isfinite(at) for at in [started, finished]) or
            not 0 <= started <= finished <= (time.time() if now is None else now) + 30):
        raise ValueError('APPLICATION_PROOF_TIMESTAMP_INVALID')
    tests = body['tests']
    if not isinstance(tests, list) or len(tests) != 4:
        raise ValueError('APPLICATION_PROOF_COMPLETE_TESTS_REQUIRED')
    for test in tests:
        if (not isinstance(test, dict) or set(test) != {'criterion_id', 'reference', 'expected', 'actual', 'outcome', 'proof_sha256'} or
                not isinstance(test['criterion_id'], str) or test['criterion_id'] not in actual_criteria or test['reference'] != 'wbs-application:' + test['criterion_id'] or
                not isinstance(test['outcome'], str) or test['outcome'] not in {'PASSED', 'FAILED', 'BLOCKED'} or
                any(not isinstance(test[k], str) or not 1 <= len(test[k].encode()) <= 4000 for k in ['expected', 'actual']) or
                not isinstance(test['proof_sha256'], str) or not SHA.fullmatch(test['proof_sha256'])):
            raise ValueError('APPLICATION_PROOF_TEST_INVALID')
    if {test['criterion_id'] for test in tests} != set(actual_criteria):
        raise ValueError('APPLICATION_PROOF_CRITERIA_COVERAGE_REQUIRED')
    verdict = 'FAILED' if any(t['outcome'] == 'FAILED' for t in tests) else 'BLOCKED' if any(t['outcome'] == 'BLOCKED' for t in tests) else 'PASSED'
    if body['verdict'] != verdict:
        raise ValueError('APPLICATION_PROOF_VERDICT_MISMATCH')
    return body

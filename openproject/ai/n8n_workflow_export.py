"""Export qualified workflow definitions; keys/owner data remain in private backups."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import uuid

from n8n_owner import provision
from n8n_status_workflow import SOURCE, DAILY_SOURCE, ERROR_SOURCE, LEGACY_SOURCE, LEGACY_DAILY_SOURCE, LocalWorkflow, matches, validate

CURRENT_SOURCES = (ERROR_SOURCE, SOURCE, DAILY_SOURCE)


def portable(actual, expected):
    validate(expected)
    if not matches(actual, expected) or actual.get('settings') != expected['settings']:
        raise PermissionError('WORKFLOW_CHANGED; preserve owner edits, no export overwrite')
    uuid.UUID(actual['versionId'])
    result = {key: actual[key] for key in expected}
    # Deployment activation IDs differ; the portable source version stays stable and inactive.
    result.update(active=False, versionId=expected['versionId'])
    return validate(result)


def export(owner_root, destination, base='http://localhost:5678'):
    if destination.exists():
        raise FileExistsError('FRESH_EXPORT_DIRECTORY_REQUIRED')
    records, documents = [], []
    for source in CURRENT_SOURCES:
        expected = json.loads(source.read_text(encoding='utf-8'))
        client = LocalWorkflow(base)
        client.workflow_id = expected['id']
        provision(owner_root, client)
        actual = client.workflow()
        document = portable(actual, expected)
        content = (json.dumps(document, ensure_ascii=False, indent=2) + '\n').encode()
        documents.append((source.name, content))
        records.append({'id': expected['id'], 'file': source.name, 'sha256': hashlib.sha256(content).hexdigest(),
                        'source_version_id': expected['versionId'], 'installed_version_id': actual['versionId']})
    destination.mkdir(parents=True)
    for filename, content in documents:
        with (destination / filename).open('xb') as stream:
            stream.write(content)
    manifest = {'schema': 1, 'workflows': records}
    with (destination / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
    verify_bundle(destination)
    return {'passed': True, 'workflow_count': len(CURRENT_SOURCES), 'credential_values_exported': False,
            'active_on_import': False, 'source_versions': records}


def verify_bundle(directory):
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema') != 1 or not isinstance(manifest.get('workflows'), list):
        raise ValueError('WORKFLOW_EXPORT_MANIFEST_INVALID')
    filenames = [entry['file'] for entry in manifest['workflows']]
    source_sets = ((LEGACY_SOURCE, LEGACY_DAILY_SOURCE), CURRENT_SOURCES)
    sources = next((group for group in source_sets if {source.name for source in group} == set(filenames)), None)
    if sources is None or len(filenames) != len(set(filenames)):
        raise ValueError('FIXED_EXPORT_FILES_REQUIRED')
    expected = {source.name: json.loads(source.read_text(encoding='utf-8')) for source in sources}
    seen = set()
    for entry in manifest['workflows']:
        name = entry['file']
        if name not in expected or name in seen:
            raise ValueError('FIXED_EXPORT_FILES_REQUIRED')
        seen.add(name)
        content = (directory / name).read_bytes()
        document = json.loads(content)
        if (hashlib.sha256(content).hexdigest() != entry['sha256'] or document != expected[name]
                or entry['id'] != document['id'] or entry['source_version_id'] != document['versionId']):
            raise ValueError('WORKFLOW_EXPORT_HASH_OR_VERSION_MISMATCH')
    return {document['id']: directory / name for name, document in expected.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/n8n-owner'
    try:
        print(json.dumps(export(root, args.output)))
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'existing_files_not_overwritten': True}))
        raise SystemExit(1)
